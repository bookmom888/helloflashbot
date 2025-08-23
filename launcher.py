#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动器
简化版启动脚本，自动检查环境和依赖
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本检查通过: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'selenium',
        'undetected-chromedriver', 
        'requests',
        'tkinter'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            else:
                spec = importlib.util.find_spec(package.replace('-', '_'))
                if spec is None:
                    missing_packages.append(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        return False
    
    print("✅ 依赖包检查通过")
    return True

def install_dependencies():
    """安装依赖包"""
    print("🔧 正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False

def create_directories():
    """创建必要目录"""
    dirs = ['data', 'logs', 'examples']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    print("✅ 目录结构检查完成")

def main():
    """主函数"""
    print("🚀 视频自动化播放工具启动器")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        input("按回车键退出...")
        return
    
    # 创建目录
    create_directories()
    
    # 检查依赖
    if not check_dependencies():
        print("\n🔧 正在尝试自动安装依赖包...")
        if os.path.exists('requirements.txt'):
            if install_dependencies():
                if not check_dependencies():
                    print("❌ 依赖包安装后仍有问题，请手动检查")
                    input("按回车键退出...")
                    return
            else:
                print("❌ 自动安装失败，请手动运行: pip install -r requirements.txt")
                input("按回车键退出...")
                return
        else:
            print("❌ 未找到requirements.txt文件")
            input("按回车键退出...")
            return
    
    # 启动主程序
    print("\n🎬 启动视频自动化播放工具...")
    print("=" * 50)
    
    try:
        import main
        main.main()
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("\n请检查日志文件获取详细信息")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
