#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理器模块
Session Manager Module

管理IP、设备指纹、URL的轮换策略：
- 会话生命周期管理
- 智能轮换算法
- 使用次数跟踪
- 会话持久化
- 冷却期管理
"""

import json
import time
import random
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import uuid

@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    proxy_id: str
    fingerprint_id: str
    current_url: str
    url_play_count: int
    total_play_count: int
    created_at: str
    last_used_at: str
    last_ip: str
    status: str  # active, cooldown, expired
    cooldown_until: Optional[str] = None

class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 会话配置
        self.max_url_plays_per_session = 3  # 每个会话最多播放同一URL的次数
        self.session_cooldown_hours = 2     # 会话冷却时间（小时）
        self.max_sessions_per_ip = 1        # 每个IP最大并发会话数（一个IP只能有一个会话）
        self.session_timeout_hours = 24     # 会话超时时间（小时）
        
        # 数据存储
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.session_history: List[SessionInfo] = []
        self.ip_session_map: Dict[str, Set[str]] = defaultdict(set)
        self.url_session_map: Dict[str, Set[str]] = defaultdict(set)
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 加载历史会话
        self.load_sessions()
    
    def create_session(self, proxy: Dict, fingerprint: Dict, url: str) -> Optional[SessionInfo]:
        """创建新会话"""
        try:
            with self.lock:
                # 生成会话ID
                session_id = str(uuid.uuid4())
                
                # 获取代理IP（如果可用）
                current_ip = proxy.get('host', 'unknown')
                
                # 检查IP对URL的播放次数限制
                if not self.can_ip_play_url(current_ip, url):
                    self.logger.warning(f"IP {current_ip} 对URL {url} 已达到最大播放次数限制 ({self.max_url_plays_per_session}次)")
                    return None
                
                # 检查IP会话限制
                if len(self.ip_session_map[current_ip]) >= self.max_sessions_per_ip:
                    # 尝试清理过期会话
                    self._cleanup_expired_sessions()
                    
                    if len(self.ip_session_map[current_ip]) >= self.max_sessions_per_ip:
                        self.logger.warning(f"IP {current_ip} 已达到最大会话数限制")
                        return None
                
                # 创建会话信息
                session = SessionInfo(
                    session_id=session_id,
                    proxy_id=self._generate_proxy_id(proxy),
                    fingerprint_id=fingerprint.get('fingerprint_id', 'unknown'),
                    current_url=url,
                    url_play_count=0,
                    total_play_count=0,
                    created_at=datetime.now().isoformat(),
                    last_used_at=datetime.now().isoformat(),
                    last_ip=current_ip,
                    status='active'
                )
                
                # 存储会话
                self.active_sessions[session_id] = session
                self.ip_session_map[current_ip].add(session_id)
                self.url_session_map[url].add(session_id)
                
                self.logger.info(f"创建新会话: {session_id[:8]}... (IP: {current_ip})")
                
                # 保存会话
                self.save_sessions()
                
                return session
        
        except Exception as e:
            self.logger.error(f"创建会话失败: {str(e)}")
            return None
    
    def update_session_usage(self, session_id: str, url: str) -> bool:
        """更新会话使用情况"""
        try:
            with self.lock:
                if session_id not in self.active_sessions:
                    self.logger.warning(f"会话不存在: {session_id}")
                    return False
                
                session = self.active_sessions[session_id]
                
                # 检查会话状态
                if session.status != 'active':
                    self.logger.warning(f"会话状态无效: {session.status}")
                    return False
                
                # 更新播放计数
                if session.current_url == url:
                    session.url_play_count += 1
                else:
                    # 切换到新URL
                    session.current_url = url
                    session.url_play_count = 1
                
                session.total_play_count += 1
                session.last_used_at = datetime.now().isoformat()
                
                # 检查是否需要轮换
                if session.url_play_count >= self.max_url_plays_per_session:
                    self.logger.info(f"会话 {session_id[:8]}... 达到URL播放限制，需要轮换")
                    return False
                
                self.logger.debug(f"更新会话使用: {session_id[:8]}... "
                                f"(URL播放次数: {session.url_play_count}/{self.max_url_plays_per_session})")
                
                # 保存会话
                self.save_sessions()
                
                return True
        
        except Exception as e:
            self.logger.error(f"更新会话使用失败: {str(e)}")
            return False
    
    def should_rotate_session(self, session_id: str, url: str) -> bool:
        """检查是否需要轮换会话"""
        try:
            with self.lock:
                if session_id not in self.active_sessions:
                    return True
                
                session = self.active_sessions[session_id]
                
                # 检查会话状态
                if session.status != 'active':
                    return True
                
                # 检查会话是否过期
                if self._is_session_expired(session):
                    return True
                
                # 检查URL播放次数
                if session.current_url == url and session.url_play_count >= self.max_url_plays_per_session:
                    return True
                
                return False
        
        except Exception as e:
            self.logger.error(f"检查会话轮换失败: {str(e)}")
            return True
    
    def rotate_session(self, old_session_id: str, new_proxy: Dict, 
                      new_fingerprint: Dict, url: str) -> Optional[SessionInfo]:
        """轮换会话"""
        try:
            with self.lock:
                # 关闭旧会话
                if old_session_id in self.active_sessions:
                    self._close_session(old_session_id)
                
                # 创建新会话
                new_session = self.create_session(new_proxy, new_fingerprint, url)
                
                if new_session:
                    self.logger.info(f"会话轮换成功: {old_session_id[:8]}... -> {new_session.session_id[:8]}...")
                
                return new_session
        
        except Exception as e:
            self.logger.error(f"会话轮换失败: {str(e)}")
            return None
    
    def close_session(self, session_id: str):
        """关闭会话"""
        try:
            with self.lock:
                self._close_session(session_id)
                self.save_sessions()
        
        except Exception as e:
            self.logger.error(f"关闭会话失败: {str(e)}")
    
    def _close_session(self, session_id: str):
        """内部关闭会话方法"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # 设置冷却期
        cooldown_until = datetime.now() + timedelta(hours=self.session_cooldown_hours)
        session.status = 'cooldown'
        session.cooldown_until = cooldown_until.isoformat()
        
        # 移动到历史记录
        self.session_history.append(session)
        
        # 从活跃会话中移除
        del self.active_sessions[session_id]
        
        # 更新映射
        self.ip_session_map[session.last_ip].discard(session_id)
        self.url_session_map[session.current_url].discard(session_id)
        
        self.logger.info(f"会话已关闭并进入冷却期: {session_id[:8]}...")
    
    def get_session_stats(self) -> Dict:
        """获取会话统计信息"""
        try:
            with self.lock:
                # 清理过期会话
                self._cleanup_expired_sessions()
                
                active_count = len(self.active_sessions)
                cooldown_count = len([s for s in self.session_history 
                                    if s.status == 'cooldown' and not self._is_cooldown_expired(s)])
                
                # IP分布
                ip_distribution = {}
                for ip, sessions in self.ip_session_map.items():
                    if sessions:  # 只统计有活跃会话的IP
                        ip_distribution[ip] = len(sessions)
                
                # URL分布
                url_distribution = {}
                for url, sessions in self.url_session_map.items():
                    if sessions:  # 只统计有活跃会话的URL
                        url_distribution[url] = len(sessions)
                
                return {
                    'active_sessions': active_count,
                    'cooldown_sessions': cooldown_count,
                    'total_history': len(self.session_history),
                    'ip_distribution': ip_distribution,
                    'url_distribution': url_distribution,
                    'max_url_plays': self.max_url_plays_per_session,
                    'cooldown_hours': self.session_cooldown_hours
                }
        
        except Exception as e:
            self.logger.error(f"获取会话统计失败: {str(e)}")
            return {}
    
    def get_active_sessions(self) -> List[SessionInfo]:
        """获取活跃会话列表"""
        with self.lock:
            self._cleanup_expired_sessions()
            return list(self.active_sessions.values())
    
    def get_session_by_id(self, session_id: str) -> Optional[SessionInfo]:
        """根据ID获取会话"""
        with self.lock:
            return self.active_sessions.get(session_id)
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            # 检查活跃会话
            for session_id, session in self.active_sessions.items():
                if self._is_session_expired(session):
                    expired_sessions.append(session_id)
            
            # 移除过期的活跃会话
            for session_id in expired_sessions:
                self._close_session(session_id)
            
            # 清理冷却期过期的历史会话
            self.session_history = [
                s for s in self.session_history 
                if not (s.status == 'cooldown' and self._is_cooldown_expired(s))
            ]
            
            if expired_sessions:
                self.logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
        
        except Exception as e:
            self.logger.error(f"清理过期会话失败: {str(e)}")
    
    def _is_session_expired(self, session: SessionInfo) -> bool:
        """检查会话是否过期"""
        try:
            last_used = datetime.fromisoformat(session.last_used_at)
            expiry_time = last_used + timedelta(hours=self.session_timeout_hours)
            return datetime.now() > expiry_time
        except Exception:
            return True
    
    def _is_cooldown_expired(self, session: SessionInfo) -> bool:
        """检查冷却期是否过期"""
        try:
            if not session.cooldown_until:
                return True
            
            cooldown_until = datetime.fromisoformat(session.cooldown_until)
            return datetime.now() > cooldown_until
        except Exception:
            return True
    
    def _generate_proxy_id(self, proxy: Dict) -> str:
        """生成代理ID"""
        return f"{proxy.get('type', 'unknown')}://{proxy.get('host', 'unknown')}:{proxy.get('port', 'unknown')}"
    
    def can_use_url_with_current_sessions(self, url: str) -> bool:
        """检查当前会话是否可以播放指定URL"""
        try:
            with self.lock:
                # 获取URL的活跃会话
                active_url_sessions = self.url_session_map.get(url, set())
                
                # 检查每个会话的播放次数
                for session_id in active_url_sessions:
                    if session_id in self.active_sessions:
                        session = self.active_sessions[session_id]
                        if (session.current_url == url and 
                            session.url_play_count < self.max_url_plays_per_session):
                            return True
                
                return False
        
        except Exception as e:
            self.logger.error(f"检查URL可用性失败: {str(e)}")
            return False
    
    def get_available_session_for_url(self, url: str) -> Optional[SessionInfo]:
        """获取可用于播放指定URL的会话"""
        try:
            with self.lock:
                # 清理过期会话
                self._cleanup_expired_sessions()
                
                # 查找可用会话
                for session in self.active_sessions.values():
                    if (session.status == 'active' and
                        session.current_url == url and
                        session.url_play_count < self.max_url_plays_per_session):
                        return session
                
                return None
        
        except Exception as e:
            self.logger.error(f"获取可用会话失败: {str(e)}")
            return None
    
    def get_ip_url_play_count(self, ip: str, url: str) -> int:
        """获取指定IP对指定URL的播放次数"""
        try:
            with self.lock:
                total_count = 0
                
                # 检查活跃会话
                for session in self.active_sessions.values():
                    if session.last_ip == ip and session.current_url == url:
                        total_count += session.url_play_count
                
                # 检查历史会话（冷却期内的）
                for session in self.session_history:
                    if (session.last_ip == ip and 
                        session.current_url == url and
                        session.status == 'cooldown' and
                        not self._is_cooldown_expired(session)):
                        total_count += session.url_play_count
                
                return total_count
        
        except Exception as e:
            self.logger.error(f"获取IP URL播放次数失败: {str(e)}")
            return 0
    
    def can_ip_play_url(self, ip: str, url: str) -> bool:
        """检查指定IP是否可以播放指定URL"""
        try:
            play_count = self.get_ip_url_play_count(ip, url)
            return play_count < self.max_url_plays_per_session
        
        except Exception as e:
            self.logger.error(f"检查IP URL播放权限失败: {str(e)}")
            return False
    
    def save_sessions(self):
        """保存会话到文件"""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            
            data = {
                'active_sessions': {k: asdict(v) for k, v in self.active_sessions.items()},
                'session_history': [asdict(s) for s in self.session_history[-1000:]],  # 只保存最近1000条
                'config': {
                    'max_url_plays_per_session': self.max_url_plays_per_session,
                    'session_cooldown_hours': self.session_cooldown_hours,
                    'max_sessions_per_ip': self.max_sessions_per_ip,
                    'session_timeout_hours': self.session_timeout_hours
                }
            }
            
            with open("data/sessions.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.logger.error(f"保存会话失败: {str(e)}")
    
    def load_sessions(self):
        """从文件加载会话"""
        try:
            with open("data/sessions.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载配置
            if 'config' in data:
                config = data['config']
                self.max_url_plays_per_session = config.get('max_url_plays_per_session', 3)
                self.session_cooldown_hours = config.get('session_cooldown_hours', 2)
                self.max_sessions_per_ip = config.get('max_sessions_per_ip', 1)
                self.session_timeout_hours = config.get('session_timeout_hours', 24)
            
            # 加载活跃会话
            if 'active_sessions' in data:
                for session_id, session_data in data['active_sessions'].items():
                    session = SessionInfo(**session_data)
                    
                    # 检查会话是否仍然有效
                    if not self._is_session_expired(session):
                        self.active_sessions[session_id] = session
                        self.ip_session_map[session.last_ip].add(session_id)
                        self.url_session_map[session.current_url].add(session_id)
            
            # 加载历史会话
            if 'session_history' in data:
                for session_data in data['session_history']:
                    session = SessionInfo(**session_data)
                    
                    # 只加载未过期的冷却期会话
                    if (session.status == 'cooldown' and 
                        not self._is_cooldown_expired(session)):
                        self.session_history.append(session)
            
            self.logger.info(f"加载了 {len(self.active_sessions)} 个活跃会话和 {len(self.session_history)} 个历史会话")
        
        except FileNotFoundError:
            self.logger.info("会话文件不存在，使用空会话")
        except Exception as e:
            self.logger.error(f"加载会话失败: {str(e)}")
    
    def clear_all_sessions(self):
        """清空所有会话"""
        try:
            with self.lock:
                self.active_sessions.clear()
                self.session_history.clear()
                self.ip_session_map.clear()
                self.url_session_map.clear()
                
                self.save_sessions()
                self.logger.info("所有会话已清空")
        
        except Exception as e:
            self.logger.error(f"清空会话失败: {str(e)}")
    
    def export_session_report(self, file_path: str) -> bool:
        """导出会话报告"""
        try:
            with self.lock:
                report_data = {
                    'generated_at': datetime.now().isoformat(),
                    'statistics': self.get_session_stats(),
                    'active_sessions': [asdict(s) for s in self.active_sessions.values()],
                    'recent_history': [asdict(s) for s in self.session_history[-100:]],
                    'configuration': {
                        'max_url_plays_per_session': self.max_url_plays_per_session,
                        'session_cooldown_hours': self.session_cooldown_hours,
                        'max_sessions_per_ip': self.max_sessions_per_ip,
                        'session_timeout_hours': self.session_timeout_hours
                    }
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"会话报告已导出到: {file_path}")
                return True
        
        except Exception as e:
            self.logger.error(f"导出会话报告失败: {str(e)}")
            return False

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建会话管理器
    sm = SessionManager()
    
    # 模拟代理和指纹
    proxy = {
        'type': 'http',
        'host': '127.0.0.1',
        'port': 8080
    }
    
    fingerprint = {
        'fingerprint_id': 'test_fingerprint_123'
    }
    
    # 创建会话
    session = sm.create_session(proxy, fingerprint, "https://example.com/video1")
    
    if session:
        print(f"创建会话成功: {session.session_id}")
        
        # 更新使用情况
        for i in range(3):
            if sm.update_session_usage(session.session_id, "https://example.com/video1"):
                print(f"更新使用 {i+1}/3")
            else:
                print("达到使用限制")
                break
        
        # 获取统计
        stats = sm.get_session_stats()
        print(f"会话统计: {stats}")
        
        # 关闭会话
        sm.close_session(session.session_id)
        print("会话已关闭")
