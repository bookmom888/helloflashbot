import asyncio
import aiohttp
import time
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import socket
import socks
from concurrent.futures import ThreadPoolExecutor

class AsyncProxyValidator:
    """异步代理验证器"""
    
    def __init__(self, max_concurrent: int = 50, timeout: int = 15):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # 验证URL列表
        self.test_urls = [
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "https://icanhazip.com",
            "https://api.myip.com"
        ]
        
        # SOCKS测试目标
        self.socks_targets = [
            ("google.com", 443),
            ("youtube.com", 443),
            ("httpbin.org", 443),
            ("8.8.8.8", 53)
        ]
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def validate_proxies_async(self, proxies: List[Dict]) -> List[Dict]:
        """异步批量验证代理"""
        if not proxies:
            return []
        
        self.logger.info(f"开始异步验证 {len(proxies)} 个代理")
        start_time = time.time()
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 创建验证任务
        tasks = []
        for proxy in proxies:
            task = self._validate_single_proxy_async(proxy, semaphore)
            tasks.append(task)
        
        # 执行所有验证任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        validated_proxies = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"代理验证异常: {proxies[i]} - {result}")
                proxy = proxies[i].copy()
                proxy.update({
                    'valid': False,
                    'last_error': str(result),
                    'last_validated': datetime.now().isoformat(),
                    'response_time': None
                })
                validated_proxies.append(proxy)
            else:
                validated_proxies.append(result)
        
        end_time = time.time()
        valid_count = sum(1 for p in validated_proxies if p.get('valid'))
        
        self.logger.info(
            f"异步验证完成: {valid_count}/{len(proxies)} 个代理有效, "
            f"耗时: {end_time - start_time:.2f}秒"
        )
        
        return validated_proxies
    
    async def _validate_single_proxy_async(self, proxy: Dict, semaphore: asyncio.Semaphore) -> Dict:
        """异步验证单个代理"""
        async with semaphore:
            proxy_copy = proxy.copy()
            
            try:
                if proxy.get('type') in ['http', 'https']:
                    result = await self._validate_http_proxy_async(proxy)
                elif proxy.get('type') in ['socks4', 'socks5']:
                    result = await self._validate_socks_proxy_async(proxy)
                else:
                    # 尝试自动检测代理类型
                    result = await self._auto_detect_and_validate_async(proxy)
                
                proxy_copy.update(result)
                return proxy_copy
                
            except Exception as e:
                self.logger.error(f"验证代理 {proxy.get('host')}:{proxy.get('port')} 时发生异常: {e}")
                proxy_copy.update({
                    'valid': False,
                    'last_error': str(e),
                    'last_validated': datetime.now().isoformat(),
                    'response_time': None
                })
                return proxy_copy
    
    async def _validate_http_proxy_async(self, proxy: Dict) -> Dict:
        """异步验证HTTP代理"""
        host = proxy.get('host')
        port = proxy.get('port')
        username = proxy.get('username')
        password = proxy.get('password')
        
        # 构建代理URL
        if username and password:
            proxy_url = f"http://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"http://{host}:{port}"
        
        # 尝试多个测试URL
        for test_url in self.test_urls:
            try:
                start_time = time.time()
                
                async with self.session.get(
                    test_url,
                    proxy=proxy_url,
                    allow_redirects=True,
                    ssl=False  # 忽略SSL证书验证
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # 验证响应内容
                        if self._is_valid_response(content, test_url):
                            return {
                                'valid': True,
                                'last_validated': datetime.now().isoformat(),
                                'response_time': round(response_time, 3),
                                'last_error': None,
                                'test_url': test_url
                            }
            
            except Exception as e:
                self.logger.debug(f"HTTP代理 {host}:{port} 在URL {test_url} 验证失败: {e}")
                continue
        
        return {
            'valid': False,
            'last_validated': datetime.now().isoformat(),
            'last_error': f"所有测试URL验证失败",
            'response_time': None
        }
    
    async def _validate_socks_proxy_async(self, proxy: Dict) -> Dict:
        """异步验证SOCKS代理"""
        host = proxy.get('host')
        port = proxy.get('port')
        username = proxy.get('username')
        password = proxy.get('password')
        proxy_type = proxy.get('type', 'socks5')
        
        # 首先尝试HTTP请求验证
        try:
            proxy_url = f"{proxy_type}://{host}:{port}"
            if username and password:
                proxy_url = f"{proxy_type}://{username}:{password}@{host}:{port}"
            
            start_time = time.time()
            async with self.session.get(
                self.test_urls[0],
                proxy=proxy_url,
                allow_redirects=True
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    content = await response.text()
                    if self._is_valid_response(content, self.test_urls[0]):
                        return {
                            'valid': True,
                            'last_validated': datetime.now().isoformat(),
                            'response_time': round(response_time, 3),
                            'last_error': None,
                            'test_method': 'http_request'
                        }
        
        except Exception as e:
            self.logger.debug(f"SOCKS代理 {host}:{port} HTTP请求验证失败: {e}")
        
        # 如果HTTP请求失败，尝试socket连接验证
        try:
            result = await self._validate_socks_socket_async(proxy)
            return result
        except Exception as e:
            return {
                'valid': False,
                'last_validated': datetime.now().isoformat(),
                'last_error': str(e),
                'response_time': None
            }
    
    async def _validate_socks_socket_async(self, proxy: Dict) -> Dict:
        """异步验证SOCKS代理的socket连接"""
        host = proxy.get('host')
        port = proxy.get('port')
        username = proxy.get('username')
        password = proxy.get('password')
        proxy_type = proxy.get('type', 'socks5')
        
        # 在线程池中执行socket操作
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                start_time = time.time()
                
                # 在线程中执行socket连接
                success = await loop.run_in_executor(
                    executor,
                    self._test_socks_connection,
                    host, port, username, password, proxy_type
                )
                
                response_time = time.time() - start_time
                
                if success:
                    return {
                        'valid': True,
                        'last_validated': datetime.now().isoformat(),
                        'response_time': round(response_time, 3),
                        'last_error': None,
                        'test_method': 'socket_connection'
                    }
                else:
                    return {
                        'valid': False,
                        'last_validated': datetime.now().isoformat(),
                        'last_error': 'Socket连接失败',
                        'response_time': None
                    }
            
            except Exception as e:
                return {
                    'valid': False,
                    'last_validated': datetime.now().isoformat(),
                    'last_error': str(e),
                    'response_time': None
                }
    
    def _test_socks_connection(self, host: str, port: int, username: str, password: str, proxy_type: str) -> bool:
        """测试SOCKS连接（在线程中执行）"""
        try:
            # 设置SOCKS代理类型
            if proxy_type == 'socks4':
                socks_type = socks.SOCKS4
            else:
                socks_type = socks.SOCKS5
            
            # 测试多个目标
            for target_host, target_port in self.socks_targets:
                try:
                    sock = socks.socksocket()
                    sock.set_proxy(socks_type, host, port, username=username, password=password)
                    sock.settimeout(self.timeout)
                    
                    # 尝试连接
                    sock.connect((target_host, target_port))
                    sock.close()
                    return True
                
                except Exception:
                    continue
            
            return False
        
        except Exception:
            return False
    
    async def _auto_detect_and_validate_async(self, proxy: Dict) -> Dict:
        """自动检测代理类型并验证"""
        host = proxy.get('host')
        port = proxy.get('port')
        
        # 尝试不同的代理类型
        proxy_types = ['http', 'socks5', 'socks4']
        
        for ptype in proxy_types:
            try:
                test_proxy = proxy.copy()
                test_proxy['type'] = ptype
                
                if ptype == 'http':
                    result = await self._validate_http_proxy_async(test_proxy)
                else:
                    result = await self._validate_socks_proxy_async(test_proxy)
                
                if result.get('valid'):
                    result['detected_type'] = ptype
                    return result
            
            except Exception as e:
                self.logger.debug(f"自动检测 {host}:{port} 为 {ptype} 类型失败: {e}")
                continue
        
        return {
            'valid': False,
            'last_validated': datetime.now().isoformat(),
            'last_error': '无法检测代理类型或所有类型验证失败',
            'response_time': None
        }
    
    def _is_valid_response(self, content: str, test_url: str) -> bool:
        """验证响应内容是否有效"""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # 检查是否包含IP地址信息
        if 'ip' in test_url.lower():
            # 简单的IP地址格式检查
            import re
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            if re.search(ip_pattern, content):
                return True
        
        # 检查常见的错误页面标识
        error_indicators = [
            'error', 'forbidden', 'access denied', 'not found',
            'timeout', 'connection refused', 'proxy error'
        ]
        
        for indicator in error_indicators:
            if indicator in content_lower:
                return False
        
        # 如果内容长度合理且不包含错误标识，认为是有效的
        return len(content.strip()) > 10
    
    async def get_validation_stats(self, results: List[Dict]) -> Dict:
        """获取验证统计信息"""
        if not results:
            return {}
        
        total = len(results)
        valid = sum(1 for r in results if r.get('valid'))
        invalid = total - valid
        
        # 计算平均响应时间
        response_times = [r.get('response_time') for r in results if r.get('response_time')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 按类型统计
        type_stats = {}
        for result in results:
            ptype = result.get('type', 'unknown')
            if ptype not in type_stats:
                type_stats[ptype] = {'total': 0, 'valid': 0}
            type_stats[ptype]['total'] += 1
            if result.get('valid'):
                type_stats[ptype]['valid'] += 1
        
        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'success_rate': round(valid / total * 100, 2) if total > 0 else 0,
            'average_response_time': round(avg_response_time, 3),
            'by_type': type_stats
        }

# 使用示例
async def main():
    """使用示例"""
    proxies = [
        {'host': '127.0.0.1', 'port': 8080, 'type': 'http'},
        {'host': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
    ]
    
    async with AsyncProxyValidator(max_concurrent=20) as validator:
        results = await validator.validate_proxies_async(proxies)
        stats = await validator.get_validation_stats(results)
        print(f"验证统计: {stats}")

if __name__ == "__main__":
    asyncio.run(main())