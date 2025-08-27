#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
Configuration Management Module

提供统一的配置管理功能，支持：
- 配置文件读取
- 环境变量覆盖
- 默认值设置
- 类型转换
"""

import os
import configparser
from typing import Dict, Any, Optional, Union
import logging


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.ini"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                self.logger.info(f"加载配置文件: {self.config_file}")
            else:
                self.logger.warning(f"配置文件不存在: {self.config_file}")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
    
    def get(self, section: str, key: str, default: Any = None, 
           value_type: type = str) -> Any:
        """
        获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            default: 默认值
            value_type: 值类型
            
        Returns:
            配置值
        """
        try:
            # 先尝试从环境变量获取
            env_key = f"{section.upper()}_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                return self._convert_type(env_value, value_type)
            
            # 从配置文件获取
            if self.config.has_section(section) and self.config.has_option(section, key):
                value = self.config.get(section, key)
                return self._convert_type(value, value_type)
            
            return default
            
        except Exception as e:
            self.logger.warning(f"获取配置失败 [{section}.{key}]: {e}")
            return default
    
    def _convert_type(self, value: str, value_type: type) -> Any:
        """类型转换"""
        try:
            if value_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif value_type == int:
                return int(value)
            elif value_type == float:
                return float(value)
            else:
                return str(value)
        except Exception:
            return value
    
    def get_section(self, section: str) -> Dict[str, str]:
        """获取整个配置节"""
        try:
            if self.config.has_section(section):
                return dict(self.config.items(section))
            return {}
        except Exception as e:
            self.logger.warning(f"获取配置节失败 [{section}]: {e}")
            return {}
    
    # 路径配置
    @property
    def logs_dir(self) -> str:
        return self.get('paths', 'logs_dir', 'logs')
    
    @property
    def data_dir(self) -> str:
        return self.get('paths', 'data_dir', 'data')
    
    @property
    def sessions_file(self) -> str:
        return self.get('paths', 'sessions_file', 'sessions.json')
    
    @property
    def proxies_file(self) -> str:
        return self.get('paths', 'proxies_file', 'proxies.json')
    
    # 自动化配置
    @property
    def max_windows(self) -> int:
        return self.get('automation', 'max_windows', 5, int)
    
    @property
    def session_timeout_hours(self) -> int:
        return self.get('automation', 'session_timeout_hours', 24, int)
    
    @property
    def session_cooldown_hours(self) -> int:
        return self.get('automation', 'session_cooldown_hours', 2, int)
    
    @property
    def max_url_plays_per_session(self) -> int:
        return self.get('automation', 'max_url_plays_per_session', 3, int)
    
    @property
    def max_sessions_per_ip(self) -> int:
        return self.get('automation', 'max_sessions_per_ip', 1, int)
    
    # 浏览器配置
    @property
    def window_width(self) -> int:
        return self.get('browser', 'window_width', 1024, int)
    
    @property
    def window_height(self) -> int:
        return self.get('browser', 'window_height', 768, int)
    
    @property
    def user_agent(self) -> str:
        return self.get('browser', 'user_agent', 
                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # 代理配置
    @property
    def proxy_validation_timeout(self) -> int:
        return self.get('proxy', 'validation_timeout', 10, int)
    
    @property
    def proxy_max_retries(self) -> int:
        return self.get('proxy', 'max_retries', 3, int)
    
    @property
    def proxy_max_threads(self) -> int:
        return self.get('proxy', 'max_threads', 10, int)
    
    # 日志配置
    @property
    def log_level(self) -> str:
        return self.get('logging', 'level', 'INFO')
    
    @property
    def log_format(self) -> str:
        return self.get('logging', 'format', 
                       '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @property
    def log_file_enabled(self) -> bool:
        return self.get('logging', 'file_enabled', True, bool)
    
    @property
    def log_console_enabled(self) -> bool:
        return self.get('logging', 'console_enabled', True, bool)


# 全局配置实例
config = Config()