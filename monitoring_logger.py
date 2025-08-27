import os
import time
import json
import logging
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from collections import defaultdict, deque
from pathlib import Path
import structlog
from logging.handlers import RotatingFileHandler

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.metrics = defaultdict(lambda: deque(maxlen=retention_minutes))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(list)
        self.lock = threading.Lock()
        
        # 系统指标
        self.system_metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_used_mb': 0.0,
            'disk_usage_percent': 0.0,
            'network_sent_mb': 0.0,
            'network_recv_mb': 0.0
        }
        
        # 代理相关指标
        self.proxy_metrics = {
            'total_proxies': 0,
            'valid_proxies': 0,
            'invalid_proxies': 0,
            'validation_success_rate': 0.0,
            'avg_response_time': 0.0,
            'validations_per_minute': 0,
            'errors_per_minute': 0
        }
        
        self.start_time = time.time()
        self.last_network_stats = psutil.net_io_counters()
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """增加计数器"""
        with self.lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """设置仪表值"""
        with self.lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """记录计时器"""
        with self.lock:
            key = self._make_key(name, tags)
            timestamp = time.time()
            self.timers[key].append((timestamp, duration))
            
            # 清理过期数据
            cutoff = timestamp - (self.retention_minutes * 60)
            self.timers[key] = [(t, d) for t, d in self.timers[key] if t > cutoff]
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """生成指标键"""
        if not tags:
            return name
        tag_str = ','.join(f'{k}={v}' for k, v in sorted(tags.items()))
        return f'{name}[{tag_str}]'
    
    def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            self.system_metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            self.system_metrics['memory_percent'] = memory.percent
            self.system_metrics['memory_used_mb'] = memory.used / 1024 / 1024
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            self.system_metrics['disk_usage_percent'] = (disk.used / disk.total) * 100
            
            # 网络使用情况
            current_network = psutil.net_io_counters()
            if self.last_network_stats:
                sent_diff = current_network.bytes_sent - self.last_network_stats.bytes_sent
                recv_diff = current_network.bytes_recv - self.last_network_stats.bytes_recv
                self.system_metrics['network_sent_mb'] = sent_diff / 1024 / 1024
                self.system_metrics['network_recv_mb'] = recv_diff / 1024 / 1024
            
            self.last_network_stats = current_network
            
            # 记录到时间序列
            timestamp = time.time()
            with self.lock:
                for metric_name, value in self.system_metrics.items():
                    self.metrics[f'system.{metric_name}'].append((timestamp, value))
                    
        except Exception as e:
            logging.error(f"收集系统指标失败: {e}")
    
    def update_proxy_metrics(self, total: int, valid: int, invalid: int, 
                           avg_response_time: float = 0.0):
        """更新代理指标"""
        self.proxy_metrics['total_proxies'] = total
        self.proxy_metrics['valid_proxies'] = valid
        self.proxy_metrics['invalid_proxies'] = invalid
        
        if total > 0:
            self.proxy_metrics['validation_success_rate'] = (valid / total) * 100
        else:
            self.proxy_metrics['validation_success_rate'] = 0.0
            
        self.proxy_metrics['avg_response_time'] = avg_response_time
        
        # 记录到时间序列
        timestamp = time.time()
        with self.lock:
            for metric_name, value in self.proxy_metrics.items():
                self.metrics[f'proxy.{metric_name}'].append((timestamp, value))
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        with self.lock:
            summary = {
                'timestamp': time.time(),
                'uptime_seconds': time.time() - self.start_time,
                'system': self.system_metrics.copy(),
                'proxy': self.proxy_metrics.copy(),
                'counters': dict(self.counters),
                'gauges': dict(self.gauges)
            }
            
            # 计算计时器统计
            timer_stats = {}
            for name, measurements in self.timers.items():
                if measurements:
                    durations = [d for _, d in measurements]
                    timer_stats[name] = {
                        'count': len(durations),
                        'avg': sum(durations) / len(durations),
                        'min': min(durations),
                        'max': max(durations)
                    }
            summary['timers'] = timer_stats
            
            return summary
    
    def get_time_series(self, metric_name: str, minutes: int = 10) -> List[Tuple[float, float]]:
        """获取时间序列数据"""
        with self.lock:
            if metric_name not in self.metrics:
                return []
            
            cutoff = time.time() - (minutes * 60)
            return [(t, v) for t, v in self.metrics[metric_name] if t > cutoff]

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> structlog.BoundLogger:
        """设置结构化日志"""
        # 配置structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # 设置标准库日志
        logging.basicConfig(
            format=self.config.get('format', '%(message)s'),
            level=getattr(logging, self.config.get('level', 'INFO').upper())
        )
        
        # 文件日志处理器
        if self.config.get('file', {}).get('enabled', False):
            log_file = self.config['file']['path']
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            max_size = self._parse_size(self.config['file'].get('max_size', '10MB'))
            backup_count = self.config['file'].get('backup_count', 5)
            
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_size, backupCount=backup_count
            )
            file_handler.setLevel(getattr(logging, self.config.get('level', 'INFO').upper()))
            
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
        
        return structlog.get_logger("proxy_manager")
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, **kwargs)
    
    def log_proxy_validation(self, proxy: str, success: bool, response_time: float, 
                           error: str = None):
        """记录代理验证日志"""
        self.logger.info(
            "代理验证完成",
            proxy=proxy,
            success=success,
            response_time_ms=response_time * 1000,
            error=error,
            event_type="proxy_validation"
        )
    
    def log_proxy_rotation(self, old_proxy: str, new_proxy: str, reason: str):
        """记录代理轮换日志"""
        self.logger.info(
            "代理轮换",
            old_proxy=old_proxy,
            new_proxy=new_proxy,
            reason=reason,
            event_type="proxy_rotation"
        )
    
    def log_system_event(self, event: str, details: Dict[str, Any]):
        """记录系统事件日志"""
        self.logger.info(
            event,
            event_type="system_event",
            **details
        )

