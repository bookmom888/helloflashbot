#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不使用代理直接播放视频
"""

import sys
import logging
from browser_automation import BrowserAutomation
from video_player import VideoPlayer
from humanization import HumanizationEngine
from fingerprint_engine import FingerprintEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('test_no_proxy')

def main():
    try:
        # 初始化组件
        browser_automation = BrowserAutomation()
        video_player = VideoPlayer()
        humanizer = HumanizationEngine()
        fingerprint_engine = FingerprintEngine()
        
        # 生成指纹
        fingerprint = fingerprint_engine.generate_fingerprint()
        
        # 测试URL - 使用Bilibili视频作为替代
        url = "https://www.bilibili.com/video/BV1GJ411x7h7"  # Bilibili示例视频
        
        # 浏览器配置
        browser_config = {
            'headless': False,  # 可视模式
            'stealth': True,
            'disable_images': False,
            'disable_js': False
        }
        
        logger.info("开始测试不使用代理直接播放视频")
        
        # 创建浏览器 - 不使用代理
        driver = browser_automation.create_browser(proxy=None, fingerprint=fingerprint, config=browser_config)
        
        if not driver:
            logger.error("创建浏览器失败")
            return
        
        logger.info(f"成功创建浏览器，开始播放视频: {url}")
        
        # 播放视频
        play_duration = 30  # 播放30秒
        success = video_player.play_video(driver, url, humanizer, play_duration)
        
        if success:
            logger.info("视频播放成功")
        else:
            logger.error("视频播放失败")
        
        # 关闭浏览器
        driver.quit()
        logger.info("测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()