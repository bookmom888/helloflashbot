#!/usr/bin/env python3
"""
测试IP对URL的播放次数限制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.session_manager import SessionManager
from src.proxy_manager import ProxyManager
from src.fingerprint_engine import FingerprintEngine
import time

def test_ip_url_limit():
    """测试IP对URL的播放次数限制"""
    print("🧪 测试IP对URL的播放次数限制...")
    
    # 创建管理器
    session_manager = SessionManager()
    proxy_manager = ProxyManager()
    fingerprint_engine = FingerprintEngine()
    
    # 添加测试代理
    test_proxies = [
        {
            'host': '192.168.1.1',
            'port': 8080,
            'type': 'http',
            'validated': True
        },
        {
            'host': '192.168.1.2', 
            'port': 8080,
            'type': 'http',
            'validated': True
        }
    ]
    
    # 直接添加到代理列表
    proxy_manager.proxies = test_proxies
    
    test_url = "https://www.youtube.com/watch?v=test123"
    
    print(f"\n1️⃣ 配置信息:")
    print(f"   最大会话数/IP: {session_manager.max_sessions_per_ip}")
    print(f"   最大URL播放次数/会话: {session_manager.max_url_plays_per_session}")
    print(f"   测试URL: {test_url}")
    
    # 测试1: 同一IP对同一URL播放3次
    print(f"\n2️⃣ 测试同一IP对同一URL播放3次:")
    ip = "192.168.1.1"
    proxy = test_proxies[0]
    
    for play_attempt in range(4):  # 尝试4次，第4次应该失败
        print(f"   尝试播放 {play_attempt + 1}:")
        
        # 检查IP是否可以播放URL
        can_play = session_manager.can_ip_play_url(ip, test_url)
        current_count = session_manager.get_ip_url_play_count(ip, test_url)
        print(f"     IP {ip} 当前播放次数: {current_count}")
        print(f"     是否可以播放: {can_play}")
        
        if not can_play:
            print(f"     ❌ IP {ip} 已达到播放限制，无法继续播放")
            break
        
        # 创建会话并模拟播放
        fingerprint = fingerprint_engine.generate_fingerprint()
        session = session_manager.create_session(proxy, fingerprint, test_url)
        
        if session:
            print(f"     ✅ 创建会话成功: {session.session_id[:8]}...")
            
            # 模拟播放
            success = session_manager.update_session_usage(session.session_id, test_url)
            if success:
                print(f"     ✅ 播放成功")
            else:
                print(f"     ❌ 播放失败")
            
            # 关闭会话
            session_manager.close_session(session.session_id)
            print(f"     🔄 会话已关闭")
        else:
            print(f"     ❌ 创建会话失败")
            break
    
    # 测试2: 不同IP对同一URL
    print(f"\n3️⃣ 测试不同IP对同一URL:")
    for i, proxy in enumerate(test_proxies):
        ip = proxy['host']
        print(f"   测试IP {ip}:")
        
        can_play = session_manager.can_ip_play_url(ip, test_url)
        current_count = session_manager.get_ip_url_play_count(ip, test_url)
        print(f"     当前播放次数: {current_count}")
        print(f"     是否可以播放: {can_play}")
        
        if can_play:
            fingerprint = fingerprint_engine.generate_fingerprint()
            session = session_manager.create_session(proxy, fingerprint, test_url)
            
            if session:
                print(f"     ✅ 可以创建会话")
                session_manager.close_session(session.session_id)
            else:
                print(f"     ❌ 无法创建会话")
        else:
            print(f"     ❌ 已达到播放限制")
    
    # 测试3: 同一IP对不同URL
    print(f"\n4️⃣ 测试同一IP对不同URL:")
    ip = "192.168.1.1"
    proxy = test_proxies[0]
    
    test_urls = [
        "https://www.youtube.com/watch?v=video1",
        "https://www.youtube.com/watch?v=video2",
        "https://www.youtube.com/watch?v=video3"
    ]
    
    for url in test_urls:
        print(f"   测试URL: {url}")
        
        can_play = session_manager.can_ip_play_url(ip, url)
        current_count = session_manager.get_ip_url_play_count(ip, url)
        print(f"     IP {ip} 对URL {url} 当前播放次数: {current_count}")
        print(f"     是否可以播放: {can_play}")
        
        if can_play:
            fingerprint = fingerprint_engine.generate_fingerprint()
            session = session_manager.create_session(proxy, fingerprint, url)
            
            if session:
                print(f"     ✅ 可以创建会话")
                session_manager.close_session(session.session_id)
            else:
                print(f"     ❌ 无法创建会话")
        else:
            print(f"     ❌ 已达到播放限制")
    
    print(f"\n✅ IP对URL播放次数限制测试完成!")
    print(f"   现在每个IP对每个URL最多只能播放 {session_manager.max_url_plays_per_session} 次")

if __name__ == "__main__":
    test_ip_url_limit()