class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: Dict[str, Any], logger: StructuredLogger):
        self.config = config
        self.logger = logger
        self.alert_history = deque(maxlen=100)
        self.alert_cooldowns = {}
        self.thresholds = config.get('thresholds', {})
        
    def check_alerts(self, metrics: Dict[str, Any]):
        """检查告警条件"""
        if not self.config.get('enabled', False):
            return
        
        current_time = time.time()
        
        # 检查成功率告警
        success_rate = metrics.get('proxy', {}).get('validation_success_rate', 100)
        min_success_rate = self.thresholds.get('success_rate_min', 80)
        if success_rate < min_success_rate:
            self._trigger_alert(
                'low_success_rate',
                f'代理验证成功率过低: {success_rate:.1f}% < {min_success_rate}%',
                {'success_rate': success_rate, 'threshold': min_success_rate},
                current_time
            )
        
        # 检查响应时间告警
        response_time = metrics.get('proxy', {}).get('avg_response_time', 0)
        max_response_time = self.thresholds.get('response_time_max', 10)
        if response_time > max_response_time:
            self._trigger_alert(
                'high_response_time',
                f'代理响应时间过长: {response_time:.2f}s > {max_response_time}s',
                {'response_time': response_time, 'threshold': max_response_time},
                current_time
            )
        
        # 检查系统资源告警
        cpu_percent = metrics.get('system', {}).get('cpu_percent', 0)
        if cpu_percent > 90:
            self._trigger_alert(
                'high_cpu_usage',
                f'CPU使用率过高: {cpu_percent:.1f}%',
                {'cpu_percent': cpu_percent},
                current_time
            )
        
        memory_percent = metrics.get('system', {}).get('memory_percent', 0)
        if memory_percent > 90:
            self._trigger_alert(
                'high_memory_usage',
                f'内存使用率过高: {memory_percent:.1f}%',
                {'memory_percent': memory_percent},
                current_time
            )
    
    def _trigger_alert(self, alert_type: str, message: str, data: Dict[str, Any], 
                      current_time: float):
        """触发告警"""
        # 检查冷却时间（避免重复告警）
        cooldown_key = f'{alert_type}_{hash(str(data))}'
        last_alert_time = self.alert_cooldowns.get(cooldown_key, 0)
        cooldown_period = 300  # 5分钟冷却时间
        
        if current_time - last_alert_time < cooldown_period:
            return
        
        # 记录告警
        alert = {
            'timestamp': current_time,
            'type': alert_type,
            'message': message,
            'data': data,
            'severity': self._get_alert_severity(alert_type)
        }
        
        self.alert_history.append(alert)
        self.alert_cooldowns[cooldown_key] = current_time
        
        # 记录告警日志
        self.logger.log_system_event('告警触发', alert)
        
        # 这里可以扩展其他告警通知方式（邮件、webhook等）
    
    def _get_alert_severity(self, alert_type: str) -> str:
        """获取告警严重程度"""
        severity_map = {
            'low_success_rate': 'high',
            'high_response_time': 'medium',
            'high_cpu_usage': 'medium',
            'high_memory_usage': 'medium'
        }
        return severity_map.get(alert_type, 'low')
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        cutoff = time.time() - (minutes * 60)
        return [alert for alert in self.alert_history if alert['timestamp'] > cutoff]

