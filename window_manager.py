#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口管理器模块
Window Manager Module

管理多窗口并发播放：
- 窗口生命周期管理
- 资源分配和回收
- 状态监控
- 错误处理和恢复
"""

import time
import threading
import logging
import queue
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum

class WindowStatus(Enum):
    """窗口状态枚举"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PLAYING = "playing"
    ERROR = "error"
    PAUSED = "paused"
    CLOSING = "closing"
    CLOSED = "closed"

@dataclass
class WindowInfo:
    """窗口信息"""
    window_id: str
    thread_id: str
    proxy_info: Dict
    fingerprint_info: Dict
    current_url: str
    status: WindowStatus
    created_at: str
    last_activity: str
    play_count: int
    error_count: int
    last_error: Optional[str] = None
    session_id: Optional[str] = None

class WindowManager:
    """窗口管理器"""
    
    def __init__(self, max_windows: int = 5):
        self.logger = logging.getLogger(__name__)
        
        # 配置
        self.max_windows = max_windows
        self.window_timeout = 300  # 5分钟超时
        
        # 窗口存储
        self.windows: Dict[str, WindowInfo] = {}
        self.window_drivers: Dict[str, object] = {}
        self.window_threads: Dict[str, threading.Thread] = {}
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_windows, 
                                         thread_name_prefix="VideoWindow")
        
        # 状态队列
        self.status_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # 锁
        self.lock = threading.Lock()
        
        # 回调函数
        self.status_callback: Optional[Callable] = None
        
        # 运行状态
        self.is_running = True
        
        # 启动管理线程
        self.management_thread = threading.Thread(
            target=self._management_loop, 
            daemon=True
        )
        self.management_thread.start()
    
    def create_window(self, proxy: Dict, fingerprint: Dict, url: str, 
                     browser_automation, video_player, humanizer, session_manager, 
                     proxy_manager=None, fingerprint_engine=None,
                     platform_config=None, selected_platform=None, 
                     earnvids_strategy=1, headless=False) -> Optional[str]:
        """创建新窗口"""
        try:
            with self.lock:
                # 检查窗口数量限制
                active_windows = len([w for w in self.windows.values() 
                                    if w.status not in [WindowStatus.CLOSED, WindowStatus.ERROR]])
                
                if active_windows >= self.max_windows:
                    self.logger.warning(f"已达到最大窗口数限制: {self.max_windows}")
                    return None
                
                # 生成窗口ID
                window_id = str(uuid.uuid4())
                
                # 创建窗口信息
                window_info = WindowInfo(
                    window_id=window_id,
                    thread_id="",
                    proxy_info=proxy.copy() if proxy else {},
                    fingerprint_info=fingerprint.copy(),
                    current_url=url,
                    status=WindowStatus.INITIALIZING,
                    created_at=datetime.now().isoformat(),
                    last_activity=datetime.now().isoformat(),
                    play_count=0,
                    error_count=0
                )
                
                # 存储窗口信息
                self.windows[window_id] = window_info
                
                # 提交窗口任务
                future = self.executor.submit(
                    self._run_window,
                    window_id, proxy, fingerprint, url,
                    browser_automation, video_player, humanizer, session_manager,
                    proxy_manager, fingerprint_engine, platform_config, selected_platform, earnvids_strategy, headless
                )
                
                self.logger.info(f"创建窗口: {window_id[:8]}... (当前活跃: {active_windows + 1}/{self.max_windows})")
                
                return window_id
        
        except Exception as e:
            self.logger.error(f"创建窗口失败: {str(e)}")
            return None
    
    def _run_window(self, window_id: str, proxy: Dict, fingerprint: Dict, url: str,
                   browser_automation, video_player, humanizer, session_manager,
                   proxy_manager=None, fingerprint_engine=None, platform_config=None, 
                   selected_platform=None, earnvids_strategy=1, headless=False):
        """运行窗口线程"""
        driver = None
        session = None
        
        try:
            # 更新线程ID
            self.windows[window_id].thread_id = threading.current_thread().name
            
            self.logger.info(f"窗口 {window_id[:8]}... 开始运行")
            
            # 创建会话
            session = session_manager.create_session(proxy, fingerprint, url)
            if session:
                self.windows[window_id].session_id = session.session_id
            
            # 创建浏览器
            self._update_window_status(window_id, WindowStatus.INITIALIZING, "创建浏览器...")
            
            browser_config = {
                'headless': headless,  # 使用传入的headless参数
                'stealth': True,
                'disable_images': False,
                'disable_js': False
            }
            
            self.logger.info(f"窗口 {window_id[:8]}... {'无头模式' if headless else '可视模式'}创建浏览器")
            
            driver = browser_automation.create_browser(proxy, fingerprint, browser_config)
            if not driver:
                raise Exception("无法创建浏览器实例")
            
            # 存储驱动
            with self.lock:
                self.window_drivers[window_id] = driver
            
            self._update_window_status(window_id, WindowStatus.ACTIVE, "浏览器创建成功")
            
            # 播放循环
            url_play_count = 0
            max_plays_per_url = 3
            
            while self.is_running and self._is_window_active(window_id):
                try:
                    # 检查会话是否需要轮换
                    if session and session_manager.should_rotate_session(session.session_id, url):
                        self.logger.info(f"窗口 {window_id[:8]}... 需要轮换会话")
                        
                        # 关闭当前浏览器
                        driver.quit()
                        
                        # 轮换会话 - 获取新的代理和指纹
                        new_proxy = proxy_manager.get_next_proxy()  # 获取下一个代理
                        new_fingerprint = fingerprint_engine.generate_fingerprint()  # 生成新指纹
                        
                        if not new_proxy:
                            self.logger.warning(f"窗口 {window_id[:8]}... 无法获取新代理，使用当前代理")
                            new_proxy = proxy
                        
                        session = session_manager.rotate_session(
                            session.session_id, new_proxy, new_fingerprint, url
                        )
                        
                        # 创建新浏览器
                        driver = browser_automation.create_browser(new_proxy, new_fingerprint, browser_config)
                        if not driver:
                            raise Exception("轮换后无法创建浏览器")
                        
                        with self.lock:
                            self.window_drivers[window_id] = driver
                            self.windows[window_id].proxy_info = new_proxy
                            self.windows[window_id].fingerprint_info = new_fingerprint
                        
                        url_play_count = 0
                    
                    # 播放视频
                    self._update_window_status(window_id, WindowStatus.PLAYING, f"播放视频: {url}")
                    
                    # 获取播放时长
                    play_duration = 300  # 默认时长
                    if platform_config and selected_platform:
                        if platform_config.is_earnvids_platform(selected_platform):
                            play_duration = platform_config.get_random_duration(selected_platform, earnvids_strategy)
                        else:
                            play_duration = platform_config.get_random_duration(selected_platform)
                    
                    success = video_player.play_video(driver, url, humanizer, play_duration)
                    
                    if success:
                        url_play_count += 1
                        self.windows[window_id].play_count += 1
                        
                        # 更新会话使用情况
                        if session:
                            session_manager.update_session_usage(session.session_id, url)
                        
                        self.logger.info(f"窗口 {window_id[:8]}... 播放完成 ({url_play_count}/{max_plays_per_url})")
                        
                        # 检查是否达到播放限制
                        if url_play_count >= max_plays_per_url:
                            self.logger.info(f"窗口 {window_id[:8]}... 达到播放限制，准备轮换")
                            url_play_count = 0
                    else:
                        self.logger.warning(f"窗口 {window_id[:8]}... 播放失败")
                        self._handle_window_error(window_id, "视频播放失败")
                    
                    # 更新活动时间
                    self.windows[window_id].last_activity = datetime.now().isoformat()
                    
                    # 随机等待
                    if humanizer:
                        humanizer.random_wait(5, 15)
                
                except Exception as e:
                    self.logger.error(f"窗口 {window_id[:8]}... 播放循环错误: {str(e)}")
                    self._handle_window_error(window_id, str(e))
                    
                    # 错误恢复等待
                    time.sleep(30)
        
        except Exception as e:
            self.logger.error(f"窗口 {window_id[:8]}... 运行失败: {str(e)}")
            self._handle_window_error(window_id, str(e))
        
        finally:
            # 清理资源
            self._cleanup_window(window_id, driver, session, session_manager)
    
    def _cleanup_window(self, window_id: str, driver, session, session_manager):
        """清理窗口资源"""
        try:
            self.logger.info(f"清理窗口资源: {window_id[:8]}...")
            
            # 关闭浏览器
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.debug(f"关闭浏览器失败: {str(e)}")
            
            # 关闭会话
            if session and session_manager:
                try:
                    session_manager.close_session(session.session_id)
                except Exception as e:
                    self.logger.debug(f"关闭会话失败: {str(e)}")
            
            # 从存储中移除
            with self.lock:
                self.window_drivers.pop(window_id, None)
                if window_id in self.windows:
                    self.windows[window_id].status = WindowStatus.CLOSED
            
            self._update_window_status(window_id, WindowStatus.CLOSED, "窗口已关闭")
        
        except Exception as e:
            self.logger.error(f"清理窗口资源失败: {str(e)}")
    
    def _update_window_status(self, window_id: str, status: WindowStatus, message: str = ""):
        """更新窗口状态"""
        try:
            with self.lock:
                if window_id in self.windows:
                    self.windows[window_id].status = status
                    self.windows[window_id].last_activity = datetime.now().isoformat()
            
            # 发送状态更新
            status_update = {
                'window_id': window_id,
                'status': status.value,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                self.status_queue.put_nowait(status_update)
            except queue.Full:
                pass  # 队列满了就丢弃
            
            # 调用回调函数
            if self.status_callback:
                try:
                    self.status_callback(status_update)
                except Exception as e:
                    self.logger.debug(f"状态回调失败: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"更新窗口状态失败: {str(e)}")
    
    def _handle_window_error(self, window_id: str, error_message: str):
        """处理窗口错误"""
        try:
            with self.lock:
                if window_id in self.windows:
                    window = self.windows[window_id]
                    window.error_count += 1
                    window.last_error = error_message
                    
                    # 如果错误次数过多，关闭窗口
                    if window.error_count >= 3:
                        window.status = WindowStatus.ERROR
                        self.logger.error(f"窗口 {window_id[:8]}... 错误次数过多，标记为错误状态")
            
            self._update_window_status(window_id, WindowStatus.ERROR, error_message)
        
        except Exception as e:
            self.logger.error(f"处理窗口错误失败: {str(e)}")
    
    def _is_window_active(self, window_id: str) -> bool:
        """检查窗口是否活跃"""
        try:
            with self.lock:
                if window_id not in self.windows:
                    return False
                
                window = self.windows[window_id]
                return window.status not in [WindowStatus.CLOSED, WindowStatus.ERROR, WindowStatus.CLOSING]
        
        except Exception:
            return False
    
    def close_window(self, window_id: str):
        """关闭指定窗口"""
        try:
            with self.lock:
                if window_id in self.windows:
                    self.windows[window_id].status = WindowStatus.CLOSING
            
            # 关闭浏览器
            if window_id in self.window_drivers:
                try:
                    driver = self.window_drivers[window_id]
                    driver.quit()
                except Exception as e:
                    self.logger.debug(f"关闭浏览器失败: {str(e)}")
            
            self.logger.info(f"窗口 {window_id[:8]}... 已请求关闭")
        
        except Exception as e:
            self.logger.error(f"关闭窗口失败: {str(e)}")
    
    def close_all_windows(self):
        """关闭所有窗口"""
        try:
            window_ids = list(self.windows.keys())
            
            for window_id in window_ids:
                self.close_window(window_id)
            
            # 等待所有任务完成
            self.executor.shutdown(wait=True)
            
            self.logger.info("所有窗口已关闭")
        
        except Exception as e:
            self.logger.error(f"关闭所有窗口失败: {str(e)}")
    
    def pause_window(self, window_id: str):
        """暂停窗口"""
        try:
            with self.lock:
                if window_id in self.windows:
                    self.windows[window_id].status = WindowStatus.PAUSED
            
            self._update_window_status(window_id, WindowStatus.PAUSED, "窗口已暂停")
        
        except Exception as e:
            self.logger.error(f"暂停窗口失败: {str(e)}")
    
    def resume_window(self, window_id: str):
        """恢复窗口"""
        try:
            with self.lock:
                if window_id in self.windows:
                    window = self.windows[window_id]
                    if window.status == WindowStatus.PAUSED:
                        window.status = WindowStatus.ACTIVE
            
            self._update_window_status(window_id, WindowStatus.ACTIVE, "窗口已恢复")
        
        except Exception as e:
            self.logger.error(f"恢复窗口失败: {str(e)}")
    
    def get_window_info(self, window_id: str) -> Optional[WindowInfo]:
        """获取窗口信息"""
        with self.lock:
            return self.windows.get(window_id)
    
    def get_all_windows(self) -> List[WindowInfo]:
        """获取所有窗口信息"""
        with self.lock:
            return list(self.windows.values())
    
    def get_active_windows_count(self) -> int:
        """获取活跃窗口数量"""
        with self.lock:
            return len([w for w in self.windows.values() 
                       if w.status not in [WindowStatus.CLOSED, WindowStatus.ERROR]])
    
    def get_status_updates(self) -> List[Dict]:
        """获取状态更新"""
        updates = []
        try:
            while not self.status_queue.empty():
                updates.append(self.status_queue.get_nowait())
        except queue.Empty:
            pass
        
        return updates
    
    def set_status_callback(self, callback: Callable):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def _management_loop(self):
        """管理循环"""
        try:
            while self.is_running:
                try:
                    # 清理已关闭的窗口
                    self._cleanup_closed_windows()
                    
                    # 检查超时窗口
                    self._check_timeout_windows()
                    
                    # 处理命令队列
                    self._process_commands()
                    
                    time.sleep(5)  # 每5秒检查一次
                
                except Exception as e:
                    self.logger.error(f"管理循环错误: {str(e)}")
                    time.sleep(5)
        
        except Exception as e:
            self.logger.error(f"管理循环失败: {str(e)}")
    
    def _cleanup_closed_windows(self):
        """清理已关闭的窗口"""
        try:
            closed_windows = []
            
            with self.lock:
                for window_id, window in self.windows.items():
                    if window.status == WindowStatus.CLOSED:
                        # 保留一段时间后删除
                        try:
                            last_activity = datetime.fromisoformat(window.last_activity)
                            if (datetime.now() - last_activity).seconds > 300:  # 5分钟后删除
                                closed_windows.append(window_id)
                        except Exception:
                            closed_windows.append(window_id)
            
            for window_id in closed_windows:
                with self.lock:
                    self.windows.pop(window_id, None)
                    self.window_drivers.pop(window_id, None)
        
        except Exception as e:
            self.logger.error(f"清理已关闭窗口失败: {str(e)}")
    
    def _check_timeout_windows(self):
        """检查超时窗口"""
        try:
            timeout_windows = []
            
            with self.lock:
                for window_id, window in self.windows.items():
                    if window.status in [WindowStatus.ACTIVE, WindowStatus.PLAYING]:
                        try:
                            last_activity = datetime.fromisoformat(window.last_activity)
                            if (datetime.now() - last_activity).seconds > self.window_timeout:
                                timeout_windows.append(window_id)
                        except Exception:
                            continue
            
            for window_id in timeout_windows:
                self.logger.warning(f"窗口 {window_id[:8]}... 超时，关闭窗口")
                self.close_window(window_id)
        
        except Exception as e:
            self.logger.error(f"检查超时窗口失败: {str(e)}")
    
    def _process_commands(self):
        """处理命令队列"""
        try:
            while not self.command_queue.empty():
                try:
                    command = self.command_queue.get_nowait()
                    self._execute_command(command)
                except queue.Empty:
                    break
        
        except Exception as e:
            self.logger.error(f"处理命令失败: {str(e)}")
    
    def _execute_command(self, command: Dict):
        """执行命令"""
        try:
            cmd_type = command.get('type')
            window_id = command.get('window_id')
            
            if cmd_type == 'close' and window_id:
                self.close_window(window_id)
            elif cmd_type == 'pause' and window_id:
                self.pause_window(window_id)
            elif cmd_type == 'resume' and window_id:
                self.resume_window(window_id)
            elif cmd_type == 'close_all':
                self.close_all_windows()
        
        except Exception as e:
            self.logger.error(f"执行命令失败: {str(e)}")
    
    def send_command(self, command: Dict):
        """发送命令"""
        try:
            self.command_queue.put_nowait(command)
        except queue.Full:
            self.logger.warning("命令队列已满，命令被丢弃")
    
    def shutdown(self):
        """关闭窗口管理器"""
        try:
            self.is_running = False
            self.close_all_windows()
            
            # 等待管理线程结束
            if self.management_thread.is_alive():
                self.management_thread.join(timeout=10)
            
            self.logger.info("窗口管理器已关闭")
        
        except Exception as e:
            self.logger.error(f"关闭窗口管理器失败: {str(e)}")

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建窗口管理器
    wm = WindowManager(max_windows=3)
    
    try:
        print("窗口管理器创建成功")
        print(f"最大窗口数: {wm.max_windows}")
        print(f"当前活跃窗口: {wm.get_active_windows_count()}")
        
        # 模拟运行一段时间
        time.sleep(5)
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    
    finally:
        wm.shutdown()
