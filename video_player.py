#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频播放器模块
Video Player Module

自动化视频播放功能：
- 智能视频检测
- 广告处理
- 播放控制
- 进度监控
- 拟人化交互
"""

import time
import random
import logging
import re
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)

class VideoPlayer:
    """视频播放器自动化"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 视频平台配置
        self.platform_configs = {
            'youtube.com': {
                'video_selectors': ['video', '.html5-video-container video'],
                'play_button_selectors': [
                    '.ytp-play-button',
                    '.ytp-large-play-button',
                    '[aria-label*="Play"]',
                    '[title*="Play"]'
                ],
                'ad_selectors': [
                    '.ytp-ad-skip-button',
                    '.ytp-ad-skip-button-modern',
                    '[class*="skip"]',
                    '.video-ads',
                    '.ytp-ad-overlay-container'
                ],
                'volume_selectors': ['.ytp-volume-slider', '.ytp-mute-button'],
                'fullscreen_selectors': ['.ytp-fullscreen-button'],
                'progress_selectors': ['.ytp-progress-bar', '.ytp-play-progress'],
                'time_selectors': ['.ytp-time-current', '.ytp-time-duration']
            },
            'bilibili.com': {
                'video_selectors': ['video', '.bilibili-player-video video'],
                'play_button_selectors': [
                    '.bilibili-player-video-btn-start',
                    '.bpx-player-ctrl-play',
                    '[aria-label*="播放"]'
                ],
                'ad_selectors': [
                    '.bilibili-player-video-toast-bottom .bilibili-player-video-toast-item-jump',
                    '.ad-skip-btn',
                    '.close-btn'
                ],
                'volume_selectors': ['.bilibili-player-video-volumebar'],
                'fullscreen_selectors': ['.bilibili-player-video-btn-fullscreen'],
                'progress_selectors': ['.bilibili-player-video-progress-bar'],
                'time_selectors': ['.bilibili-player-video-time-now', '.bilibili-player-video-time-total']
            },
            'default': {
                'video_selectors': ['video'],
                'play_button_selectors': [
                    '[aria-label*="play"]',
                    '[title*="play"]',
                    '.play-button',
                    '.play-btn',
                    'button[class*="play"]'
                ],
                'ad_selectors': [
                    '[class*="skip"]',
                    '[class*="close"]',
                    '.ad-skip',
                    '.skip-ad',
                    '.close-ad'
                ],
                'volume_selectors': ['.volume-control', '.volume-slider'],
                'fullscreen_selectors': ['.fullscreen-button', '.fullscreen-btn'],
                'progress_selectors': ['.progress-bar', '.seek-bar'],
                'time_selectors': ['.current-time', '.duration', '.time-display']
            }
        }
        
        # 播放状态
        self.video_states = {}
        
        # 超时配置
        self.page_load_timeout = 30
        self.element_wait_timeout = 10
        self.video_load_timeout = 15
        self.ad_wait_timeout = 5
    
    def play_video(self, driver, url: str, humanizer=None, play_duration: int = 300) -> bool:
        """播放视频主流程"""
        try:
            self.logger.info(f"开始播放视频: {url}")
            
            # 检查鼠标控制状态
            if humanizer and hasattr(humanizer, 'can_perform_mouse_action'):
                if not humanizer.can_perform_mouse_action():
                    self.logger.info("鼠标操作被禁用或处于冷却期，继续自动化播放")
                else:
                    self.logger.debug("鼠标操作已启用，用户可以进行手动操作")
            
            # 导航到视频页面
            if not self._navigate_to_video(driver, url):
                return False
            
            # 等待页面加载
            if humanizer:
                humanizer.random_wait(2, 5)
            
            # 检测平台
            platform = self._detect_platform(url)
            config = self.platform_configs.get(platform, self.platform_configs['default'])
            
            # 等待视频元素加载
            video_element = self._wait_for_video_element(driver, config)
            if not video_element:
                self.logger.error("未找到视频元素")
                return False
            
            # 处理初始广告
            self._handle_pre_roll_ads(driver, config, humanizer)
            
            # 开始播放
            if not self._start_video_playback(driver, config, humanizer):
                self.logger.error("无法开始播放")
                return False
            
            # 监控播放过程
            return self._monitor_playback(driver, config, humanizer, play_duration)
        
        except Exception as e:
            self.logger.error(f"播放视频失败: {str(e)}")
            return False
    
    def _navigate_to_video(self, driver, url: str) -> bool:
        """导航到视频页面"""
        try:
            driver.get(url)
            
            # 等待页面基本加载
            WebDriverWait(driver, self.page_load_timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            self.logger.debug(f"成功导航到: {url}")
            return True
        
        except TimeoutException:
            self.logger.error(f"页面加载超时: {url}")
            return False
        except Exception as e:
            self.logger.error(f"导航失败: {url} - {str(e)}")
            return False
    
    def _detect_platform(self, url: str) -> str:
        """检测视频平台"""
        for platform in self.platform_configs:
            if platform != 'default' and platform in url.lower():
                self.logger.debug(f"检测到平台: {platform}")
                return platform
        
        self.logger.debug("使用默认平台配置")
        return 'default'
    
    def _wait_for_video_element(self, driver, config: Dict) -> Optional:
        """等待视频元素加载"""
        try:
            for selector in config['video_selectors']:
                try:
                    element = WebDriverWait(driver, self.video_load_timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.debug(f"找到视频元素: {selector}")
                    return element
                except TimeoutException:
                    continue
            
            return None
        
        except Exception as e:
            self.logger.error(f"等待视频元素失败: {str(e)}")
            return None
    
    def _handle_pre_roll_ads(self, driver, config: Dict, humanizer=None):
        """处理前置广告"""
        try:
            self.logger.info("检查前置广告...")
            
            ad_detected = False
            start_time = time.time()
            max_ad_wait = 60  # 最大等待广告时间
            
            while time.time() - start_time < max_ad_wait:
                # 检查是否有广告元素
                ad_elements = []
                for selector in config['ad_selectors']:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        ad_elements.extend(elements)
                    except Exception:
                        continue
                
                if ad_elements:
                    ad_detected = True
                    self.logger.info("检测到广告，等待播放完成...")
                    
                    # 模拟观看广告的行为
                    if humanizer:
                        humanizer.simulate_ad_behavior(driver)
                    
                    # 让广告完整播放，不点击跳过按钮
                    self.logger.info("允许广告完整播放...")
                    
                    # 检查广告播放状态
                    ad_duration = self._get_ad_duration(driver)
                    if ad_duration > 0:
                        self.logger.info(f"广告时长: {ad_duration}秒，等待播放完成...")
                        
                        # 模拟观看广告的行为，但不跳过
                        if humanizer:
                            # 使用高级行为模拟观看广告
                            humanizer.simulate_with_advanced_behavior(driver, "ad_watching", ad_duration)
                            humanizer.simulate_ad_watching_behavior(driver, ad_duration)
                        else:
                            # 等待广告播放完成
                            time.sleep(min(ad_duration + 2, 30))  # 最多等待30秒
                    else:
                        # 如果无法获取广告时长，等待固定时间
                        wait_time = random.uniform(15, 30)  # 15-30秒
                        self.logger.info(f"无法获取广告时长，等待 {wait_time:.1f} 秒...")
                        
                        if humanizer:
                            humanizer.simulate_ad_watching_behavior(driver, wait_time)
                        else:
                            time.sleep(wait_time)
                
                # 检查广告是否结束
                elif ad_detected:
                    self.logger.info("广告播放完成")
                    break
                
                # 短暂等待
                time.sleep(1)
            
            if not ad_detected:
                self.logger.debug("未检测到前置广告")
        
        except Exception as e:
            self.logger.error(f"处理前置广告失败: {str(e)}")
    
    def _get_ad_duration(self, driver) -> float:
        """获取广告时长"""
        try:
            # 尝试多种方法获取广告时长
            ad_selectors = [
                ".ytp-ad-duration-remaining",
                ".ytp-time-duration",
                ".ad-duration",
                "[class*='duration']",
                "[class*='time']"
            ]
            
            for selector in ad_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if self._is_element_visible(element):
                            text = element.text.strip()
                            # 尝试解析时间格式 (如: "0:15", "15", "15s")
                            duration = self._parse_duration_text(text)
                            if 0 < duration <= 60:  # 假设广告时长不超过60秒
                                return duration
                except Exception:
                    continue
            
            # 尝试通过JavaScript获取视频元素的时长，但仅如果确认是广告
            if self._is_ad_present(driver):
                try:
                    duration = driver.execute_script("""
                        var videos = document.querySelectorAll('video');
                        for (var i = 0; i < videos.length; i++) {
                            var video = videos[i];
                            if (video.duration && video.duration > 0 && video.duration <= 60) {
                                return video.duration;
                            }
                        }
                        return 0;
                    """)
                    if duration and duration > 0:
                        return duration
                except Exception:
                    pass
            
            return 0
        
        except Exception as e:
            self.logger.debug(f"获取广告时长失败: {str(e)}")
            return 0
    
    def _is_ad_present(self, driver) -> bool:
        """检查是否真的有广告"""
        ad_indicators = [
            '.ytp-ad-module',
            '.video-ads',
            '[class*="ad-"]',
            '[class*="advert"]'
        ]
        for selector in ad_indicators:
            try:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    return True
            except Exception:
                continue
        return False
    
    def _parse_duration_text(self, text: str) -> float:
        """解析时长文本"""
        try:
            if not text:
                return 0
            
            # 移除非数字字符（除了冒号）
            clean_text = re.sub(r'[^\d:]', '', text)
            
            if ':' in clean_text:
                # 格式: "1:30" or "0:15"
                parts = clean_text.split(':')
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    return minutes * 60 + seconds
            else:
                # 格式: "15" (秒)
                if clean_text.isdigit():
                    return float(clean_text)
            
            return 0
        
        except Exception:
            return 0
    
    def _find_skip_button(self, driver, config: Dict) -> Optional:
        """查找跳过广告按钮"""
        skip_selectors = config['ad_selectors'] + [
            '[class*="skip"]:not([style*="display: none"])',
            '[class*="close"]:not([style*="display: none"])',
            'button[class*="skip"]',
            'div[class*="skip"][role="button"]'
        ]
        
        for selector in skip_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if (self._is_element_visible(element) and 
                        self._is_element_clickable(element) and
                        self._is_skip_button(element)):
                        return element
            except Exception:
                continue
        
        return None
    
    def _is_skip_button(self, element) -> bool:
        """判断是否为跳过按钮"""
        try:
            text = element.text.lower() if element.text else ""
            aria_label = element.get_attribute('aria-label')
            aria_label = aria_label.lower() if aria_label else ""
            title = element.get_attribute('title')
            title = title.lower() if title else ""
            
            skip_keywords = ['skip', 'close', '跳过', '关闭', '×', '✕']
            
            for keyword in skip_keywords:
                if keyword in text or keyword in aria_label or keyword in title:
                    return True
            
            return False
        except Exception:
            return False
    
    def _start_video_playback(self, driver, config: Dict, humanizer=None) -> bool:
        """开始视频播放"""
        try:
            self.logger.info("开始播放视频...")
            
            # 尝试多种方式启动播放
            play_attempts = [
                lambda: self._click_play_button(driver, config, humanizer),
                lambda: self._click_video_element(driver, config, humanizer),
                lambda: self._use_keyboard_control(driver),
                lambda: self._use_javascript_control(driver)
            ]
            
            for attempt in play_attempts:
                try:
                    if attempt():
                        # 等待播放开始
                        if self._wait_for_playback_start(driver):
                            self.logger.info("视频播放已开始")
                            return True
                except Exception as e:
                    self.logger.debug(f"播放尝试失败: {str(e)}")
                    continue
            
            self.logger.error("所有播放尝试均失败")
            return False
        
        except Exception as e:
            self.logger.error(f"开始播放失败: {str(e)}")
            return False
    
    def _click_play_button(self, driver, config: Dict, humanizer=None) -> bool:
        """点击播放按钮"""
        try:
            for selector in config['play_button_selectors']:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if (self._is_element_visible(element) and 
                            self._is_element_clickable(element)):
                            
                            self.logger.debug(f"点击播放按钮: {selector}")
                            
                            if humanizer:
                                humanizer.human_click(driver, element)
                            else:
                                element.click()
                            
                            return True
                except Exception:
                    continue
            
            return False
        
        except Exception as e:
            self.logger.debug(f"点击播放按钮失败: {str(e)}")
            return False
    
    def _click_video_element(self, driver, config: Dict, humanizer=None) -> bool:
        """点击视频元素"""
        try:
            for selector in config['video_selectors']:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if self._is_element_visible(element):
                            self.logger.debug(f"点击视频元素: {selector}")
                            
                            if humanizer:
                                humanizer.human_click(driver, element)
                            else:
                                element.click()
                            
                            return True
                except Exception:
                    continue
            
            return False
        
        except Exception as e:
            self.logger.debug(f"点击视频元素失败: {str(e)}")
            return False
    
    def _use_keyboard_control(self, driver) -> bool:
        """使用键盘控制播放"""
        try:
            # 按空格键开始播放
            body = driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.SPACE)
            self.logger.debug("使用空格键开始播放")
            return True
        
        except Exception as e:
            self.logger.debug(f"键盘控制失败: {str(e)}")
            return False
    
    def _use_javascript_control(self, driver) -> bool:
        """使用JavaScript控制播放"""
        try:
            # 查找视频元素并调用play()方法
            result = driver.execute_script("""
                var videos = document.querySelectorAll('video');
                if (videos.length > 0) {
                    var video = videos[0];
                    if (video.paused) {
                        video.play();
                        return true;
                    }
                }
                return false;
            """)
            
            if result:
                self.logger.debug("使用JavaScript开始播放")
                return True
            
            return False
        
        except Exception as e:
            self.logger.debug(f"JavaScript控制失败: {str(e)}")
            return False
    
    def _wait_for_playback_start(self, driver, timeout: int = 10) -> bool:
        """等待播放开始"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 检查视频是否在播放
                is_playing = driver.execute_script("""
                    var videos = document.querySelectorAll('video');
                    for (var i = 0; i < videos.length; i++) {
                        var video = videos[i];
                        if (!video.paused && video.currentTime > 0 && !video.ended) {
                            return true;
                        }
                    }
                    return false;
                """)
                
                if is_playing:
                    return True
                
                time.sleep(0.5)
            
            return False
        
        except Exception as e:
            self.logger.error(f"等待播放开始失败: {str(e)}")
            return False
    
    def _monitor_playback(self, driver, config: Dict, humanizer=None, play_duration: int = 300) -> bool:
        """监控播放过程"""
        try:
            self.logger.info(f"开始监控播放过程... 设定播放时长: {play_duration}秒")
            
            video_info = self._get_video_info(driver)
            self.logger.info(f"视频信息: 时长={video_info.get('duration', 'Unknown')}秒")
            
            # 开始播放行为模拟
            if humanizer:
                # 使用高级行为模拟视频观看
                humanizer.simulate_with_advanced_behavior(driver, "video_watching", play_duration)
                # 使用设定的播放时长而不是视频实际时长
                humanizer.simulate_video_watching_behavior(driver, play_duration)
            
            # 记录开始时间
            start_time = time.time()
            
            last_progress_check = time.time()
            last_current_time = 0
            stuck_count = 0
            max_stuck_count = 5
            
            while True:
                try:
                    # 获取当前播放状态
                    status = self._get_playback_status(driver)
                    
                    if status['ended']:
                        self.logger.info("视频播放完成")
                        return True
                    
                    if status['error']:
                        self.logger.error(f"视频播放错误: {status['error']}")
                        return False
                    
                    # 检查是否暂停或卡住
                    if status['paused']:
                        self.logger.warning("视频暂停，尝试恢复播放")
                        self._resume_playback(driver, config, humanizer)
                    
                    # 检查是否达到设定的播放时长
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= play_duration:
                        self.logger.info(f"已播放 {elapsed_time:.1f}秒，达到设定时长 {play_duration}秒，结束播放")
                        return True
                    
                    # 检查播放进度
                    current_time = status['current_time']
                    if current_time == last_current_time:
                        stuck_count += 1
                        if stuck_count >= max_stuck_count:
                            self.logger.warning("视频播放可能卡住，尝试恢复")
                            self._handle_playback_stuck(driver, config, humanizer)
                            stuck_count = 0
                    else:
                        stuck_count = 0
                        last_current_time = current_time
                    
                    # 处理播放中的广告
                    self._handle_mid_roll_ads(driver, config, humanizer)
                    
                    # 定期进度报告
                    now = time.time()
                    if now - last_progress_check > 30:  # 每30秒报告一次
                        progress = (current_time / status['duration'] * 100) if status['duration'] > 0 else 0
                        self.logger.info(f"播放进度: {current_time:.1f}s / {status['duration']:.1f}s ({progress:.1f}%)")
                        last_progress_check = now
                    
                    # 检查鼠标控制状态
                    if humanizer and hasattr(humanizer, 'can_perform_mouse_action'):
                        if not humanizer.can_perform_mouse_action():
                            self.logger.debug("鼠标操作处于冷却期，继续自动化播放")
                    
                    # 随机进行拟人化操作
                    if humanizer and random.random() < 0.1:  # 10%概率
                        humanizer.simulate_page_interaction(driver)
                    
                    # 等待间隔
                    time.sleep(2)
                
                except StaleElementReferenceException:
                    # 页面元素已失效，可能页面发生了变化
                    self.logger.debug("页面元素已失效，继续监控")
                    time.sleep(1)
                    continue
                except Exception as e:
                    self.logger.warning(f"监控过程中发生错误: {str(e)}")
                    time.sleep(2)
                    continue
        
        except Exception as e:
            self.logger.error(f"监控播放失败: {str(e)}")
            return False
    
    def _get_video_info(self, driver) -> Dict:
        """获取视频信息"""
        try:
            info = driver.execute_script("""
                var videos = document.querySelectorAll('video');
                if (videos.length > 0) {
                    var video = videos[0];
                    return {
                        duration: video.duration || 0,
                        current_time: video.currentTime || 0,
                        width: video.videoWidth || 0,
                        height: video.videoHeight || 0,
                        ready_state: video.readyState,
                        network_state: video.networkState
                    };
                }
                return {};
            """)
            
            return info or {}
        
        except Exception as e:
            self.logger.debug(f"获取视频信息失败: {str(e)}")
            return {}
    
    def _get_playback_status(self, driver) -> Dict:
        """获取播放状态"""
        try:
            status = driver.execute_script("""
                var videos = document.querySelectorAll('video');
                if (videos.length > 0) {
                    var video = videos[0];
                    return {
                        paused: video.paused,
                        ended: video.ended,
                        current_time: video.currentTime || 0,
                        duration: video.duration || 0,
                        error: video.error ? video.error.message : null,
                        buffered: video.buffered.length > 0 ? video.buffered.end(video.buffered.length - 1) : 0,
                        ready_state: video.readyState,
                        seeking: video.seeking
                    };
                }
                return {
                    paused: true,
                    ended: false,
                    current_time: 0,
                    duration: 0,
                    error: 'No video element found',
                    buffered: 0,
                    ready_state: 0,
                    seeking: false
                };
            """)
            
            return status
        
        except Exception as e:
            self.logger.debug(f"获取播放状态失败: {str(e)}")
            return {
                'paused': True,
                'ended': False,
                'current_time': 0,
                'duration': 0,
                'error': str(e),
                'buffered': 0,
                'ready_state': 0,
                'seeking': False
            }
    
    def _resume_playback(self, driver, config: Dict, humanizer=None):
        """恢复播放"""
        try:
            self.logger.debug("尝试恢复播放...")
            
            # 尝试点击播放按钮
            if self._click_play_button(driver, config, humanizer):
                return
            
            # 尝试点击视频
            if self._click_video_element(driver, config, humanizer):
                return
            
            # 使用JavaScript恢复
            driver.execute_script("""
                var videos = document.querySelectorAll('video');
                if (videos.length > 0) {
                    videos[0].play();
                }
            """)
        
        except Exception as e:
            self.logger.debug(f"恢复播放失败: {str(e)}")
    
    def _handle_playback_stuck(self, driver, config: Dict, humanizer=None):
        """处理播放卡住"""
        try:
            self.logger.debug("处理播放卡住...")
            
            # 刷新页面
            driver.refresh()
            
            if humanizer:
                humanizer.random_wait(3, 6)
            
            # 重新开始播放
            self._start_video_playback(driver, config, humanizer)
        
        except Exception as e:
            self.logger.error(f"处理播放卡住失败: {str(e)}")
    
    def _handle_mid_roll_ads(self, driver, config: Dict, humanizer=None):
        """处理播放中的广告"""
        try:
            # 检查是否有广告
            ad_elements = []
            for selector in config['ad_selectors']:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    ad_elements.extend([e for e in elements if self._is_element_visible(e)])
                except Exception:
                    continue
            
            if ad_elements:
                self.logger.info("检测到播放中广告")
                
                # 让播放中的广告完整播放
                self.logger.info("检测到播放中广告，允许完整播放...")
                
                ad_duration = self._get_ad_duration(driver)
                if ad_duration > 0:
                    self.logger.info(f"播放中广告时长: {ad_duration}秒")
                    if humanizer:
                        # 使用高级行为模拟播放中广告观看
                        humanizer.simulate_with_advanced_behavior(driver, "ad_watching", ad_duration)
                        humanizer.simulate_ad_watching_behavior(driver, ad_duration)
                    else:
                        time.sleep(min(ad_duration + 2, 45))  # 最多等待45秒
                else:
                    # 等待播放中广告的默认时间
                    wait_time = random.uniform(20, 40)  # 20-40秒
                    self.logger.info(f"播放中广告等待 {wait_time:.1f} 秒...")
                    
                    if humanizer:
                        humanizer.simulate_ad_watching_behavior(driver, wait_time)
                    else:
                        time.sleep(wait_time)
                
                self.logger.info("播放中广告处理完成")
        
        except Exception as e:
            self.logger.debug(f"处理播放中广告失败: {str(e)}")
    
    def _is_element_visible(self, element) -> bool:
        """检查元素是否可见"""
        try:
            return (element.is_displayed() and 
                   element.size['height'] > 0 and 
                   element.size['width'] > 0)
        except Exception:
            return False
    
    def _is_element_clickable(self, element) -> bool:
        """检查元素是否可点击"""
        try:
            return (self._is_element_visible(element) and 
                   element.is_enabled())
        except Exception:
            return False

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("视频播放器模块加载完成")
    
    # 这里可以添加更多测试代码
    player = VideoPlayer()
    print(f"支持的平台: {list(player.platform_configs.keys())}")
