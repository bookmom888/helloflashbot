#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拟人化操作引擎
Humanization Engine

模拟真实用户行为，包括：
- 随机延迟
- 自然鼠标移动
- 随机滚动
- 页面交互
- 打字模拟
- 窗口操作
"""

import random
import time
import math
import logging
from typing import Tuple, List, Optional, Dict
import threading
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pyautogui
from human_behavior_advanced import AdvancedHumanBehavior

class HumanizationEngine:
    """拟人化操作引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 延迟配置
        self.min_delay = 0.5
        self.max_delay = 3.0
        self.typing_delay_range = (0.05, 0.15)
        self.click_delay_range = (0.1, 0.3)
        
        # 鼠标移动配置
        self.mouse_speed_range = (0.5, 2.0)
        self.mouse_variance = 5  # 鼠标位置随机偏移
        
        # 滚动配置
        self.scroll_speed_range = (100, 500)
        self.scroll_pause_range = (0.2, 1.0)
        
        # 行为模式配置
        self.read_time_per_word = 0.2  # 每个单词的阅读时间（秒）
        self.pause_probability = 0.15   # 随机暂停概率
        self.scroll_probability = 0.3   # 随机滚动概率
        self.mouse_move_probability = 0.25  # 随机鼠标移动概率
        
        # 禁用pyautogui的安全检查
        pyautogui.FAILSAFE = False
        
        # 高级人性化行为引擎
        self.advanced_behavior = AdvancedHumanBehavior()
        
        # 鼠标操作管理
        self.mouse_control_enabled = True  # 是否允许手动鼠标操作
        self.mouse_safe_zones = []  # 鼠标安全区域
        self.last_mouse_position = None  # 记录上次鼠标位置
        self.mouse_interaction_cooldown = 2.0  # 鼠标交互冷却时间（秒）
        self.last_mouse_interaction = 0  # 上次鼠标交互时间
    
    def random_wait(self, min_time: float = None, max_time: float = None):
        """随机等待"""
        min_time = min_time or self.min_delay
        max_time = max_time or self.max_delay
        
        wait_time = random.uniform(min_time, max_time)
        self.logger.debug(f"随机等待 {wait_time:.2f} 秒")
        time.sleep(wait_time)
    
    def human_type(self, element, text: str, clear_first: bool = True):
        """拟人化打字"""
        try:
            if clear_first:
                element.clear()
                self.random_wait(0.1, 0.3)
            
            for char in text:
                element.send_keys(char)
                
                # 随机打字延迟
                delay = random.uniform(*self.typing_delay_range)
                time.sleep(delay)
                
                # 偶尔暂停
                if random.random() < 0.1:
                    self.random_wait(0.2, 0.8)
        
        except Exception as e:
            self.logger.error(f"拟人化打字失败: {str(e)}")
    
    def human_click(self, driver, element):
        """拟人化点击"""
        try:
            # 先移动到元素附近
            self.move_to_element_naturally(driver, element)
            
            # 随机延迟
            delay = random.uniform(*self.click_delay_range)
            time.sleep(delay)
            
            # 点击
            element.click()
            
            # 点击后延迟
            self.random_wait(0.2, 0.8)
        
        except Exception as e:
            self.logger.error(f"拟人化点击失败: {str(e)}")
    
    def move_to_element_naturally(self, driver, element):
        """自然地移动到元素"""
        try:
            # 获取元素位置和大小
            location = element.location
            size = element.size
            
            # 计算目标位置（元素中心附近的随机点）
            target_x = location['x'] + size['width'] // 2 + random.randint(-self.mouse_variance, self.mouse_variance)
            target_y = location['y'] + size['height'] // 2 + random.randint(-self.mouse_variance, self.mouse_variance)
            
            # 使用ActionChains移动鼠标
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(element, 
                                              random.randint(-5, 5), 
                                              random.randint(-5, 5))
            actions.perform()
            
            # 随机短暂停留
            if random.random() < 0.3:
                self.random_wait(0.1, 0.5)
        
        except Exception as e:
            self.logger.debug(f"鼠标移动失败: {str(e)}")
    
    def enable_mouse_control(self, enabled: bool = True):
        """启用或禁用鼠标控制"""
        self.mouse_control_enabled = enabled
        self.logger.info(f"鼠标控制已{'启用' if enabled else '禁用'}")
    
    def add_mouse_safe_zone(self, x1: int, y1: int, x2: int, y2: int, description: str = ""):
        """添加鼠标安全区域"""
        safe_zone = {
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'description': description
        }
        self.mouse_safe_zones.append(safe_zone)
        self.logger.info(f"添加鼠标安全区域: {description} ({x1},{y1}) - ({x2},{y2})")
    
    def is_mouse_in_safe_zone(self, x: int, y: int) -> bool:
        """检查鼠标是否在安全区域内"""
        for zone in self.mouse_safe_zones:
            if zone['x1'] <= x <= zone['x2'] and zone['y1'] <= y <= zone['y2']:
                return True
        return False
    
    def can_perform_mouse_action(self) -> bool:
        """检查是否可以执行鼠标操作"""
        if not self.mouse_control_enabled:
            return False
        
        current_time = time.time()
        if current_time - self.last_mouse_interaction < self.mouse_interaction_cooldown:
            return False
        
        return True
    
    def record_mouse_interaction(self):
        """记录鼠标交互时间"""
        self.last_mouse_interaction = time.time()
    
    def get_mouse_guidelines(self) -> Dict:
        """获取鼠标操作指南"""
        return {
            'enabled': self.mouse_control_enabled,
            'safe_zones': self.mouse_safe_zones,
            'cooldown': self.mouse_interaction_cooldown,
            'guidelines': [
                "✅ 可以在安全区域内自由移动鼠标",
                "✅ 避免在视频播放区域进行点击",
                "✅ 保持鼠标移动自然，避免突然跳跃",
                "⚠️ 不要干扰自动化操作区域",
                "⚠️ 避免在广告或弹窗区域点击",
                "⏱️ 每次交互后有冷却时间"
            ]
        }
    
    def random_mouse_movement(self, driver):
        """随机鼠标移动"""
        try:
            if random.random() < self.mouse_move_probability:
                # 获取页面大小
                viewport_width = driver.execute_script("return window.innerWidth")
                viewport_height = driver.execute_script("return window.innerHeight")
                
                # 随机移动到页面某个位置
                x = random.randint(50, viewport_width - 50)
                y = random.randint(50, viewport_height - 50)
                
                actions = ActionChains(driver)
                actions.move_by_offset(x - viewport_width//2, y - viewport_height//2)
                actions.perform()
                
                self.logger.debug(f"随机鼠标移动到 ({x}, {y})")
        
        except Exception as e:
            self.logger.debug(f"随机鼠标移动失败: {str(e)}")
    
    def random_scroll(self, driver):
        """随机滚动"""
        try:
            if random.random() < self.scroll_probability:
                # 随机滚动方向和距离
                scroll_direction = random.choice([-1, 1])
                scroll_distance = random.randint(*self.scroll_speed_range)
                
                # 执行滚动
                driver.execute_script(f"window.scrollBy(0, {scroll_direction * scroll_distance});")
                
                # 滚动后暂停
                pause_time = random.uniform(*self.scroll_pause_range)
                time.sleep(pause_time)
                
                self.logger.debug(f"随机滚动 {scroll_direction * scroll_distance} 像素")
        
        except Exception as e:
            self.logger.debug(f"随机滚动失败: {str(e)}")
    
    def simulate_reading(self, text_length: int = 100):
        """模拟阅读时间"""
        word_count = text_length // 5  # 假设平均每个单词5个字符
        reading_time = word_count * self.read_time_per_word
        
        # 添加随机性
        reading_time *= random.uniform(0.8, 1.2)
        
        # 分段等待，期间可能有其他操作
        segments = random.randint(2, 5)
        segment_time = reading_time / segments
        
        for i in range(segments):
            time.sleep(segment_time)
            
            # 随机进行一些操作
            if random.random() < 0.3:
                # 可能的鼠标移动或暂停
                self.random_wait(0.1, 0.5)
        
        self.logger.debug(f"模拟阅读 {reading_time:.2f} 秒")
    
    def simulate_page_interaction(self, driver):
        """模拟页面交互"""
        try:
            interactions = []
            
            # 添加可能的交互
            if random.random() < self.mouse_move_probability:
                interactions.append(lambda: self.random_mouse_movement(driver))
            
            if random.random() < self.scroll_probability:
                interactions.append(lambda: self.random_scroll(driver))
            
            if random.random() < self.pause_probability:
                interactions.append(lambda: self.random_wait(1.0, 3.0))
            
            # 随机执行交互
            if interactions:
                random.shuffle(interactions)
                for interaction in interactions[:random.randint(1, len(interactions))]:
                    interaction()
        
        except Exception as e:
            self.logger.debug(f"页面交互模拟失败: {str(e)}")
    
    def wait_for_element_naturally(self, driver, by, value, timeout: int = 10):
        """自然地等待元素出现"""
        try:
            # 添加一些随机延迟
            self.random_wait(0.5, 1.5)
            
            # 等待元素
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            
            # 等待后可能的交互
            self.simulate_page_interaction(driver)
            
            return element
        
        except TimeoutException:
            self.logger.warning(f"等待元素超时: {value}")
            return None
    
    def scroll_to_element_naturally(self, driver, element):
        """自然地滚动到元素"""
        try:
            # 获取元素位置
            location = element.location
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # 计算需要滚动的距离
            scroll_to = location['y'] - viewport_height // 2
            
            # 分段滚动，模拟用户寻找元素的过程
            current_scroll = driver.execute_script("return window.pageYOffset")
            distance = scroll_to - current_scroll
            
            if abs(distance) > 100:  # 只有距离足够大才滚动
                segments = random.randint(2, 4)
                segment_distance = distance / segments
                
                for i in range(segments):
                    # 滚动一段
                    current_scroll += segment_distance
                    driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                    
                    # 随机暂停
                    pause_time = random.uniform(0.3, 0.8)
                    time.sleep(pause_time)
                    
                    # 可能的鼠标移动
                    if random.random() < 0.4:
                        self.random_mouse_movement(driver)
                
                # 最终精确滚动到元素
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                self.random_wait(0.5, 1.0)
        
        except Exception as e:
            self.logger.debug(f"滚动到元素失败: {str(e)}")
    
    def find_and_click_naturally(self, driver, by, value, timeout: int = 10):
        """自然地查找并点击元素"""
        try:
            # 先等待元素出现
            element = self.wait_for_element_naturally(driver, by, value, timeout)
            if not element:
                return False
            
            # 滚动到元素
            self.scroll_to_element_naturally(driver, element)
            
            # 等待一下，模拟用户确认
            self.random_wait(0.5, 1.5)
            
            # 点击
            self.human_click(driver, element)
            
            return True
        
        except Exception as e:
            self.logger.error(f"自然点击失败: {str(e)}")
            return False
    
    def simulate_video_watching_behavior(self, driver, video_duration: int = 0):
        """模拟视频观看行为"""
        try:
            self.logger.info("开始模拟视频观看行为")
            
            behaviors = []
            
            # 如果知道视频时长，计算观看行为
            if video_duration > 0:
                # 视频观看期间的行为
                watch_intervals = random.randint(3, 8)
                interval_duration = video_duration / watch_intervals
                
                for i in range(watch_intervals):
                    # 正常观看
                    time.sleep(interval_duration * 0.8)
                    
                    # 随机行为
                    behavior = random.choice([
                        'mouse_move',
                        'small_scroll', 
                        'pause_resume',
                        'volume_adjust',
                        'fullscreen_toggle',
                        'nothing'
                    ])
                    
                    if behavior == 'mouse_move':
                        self.random_mouse_movement(driver)
                    elif behavior == 'small_scroll':
                        self.small_random_scroll(driver)
                    elif behavior == 'pause_resume':
                        self.simulate_pause_resume(driver)
                    elif behavior == 'volume_adjust':
                        self.simulate_volume_adjust(driver)
                    elif behavior == 'fullscreen_toggle':
                        self.simulate_fullscreen_toggle(driver)
                    
                    # 剩余时间
                    time.sleep(interval_duration * 0.2)
            else:
                # 未知时长，使用定时行为
                behavior_thread = threading.Thread(
                    target=self._continuous_video_behaviors,
                    args=(driver,),
                    daemon=True
                )
                behavior_thread.start()
        
        except Exception as e:
            self.logger.error(f"视频观看行为模拟失败: {str(e)}")
    
    def _continuous_video_behaviors(self, driver):
        """持续的视频观看行为"""
        try:
            while True:
                # 随机等待
                wait_time = random.uniform(10, 60)
                time.sleep(wait_time)
                
                # 随机行为
                behavior = random.choice([
                    'mouse_move', 'small_scroll', 'pause_resume', 'nothing'
                ])
                
                if behavior == 'mouse_move':
                    self.random_mouse_movement(driver)
                elif behavior == 'small_scroll':
                    self.small_random_scroll(driver)
                elif behavior == 'pause_resume':
                    self.simulate_pause_resume(driver)
        
        except Exception as e:
            self.logger.debug(f"持续行为模拟停止: {str(e)}")
    
    def small_random_scroll(self, driver):
        """小幅随机滚动"""
        try:
            scroll_distance = random.randint(50, 150)
            direction = random.choice([-1, 1])
            
            driver.execute_script(f"window.scrollBy(0, {direction * scroll_distance});")
            self.random_wait(0.2, 0.5)
        
        except Exception as e:
            self.logger.debug(f"小幅滚动失败: {str(e)}")
    
    def simulate_pause_resume(self, driver):
        """模拟暂停/恢复操作"""
        try:
            # 查找视频播放器
            video_selectors = [
                'video',
                '.video-player',
                '[role="button"][aria-label*="play"]',
                '[role="button"][aria-label*="pause"]',
                '.play-button',
                '.pause-button'
            ]
            
            for selector in video_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        element = elements[0]
                        
                        # 移动到播放器
                        self.move_to_element_naturally(driver, element)
                        
                        # 点击暂停
                        element.click()
                        self.logger.debug("模拟暂停视频")
                        
                        # 暂停一段时间
                        pause_time = random.uniform(2, 8)
                        time.sleep(pause_time)
                        
                        # 点击恢复
                        element.click()
                        self.logger.debug("模拟恢复播放")
                        
                        break
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.debug(f"暂停/恢复模拟失败: {str(e)}")
    
    def simulate_volume_adjust(self, driver):
        """模拟音量调整"""
        try:
            # 查找音量控制
            volume_selectors = [
                '.volume-slider',
                '.volume-control',
                '[aria-label*="volume"]',
                '.volume-button'
            ]
            
            for selector in volume_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        element = elements[0]
                        self.move_to_element_naturally(driver, element)
                        element.click()
                        self.logger.debug("模拟音量调整")
                        break
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.debug(f"音量调整模拟失败: {str(e)}")
    
    def simulate_fullscreen_toggle(self, driver):
        """模拟全屏切换"""
        try:
            # 查找全屏按钮
            fullscreen_selectors = [
                '.fullscreen-button',
                '[aria-label*="fullscreen"]',
                '[title*="fullscreen"]',
                '.fullscreen-toggle'
            ]
            
            for selector in fullscreen_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        element = elements[0]
                        self.move_to_element_naturally(driver, element)
                        element.click()
                        self.logger.debug("模拟全屏切换")
                        
                        # 全屏状态停留一段时间
                        time.sleep(random.uniform(3, 8))
                        
                        # 退出全屏
                        from selenium.webdriver.common.action_chains import ActionChains
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        break
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.debug(f"全屏切换模拟失败: {str(e)}")
    
    def simulate_ad_behavior(self, driver):
        """模拟广告期间的行为"""
        try:
            self.logger.info("模拟广告观看行为")
            
            # 广告期间的行为更加有限
            behaviors = ['wait', 'small_mouse_move', 'tiny_scroll']
            
            behavior_count = random.randint(1, 3)
            for _ in range(behavior_count):
                behavior = random.choice(behaviors)
                
                if behavior == 'wait':
                    self.random_wait(2, 8)
                elif behavior == 'small_mouse_move':
                    self.random_mouse_movement(driver)
                elif behavior == 'tiny_scroll':
                    scroll_distance = random.randint(10, 50)
                    direction = random.choice([-1, 1])
                    driver.execute_script(f"window.scrollBy(0, {direction * scroll_distance});")
                
                # 行为间隔
                self.random_wait(1, 4)
        
        except Exception as e:
            self.logger.debug(f"广告行为模拟失败: {str(e)}")
    
    def simulate_ad_watching_behavior(self, driver, duration: float):
        """模拟观看广告的行为（完整观看）"""
        try:
            self.logger.info(f"开始模拟观看广告行为，时长: {duration:.1f}秒")
            
            start_time = time.time()
            end_time = start_time + duration
            
            # 在广告播放期间执行各种拟人化行为
            while time.time() < end_time:
                remaining_time = end_time - time.time()
                
                if remaining_time <= 0:
                    break
                
                # 随机选择一种行为
                action_choice = random.choices(
                    ['wait', 'scroll', 'mouse_move', 'volume_check', 'tab_focus', 'read_ad'],
                    weights=[35, 10, 15, 10, 10, 20],
                    k=1
                )[0]
                
                if action_choice == 'wait':
                    # 静静观看
                    wait_time = min(random.uniform(3, 8), remaining_time)
                    time.sleep(wait_time)
                
                elif action_choice == 'scroll' and remaining_time > 2:
                    # 轻微滚动（模拟调整观看位置）
                    try:
                        scroll_amount = random.randint(-50, 50)
                        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                        time.sleep(random.uniform(0.5, 1.5))
                    except Exception:
                        pass
                
                elif action_choice == 'mouse_move' and remaining_time > 1:
                    # 随机鼠标移动
                    try:
                        self.random_mouse_movement(driver)
                        time.sleep(random.uniform(0.3, 1.0))
                    except Exception:
                        pass
                
                elif action_choice == 'volume_check' and remaining_time > 3:
                    # 模拟检查音量（鼠标悬停在视频上）
                    try:
                        video_elements = driver.find_elements(By.TAG_NAME, "video")
                        if video_elements:
                            video = video_elements[0]
                            ActionChains(driver).move_to_element(video).perform()
                            time.sleep(random.uniform(1, 2))
                    except Exception:
                        pass
                
                elif action_choice == 'tab_focus':
                    # 模拟页面焦点变化
                    try:
                        driver.execute_script("window.focus();")
                        time.sleep(random.uniform(0.5, 1.0))
                    except Exception:
                        pass
                
                elif action_choice == 'read_ad' and remaining_time > 2:
                    # 模拟阅读广告内容
                    try:
                        # 查找可能的广告文本元素
                        ad_text_elements = driver.find_elements(By.CSS_SELECTOR, 
                            "[class*='ad'] [class*='title'], [class*='ad'] [class*='text'], .ytp-ad-text")
                        
                        if ad_text_elements:
                            for element in ad_text_elements[:2]:  # 最多看2个元素
                                try:
                                    if element.is_displayed():
                                        text_length = len(element.text) if element.text else 20
                                        read_time = min(text_length * 0.1, remaining_time / 2)
                                        time.sleep(max(1, read_time))
                                        break
                                except Exception:
                                    continue
                        else:
                            time.sleep(random.uniform(1, 3))
                    except Exception:
                        time.sleep(random.uniform(1, 2))
                
                # 确保不超时
                if time.time() >= end_time:
                    break
            
            self.logger.info("广告观看行为模拟完成")
            
        except Exception as e:
            self.logger.error(f"模拟广告观看行为失败: {str(e)}")
            # 如果模拟失败，至少等待剩余时间
            remaining = max(0, duration - (time.time() - start_time))
            if remaining > 0:
                time.sleep(remaining)
    
    def simulate_with_advanced_behavior(self, driver, action_type: str = "general", duration: float = 30):
        """使用高级行为模拟"""
        try:
            self.logger.info(f"开始高级行为模拟: {action_type}")
            
            # 更新疲劳度
            session_duration = time.time() - getattr(self.advanced_behavior, 'session_start_time', time.time())
            self.advanced_behavior.update_fatigue(session_duration)
            
            # 随机触发人为错误
            if random.random() < 0.15:  # 15%概率
                error_occurred = self.advanced_behavior.simulate_human_errors(driver, action_type)
                if error_occurred:
                    self.logger.debug("触发了人为错误行为")
            
            # 随机触发分心行为
            if random.random() < 0.08:  # 8%概率
                distraction = self.advanced_behavior.simulate_distraction_behavior(driver, min(10, duration * 0.3))
                if distraction:
                    self.logger.debug("触发了分心行为")
            
            # 模拟情绪响应
            if action_type == "ad_watching":
                self.advanced_behavior.simulate_emotional_response(driver, "ad")
            elif action_type == "page_loading":
                self.advanced_behavior.simulate_emotional_response(driver, "loading")
            
            # 应用学习适应
            action_success = random.random() > 0.1  # 90%成功率
            self.advanced_behavior.simulate_learning_adaptation(driver, action_success)
            
            return True
            
        except Exception as e:
            self.logger.error(f"高级行为模拟失败: {str(e)}")
            return False
    
    def get_behavior_insights(self) -> Dict:
        """获取行为洞察"""
        try:
            return self.advanced_behavior.get_behavior_report()
        except Exception as e:
            self.logger.error(f"获取行为洞察失败: {str(e)}")
            return {}
    
    def simulate_natural_browsing_behavior(self, driver, duration: int = 60):
        """模拟自然的浏览行为"""
        try:
            self.logger.info(f"开始模拟自然浏览行为，时长: {duration}秒")
            
            start_time = time.time()
            end_time = start_time + duration
            
            behaviors = [
                'idle_reading',
                'page_interaction', 
                'attention_shift',
                'micro_break',
                'content_engagement',
                'navigation_exploration',
                'UI_familiarization'
            ]
            
            while time.time() < end_time:
                remaining = end_time - time.time()
                if remaining <= 0:
                    break
                
                behavior = random.choice(behaviors)
                
                if behavior == 'idle_reading':
                    self._simulate_idle_reading(driver, min(random.uniform(5, 15), remaining))
                elif behavior == 'page_interaction':
                    self._simulate_page_interaction(driver, min(random.uniform(3, 8), remaining))
                elif behavior == 'attention_shift':
                    self._simulate_attention_shift(driver, min(random.uniform(2, 5), remaining))
                elif behavior == 'micro_break':
                    self._simulate_micro_break(driver, min(random.uniform(1, 3), remaining))
                elif behavior == 'content_engagement':
                    self._simulate_content_engagement(driver, min(random.uniform(4, 10), remaining))
                elif behavior == 'navigation_exploration':
                    self._simulate_navigation_exploration(driver, min(random.uniform(2, 6), remaining))
                elif behavior == 'UI_familiarization':
                    self._simulate_ui_familiarization(driver, min(random.uniform(3, 7), remaining))
            
            self.logger.info("自然浏览行为模拟完成")
            
        except Exception as e:
            self.logger.error(f"自然浏览行为模拟失败: {str(e)}")
    
    def _simulate_idle_reading(self, driver, duration: float):
        """模拟静止阅读"""
        try:
            # 偶尔小幅滚动以保持"活跃"状态
            scroll_intervals = max(1, int(duration / 3))
            interval_time = duration / scroll_intervals
            
            for _ in range(scroll_intervals):
                time.sleep(interval_time * 0.8)
                
                # 20%概率进行微小滚动
                if random.random() < 0.2:
                    scroll_amount = random.randint(-30, 30)
                    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                
                time.sleep(interval_time * 0.2)
            
        except Exception as e:
            self.logger.debug(f"静止阅读模拟失败: {str(e)}")
    
    def _simulate_attention_shift(self, driver, duration: float):
        """模拟注意力转移"""
        try:
            # 模拟用户注意力分散的行为
            actions = ['tab_switch', 'window_blur', 'cursor_drift', 'quick_scroll']
            
            for _ in range(random.randint(1, 3)):
                if duration <= 0:
                    break
                
                action = random.choice(actions)
                action_time = min(random.uniform(0.5, 2), duration)
                
                if action == 'tab_switch':
                    # 模拟切换标签页的意图（但不真正切换）
                    try:
                        # 按下Ctrl键但不完成切换
                        from selenium.webdriver.common.keys import Keys
                        from selenium.webdriver.common.action_chains import ActionChains
                        ActionChains(driver).key_down(Keys.CONTROL).pause(0.1).key_up(Keys.CONTROL).perform()
                    except:
                        pass
                
                elif action == 'window_blur':
                    # 模拟窗口失焦
                    try:
                        driver.execute_script("window.blur(); setTimeout(() => window.focus(), 500);")
                    except:
                        pass
                
                elif action == 'cursor_drift':
                    # 鼠标漂移
                    self.random_mouse_movement(driver)
                
                elif action == 'quick_scroll':
                    # 快速浏览式滚动
                    for _ in range(random.randint(2, 5)):
                        scroll_amount = random.randint(100, 300)
                        direction = random.choice([-1, 1])
                        driver.execute_script(f"window.scrollBy(0, {direction * scroll_amount});")
                        time.sleep(random.uniform(0.2, 0.5))
                
                duration -= action_time
                time.sleep(action_time)
            
        except Exception as e:
            self.logger.debug(f"注意力转移模拟失败: {str(e)}")
    
    def _simulate_micro_break(self, driver, duration: float):
        """模拟微休息（短暂停顿）"""
        try:
            # 完全静止一段时间，模拟用户思考或分神
            pause_time = min(duration, random.uniform(1, 3))
            time.sleep(pause_time)
            
            # 偶尔移动鼠标表示"回到"
            if random.random() < 0.3:
                self.random_mouse_movement(driver)
            
        except Exception as e:
            self.logger.debug(f"微休息模拟失败: {str(e)}")
    
    def _simulate_content_engagement(self, driver, duration: float):
        """模拟内容互动"""
        try:
            engagement_actions = ['hover_elements', 'read_text', 'examine_media', 'scroll_review']
            
            for _ in range(random.randint(1, 3)):
                if duration <= 0:
                    break
                
                action = random.choice(engagement_actions)
                action_time = min(random.uniform(1, 3), duration / 2)
                
                if action == 'hover_elements':
                    # 悬停在可点击元素上
                    try:
                        clickable_elements = driver.find_elements(By.CSS_SELECTOR, 
                            'a, button, [role="button"], .btn, [onclick]')
                        if clickable_elements:
                            element = random.choice(clickable_elements[:5])
                            if element.is_displayed():
                                ActionChains(driver).move_to_element(element).pause(action_time).perform()
                    except:
                        time.sleep(action_time)
                
                elif action == 'read_text':
                    # 模拟阅读行为
                    try:
                        text_elements = driver.find_elements(By.CSS_SELECTOR, 'p, h1, h2, h3, span, div')
                        if text_elements:
                            element = random.choice(text_elements[:10])
                            if element.is_displayed() and element.text:
                                # 根据文本长度计算阅读时间
                                read_time = min(len(element.text) * 0.05, action_time)
                                ActionChains(driver).move_to_element(element).perform()
                                time.sleep(read_time)
                    except:
                        time.sleep(action_time)
                
                elif action == 'examine_media':
                    # 检查图片或视频
                    try:
                        media_elements = driver.find_elements(By.CSS_SELECTOR, 'img, video, canvas')
                        if media_elements:
                            element = random.choice(media_elements[:3])
                            if element.is_displayed():
                                ActionChains(driver).move_to_element(element).pause(action_time).perform()
                    except:
                        time.sleep(action_time)
                
                elif action == 'scroll_review':
                    # 回顾式滚动
                    for _ in range(random.randint(2, 4)):
                        scroll_amount = random.randint(50, 150)
                        direction = random.choice([-1, 1])
                        driver.execute_script(f"window.scrollBy(0, {direction * scroll_amount});")
                        time.sleep(random.uniform(0.5, 1.5))
                
                duration -= action_time
            
        except Exception as e:
            self.logger.debug(f"内容互动模拟失败: {str(e)}")
    
    def _simulate_navigation_exploration(self, driver, duration: float):
        """模拟导航探索"""
        try:
            # 模拟用户熟悉页面结构的行为
            nav_actions = ['check_menu', 'explore_links', 'examine_footer', 'check_sidebar']
            
            for _ in range(random.randint(1, 2)):
                if duration <= 0:
                    break
                
                action = random.choice(nav_actions)
                action_time = min(random.uniform(2, 4), duration / 2)
                
                if action == 'check_menu':
                    try:
                        menu_elements = driver.find_elements(By.CSS_SELECTOR, 
                            'nav, .menu, .navigation, header a, .navbar')
                        if menu_elements:
                            for element in menu_elements[:3]:
                                if element.is_displayed():
                                    ActionChains(driver).move_to_element(element).pause(0.5).perform()
                    except:
                        pass
                
                elif action == 'explore_links':
                    try:
                        links = driver.find_elements(By.TAG_NAME, 'a')[:10]
                        for link in random.sample(links, min(3, len(links))):
                            if link.is_displayed():
                                ActionChains(driver).move_to_element(link).pause(0.3).perform()
                    except:
                        pass
                
                elif action == 'examine_footer':
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        footer_elements = driver.find_elements(By.CSS_SELECTOR, 'footer, .footer')
                        if footer_elements:
                            ActionChains(driver).move_to_element(footer_elements[0]).pause(1).perform()
                    except:
                        pass
                
                time.sleep(action_time)
                duration -= action_time
            
        except Exception as e:
            self.logger.debug(f"导航探索模拟失败: {str(e)}")
    
    def _simulate_ui_familiarization(self, driver, duration: float):
        """模拟UI熟悉过程"""
        try:
            # 模拟用户第一次使用界面时的探索行为
            ui_elements = ['buttons', 'inputs', 'controls', 'icons']
            
            for element_type in random.sample(ui_elements, min(2, len(ui_elements))):
                if duration <= 0:
                    break
                
                action_time = min(random.uniform(1, 3), duration / 2)
                
                if element_type == 'buttons':
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, 'button, .btn, [role="button"]')
                        for btn in random.sample(buttons, min(3, len(buttons))):
                            if btn.is_displayed():
                                ActionChains(driver).move_to_element(btn).pause(0.5).perform()
                    except:
                        pass
                
                elif element_type == 'inputs':
                    try:
                        inputs = driver.find_elements(By.CSS_SELECTOR, 'input, textarea, select')
                        for inp in random.sample(inputs, min(2, len(inputs))):
                            if inp.is_displayed():
                                ActionChains(driver).move_to_element(inp).pause(0.3).perform()
                    except:
                        pass
                
                time.sleep(action_time)
                duration -= action_time
            
        except Exception as e:
            self.logger.debug(f"UI熟悉模拟失败: {str(e)}")
    
    def get_random_delays(self) -> Dict[str, Tuple[float, float]]:
        """获取随机延迟配置"""
        return {
            'page_load': (2.0, 5.0),
            'element_wait': (0.5, 2.0),
            'click_delay': self.click_delay_range,
            'type_delay': self.typing_delay_range,
            'scroll_pause': self.scroll_pause_range,
            'video_start': (1.0, 3.0),
            'video_end': (0.5, 2.0),
            'ad_skip': (0.8, 2.0)
        }

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.DEBUG)
    
    # 创建拟人化引擎
    humanizer = HumanizationEngine()
    
    # 测试各种延迟
    print("测试随机等待...")
    humanizer.random_wait(1, 2)
    
    print("测试模拟阅读...")
    humanizer.simulate_reading(200)
    
    print("拟人化引擎测试完成")
