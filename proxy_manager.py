#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理管理器模块
Proxy Manager Module

支持HTTP/HTTPS/SOCKS4/SOCKS5/API代理
提供代理验证、轮换、文件导入等功能
"""

import json
import random
import requests
import socket
import socks
import threading
import time
from typing import Dict, List, Optional, Tuple
import re
from urllib.parse import urlparse
import concurrent.futures
from datetime import datetime
import logging
import asyncio
from .async_proxy_validator import AsyncProxyValidator
from .database_manager import DatabaseManager
from .config_manager import get_config_manager, ConfigManager
from .monitoring_logger import get_monitoring_system

class ProxyManager:
    """代理管理器"""
    
    def __init__(self, proxy_file: str = None, 
                 validation_timeout: int = None, 
                 validation_urls: List[str] = None,
                 max_validation_threads: int = None,
                 max_retries: int = None,
                 retry_delay: float = None,
                 api_proxies: List[str] = None,
                 health_check_interval: int = None,
                 max_error_count: int = None,
                 use_database: bool = None,
                 db_path: str = None,
                 config_manager: ConfigManager = None):
        self.proxies = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # 初始化配置管理器
        self.config_manager = config_manager or get_config_manager()
        
        # 从配置中获取设置，参数优先级高于配置文件
        validation_config = self.config_manager.get_validation_config()
        storage_config = self.config_manager.get_storage_config()
        health_config = self.config_manager.get('proxy_manager.health_check', {})
        
        # 代理验证配置
        self.validation_timeout = validation_timeout or validation_config.get('timeout', 10)
        self.validation_url = "http://httpbin.org/ip"
        self.backup_validation_urls = validation_urls or validation_config.get('urls', [
            "https://api.ipify.org?format=json",
            "http://ip-api.com/json",
            "https://httpbin.org/ip"
        ])
        self.max_validation_threads = max_validation_threads or validation_config.get('max_threads', 10)
        self.max_retries = max_retries or validation_config.get('max_retries', 3)
        self.retry_delay = retry_delay or validation_config.get('retry_delay', 1.0)
        
        # API代理配置
        self.api_proxies = {}  # 存储API代理配置
        self.api_endpoints = {}  # 存储API端点配置
        
        # 代理健康检查配置
        self.health_check_interval = health_check_interval or health_config.get('interval', 300)
        self.last_health_check = 0
        self.max_error_count = max_error_count or health_config.get('max_error_count', 5)
        
        # 数据库配置
        self.use_database = use_database if use_database is not None else storage_config.get('use_database', True)
        self.db_path = db_path or storage_config.get('db_path', 'data/proxies.db')
        self.proxy_file = proxy_file or storage_config.get('json_backup_path', 'data/proxies.json')
        
        # 初始化数据库管理器
        if self.use_database:
            try:
                self.db_manager = DatabaseManager(self.db_path)
            except Exception as e:
                self.logger.warning(f"数据库初始化失败，回退到文件存储: {e}")
                self.use_database = False
                self.db_manager = None
        else:
            self.db_manager = None
        
        # 初始化监控系统
        monitoring_config = self.config_manager.get_monitoring_config()
        self.monitoring = get_monitoring_system(monitoring_config)
        if self.monitoring and monitoring_config.get('enabled', False):
            self.monitoring.start()
            self.logger.info("监控系统已启动")
        
        # 加载已保存的代理
        self.load_proxies()
    
    def add_proxy(self, proxy_type: str, host: str, port: int, 
                  username: str = None, password: str = None) -> bool:
        """添加单个代理"""
        try:
            proxy = {
                'type': proxy_type.lower(),
                'host': host,
                'port': int(port),
                'username': username,
                'password': password,
                'valid': None,
                'last_used': None,
                'use_count': 0,
                'created_at': datetime.now().isoformat()
            }
            
            # 检查是否已存在
            if not self._proxy_exists(proxy):
                with self.lock:
                    self.proxies.append(proxy)
                
                # 保存到数据库或文件
                if self.use_database and self.db_manager:
                    try:
                        proxy_id = self.db_manager.add_proxy(proxy)
                        if proxy_id:
                            proxy['id'] = proxy_id
                            self.logger.debug(f"代理已保存到数据库，ID: {proxy_id}")
                        else:
                            self.logger.warning(f"保存代理到数据库失败: {host}:{port}")
                    except Exception as e:
                        self.logger.error(f"数据库操作失败: {e}")
                        # 回退到文件保存
                        self.save_proxies()
                else:
                    # 保存到文件
                    self.save_proxies()
                
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"添加代理失败: {str(e)}")
            return False
    
    def add_api_proxy(self, name: str, api_url: str, api_key: str = None, 
                      headers: Dict = None, params: Dict = None) -> bool:
        """添加API代理配置"""
        try:
            api_proxy = {
                'name': name,
                'api_url': api_url,
                'api_key': api_key,
                'headers': headers or {},
                'params': params or {},
                'type': 'api',
                'valid': None,
                'last_used': None,
                'use_count': 0,
                'created_at': datetime.now().isoformat()
            }
            
            # 添加默认headers
            if api_key:
                api_proxy['headers']['Authorization'] = f"Bearer {api_key}"
            
            with self.lock:
                self.api_proxies[name] = api_proxy
            
            self.save_proxies()
            self.logger.info(f"添加API代理成功: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加API代理失败: {str(e)}")
            return False
    
    def get_api_proxy_list(self) -> List[str]:
        """获取可用的代理列表"""
        try:
            # 这个方法可以通过API获取代理列表
            # 具体实现根据API提供商而定
            api_proxies = []
            
            for name, config in self.api_proxies.items():
                try:
                    response = requests.get(
                        config['api_url'],
                        headers=config['headers'],
                        params=config['params'],
                        timeout=self.validation_timeout
                    )
                    
                    if response.status_code == 200:
                        # 解析API响应获取代理列表
                        # 这里需要根据具体API格式调整
                        data = response.json()
                        
                        # 示例：假设API返回格式为 {"proxies": [{"host": "...", "port": ...}]}
                        if 'proxies' in data:
                            for proxy_data in data['proxies']:
                                proxy = {
                                    'type': 'http',  # 默认类型
                                    'host': proxy_data.get('host'),
                                    'port': proxy_data.get('port'),
                                    'username': proxy_data.get('username'),
                                    'password': proxy_data.get('password'),
                                    'api_source': name,
                                    'valid': True,
                                    'last_used': None,
                                    'use_count': 0,
                                    'created_at': datetime.now().isoformat()
                                }
                                api_proxies.append(proxy)
                        
                        config['last_used'] = datetime.now().isoformat()
                        config['use_count'] += 1
                        
                except Exception as e:
                    self.logger.error(f"获取API代理失败 {name}: {str(e)}")
                    continue
            
            return api_proxies
            
        except Exception as e:
            self.logger.error(f"获取API代理列表失败: {str(e)}")
            return []
    
    def _proxy_exists(self, new_proxy: Dict) -> bool:
        """检查代理是否已存在"""
        for proxy in self.proxies:
            if (proxy['host'] == new_proxy['host'] and 
                proxy['port'] == new_proxy['port'] and
                proxy['type'] == new_proxy['type']):
                return True
        return False
    
    def _is_duplicate_proxy(self, new_proxy: Dict) -> bool:
        """检查是否为重复代理"""
        for proxy in self.proxies:
            if (proxy.get('host') == new_proxy.get('host') and
                proxy.get('port') == new_proxy.get('port') and
                proxy.get('type') == new_proxy.get('type')):
                return True
        return False
    
    def import_from_file(self, file_path: str) -> int:
        """从文件导入代理"""
        try:
            imported_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # 优先使用新的TXT解析方法
                    proxy = self._parse_proxy_from_txt(line)
                    if proxy:
                        # 直接添加到代理列表，避免重复检查
                        if not self._is_duplicate_proxy(proxy):
                            self.proxies.append(proxy)
                            imported_count += 1
                    else:
                        # 如果新方法失败，尝试旧的解析方法
                        proxy_info = self._parse_proxy_line(line)
                        if proxy_info:
                            if self.add_proxy(**proxy_info):
                                imported_count += 1
                        else:
                            self.logger.warning(f"文件第{line_num}行格式错误: {line}")
            
            self.save_proxies()  # 保存导入的代理
            self.logger.info(f"从文件导入 {imported_count} 个代理")
            return imported_count
        
        except Exception as e:
            self.logger.error(f"导入代理文件失败: {str(e)}")
            raise
    
    def _parse_proxy_line(self, line: str) -> Optional[Dict]:
        """解析代理行"""
        try:
            # 支持多种格式
            # 格式1: type://host:port
            # 格式2: type://username:password@host:port
            # 格式3: host:port:username:password:type
            # 格式4: host:port
            
            # 先尝试URL格式
            if '://' in line:
                parsed = urlparse(line)
                if parsed.hostname and parsed.port:
                    return {
                        'proxy_type': parsed.scheme,
                        'host': parsed.hostname,
                        'port': parsed.port,
                        'username': parsed.username,
                        'password': parsed.password
                    }
            
            # 尝试冒号分隔格式
            parts = line.split(':')
            
            if len(parts) == 2:
                # host:port
                return {
                    'proxy_type': 'http',
                    'host': parts[0].strip(),
                    'port': int(parts[1].strip()),
                    'username': None,
                    'password': None
                }
            elif len(parts) == 4:
                # host:port:username:password
                return {
                    'proxy_type': 'http',
                    'host': parts[0].strip(),
                    'port': int(parts[1].strip()),
                    'username': parts[2].strip(),
                    'password': parts[3].strip()
                }
            elif len(parts) == 5:
                # host:port:username:password:type
                return {
                    'proxy_type': parts[4].strip().lower(),
                    'host': parts[0].strip(),
                    'port': int(parts[1].strip()),
                    'username': parts[2].strip(),
                    'password': parts[3].strip()
                }
            
            return None
        
        except Exception as e:
            self.logger.warning(f"解析代理行失败: {line} - {str(e)}")
            return None
    
    def validate_proxy(self, proxy: Dict) -> bool:
        """验证单个代理（带重试机制）"""
        start_time = time.time()
        proxy_str = f"{proxy['host']}:{proxy['port']}"
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(self.retry_delay)
                    self.logger.debug(f"代理验证重试 {attempt}/{self.max_retries}: {proxy_str}")
                
                proxy_dict = self._build_proxy_dict(proxy)
                
                # 根据代理类型选择验证方法
                if proxy['type'] in ['http', 'https']:
                    result = self._validate_http_proxy(proxy_dict)
                elif proxy['type'] in ['socks4', 'socks5']:
                    # 对于SOCKS代理，首先尝试改进的验证方法
                    result = self._validate_socks_proxy(proxy)
                    if not result:
                        # 如果改进的方法失败，尝试浏览器验证方法
                        result = self._validate_proxy_with_browser(proxy)
                else:
                    result = False
                
                if result:
                    # 验证成功，记录响应时间
                    response_time = time.time() - start_time
                    proxy['last_validated'] = datetime.now().isoformat()
                    proxy['validation_attempts'] = attempt + 1
                    proxy['response_time'] = response_time
                    
                    # 记录监控数据
                    if hasattr(self, 'monitoring') and self.monitoring:
                        self.monitoring.record_proxy_validation(proxy_str, True, response_time)
                    
                    return True
                    
            except Exception as e:
                self.logger.debug(f"代理验证异常 (尝试 {attempt + 1}): {proxy_str} - {str(e)}")
                if attempt == self.max_retries:
                    proxy['last_error'] = str(e)
                    proxy['last_validated'] = datetime.now().isoformat()
        
        # 验证失败
        response_time = time.time() - start_time
        if hasattr(self, 'monitoring') and self.monitoring:
            error_msg = proxy.get('last_error', 'Unknown error')
            self.monitoring.record_proxy_validation(proxy_str, False, response_time, error_msg)
        
        return False
    
    def mark_proxy_as_validated(self, proxy_host: str, proxy_port: int, is_valid: bool = True):
        """手动标记代理为已验证（用于已知可用的代理）"""
        try:
            for proxy in self.proxies:
                if proxy.get('host') == proxy_host and proxy.get('port') == proxy_port:
                    proxy['validated'] = is_valid
                    proxy['last_check'] = time.time()
                    if is_valid:
                        proxy['response_time'] = 1.0  # 设置一个合理的响应时间
                        self.logger.info(f"手动标记代理为可用: {proxy_host}:{proxy_port}")
                    else:
                        self.logger.info(f"手动标记代理为不可用: {proxy_host}:{proxy_port}")
                    
                    # 保存更新
                    self.save_proxies()
                    return True
            
            self.logger.warning(f"未找到指定的代理: {proxy_host}:{proxy_port}")
            return False
            
        except Exception as e:
            self.logger.error(f"标记代理状态失败: {str(e)}")
            return False
    
    def _validate_http_proxy(self, proxy_dict: Dict) -> bool:
        """验证HTTP代理（使用多个验证URL）"""
        # 尝试主要验证URL
        urls_to_try = [self.validation_url] + self.backup_validation_urls
        
        for url in urls_to_try:
            try:
                start_time = time.time()
                response = requests.get(
                    url,
                    proxies=proxy_dict,
                    timeout=self.validation_timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate'
                    },
                    allow_redirects=True,
                    verify=False  # 忽略SSL证书验证
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    # 检查响应内容
                    try:
                        if 'json' in response.headers.get('content-type', '').lower():
                            data = response.json()
                            # 检查是否包含IP信息
                            if any(key in data for key in ['origin', 'ip', 'query']):
                                self.logger.debug(f"HTTP代理验证成功，响应时间: {response_time:.2f}s")
                                return True
                        else:
                            # 非JSON响应，检查内容长度
                            if len(response.text) > 10:
                                self.logger.debug(f"HTTP代理验证成功，响应时间: {response_time:.2f}s")
                                return True
                    except:
                        # JSON解析失败，但状态码200，认为代理可用
                        if len(response.text) > 0:
                            self.logger.debug(f"HTTP代理验证成功（非JSON响应），响应时间: {response_time:.2f}s")
                            return True
                
            except requests.exceptions.Timeout:
                self.logger.debug(f"HTTP代理验证超时: {url}")
                continue
            except requests.exceptions.ProxyError:
                self.logger.debug(f"HTTP代理连接错误: {url}")
                continue
            except requests.exceptions.ConnectionError:
                self.logger.debug(f"HTTP代理连接失败: {url}")
                continue
            except Exception as e:
                self.logger.debug(f"HTTP代理验证异常: {url} - {str(e)}")
                continue
        
        return False
    
    def _validate_socks_proxy(self, proxy: Dict) -> bool:
        """验证SOCKS代理"""
        try:
            # 方法1: 使用requests通过SOCKS代理发送HTTP请求
            try:
                import requests
                
                if proxy.get('username') and proxy.get('password'):
                    proxy_url = f"socks5://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
                else:
                    proxy_url = f"socks5://{proxy['host']}:{proxy['port']}"
                
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                
                # 尝试发送HTTP请求
                response = requests.get(
                    'http://httpbin.org/ip',
                    proxies=proxies,
                    timeout=self.validation_timeout,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
                if response.status_code == 200:
                    return True
                
            except Exception:
                pass
            
            # 方法2: 备用socket连接测试（使用更宽松的目标）
            try:
                sock = socks.socksocket()
                
                if proxy['type'] == 'socks4':
                    sock.set_proxy(socks.SOCKS4, proxy['host'], proxy['port'])
                else:  # socks5
                    sock.set_proxy(socks.SOCKS5, proxy['host'], proxy['port'], 
                                 username=proxy.get('username'), 
                                 password=proxy.get('password'))
                
                sock.settimeout(self.validation_timeout)
                
                # 尝试多个目标，增加成功率
                test_targets = [
                    ('google.com', 443),
                    ('youtube.com', 443), 
                    ('httpbin.org', 443),
                    ('8.8.8.8', 53)
                ]
                
                for target_host, target_port in test_targets:
                    try:
                        sock.connect((target_host, target_port))
                        sock.close()
                        return True
                    except:
                        continue
                
                sock.close()
                
            except Exception:
                pass
            
            return False
        
        except Exception:
            return False
    
    def _validate_proxy_with_browser(self, proxy: Dict) -> bool:
        """使用浏览器验证代理（最后的备用方法）"""
        try:
            # 导入浏览器自动化模块
            from .browser_automation import BrowserAutomation
            from .fingerprint_engine import FingerprintEngine
            
            browser_automation = BrowserAutomation()
            fingerprint_engine = FingerprintEngine()
            
            # 生成简单的设备指纹
            fingerprint = fingerprint_engine.generate_fingerprint()
            
            # 创建浏览器实例（使用代理）
            config = {
                'headless': True,  # 无头模式，更快
                'stealth': True
            }
            
            driver = browser_automation.create_browser(
                proxy=proxy,
                fingerprint=fingerprint,
                config=config
            )
            
            if not driver:
                return False
            
            try:
                # 尝试访问一个简单的页面
                driver.get('http://httpbin.org/ip')
                
                # 等待页面加载
                import time
                time.sleep(3)
                
                # 检查页面是否加载成功
                page_source = driver.page_source
                if 'origin' in page_source or 'ip' in page_source.lower():
                    return True
                
                return False
                
            finally:
                try:
                    driver.quit()
                except:
                    pass
                    
        except Exception as e:
            self.logger.debug(f"浏览器验证代理失败: {str(e)}")
            return False
    
    def _build_proxy_dict(self, proxy: Dict) -> Dict:
        """构建代理字典"""
        if proxy.get('username') and proxy.get('password'):
            proxy_url = f"{proxy['type']}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        else:
            proxy_url = f"{proxy['type']}://{proxy['host']}:{proxy['port']}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def validate_all_proxies(self) -> Tuple[int, int]:
        """验证所有代理（同步版本，保持向后兼容）"""
        valid_count = 0
        invalid_count = 0
        
        def validate_single(proxy):
            is_valid = self.validate_proxy(proxy)
            proxy['valid'] = is_valid
            proxy['validated_at'] = datetime.now().isoformat()
            return is_valid
        
        # 使用线程池并发验证
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_validation_threads) as executor:
            futures = {executor.submit(validate_single, proxy): proxy for proxy in self.proxies}
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    is_valid = future.result()
                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                except Exception as e:
                    invalid_count += 1
                    self.logger.error(f"代理验证异常: {str(e)}")
        
        # 保存验证结果
        self.save_proxies()
        
        self.logger.info(f"代理验证完成 - 有效: {valid_count}, 无效: {invalid_count}")
        return valid_count, invalid_count
    
    async def validate_all_proxies_async(self, max_concurrent: int = 50) -> Tuple[int, int]:
        """异步验证所有代理（高性能版本）"""
        if not self.proxies:
            return 0, 0
        
        self.logger.info(f"开始异步验证 {len(self.proxies)} 个代理")
        start_time = time.time()
        
        # 使用异步验证器
        async with AsyncProxyValidator(max_concurrent=max_concurrent, timeout=self.validation_timeout) as validator:
            validated_proxies = await validator.validate_proxies_async(self.proxies.copy())
            
            # 更新代理状态
            with self.lock:
                for i, validated_proxy in enumerate(validated_proxies):
                    if i < len(self.proxies):
                        self.proxies[i].update(validated_proxy)
            
            # 获取统计信息
            stats = await validator.get_validation_stats(validated_proxies)
            
        # 保存验证结果
        self.save_proxies()
        
        end_time = time.time()
        valid_count = stats.get('valid', 0)
        invalid_count = stats.get('invalid', 0)
        
        self.logger.info(
            f"异步验证完成 - 有效: {valid_count}, 无效: {invalid_count}, "
            f"成功率: {stats.get('success_rate', 0)}%, "
            f"平均响应时间: {stats.get('average_response_time', 0)}s, "
            f"总耗时: {end_time - start_time:.2f}s"
        )
        
        return valid_count, invalid_count
    
    def validate_all_proxies_sync_wrapper(self, use_async: bool = True, max_concurrent: int = 50) -> Tuple[int, int]:
        """同步包装器，可选择使用异步验证"""
        if use_async:
            try:
                # 尝试使用异步验证
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.validate_all_proxies_async(max_concurrent))
                finally:
                    loop.close()
            except Exception as e:
                self.logger.warning(f"异步验证失败，回退到同步验证: {e}")
                return self.validate_all_proxies()
        else:
            return self.validate_all_proxies()
    
    def get_valid_proxies(self) -> List[Dict]:
        """获取有效代理列表"""
        return [proxy for proxy in self.proxies if proxy.get('valid') == True]
    
    def get_next_proxy(self) -> Optional[Dict]:
        """获取下一个可用代理（轮换，带健康检查）"""
        valid_proxies = self.get_valid_proxies()
        
        if not valid_proxies:
            return None
        
        old_proxy = None
        if hasattr(self, '_last_used_proxy'):
            old_proxy = self._last_used_proxy
        
        with self.lock:
            # 尝试获取健康的代理，最多尝试所有代理一轮
            attempts = 0
            max_attempts = len(valid_proxies)
            
            while attempts < max_attempts:
                if self.current_index >= len(valid_proxies):
                    self.current_index = 0
                
                proxy = valid_proxies[self.current_index]
                self.current_index += 1
                attempts += 1
                
                # 检查代理健康状态
                if self._is_proxy_healthy(proxy):
                    # 更新使用记录
                    proxy['last_used'] = datetime.now().isoformat()
                    proxy['use_count'] = proxy.get('use_count', 0) + 1
                    self.logger.debug(f"获取健康代理: {proxy['host']}:{proxy['port']}")
                    
                    # 记录代理轮换
                    if hasattr(self, 'monitoring') and self.monitoring and old_proxy:
                        old_proxy_str = f"{old_proxy['host']}:{old_proxy['port']}"
                        new_proxy_str = f"{proxy['host']}:{proxy['port']}"
                        if old_proxy_str != new_proxy_str:
                            self.monitoring.record_proxy_rotation(old_proxy_str, new_proxy_str, "轮换到健康代理")
                    
                    self._last_used_proxy = proxy
                    return proxy
                else:
                    self.logger.debug(f"跳过不健康代理: {proxy['host']}:{proxy['port']}")
            
            # 如果没有健康的代理，返回第一个可用代理
            if valid_proxies:
                proxy = valid_proxies[0]
                proxy['last_used'] = datetime.now().isoformat()
                proxy['use_count'] = proxy.get('use_count', 0) + 1
                self.logger.warning(f"没有健康代理，返回第一个可用代理: {proxy['host']}:{proxy['port']}")
                
                # 记录代理轮换
                if hasattr(self, 'monitoring') and self.monitoring and old_proxy:
                    old_proxy_str = f"{old_proxy['host']}:{old_proxy['port']}"
                    new_proxy_str = f"{proxy['host']}:{proxy['port']}"
                    if old_proxy_str != new_proxy_str:
                        self.monitoring.record_proxy_rotation(old_proxy_str, new_proxy_str, "回退到第一个可用代理")
                
                self._last_used_proxy = proxy
                return proxy
        
        return None
    
    def get_random_proxy(self) -> Optional[Dict]:
        """随机获取一个有效代理"""
        valid_proxies = self.get_valid_proxies()
        
        if not valid_proxies:
            return None
        
        proxy = random.choice(valid_proxies)
        
        # 更新使用记录
        with self.lock:
            proxy['last_used'] = datetime.now().isoformat()
            proxy['use_count'] = proxy.get('use_count', 0) + 1
        
        return proxy
    
    def remove_invalid_proxies(self) -> int:
        """移除无效代理"""
        with self.lock:
            original_count = len(self.proxies)
            self.proxies = [proxy for proxy in self.proxies if proxy.get('valid') != False]
            removed_count = original_count - len(self.proxies)
        
        self.save_proxies()
        self.logger.info(f"移除了 {removed_count} 个无效代理")
        return removed_count
    
    def get_all_proxies(self) -> List[Dict]:
        """获取所有代理"""
        return self.proxies.copy()
    
    def clear_all_proxies(self):
        """清空所有代理"""
        with self.lock:
            self.proxies.clear()
            self.current_index = 0
        
        self.save_proxies()
        self.logger.info("已清空所有代理")
    
    def save_proxies(self):
        """保存代理到数据库或文件"""
        try:
            if self.use_database and self.db_manager:
                # 保存到数据库
                try:
                    self.db_manager.save_proxies(self.proxies)
                    self.logger.debug(f"成功保存 {len(self.proxies)} 个代理到数据库")
                except Exception as e:
                    self.logger.error(f"保存代理到数据库失败: {e}")
                    # 数据库保存失败时，回退到文件保存
                    self._save_to_files()
            else:
                # 保存到文件
                self._save_to_files()
        
        except Exception as e:
            self.logger.error(f"保存代理失败: {str(e)}")
    
    def _save_to_files(self):
        """保存代理到文件"""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            
            # 保存为TXT格式（新的默认格式）
            self._save_proxies_txt()
            
            # 同时保存JSON格式作为备份
            with open("data/proxies.json", 'w', encoding='utf-8') as f:
                json.dump(self.proxies, f, ensure_ascii=False, indent=2)
            
            # 保存API代理配置
            with open("data/api_proxies.json", 'w', encoding='utf-8') as f:
                json.dump(self.api_proxies, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.logger.error(f"保存代理到文件失败: {str(e)}")
    
    def _save_proxies_txt(self):
        """保存代理到TXT文件"""
        try:
            with open("data/proxies.txt", 'w', encoding='utf-8') as f:
                f.write("# 代理列表 - 格式说明:\n")
                f.write("# HTTP/HTTPS: http://ip:port 或 http://username:password@ip:port\n")
                f.write("# SOCKS4: socks4://ip:port\n")
                f.write("# SOCKS5: socks5://ip:port 或 socks5://username:password@ip:port\n")
                f.write("# 每行一个代理\n")
                f.write("\n")
                
                for proxy in self.proxies:
                    proxy_line = self._format_proxy_to_txt(proxy)
                    if proxy_line:
                        f.write(proxy_line + "\n")
                        
            self.logger.info(f"成功保存 {len(self.proxies)} 个代理到 TXT 文件")
        except Exception as e:
            self.logger.error(f"保存TXT代理文件失败: {str(e)}")
    
    def _format_proxy_to_txt(self, proxy: Dict) -> str:
        """将代理对象格式化为TXT行"""
        try:
            proxy_type = proxy.get('type', 'http').lower()
            host = proxy.get('host', '')
            port = proxy.get('port', '')
            username = proxy.get('username')
            password = proxy.get('password')
            
            if not host or not port:
                return ""
            
            if username and password:
                return f"{proxy_type}://{username}:{password}@{host}:{port}"
            else:
                return f"{proxy_type}://{host}:{port}"
                
        except Exception as e:
            self.logger.error(f"格式化代理到TXT失败: {str(e)}")
            return ""
    
    def load_proxies(self):
        """从数据库或文件加载代理"""
        if self.use_database and self.db_manager:
            try:
                self.proxies = self.db_manager.get_all_proxies()
                self.logger.info(f"从数据库加载了 {len(self.proxies)} 个代理")
                
                # 如果数据库为空且存在JSON文件，则迁移数据
                if not self.proxies and os.path.exists(self.proxy_file):
                    migrated_count = self.db_manager.migrate_from_json(self.proxy_file)
                    if migrated_count > 0:
                        self.proxies = self.db_manager.get_all_proxies()
                        self.logger.info(f"从JSON文件迁移了 {migrated_count} 个代理到数据库")
                        
                        # 备份原JSON文件
                        backup_file = self.proxy_file + '.backup'
                        try:
                            import os
                            os.rename(self.proxy_file, backup_file)
                            self.logger.info(f"原JSON文件已备份为: {backup_file}")
                        except Exception as e:
                            self.logger.warning(f"备份原JSON文件失败: {e}")
                            
            except Exception as e:
                self.logger.error(f"从数据库加载代理失败: {e}")
                self.proxies = []
        else:
            # 使用文件存储
            # 优先尝试加载TXT格式
            if self._load_proxies_txt():
                self.logger.info(f"从TXT文件加载了 {len(self.proxies)} 个代理")
            else:
                # 如果TXT文件不存在或加载失败，尝试JSON格式
                try:
                    with open("data/proxies.json", 'r', encoding='utf-8') as f:
                        self.proxies = json.load(f)
                    
                    self.logger.info(f"从JSON文件加载了 {len(self.proxies)} 个代理")
                
                except FileNotFoundError:
                    self.proxies = []
                    self.logger.info("代理文件不存在，使用空列表")
                except Exception as e:
                    self.proxies = []
                    self.logger.error(f"加载代理失败: {str(e)}")
        
        try:
            # 加载API代理配置
            with open("data/api_proxies.json", 'r', encoding='utf-8') as f:
                self.api_proxies = json.load(f)
            
            self.logger.info(f"加载了 {len(self.api_proxies)} 个API代理配置")
        
        except FileNotFoundError:
            self.api_proxies = {}
            self.logger.info("API代理文件不存在，使用空字典")
        
        except Exception as e:
            self.api_proxies = {}
            self.logger.error(f"加载API代理失败: {str(e)}")
    
    def _load_proxies_txt(self) -> bool:
        """从TXT文件加载代理"""
        try:
            import os
            if not os.path.exists("data/proxies.txt"):
                return False
                
            self.proxies = []
            with open("data/proxies.txt", 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释行
                    if not line or line.startswith('#'):
                        continue
                    
                    proxy = self._parse_proxy_from_txt(line)
                    if proxy:
                        self.proxies.append(proxy)
                    else:
                        self.logger.warning(f"TXT文件第{line_num}行格式错误: {line}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"从TXT文件加载代理失败: {str(e)}")
            return False
    
    def _parse_proxy_from_txt(self, line: str) -> Optional[Dict]:
        """从TXT行解析代理"""
        try:
            import re
            
            line = line.strip()
            
            # 格式1: protocol://[username:password@]host:port
            pattern1 = r'^(https?|socks[45])://(?:([^:]+):([^@]+)@)?([^:]+):(\d+)$'
            match = re.match(pattern1, line)
            
            if match:
                protocol, username, password, host, port = match.groups()
                return {
                    'type': protocol.lower(),
                    'host': host,
                    'port': int(port),
                    'username': username if username else None,
                    'password': password if password else None,
                    'validated': False,
                    'last_check': None,
                    'response_time': None
                }
            
            # 格式2: host:port (默认为HTTP代理)
            pattern2 = r'^([^:]+):(\d+)$'
            match = re.match(pattern2, line)
            
            if match:
                host, port = match.groups()
                return {
                    'type': 'http',
                    'host': host,
                    'port': int(port),
                    'username': None,
                    'password': None,
                    'validated': False,
                    'last_check': None,
                    'response_time': None
                }
            
            # 格式3: host:port:username:password (默认为HTTP代理)
            pattern3 = r'^([^:]+):(\d+):([^:]+):([^:]+)$'
            match = re.match(pattern3, line)
            
            if match:
                host, port, username, password = match.groups()
                return {
                    'type': 'http',
                    'host': host,
                    'port': int(port),
                    'username': username,
                    'password': password,
                    'validated': False,
                    'last_check': None,
                    'response_time': None
                }
            
            # 格式4: host:port:username:password:type
            pattern4 = r'^([^:]+):(\d+):([^:]+):([^:]+):(https?|socks[45])$'
            match = re.match(pattern4, line)
            
            if match:
                host, port, username, password, proxy_type = match.groups()
                return {
                    'type': proxy_type.lower(),
                    'host': host,
                    'port': int(port),
                    'username': username,
                    'password': password,
                    'validated': False,
                    'last_check': None,
                    'response_time': None
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"解析TXT代理行失败: {line} - {str(e)}")
            return None
    
    def get_proxy_stats(self) -> Dict:
        """获取代理统计信息"""
        if self.use_database and self.db_manager:
            try:
                # 从数据库获取统计信息
                stats = self.db_manager.get_proxy_stats()
                
                # 添加健康代理统计（需要从内存中计算）
                if self.proxies:
                    healthy = sum(1 for p in self.proxies if p.get('valid') == True and self._is_proxy_healthy(p))
                    stats['healthy'] = healthy
                    
                    # 更新按类型统计中的健康代理数
                    for proxy_type in stats.get('by_type', {}):
                        healthy_of_type = sum(1 for p in self.proxies 
                                            if p.get('type') == proxy_type and p.get('valid') == True and self._is_proxy_healthy(p))
                        stats['by_type'][proxy_type]['healthy'] = healthy_of_type
                else:
                    stats['healthy'] = 0
                
                return stats
            except Exception as e:
                self.logger.error(f"从数据库获取统计信息失败: {e}")
                # 回退到内存统计
        
        # 内存统计（文件存储或数据库失败时的回退）
        total = len(self.proxies)
        valid = sum(1 for p in self.proxies if p.get('valid') == True)
        invalid = sum(1 for p in self.proxies if p.get('valid') == False)
        unvalidated = total - valid - invalid
        healthy = sum(1 for p in self.proxies if p.get('valid') == True and self._is_proxy_healthy(p))
        
        # 按类型统计
        type_stats = {}
        for proxy in self.proxies:
            proxy_type = proxy.get('type', 'unknown')
            if proxy_type not in type_stats:
                type_stats[proxy_type] = {'total': 0, 'valid': 0, 'invalid': 0, 'healthy': 0}
            type_stats[proxy_type]['total'] += 1
            if proxy.get('valid') == True:
                type_stats[proxy_type]['valid'] += 1
                if self._is_proxy_healthy(proxy):
                    type_stats[proxy_type]['healthy'] += 1
            elif proxy.get('valid') == False:
                type_stats[proxy_type]['invalid'] += 1
        
        stats = {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'unvalidated': unvalidated,
            'healthy': healthy,
            'by_type': type_stats
        }
        
        # 更新监控系统的代理统计
        if hasattr(self, 'monitoring') and self.monitoring:
            # 计算平均响应时间
            response_times = [p.get('response_time', 0) for p in self.proxies if p.get('response_time')]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            self.monitoring.update_proxy_stats(total, valid, invalid, avg_response_time)
        
        return stats
    
    def export_valid_proxies(self, file_path: str) -> int:
        """导出有效代理到文件"""
        try:
            valid_proxies = self.get_valid_proxies()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for proxy in valid_proxies:
                    if proxy.get('username') and proxy.get('password'):
                        line = f"{proxy['type']}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}\n"
                    else:
                        line = f"{proxy['type']}://{proxy['host']}:{proxy['port']}\n"
                    
                    f.write(line)
            
            self.logger.info(f"导出 {len(valid_proxies)} 个有效代理到 {file_path}")
            return len(valid_proxies)
        
        except Exception as e:
            self.logger.error(f"导出代理失败: {str(e)}")
            raise

    def validate_proxy_with_type_detection(self, proxy: Dict) -> Dict:
        """验证代理并尝试检测正确的代理类型"""
        result = {
            'original_proxy': proxy.copy(),
            'valid': False,
            'detected_type': None,
            'response_time': None,
            'error': None
        }
        
        # 可能的代理类型
        proxy_types = ['http', 'https', 'socks4', 'socks5']
        
        # 如果代理已经有明确的类型，优先测试该类型
        if proxy.get('type') and proxy['type'] in proxy_types:
            proxy_types.insert(0, proxy['type'])
            proxy_types = list(dict.fromkeys(proxy_types))  # 去重保持顺序
        
        for proxy_type in proxy_types:
            try:
                # 创建测试用的代理配置
                test_proxy = proxy.copy()
                test_proxy['type'] = proxy_type
                
                start_time = time.time()
                is_valid = self.validate_proxy(test_proxy)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                
                if is_valid:
                    result['valid'] = True
                    result['detected_type'] = proxy_type
                    result['response_time'] = response_time
                    result['working_proxy'] = test_proxy
                    return result
                    
            except Exception as e:
                if result['error'] is None:
                    result['error'] = str(e)
                continue
        
        # 如果所有类型都无效，记录响应时间
        if result['response_time'] is None:
            result['response_time'] = 0
        
        return result
    
    def _is_proxy_healthy(self, proxy: Dict) -> bool:
        """检查代理健康状态"""
        if not proxy.get('valid'):
            return False
        
        # 检查最近是否有错误
        if proxy.get('last_error'):
            last_error_time = proxy.get('last_error_time')
            if last_error_time:
                try:
                    error_time = datetime.fromisoformat(last_error_time)
                    # 如果最近5分钟内有错误，认为不健康
                    if (datetime.now() - error_time).total_seconds() < 300:
                        return False
                except:
                    pass
        
        # 检查使用频率（避免过度使用同一代理）
        last_used = proxy.get('last_used')
        if last_used:
            try:
                used_time = datetime.fromisoformat(last_used)
                # 如果刚刚使用过（30秒内），优先选择其他代理
                if (datetime.now() - used_time).total_seconds() < 30:
                    return False
            except:
                pass
        
        return True
    
    def mark_proxy_error(self, proxy_host: str, proxy_port: int, error_msg: str = None):
        """标记代理错误"""
        with self.lock:
            for proxy in self.proxies:
                if proxy['host'] == proxy_host and proxy['port'] == proxy_port:
                    proxy['last_error'] = error_msg or "连接失败"
                    proxy['last_error_time'] = datetime.now().isoformat()
                    proxy['error_count'] = proxy.get('error_count', 0) + 1
                    
                    # 如果错误次数过多，标记为无效
                    if proxy.get('error_count', 0) >= 3:
                        proxy['valid'] = False
                        self.logger.warning(f"代理错误次数过多，标记为无效: {proxy_host}:{proxy_port}")
                    break
        
        self.save_proxies()
    
    def cleanup_old_errors(self):
        """清理旧的错误记录"""
        with self.lock:
            current_time = datetime.now()
            for proxy in self.proxies:
                last_error_time = proxy.get('last_error_time')
                if last_error_time:
                    try:
                        error_time = datetime.fromisoformat(last_error_time)
                        # 清理24小时前的错误记录
                        if (current_time - error_time).total_seconds() > 86400:
                            proxy.pop('last_error', None)
                            proxy.pop('last_error_time', None)
                            proxy['error_count'] = 0
                    except:
                        pass
        
        self.save_proxies()

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建代理管理器
    pm = ProxyManager()
    
    # 添加测试代理
    pm.add_proxy('http', '127.0.0.1', 8080)
    pm.add_proxy('socks5', '127.0.0.1', 1080, 'user', 'pass')
    
    # 获取统计
    stats = pm.get_proxy_stats()
    print(f"代理统计: {stats}")
    
    # 获取代理
    proxy = pm.get_next_proxy()
    print(f"获取到代理: {proxy}")
