#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鼠标操作状态监控器
Mouse Operation Status Monitor

功能：
- 监控鼠标操作状态
- 提供安全操作建议
- 记录鼠标交互历史
- 防止冲突操作
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class MouseActionType(Enum):
    """鼠标操作类型"""
    MOVE = "move"
    CLICK = "click"
    SCROLL = "scroll"
    DRAG = "drag"
    HOVER = "hover"

@dataclass
class MouseEvent:
    """鼠标事件记录"""
    timestamp: float
    action_type: MouseActionType
    x: int
    y: int
    target_element: Optional[str] = None
    is_automated: bool = False
    is_safe: bool = True

class MouseMonitor:
    """鼠标操作状态监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 鼠标事件历史
        self.mouse_events: List[MouseEvent] = []
        self.max_events = 100  # 最大记录事件数
        
        # 安全区域配置
        self.safe_zones: List[Dict] = []
        self.danger_zones: List[Dict] = []
        
        # 操作限制
        self.cooldown_period = 2.0  # 冷却时间（秒）
        self.last_interaction_time = 0.0
        
        # 统计信息
        self.stats = {
            'total_events': 0,
            'safe_events': 0,
            'dangerous_events': 0,
            'automated_events': 0,
            'manual_events': 0
        }
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("鼠标监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        self.logger.info("鼠标监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 检查鼠标状态
                self._check_mouse_status()
                
                # 清理旧事件
                self._cleanup_old_events()
                
                time.sleep(0.1)  # 100ms检查间隔
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {str(e)}")
                time.sleep(1)
    
    def _check_mouse_status(self):
        """检查鼠标状态"""
        # 这里可以添加实际的鼠标状态检查
        # 例如：检查鼠标是否在安全区域内
        pass
    
    def _cleanup_old_events(self):
        """清理旧事件"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 保留1小时内的事件
        
        # 移除超过1小时的事件
        self.mouse_events = [
            event for event in self.mouse_events 
            if event.timestamp > cutoff_time
        ]
        
        # 限制事件数量
        if len(self.mouse_events) > self.max_events:
            self.mouse_events = self.mouse_events[-self.max_events:]
    
    def record_event(self, action_type: MouseActionType, x: int, y: int, 
                    target_element: Optional[str] = None, is_automated: bool = False):
        """记录鼠标事件"""
        current_time = time.time()
        
        # 检查是否在安全区域
        is_safe = self._is_position_safe(x, y)
        
        # 创建事件记录
        event = MouseEvent(
            timestamp=current_time,
            action_type=action_type,
            x=x,
            y=y,
            target_element=target_element,
            is_automated=is_automated,
            is_safe=is_safe
        )
        
        # 添加到事件列表
        self.mouse_events.append(event)
        
        # 更新统计信息
        self.stats['total_events'] += 1
        if is_safe:
            self.stats['safe_events'] += 1
        else:
            self.stats['dangerous_events'] += 1
        
        if is_automated:
            self.stats['automated_events'] += 1
        else:
            self.stats['manual_events'] += 1
        
        # 记录日志
        if not is_safe and not is_automated:
            self.logger.warning(f"检测到危险鼠标操作: {action_type.value} at ({x}, {y})")
        
        # 更新最后交互时间
        if not is_automated:
            self.last_interaction_time = current_time
    
    def _is_position_safe(self, x: int, y: int) -> bool:
        """检查位置是否安全"""
        # 检查是否在安全区域内
        for zone in self.safe_zones:
            if (zone['x1'] <= x <= zone['x2'] and 
                zone['y1'] <= y <= zone['y2']):
                return True
        
        # 检查是否在危险区域内
        for zone in self.danger_zones:
            if (zone['x1'] <= x <= zone['x2'] and 
                zone['y1'] <= y <= zone['y2']):
                return False
        
        # 默认认为安全
        return True
    
    def add_safe_zone(self, x1: int, y1: int, x2: int, y2: int, description: str = ""):
        """添加安全区域"""
        safe_zone = {
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'description': description
        }
        self.safe_zones.append(safe_zone)
        self.logger.info(f"添加安全区域: {description} ({x1},{y1}) - ({x2},{y2})")
    
    def add_danger_zone(self, x1: int, y1: int, x2: int, y2: int, description: str = ""):
        """添加危险区域"""
        danger_zone = {
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'description': description
        }
        self.danger_zones.append(danger_zone)
        self.logger.info(f"添加危险区域: {description} ({x1},{y1}) - ({x2},{y2})")
    
    def can_perform_action(self) -> bool:
        """检查是否可以执行操作"""
        current_time = time.time()
        return current_time - self.last_interaction_time >= self.cooldown_period
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        current_time = time.time()
        time_since_last = current_time - self.last_interaction_time
        
        return {
            'is_monitoring': self.is_monitoring,
            'can_perform_action': self.can_perform_action(),
            'time_since_last_interaction': time_since_last,
            'cooldown_remaining': max(0, self.cooldown_period - time_since_last),
            'safe_zones_count': len(self.safe_zones),
            'danger_zones_count': len(self.danger_zones),
            'recent_events_count': len(self.mouse_events),
            'stats': self.stats.copy(),
            'recent_events': [
                {
                    'timestamp': event.timestamp,
                    'action_type': event.action_type.value,
                    'position': (event.x, event.y),
                    'is_safe': event.is_safe,
                    'is_automated': event.is_automated
                }
                for event in self.mouse_events[-10:]  # 最近10个事件
            ]
        }
    
    def get_safety_advice(self) -> List[str]:
        """获取安全建议"""
        advice = []
        
        if not self.can_perform_action():
            remaining = self.cooldown_period - (time.time() - self.last_interaction_time)
            advice.append(f"⏱️ 请等待 {remaining:.1f} 秒后再进行操作")
        
        if self.stats['dangerous_events'] > 0:
            advice.append("⚠️ 检测到危险操作，请避免在视频播放区域点击")
        
        if self.stats['manual_events'] > self.stats['automated_events']:
            advice.append("💡 建议减少手动操作，让自动化程序处理")
        
        if not advice:
            advice.append("✅ 当前操作安全，可以继续")
        
        return advice
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_events': 0,
            'safe_events': 0,
            'dangerous_events': 0,
            'automated_events': 0,
            'manual_events': 0
        }
        self.mouse_events.clear()
        self.logger.info("鼠标监控统计已重置")