class MonitoringSystem:
    """监控系统"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
        
        if not self.enabled:
            return
        
        # 初始化组件
        self.metrics_collector = MetricsCollector(
            retention_minutes=config.get('metrics', {}).get('retention_minutes', 60)
        )
        
        logging_config = config.get('logging', {})
        self.logger = StructuredLogger(logging_config)
        
        self.alert_manager = AlertManager(
            config.get('alerts', {}), 
            self.logger
        )
        
        # 监控线程
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        self.collect_interval = config.get('metrics', {}).get('collect_interval', 60)
        
        self.logger.info("监控系统初始化完成")
    
    def start(self):
        """启动监控"""
        if not self.enabled or self.monitoring_thread:
            return
        
        self.stop_event.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("监控系统已启动")
    
    def stop(self):
        """停止监控"""
        if not self.monitoring_thread:
            return
        
        self.stop_event.set()
        self.monitoring_thread.join(timeout=5)
        self.monitoring_thread = None
        
        self.logger.info("监控系统已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while not self.stop_event.is_set():
            try:
                # 收集系统指标
                self.metrics_collector.collect_system_metrics()
                
                # 获取指标摘要
                metrics_summary = self.metrics_collector.get_metrics_summary()
                
                # 检查告警
                self.alert_manager.check_alerts(metrics_summary)
                
                # 记录监控日志
                self.logger.debug("监控指标收集完成", metrics=metrics_summary)
                
            except Exception as e:
                self.logger.error("监控循环异常", error=str(e))
            
            # 等待下次收集
            self.stop_event.wait(self.collect_interval)
    
    def record_proxy_validation(self, proxy: str, success: bool, response_time: float, 
                              error: str = None):
        """记录代理验证"""
        if not self.enabled:
            return
        
        # 更新指标
        self.metrics_collector.increment_counter('proxy.validations')
        if success:
            self.metrics_collector.increment_counter('proxy.validations.success')
        else:
            self.metrics_collector.increment_counter('proxy.validations.failure')
        
        self.metrics_collector.record_timer('proxy.validation.duration', response_time)
        
        # 记录日志
        self.logger.log_proxy_validation(proxy, success, response_time, error)
    
    def record_proxy_rotation(self, old_proxy: str, new_proxy: str, reason: str):
        """记录代理轮换"""
        if not self.enabled:
            return
        
        self.metrics_collector.increment_counter('proxy.rotations')
        self.logger.log_proxy_rotation(old_proxy, new_proxy, reason)
    
    def update_proxy_stats(self, total: int, valid: int, invalid: int, 
                          avg_response_time: float = 0.0):
        """更新代理统计"""
        if not self.enabled:
            return
        
        self.metrics_collector.update_proxy_stats(total, valid, invalid, avg_response_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标"""
        if not self.enabled:
            return {}
        
        return self.metrics_collector.get_metrics_summary()
    
    def get_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取告警信息"""
        if not self.enabled:
            return []
        
        return self.alert_manager.get_recent_alerts(minutes)
    
    def get_time_series(self, metric_name: str, minutes: int = 10) -> List[Tuple[float, float]]:
        """获取时间序列数据"""
        if not self.enabled:
            return []
        
        return self.metrics_collector.get_time_series(metric_name, minutes)

# 全局监控实例
_monitoring_system = None

def get_monitoring_system(config: Dict[str, Any] = None) -> MonitoringSystem:
    """获取全局监控系统实例"""
    global _monitoring_system
    if _monitoring_system is None and config:
        _monitoring_system = MonitoringSystem(config)
    return _monitoring_system

def init_monitoring(config: Dict[str, Any]) -> MonitoringSystem:
    """初始化监控系统"""
    global _monitoring_system
    _monitoring_system = MonitoringSystem(config)
    return _monitoring_system