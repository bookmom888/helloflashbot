import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = 'config/proxy_config.yaml', env_file: str = '.env'):
        self.config_file = config_file
        self.env_file = env_file
        self.logger = logging.getLogger(__name__)
        self._config = {}
        
        # 加载环境变量
        self._load_env_file()
        
        # 加载配置文件
        self._load_config_file()
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
        
        self.logger.info(f"配置管理器初始化完成: {config_file}")
    
    def _load_env_file(self):
        """加载环境变量文件"""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            self.logger.info(f"加载环境变量文件: {self.env_file}")
        else:
            self.logger.info(f"环境变量文件不存在: {self.env_file}")
    
    def _load_config_file(self):
        """加载YAML配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                self.logger.info(f"加载配置文件: {self.config_file}")
            else:
                # 创建默认配置文件
                self._create_default_config()
                self.logger.info(f"创建默认配置文件: {self.config_file}")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = self._get_default_config()
        
        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_file)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            self._config = default_config
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")
            self._config = default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'proxy_manager': {
                'validation': {
                    'timeout': 10,
                    'max_retries': 3,
                    'retry_delay': 1.0,
                    'max_threads': 10,
                    'urls': [
                        'http://httpbin.org/ip',
                        'https://api.ipify.org?format=json',
                        'http://ip-api.com/json'
                    ]
                },
                'storage': {
                    'use_database': True,
                    'db_path': 'data/proxies.db',
                    'json_backup_path': 'data/proxies.json',
                    'auto_backup': True,
                    'backup_interval': 3600  # 1小时
                },
                'health_check': {
                    'interval': 300,  # 5分钟
                    'max_error_count': 5,
                    'error_threshold_time': 300  # 5分钟内的错误
                },
                'rotation': {
                    'strategy': 'round_robin',  # round_robin, random, weighted
                    'avoid_recent_used': True,
                    'recent_used_threshold': 30  # 30秒
                }
            },
            'async_validation': {
                'enabled': True,
                'max_concurrent': 50,
                'timeout': 10,
                'test_urls': [
                    'http://httpbin.org/ip',
                    'https://api.ipify.org?format=json'
                ]
            },
            'api_proxies': {
                'enabled': False,
                'providers': {
                    # 示例API配置
                    'example_provider': {
                        'api_url': 'https://api.example.com/proxies',
                        'api_key': '',
                        'headers': {
                            'Authorization': 'Bearer {api_key}'
                        },
                        'params': {
                            'format': 'json',
                            'type': 'http'
                        },
                        'rate_limit': 100  # 每小时请求限制
                    }
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': {
                    'enabled': True,
                    'path': 'logs/proxy_manager.log',
                    'max_size': '10MB',
                    'backup_count': 5
                },
                'console': {
                    'enabled': True
                }
            },
            'monitoring': {
                'enabled': False,
                'metrics': {
                    'collect_interval': 60,  # 1分钟
                    'retention_days': 7
                },
                'alerts': {
                    'enabled': False,
                    'thresholds': {
                        'success_rate_min': 80,  # 成功率低于80%时告警
                        'response_time_max': 10,  # 响应时间超过10秒时告警
                        'error_rate_max': 20  # 错误率超过20%时告警
                    }
                }
            }
        }
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        env_mappings = {
            # 代理管理器配置
            'PROXY_VALIDATION_TIMEOUT': ('proxy_manager.validation.timeout', int),
            'PROXY_MAX_RETRIES': ('proxy_manager.validation.max_retries', int),
            'PROXY_MAX_THREADS': ('proxy_manager.validation.max_threads', int),
            'PROXY_USE_DATABASE': ('proxy_manager.storage.use_database', self._str_to_bool),
            'PROXY_DB_PATH': ('proxy_manager.storage.db_path', str),
            'PROXY_HEALTH_CHECK_INTERVAL': ('proxy_manager.health_check.interval', int),
            'PROXY_MAX_ERROR_COUNT': ('proxy_manager.health_check.max_error_count', int),
            
            # 异步验证配置
            'ASYNC_VALIDATION_ENABLED': ('async_validation.enabled', self._str_to_bool),
            'ASYNC_MAX_CONCURRENT': ('async_validation.max_concurrent', int),
            'ASYNC_TIMEOUT': ('async_validation.timeout', int),
            
            # 日志配置
            'LOG_LEVEL': ('logging.level', str),
            'LOG_FILE_ENABLED': ('logging.file.enabled', self._str_to_bool),
            'LOG_FILE_PATH': ('logging.file.path', str),
            
            # 监控配置
            'MONITORING_ENABLED': ('monitoring.enabled', self._str_to_bool),
            'METRICS_COLLECT_INTERVAL': ('monitoring.metrics.collect_interval', int),
        }
        
        for env_var, (config_path, converter) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    converted_value = converter(env_value)
                    self._set_nested_config(config_path, converted_value)
                    self.logger.debug(f"环境变量覆盖: {env_var} -> {config_path} = {converted_value}")
                except Exception as e:
                    self.logger.warning(f"环境变量转换失败: {env_var} = {env_value}, 错误: {e}")
    
    def _str_to_bool(self, value: str) -> bool:
        """字符串转布尔值"""
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def _set_nested_config(self, path: str, value: Any):
        """设置嵌套配置值"""
        keys = path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            keys = path.split('.')
            value = self._config
            
            for key in keys:
                value = value[key]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any):
        """设置配置值"""
        self._set_nested_config(path, value)
    
    def get_proxy_manager_config(self) -> Dict[str, Any]:
        """获取代理管理器配置"""
        return self.get('proxy_manager', {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """获取验证配置"""
        return self.get('proxy_manager.validation', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get('proxy_manager.storage', {})
    
    def get_async_validation_config(self) -> Dict[str, Any]:
        """获取异步验证配置"""
        return self.get('async_validation', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.get('monitoring', {})
    
    def get_api_proxies_config(self) -> Dict[str, Any]:
        """获取API代理配置"""
        return self.get('api_proxies', {})
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.logger.info(f"配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            self._load_config_file()
            self._apply_env_overrides()
            self.logger.info("配置重新加载完成")
            return True
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []
        
        # 验证必需的配置项
        required_configs = [
            ('proxy_manager.validation.timeout', int),
            ('proxy_manager.validation.max_retries', int),
            ('proxy_manager.storage.use_database', bool),
            ('logging.level', str)
        ]
        
        for config_path, expected_type in required_configs:
            value = self.get(config_path)
            if value is None:
                errors.append(f"缺少必需配置: {config_path}")
            elif not isinstance(value, expected_type):
                errors.append(f"配置类型错误: {config_path} 应为 {expected_type.__name__}")
        
        # 验证数值范围
        numeric_validations = [
            ('proxy_manager.validation.timeout', 1, 300),
            ('proxy_manager.validation.max_retries', 0, 10),
            ('proxy_manager.validation.max_threads', 1, 100),
            ('async_validation.max_concurrent', 1, 200)
        ]
        
        for config_path, min_val, max_val in numeric_validations:
            value = self.get(config_path)
            if value is not None and isinstance(value, (int, float)):
                if not (min_val <= value <= max_val):
                    errors.append(f"配置值超出范围: {config_path} = {value}, 应在 [{min_val}, {max_val}] 范围内")
        
        # 验证文件路径
        path_configs = [
            'proxy_manager.storage.db_path',
            'logging.file.path'
        ]
        
        for config_path in path_configs:
            path_value = self.get(config_path)
            if path_value:
                try:
                    # 检查目录是否可创建
                    parent_dir = os.path.dirname(path_value)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"路径配置无效: {config_path} = {path_value}, 错误: {e}")
        
        return errors
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """批量更新配置"""
        def update_nested(target: Dict, source: Dict):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    update_nested(target[key], value)
                else:
                    target[key] = value
        
        update_nested(self._config, updates)
        self.logger.info("配置已批量更新")
    
    def create_env_template(self, output_file: str = '.env.template') -> bool:
        """创建环境变量模板文件"""
        template_content = '''# 代理管理器环境变量配置模板
# 复制此文件为 .env 并修改相应的值

# 代理验证配置
PROXY_VALIDATION_TIMEOUT=10
PROXY_MAX_RETRIES=3
PROXY_MAX_THREADS=10

# 存储配置
PROXY_USE_DATABASE=true
PROXY_DB_PATH=data/proxies.db

# 健康检查配置
PROXY_HEALTH_CHECK_INTERVAL=300
PROXY_MAX_ERROR_COUNT=5

# 异步验证配置
ASYNC_VALIDATION_ENABLED=true
ASYNC_MAX_CONCURRENT=50
ASYNC_TIMEOUT=10

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_ENABLED=true
LOG_FILE_PATH=logs/proxy_manager.log

# 监控配置
MONITORING_ENABLED=false
METRICS_COLLECT_INTERVAL=60

# API密钥（如果使用API代理服务）
# API_KEY_PROVIDER1=your_api_key_here
# API_KEY_PROVIDER2=your_api_key_here
'''
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            self.logger.info(f"环境变量模板已创建: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"创建环境变量模板失败: {e}")
            return False

# 全局配置实例
_config_manager = None

def get_config_manager(config_file: str = 'config/proxy_config.yaml', env_file: str = '.env') -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file, env_file)
    return _config_manager

def get_config(path: str, default: Any = None) -> Any:
    """快捷方式：获取配置值"""
    return get_config_manager().get(path, default)

def set_config(path: str, value: Any):
    """快捷方式：设置配置值"""
    get_config_manager().set(path, value)