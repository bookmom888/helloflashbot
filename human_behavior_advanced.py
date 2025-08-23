"""
高级人性化行为模拟引擎
包含更复杂的人类行为模式
"""

import random
import time
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchElementException


class AdvancedHumanBehavior:
    """高级人性化行为引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 行为状态跟踪
        self.session_start_time = time.time()
        self.fatigue_level = 0.0  # 疲劳度 0-1
        self.learning_curve = 0.5  # 学习曲线 0-1
        self.error_count = 0
        self.behavior_consistency = 0.8  # 行为一致性
        
        # 人格特征
        self.personality = self._generate_personality()
        
        # 行为模式记录
        self.behavior_history = {
            "mouse_movements": [],
            "click_patterns": [],
            "scroll_patterns": [],
            "typing_patterns": [],
            "errors": [],
            "attention_shifts": [],
        }
        
        # 情绪状态
        self.emotional_state = {
            "stress_level": random.uniform(0.1, 0.3),
            "boredom_level": random.uniform(0.0, 0.2),
            "focus_level": random.uniform(0.7, 0.9),
            "patience_level": random.uniform(0.6, 0.9),
        }
    
    def _generate_personality(self) -> Dict:
        """生成个性特征"""
        return {
            "impulsiveness": random.uniform(0.1, 0.9),
            "attention_span": random.uniform(0.3, 0.8),
            "risk_tolerance": random.uniform(0.2, 0.7),
            "tech_savviness": random.uniform(0.4, 0.9),
            "perfectionism": random.uniform(0.2, 0.8),
            "multitasking_ability": random.uniform(0.3, 0.8),
        }
    
    def update_fatigue(self, session_duration: float):
        """更新疲劳度"""
        # 基于会话时长更新疲劳度
        base_fatigue = min(session_duration / 3600, 1.0)  # 1小时为基准
        personality_factor = 1.0 - self.personality["attention_span"] * 0.3
        self.fatigue_level = min(base_fatigue * personality_factor, 1.0)
        
        # 疲劳度影响其他状态
        if self.fatigue_level > 0.6:
            self.emotional_state["focus_level"] *= (1.0 - self.fatigue_level * 0.3)
            self.emotional_state["patience_level"] *= (1.0 - self.fatigue_level * 0.2)
    
    def simulate_human_errors(self, driver, action_type: str = "general") -> bool:
        """模拟人为错误"""
        try:
            # 错误概率基于疲劳度和个性
            error_probability = (
                self.fatigue_level * 0.1 +
                (1.0 - self.personality["tech_savviness"]) * 0.05 +
                self.emotional_state["stress_level"] * 0.03
            )
            
            if random.random() < error_probability:
                error_type = random.choice([
                    "misclick", "wrong_key", "missed_element", 
                    "premature_action", "hesitation"
                ])
                
                self.logger.debug(f"模拟人为错误: {error_type}")
                
                if error_type == "misclick":
                    return self._simulate_misclick(driver)
                elif error_type == "wrong_key":
                    return self._simulate_wrong_key(driver)
                elif error_type == "missed_element":
                    return self._simulate_missed_element(driver)
                elif error_type == "premature_action":
                    return self._simulate_premature_action(driver)
                elif error_type == "hesitation":
                    return self._simulate_hesitation(driver)
                
                self.error_count += 1
                self.behavior_history["errors"].append({
                    "type": error_type,
                    "timestamp": time.time(),
                    "context": action_type
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"人为错误模拟失败: {str(e)}")
            return False
    
    def _simulate_misclick(self, driver) -> bool:
        """模拟误点击"""
        try:
            # 在当前鼠标位置附近随机点击
            action = ActionChains(driver)
            
            # 获取当前窗口大小
            window_size = driver.get_window_size()
            
            # 在窗口中心附近随机点击
            x_offset = random.randint(-50, 50)
            y_offset = random.randint(-50, 50)
            
            action.move_by_offset(x_offset, y_offset).click().perform()
            
            # 短暂停顿（意识到错误）
            time.sleep(random.uniform(0.2, 0.5))
            
            # 移回原位置
            action.move_by_offset(-x_offset, -y_offset).perform()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"误点击模拟失败: {str(e)}")
            return False
    
    def _simulate_wrong_key(self, driver) -> bool:
        """模拟按错键"""
        try:
            # 常见的错误按键
            wrong_keys = [Keys.SPACE, Keys.ENTER, Keys.TAB, Keys.ESCAPE]
            key = random.choice(wrong_keys)
            
            action = ActionChains(driver)
            action.send_keys(key).perform()
            
            # 短暂停顿
            time.sleep(random.uniform(0.3, 0.7))
            
            # 可能会撤销
            if random.random() < 0.7:
                action.key_down(Keys.CONTROL).send_keys('z').key_up(Keys.CONTROL).perform()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"错误按键模拟失败: {str(e)}")
            return False
    
    def _simulate_missed_element(self, driver) -> bool:
        """模拟错过元素"""
        try:
            # 快速移动鼠标然后停止（好像在寻找什么）
            action = ActionChains(driver)
            
            for _ in range(random.randint(2, 4)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                action.move_by_offset(x_offset, y_offset)
                time.sleep(random.uniform(0.1, 0.3))
            
            action.perform()
            
            # 停顿（寻找）
            time.sleep(random.uniform(0.5, 1.5))
            
            return True
            
        except Exception as e:
            self.logger.debug(f"错过元素模拟失败: {str(e)}")
            return False
    
    def _simulate_premature_action(self, driver) -> bool:
        """模拟过早操作"""
        try:
            # 快速点击（太着急）
            action = ActionChains(driver)
            action.click().perform()
            
            # 立即意识到错误，短暂停顿
            time.sleep(random.uniform(0.1, 0.3))
            
            return True
            
        except Exception as e:
            self.logger.debug(f"过早操作模拟失败: {str(e)}")
            return False
    
    def _simulate_hesitation(self, driver) -> bool:
        """模拟犹豫行为"""
        try:
            # 鼠标悬停但不点击
            action = ActionChains(driver)
            
            # 在小范围内移动鼠标（犹豫）
            for _ in range(random.randint(3, 6)):
                x_offset = random.randint(-10, 10)
                y_offset = random.randint(-10, 10)
                action.move_by_offset(x_offset, y_offset)
                time.sleep(random.uniform(0.1, 0.2))
            
            action.perform()
            
            # 长时间停顿（思考）
            time.sleep(random.uniform(1.0, 2.5))
            
            return True
            
        except Exception as e:
            self.logger.debug(f"犹豫行为模拟失败: {str(e)}")
            return False
    
    def simulate_distraction_behavior(self, driver, duration: float = 5.0) -> bool:
        """模拟分心行为"""
        try:
            self.logger.debug(f"模拟分心行为，时长: {duration}秒")
            
            distraction_type = random.choice([
                "tab_switching", "window_interaction", "idle_browsing", 
                "notification_check", "multitasking"
            ])
            
            if distraction_type == "tab_switching":
                return self._simulate_tab_switching(driver, duration)
            elif distraction_type == "window_interaction":
                return self._simulate_window_interaction(driver, duration)
            elif distraction_type == "idle_browsing":
                return self._simulate_idle_browsing(driver, duration)
            elif distraction_type == "notification_check":
                return self._simulate_notification_check(driver, duration)
            elif distraction_type == "multitasking":
                return self._simulate_multitasking(driver, duration)
            
            return False
            
        except Exception as e:
            self.logger.debug(f"分心行为模拟失败: {str(e)}")
            return False
    
    def _simulate_tab_switching(self, driver, duration: float) -> bool:
        """模拟标签页切换"""
        try:
            end_time = time.time() + duration
            
            while time.time() < end_time:
                # 切换到其他标签页
                action = ActionChains(driver)
                action.key_down(Keys.CONTROL).send_keys(Keys.TAB).key_up(Keys.CONTROL).perform()
                
                time.sleep(random.uniform(1.0, 3.0))
                
                # 有概率切换回来
                if random.random() < 0.7:
                    action.key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT).key_up(Keys.CONTROL).perform()
                    time.sleep(random.uniform(0.5, 1.5))
            
            return True
            
        except Exception as e:
            self.logger.debug(f"标签页切换模拟失败: {str(e)}")
            return False
    
    def _simulate_window_interaction(self, driver, duration: float) -> bool:
        """模拟窗口交互"""
        try:
            # 模拟最小化/恢复窗口
            time.sleep(duration * 0.3)
            
            # Alt+Tab 切换窗口
            action = ActionChains(driver)
            action.key_down(Keys.ALT).send_keys(Keys.TAB).key_up(Keys.ALT).perform()
            
            time.sleep(duration * 0.7)
            
            # 切换回来
            action.key_down(Keys.ALT).send_keys(Keys.TAB).key_up(Keys.ALT).perform()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"窗口交互模拟失败: {str(e)}")
            return False
    
    def _simulate_idle_browsing(self, driver, duration: float) -> bool:
        """模拟无目的浏览"""
        try:
            end_time = time.time() + duration
            
            while time.time() < end_time:
                # 随机滚动
                scroll_amount = random.randint(-3, 3)
                if scroll_amount != 0:
                    action = ActionChains(driver)
                    for _ in range(abs(scroll_amount)):
                        key = Keys.PAGE_DOWN if scroll_amount > 0 else Keys.PAGE_UP
                        action.send_keys(key)
                    action.perform()
                
                # 随机移动鼠标
                action = ActionChains(driver)
                x_offset = random.randint(-200, 200)
                y_offset = random.randint(-200, 200)
                action.move_by_offset(x_offset, y_offset).perform()
                
                time.sleep(random.uniform(0.5, 2.0))
            
            return True
            
        except Exception as e:
            self.logger.debug(f"无目的浏览模拟失败: {str(e)}")
            return False
    
    def _simulate_notification_check(self, driver, duration: float) -> bool:
        """模拟检查通知"""
        try:
            # 模拟查看系统通知区域
            action = ActionChains(driver)
            
            # 移动到右下角（通知区域）
            window_size = driver.get_window_size()
            action.move_by_offset(window_size['width'] // 2, window_size['height'] // 2).perform()
            
            time.sleep(duration)
            
            return True
            
        except Exception as e:
            self.logger.debug(f"通知检查模拟失败: {str(e)}")
            return False
    
    def _simulate_multitasking(self, driver, duration: float) -> bool:
        """模拟多任务处理"""
        try:
            # 快速切换多个应用
            for _ in range(random.randint(2, 4)):
                action = ActionChains(driver)
                action.key_down(Keys.ALT).send_keys(Keys.TAB).key_up(Keys.ALT).perform()
                time.sleep(random.uniform(0.3, 0.8))
            
            time.sleep(duration * 0.7)
            
            # 回到原窗口
            action = ActionChains(driver)
            action.key_down(Keys.ALT).send_keys(Keys.TAB).key_up(Keys.ALT).perform()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"多任务处理模拟失败: {str(e)}")
            return False
    
    def simulate_emotional_response(self, driver, context: str = "general"):
        """模拟情绪响应"""
        try:
            if context == "ad":
                # 广告相关的情绪响应
                if self.emotional_state["patience_level"] < 0.4:
                    # 不耐烦：快速移动鼠标
                    action = ActionChains(driver)
                    for _ in range(random.randint(3, 6)):
                        x_offset = random.randint(-50, 50)
                        y_offset = random.randint(-50, 50)
                        action.move_by_offset(x_offset, y_offset)
                        time.sleep(0.1)
                    action.perform()
                
            elif context == "loading":
                # 加载等待的情绪响应
                if self.emotional_state["patience_level"] < 0.5:
                    # 不耐烦：点击或刷新
                    if random.random() < 0.3:
                        action = ActionChains(driver)
                        action.key_down(Keys.F5).key_up(Keys.F5).perform()  # 刷新
                        time.sleep(random.uniform(0.5, 1.0))
            
            # 更新情绪状态
            self.emotional_state["stress_level"] = min(
                self.emotional_state["stress_level"] + random.uniform(-0.05, 0.1), 
                1.0
            )
            
        except Exception as e:
            self.logger.debug(f"情绪响应模拟失败: {str(e)}")
    
    def simulate_learning_adaptation(self, driver, action_success: bool):
        """模拟学习适应"""
        try:
            if action_success:
                # 成功操作提升学习曲线
                self.learning_curve = min(self.learning_curve + 0.01, 1.0)
                self.behavior_consistency = min(self.behavior_consistency + 0.005, 1.0)
            else:
                # 失败操作降低一致性，但可能提升学习
                self.behavior_consistency = max(self.behavior_consistency - 0.01, 0.0)
                if random.random() < 0.3:  # 从错误中学习
                    self.learning_curve = min(self.learning_curve + 0.005, 1.0)
            
            # 学习曲线影响行为速度
            if self.learning_curve > 0.8:
                # 熟练用户，操作更快
                pass
            elif self.learning_curve < 0.3:
                # 新手用户，操作更慢，更多犹豫
                time.sleep(random.uniform(0.2, 0.5))
            
        except Exception as e:
            self.logger.debug(f"学习适应模拟失败: {str(e)}")
    
    def get_behavior_report(self) -> Dict:
        """获取行为分析报告"""
        session_duration = time.time() - self.session_start_time
        
        return {
            "session_duration": session_duration,
            "fatigue_level": self.fatigue_level,
            "learning_curve": self.learning_curve,
            "error_count": self.error_count,
            "behavior_consistency": self.behavior_consistency,
            "emotional_state": self.emotional_state.copy(),
            "personality": self.personality.copy(),
            "behavior_patterns": {
                "total_mouse_movements": len(self.behavior_history["mouse_movements"]),
                "total_clicks": len(self.behavior_history["click_patterns"]),
                "total_scrolls": len(self.behavior_history["scroll_patterns"]),
                "total_errors": len(self.behavior_history["errors"]),
                "attention_shifts": len(self.behavior_history["attention_shifts"]),
            }
        }