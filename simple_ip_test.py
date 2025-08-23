#!/usr/bin/env python3
"""
简单测试IP对URL的播放次数限制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.session_manager import SessionManager
from src.fingerprint_engine import FingerprintEngine

def simple_test():
    """简单测试"""
    print("🧪 简单测试IP对URL播放次数限制...")
    
    # 创建管理器
    session_manager = SessionManager()
    fingerprint_engine = FingerprintEngine()
    
    # 测试代理
    proxy = {
        'host': '192.168.1.1',
        'port': 8080,
        'type': 'http',
        'validated': True
    }
    
    test_url = "https://www.youtube.com/watch?v=test123"
    
    print(f"配置:")
    print(f"  最大会话数/IP: {session_manager.max_sessions_per_ip}")
    print(f"  最大URL播放次数: {session_manager.max_url_plays_per_session}")
    print(f"  测试URL: {test_url}")
    print(f"  测试IP: {proxy['host']}")
    
    # 测试同一IP对同一URL播放3次
    print(f"\n测试同一IP对同一URL播放3次:")
    
    for i in range(4):  # 尝试4次
        print(f"\n尝试 {i+1}:")
        
        # 检查是否可以播放
        can_play = session_manager.can_ip_play_url(proxy['host'], test_url)
        current_count = session_manager.get_ip_url_play_count(proxy['host'], test_url)
        
        print(f"  当前播放次数: {current_count}")
        print(f"  是否可以播放: {can_play}")
        
        if not can_play:
            print(f"  ❌ 已达到播放限制")
            break
        
        # 创建会话
        fingerprint = fingerprint_engine.generate_fingerprint()
        session = session_manager.create_session(proxy, fingerprint, test_url)
        
        if session:
            print(f"  ✅ 创建会话成功")
            
            # 模拟播放
            success = session_manager.update_session_usage(session.session_id, test_url)
            if success:
                print(f"  ✅ 播放成功")
            else:
                print(f"  ❌ 播放失败")
            
            # 关闭会话
            session_manager.close_session(session.session_id)
            print(f"  🔄 会话已关闭")
        else:
            print(f"  ❌ 创建会话失败")
            break
    
    print(f"\n✅ 测试完成!")

if __name__ == "__main__":
    simple_test()
