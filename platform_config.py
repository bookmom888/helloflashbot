#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台配置模块
Platform Configuration Module

管理不同平台的播放策略和配置
"""

import random
from typing import Dict, Tuple, List
from enum import Enum
from dataclasses import dataclass

class PlatformType(Enum):
    """支持的平台类型"""
    BIGWINGS = "bigwings.io"
    EARNVIDS = "earnvids.com"
    POPCASH = "popcash.net"
    UP4STREAM = "up4stream.com"
    LIXSTREAM = "lixstream.com"
    STREAMBOLT = "streambolt.tv"
    GENERIC = "generic"  # 通用平台

@dataclass
class PlayStrategy:
    """播放策略"""
    min_duration: int  # 最小播放时长（秒）
    max_duration: int  # 最大播放时长（秒）
    description: str   # 策略描述
    level: int = 1     # 等级

class PlatformConfig:
    """平台配置管理器"""
    
    def __init__(self):
        self.platforms = {
            PlatformType.BIGWINGS: {
                'name': 'BigWings.io',
                'strategies': [PlayStrategy(30, 300, '标准播放模式')]
            },
            PlatformType.EARNVIDS: {
                'name': 'EarnVids.com', 
                'strategies': [
                    PlayStrategy(30, 60, '短时长播放 (30-60秒)', 1),
                    PlayStrategy(60, 120, '中等时长播放 (60-120秒)', 2),
                    PlayStrategy(120, 180, '较长时长播放 (120-180秒)', 3),
                    PlayStrategy(180, 240, '长时长播放 (180-240秒)', 4),
                    PlayStrategy(240, 300, '超长时长播放 (240-300秒)', 5)
                ]
            },
            PlatformType.POPCASH: {
                'name': 'PopCash.net',
                'strategies': [PlayStrategy(30, 300, '标准播放模式')]
            },
            PlatformType.UP4STREAM: {
                'name': 'Up4Stream.com',
                'strategies': [PlayStrategy(30, 300, '标准播放模式')]
            },
            PlatformType.LIXSTREAM: {
                'name': 'LixStream.com',
                'strategies': [PlayStrategy(30, 300, '标准播放模式')]
            },
            PlatformType.STREAMBOLT: {
                'name': 'StreamBolt.tv',
                'strategies': [PlayStrategy(30, 300, '标准播放模式')]
            },
            PlatformType.GENERIC: {
                'name': '通用平台',
                'strategies': [PlayStrategy(30, 300, '标准播放模式')]
            }
        }
    
    def get_platform_by_url(self, url: str) -> PlatformType:
        """根据URL识别平台"""
        url_lower = url.lower()
        
        if 'bigwings.io' in url_lower:
            return PlatformType.BIGWINGS
        elif 'earnvids.com' in url_lower:
            return PlatformType.EARNVIDS
        elif 'popcash.net' in url_lower:
            return PlatformType.POPCASH
        elif 'up4stream.com' in url_lower:
            return PlatformType.UP4STREAM
        elif 'lixstream.com' in url_lower:
            return PlatformType.LIXSTREAM
        elif 'streambolt.tv' in url_lower:
            return PlatformType.STREAMBOLT
        else:
            return PlatformType.GENERIC
    
    def get_platform_strategies(self, platform: PlatformType) -> List[PlayStrategy]:
        """获取平台的播放策略"""
        return self.platforms.get(platform, {}).get('strategies', [])
    
    def get_platform_name(self, platform: PlatformType) -> str:
        """获取平台名称"""
        return self.platforms.get(platform, {}).get('name', '未知平台')
    
    def get_random_duration(self, platform: PlatformType, strategy_level: int = 1) -> int:
        """获取随机播放时长"""
        strategies = self.get_platform_strategies(platform)
        
        # 查找对应等级的策略
        target_strategy = None
        for strategy in strategies:
            if strategy.level == strategy_level:
                target_strategy = strategy
                break
        
        # 如果没找到对应等级，使用第一个策略
        if not target_strategy and strategies:
            target_strategy = strategies[0]
        
        if target_strategy:
            return random.randint(target_strategy.min_duration, target_strategy.max_duration)
        else:
            return random.randint(30, 300)  # 默认时长
    
    def get_all_platforms(self) -> Dict[PlatformType, str]:
        """获取所有平台"""
        return {platform: info['name'] for platform, info in self.platforms.items()}
    
    def is_earnvids_platform(self, platform: PlatformType) -> bool:
        """检查是否为EarnVids平台"""
        return platform == PlatformType.EARNVIDS
    
    def get_earnvids_strategy_info(self) -> List[str]:
        """获取EarnVids策略信息"""
        strategies = self.get_platform_strategies(PlatformType.EARNVIDS)
        return [f"等级{s.level}: {s.description}" for s in strategies]
