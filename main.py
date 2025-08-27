#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化播放工具
Video Automation Playback Tool

主要功能：
- 智能代理管理和轮换
- 真实设备指纹生成
- 拟人化操作模拟
- 反检测浏览器自动化
- 多窗口并发支持
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
import os
import time
import random
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
import sys

# 导入自定义模块
from proxy_manager import ProxyManager
from fingerprint_engine import FingerprintEngine
from browser_automation import BrowserAutomation
from humanization import HumanizationEngine
from session_manager import SessionManager
from video_player import VideoPlayer
from window_manager import WindowManager
from platform_config import PlatformConfig, PlatformType
from logger import setup_logger
from config import config

class VideoAutomationTool:
    """视频自动化播放工具主界面"""
    
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("视频自动化播放工具 v1.0")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2b2b2b")
        
        # 初始化组件
        self.proxy_manager = ProxyManager()
        self.fingerprint_engine = FingerprintEngine()
        self.session_manager = SessionManager()
        self.browser_automation = BrowserAutomation()
        self.humanization = HumanizationEngine()
        self.video_player = VideoPlayer()
        self.window_manager = WindowManager(max_windows=config.max_windows)
        self.platform_config = PlatformConfig()
        
        # 状态变量
        self.is_running = False
        self.video_urls = []
        self.start_time = None
        self.played_videos_count = 0
        
        # 线程锁保护共享变量
        self._status_lock = threading.Lock()
        self._urls_lock = threading.Lock()
        self._count_lock = threading.Lock()
        
        # 日志队列
        self.log_queue = queue.Queue()
        self.logger = setup_logger("video_automation")
        
        # 设置窗口管理器回调
        self.window_manager.set_status_callback(self.on_window_status_update)
        
        # 创建界面
        self.create_interface()
        
        # 启动日志监听
        self.process_log_queue()
        
        # 启动状态更新
        self.update_status_display()
    
    def create_interface(self) -> None:
        """创建主界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建笔记本控件
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页
        self.create_main_tab(notebook)
        self.create_proxy_tab(notebook)
        self.create_config_tab(notebook)
        self.create_mouse_control_tab(notebook)  # 新增鼠标控制标签页
        self.create_monitor_tab(notebook)
        self.create_log_tab(notebook)
    
    def create_main_tab(self, parent):
        """创建主控制标签页"""
        main_tab = ttk.Frame(parent)
        parent.add(main_tab, text="主控制")
        
        # 视频URL配置
        url_frame = ttk.LabelFrame(main_tab, text="视频URL配置")
        url_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # URL输入框
        ttk.Label(url_frame, text="视频URL列表:").pack(anchor=tk.W, padx=5, pady=2)
        self.url_text = scrolledtext.ScrolledText(url_frame, height=8)
        self.url_text.pack(fill=tk.X, padx=5, pady=5)
        
        # URL操作按钮
        url_btn_frame = ttk.Frame(url_frame)
        url_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(url_btn_frame, text="导入URL文件", 
                  command=self.import_urls).pack(side=tk.LEFT, padx=2)
        ttk.Button(url_btn_frame, text="保存URL列表", 
                  command=self.save_urls).pack(side=tk.LEFT, padx=2)
        ttk.Button(url_btn_frame, text="清空列表", 
                  command=self.clear_urls).pack(side=tk.LEFT, padx=2)
        
        # 平台选择配置
        platform_frame = ttk.LabelFrame(main_tab, text="平台配置")
        platform_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 平台选择
        platform_select_frame = ttk.Frame(platform_frame)
        platform_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(platform_select_frame, text="目标平台:").pack(side=tk.LEFT, padx=5)
        self.platform_var = tk.StringVar()
        self.platform_combo = ttk.Combobox(platform_select_frame, 
                                          textvariable=self.platform_var,
                                          state="readonly", width=20)
        
        # 填充平台选项
        platforms = self.platform_config.get_all_platforms()
        platform_names = [f"{platform.value} - {name}" for platform, name in platforms.items()]
        self.platform_combo['values'] = platform_names
        self.platform_combo.set(platform_names[0] if platform_names else "")
        self.platform_combo.pack(side=tk.LEFT, padx=5)
        self.platform_combo.bind('<<ComboboxSelected>>', self.on_platform_changed)
        
        # EarnVids策略选择（默认隐藏）
        self.earnvids_frame = ttk.Frame(platform_frame)
        
        ttk.Label(self.earnvids_frame, text="播放策略:").pack(side=tk.LEFT, padx=5)
        self.earnvids_strategy_var = tk.StringVar()
        self.earnvids_strategy_combo = ttk.Combobox(self.earnvids_frame,
                                                   textvariable=self.earnvids_strategy_var,
                                                   state="readonly", width=30)
        
        # 填充EarnVids策略
        earnvids_strategies = self.platform_config.get_earnvids_strategy_info()
        self.earnvids_strategy_combo['values'] = earnvids_strategies
        self.earnvids_strategy_combo.set(earnvids_strategies[0] if earnvids_strategies else "")
        self.earnvids_strategy_combo.pack(side=tk.LEFT, padx=5)
        
        # 平台信息显示
        self.platform_info_label = ttk.Label(platform_frame, 
                                            text="选择平台以查看详细信息", 
                                            foreground="gray")
        self.platform_info_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 运行控制
        control_frame = ttk.LabelFrame(main_tab, text="运行控制")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 窗口数量控制
        window_frame = ttk.Frame(control_frame)
        window_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(window_frame, text="并发窗口数:").pack(side=tk.LEFT, padx=5)
        self.window_count_var = tk.StringVar(value="3")
        window_spinbox = ttk.Spinbox(window_frame, from_=1, to=5, width=5, 
                                   textvariable=self.window_count_var)
        window_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 运行模式选择
        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(mode_frame, text="运行模式:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="visible")
        ttk.Radiobutton(mode_frame, text="可视模式", variable=self.mode_var, 
                       value="visible").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="无头模式", variable=self.mode_var, 
                       value="headless").pack(side=tk.LEFT, padx=5)
        
        # 主控制按钮
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="开始播放", 
                                  command=self.start_automation, 
                                  style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="停止播放", 
                                 command=self.stop_automation, 
                                 state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="暂停/恢复", 
                  command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
    
    def create_proxy_tab(self, parent):
        """创建代理管理标签页"""
        proxy_tab = ttk.Frame(parent)
        parent.add(proxy_tab, text="代理管理")
        
        # 代理导入
        import_frame = ttk.LabelFrame(proxy_tab, text="代理导入")
        import_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(import_frame, text="导入代理文件", 
                  command=self.import_proxies).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(import_frame, text="检测代理有效性", 
                  command=self.validate_proxies).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(import_frame, text="清理无效代理", 
                  command=self.clean_invalid_proxies).pack(side=tk.LEFT, padx=5, pady=5)
        
        # API代理配置
        api_frame = ttk.LabelFrame(proxy_tab, text="API代理配置")
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # API代理输入
        api_input_frame = ttk.Frame(api_frame)
        api_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_input_frame, text="API名称:").grid(row=0, column=0, sticky=tk.W, padx=2)
        self.api_name_entry = ttk.Entry(api_input_frame, width=15)
        self.api_name_entry.grid(row=0, column=1, padx=2)
        
        ttk.Label(api_input_frame, text="API URL:").grid(row=0, column=2, sticky=tk.W, padx=2)
        self.api_url_entry = ttk.Entry(api_input_frame, width=30)
        self.api_url_entry.grid(row=0, column=3, padx=2)
        
        ttk.Label(api_input_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, padx=2)
        self.api_key_entry = ttk.Entry(api_input_frame, width=20, show="*")
        self.api_key_entry.grid(row=1, column=1, padx=2)
        
        ttk.Button(api_input_frame, text="添加API代理", 
                  command=self.add_api_proxy).grid(row=1, column=2, padx=5)
        ttk.Button(api_input_frame, text="获取代理列表", 
                  command=self.fetch_api_proxies).grid(row=1, column=3, padx=5)
        
        # 代理列表
        list_frame = ttk.LabelFrame(proxy_tab, text="代理列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建树形视图
        columns = ("类型", "地址", "端口", "用户名", "密码", "状态")
        self.proxy_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.proxy_tree.heading(col, text=col)
            self.proxy_tree.column(col, width=100)
        
        # 滚动条
        proxy_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.proxy_tree.yview)
        self.proxy_tree.configure(yscrollcommand=proxy_scrollbar.set)
        
        self.proxy_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        proxy_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 代理统计
        stats_frame = ttk.LabelFrame(proxy_tab, text="代理统计")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.proxy_stats_label = ttk.Label(stats_frame, text="总计: 0, 有效: 0, 无效: 0")
        self.proxy_stats_label.pack(padx=5, pady=5)
    
    def create_config_tab(self, parent):
        """创建配置标签页"""
        config_tab = ttk.Frame(parent)
        parent.add(config_tab, text="高级配置")
        
        # 设备指纹配置
        fingerprint_frame = ttk.LabelFrame(config_tab, text="设备指纹配置")
        fingerprint_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 浏览器配置
        browser_frame = ttk.Frame(fingerprint_frame)
        browser_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(browser_frame, text="浏览器类型:").pack(side=tk.LEFT, padx=5)
        self.browser_var = tk.StringVar(value="chrome")
        browser_combo = ttk.Combobox(browser_frame, textvariable=self.browser_var, 
                                   values=["chrome", "firefox", "edge"])
        browser_combo.pack(side=tk.LEFT, padx=5)
        
        # 反检测配置
        antidetect_frame = ttk.LabelFrame(config_tab, text="反检测配置")
        antidetect_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stealth_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(antidetect_frame, text="启用隐身模式", 
                       variable=self.stealth_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.disable_images_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(antidetect_frame, text="禁用图片加载", 
                       variable=self.disable_images_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.disable_js_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(antidetect_frame, text="禁用JavaScript", 
                       variable=self.disable_js_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # 拟人化配置
        humanization_frame = ttk.LabelFrame(config_tab, text="拟人化配置")
        humanization_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 延迟配置
        delay_frame = ttk.Frame(humanization_frame)
        delay_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(delay_frame, text="操作延迟范围(秒):").pack(side=tk.LEFT, padx=5)
        self.min_delay_var = tk.StringVar(value="1")
        ttk.Entry(delay_frame, textvariable=self.min_delay_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(delay_frame, text="-").pack(side=tk.LEFT)
        self.max_delay_var = tk.StringVar(value="3")
        ttk.Entry(delay_frame, textvariable=self.max_delay_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # 鼠标移动配置
        mouse_frame = ttk.Frame(humanization_frame)
        mouse_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.random_mouse_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mouse_frame, text="随机鼠标移动", 
                       variable=self.random_mouse_var).pack(side=tk.LEFT, padx=5)
        
        self.random_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mouse_frame, text="随机页面滚动", 
                       variable=self.random_scroll_var).pack(side=tk.LEFT, padx=5)
    
    def create_mouse_control_tab(self, parent):
        """创建鼠标控制标签页"""
        mouse_tab = ttk.Frame(parent)
        parent.add(mouse_tab, text="鼠标控制")
        
        # 鼠标控制框架
        control_frame = ttk.LabelFrame(mouse_tab, text="鼠标操作控制", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 启用/禁用鼠标控制
        self.mouse_control_var = tk.BooleanVar(value=True)
        mouse_control_check = ttk.Checkbutton(
            control_frame, 
            text="允许手动鼠标操作", 
            variable=self.mouse_control_var,
            command=self.toggle_mouse_control
        )
        mouse_control_check.pack(anchor=tk.W, pady=5)
        
        # 鼠标操作指南
        guide_frame = ttk.LabelFrame(mouse_tab, text="操作指南", padding=10)
        guide_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        guide_text = tk.Text(guide_frame, height=10, wrap=tk.WORD)
        guide_text.pack(fill=tk.BOTH, expand=True)
        
        # 插入指南内容
        guidelines = [
            "🎯 鼠标操作指南：",
            "",
            "✅ 安全操作：",
            "   • 可以在浏览器窗口外自由移动鼠标",
            "   • 可以切换窗口、调整音量等",
            "   • 可以查看其他应用程序",
            "",
            "⚠️ 注意事项：",
            "   • 避免在视频播放区域点击",
            "   • 不要干扰自动化操作",
            "   • 避免在广告或弹窗区域点击",
            "   • 保持鼠标移动自然",
            "",
            "⏱️ 交互限制：",
            "   • 每次交互后有2秒冷却时间",
            "   • 避免频繁的鼠标操作",
            "",
            "🛡️ 安全建议：",
            "   • 建议在自动化运行期间减少手动操作",
            "   • 如需操作，请保持自然和缓慢",
            "   • 遇到问题时可以暂停自动化"
        ]
        
        for line in guidelines:
            guide_text.insert(tk.END, line + "\n")
        
        guide_text.config(state=tk.DISABLED)
        
        # 状态显示
        status_frame = ttk.LabelFrame(mouse_tab, text="当前状态", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mouse_status_label = ttk.Label(status_frame, text="鼠标控制: 已启用")
        self.mouse_status_label.pack(anchor=tk.W)
        
        # 更新鼠标状态
        self.update_mouse_status()
    
    def toggle_mouse_control(self):
        """切换鼠标控制状态"""
        enabled = self.mouse_control_var.get()
        self.humanization.enable_mouse_control(enabled)
        self.update_mouse_status()
        self.log_message("INFO", f"鼠标控制已{'启用' if enabled else '禁用'}")
    
    def update_mouse_status(self):
        """更新鼠标状态显示"""
        enabled = self.mouse_control_var.get()
        status_text = f"鼠标控制: {'已启用' if enabled else '已禁用'}"
        if hasattr(self, 'mouse_status_label'):
            self.mouse_status_label.config(text=status_text)
        
    def create_monitor_tab(self, parent):
        """创建监控标签页"""
        monitor_tab = ttk.Frame(parent)
        parent.add(monitor_tab, text="运行监控")
        
        # 实时状态
        status_frame = ttk.LabelFrame(monitor_tab, text="实时状态")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态网格
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行
        row1 = ttk.Frame(status_grid)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="活跃窗口:").pack(side=tk.LEFT, padx=5)
        self.active_windows_label = ttk.Label(row1, text="0/5", foreground="green")
        self.active_windows_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="已播放视频:").pack(side=tk.LEFT, padx=20)
        self.played_videos_label = ttk.Label(row1, text="0", foreground="blue")
        self.played_videos_label.pack(side=tk.LEFT, padx=5)
        
        # 第二行
        row2 = ttk.Frame(status_grid)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="当前IP:").pack(side=tk.LEFT, padx=5)
        self.current_ip_label = ttk.Label(row2, text="未获取", foreground="orange")
        self.current_ip_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="运行时间:").pack(side=tk.LEFT, padx=20)
        self.runtime_label = ttk.Label(row2, text="00:00:00", foreground="purple")
        self.runtime_label.pack(side=tk.LEFT, padx=5)
        
        # 窗口状态列表
        windows_frame = ttk.LabelFrame(monitor_tab, text="窗口状态")
        windows_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 窗口状态树形视图
        window_columns = ("窗口ID", "代理", "设备指纹", "当前URL", "播放状态", "播放次数")
        self.window_tree = ttk.Treeview(windows_frame, columns=window_columns, show="headings")
        
        for col in window_columns:
            self.window_tree.heading(col, text=col)
            self.window_tree.column(col, width=120)
        
        # 滚动条
        window_scrollbar = ttk.Scrollbar(windows_frame, orient=tk.VERTICAL, command=self.window_tree.yview)
        self.window_tree.configure(yscrollcommand=window_scrollbar.set)
        
        self.window_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        window_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_log_tab(self, parent):
        """创建日志标签页"""
        log_tab = ttk.Frame(parent)
        parent.add(log_tab, text="运行日志")
        
        # 日志控制
        log_control_frame = ttk.Frame(log_tab)
        log_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(log_control_frame, text="清空日志", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_control_frame, text="保存日志", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
        # 日志级别选择
        ttk.Label(log_control_frame, text="日志级别:").pack(side=tk.LEFT, padx=(20, 5))
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_control_frame, textvariable=self.log_level_var,
                                     values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        log_level_combo.pack(side=tk.LEFT, padx=5)
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, 
                                                 bg="#1e1e1e", fg="#ffffff",
                                                 font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 配置日志颜色标签
        self.log_text.tag_configure("INFO", foreground="#00ff00")
        self.log_text.tag_configure("WARNING", foreground="#ffff00")
        self.log_text.tag_configure("ERROR", foreground="#ff0000")
        self.log_text.tag_configure("DEBUG", foreground="#00ffff")
    
    def import_urls(self):
        """导入视频URL文件"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择URL文件",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = f.read().strip()
                    self.url_text.delete(1.0, tk.END)
                    self.url_text.insert(1.0, urls)
                
                self.log_message("INFO", f"成功导入URL文件: {file_path}")
        except (IOError, OSError, UnicodeDecodeError) as e:
            self.log_message("ERROR", f"导入URL文件失败: {str(e)}")
            messagebox.showerror("错误", f"导入文件失败: {str(e)}")
        except Exception as e:
            self.log_message("ERROR", f"导入URL文件时发生未知错误: {str(e)}")
            messagebox.showerror("错误", f"导入文件失败: {str(e)}")
    
    def save_urls(self):
        """保存URL列表"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存URL文件",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if file_path:
                urls = self.url_text.get(1.0, tk.END).strip()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(urls)
                
                self.log_message("INFO", f"成功保存URL文件: {file_path}")
        except (IOError, OSError, UnicodeEncodeError) as e:
            self.log_message("ERROR", f"保存URL文件失败: {str(e)}")
            messagebox.showerror("错误", f"保存文件失败: {str(e)}")
        except Exception as e:
            self.log_message("ERROR", f"保存URL文件时发生未知错误: {str(e)}")
            messagebox.showerror("错误", f"保存文件失败: {str(e)}")
    
    def clear_urls(self):
        """清空URL列表"""
        self.url_text.delete(1.0, tk.END)
        self.log_message("INFO", "已清空URL列表")
    
    def on_platform_changed(self, event=None):
        """平台选择变化处理"""
        try:
            selected = self.platform_var.get()
            if not selected:
                return
            
            # 解析选择的平台
            platform_value = selected.split(' - ')[0]
            platform_type = None
            
            for platform in PlatformType:
                if platform.value == platform_value:
                    platform_type = platform
                    break
            
            if not platform_type:
                return
            
            # 更新平台信息显示
            platform_name = self.platform_config.get_platform_name(platform_type)
            strategies = self.platform_config.get_platform_strategies(platform_type)
            
            if self.platform_config.is_earnvids_platform(platform_type):
                # 显示EarnVids策略选择
                self.earnvids_frame.pack(fill=tk.X, padx=5, pady=2)
                info_text = f"平台: {platform_name}\n特殊播放策略: 分等级时长控制"
            else:
                # 隐藏EarnVids策略选择
                self.earnvids_frame.pack_forget()
                if strategies:
                    strategy = strategies[0]
                    info_text = f"平台: {platform_name}\n播放时长: {strategy.min_duration}-{strategy.max_duration}秒"
                else:
                    info_text = f"平台: {platform_name}\n使用默认播放策略"
            
            self.platform_info_label.config(text=info_text, foreground="blue")
            self.log_message("INFO", f"选择平台: {platform_name}")
            
        except Exception as e:
            self.log_message("ERROR", f"平台选择处理失败: {str(e)}")
    
    def get_selected_platform(self) -> PlatformType:
        """获取当前选择的平台"""
        try:
            selected = self.platform_var.get()
            if not selected:
                return PlatformType.GENERIC
            
            platform_value = selected.split(' - ')[0]
            for platform in PlatformType:
                if platform.value == platform_value:
                    return platform
            
            return PlatformType.GENERIC
        except:
            return PlatformType.GENERIC
    
    def get_selected_earnvids_strategy(self) -> int:
        """获取选择的EarnVids策略等级"""
        try:
            selected = self.earnvids_strategy_var.get()
            if not selected:
                return 1
            
            # 从"等级X: 描述"中提取等级
            if selected.startswith("等级"):
                level_str = selected.split(':')[0].replace("等级", "")
                return int(level_str)
            
            return 1
        except:
            return 1
    
    def import_proxies(self):
        """导入代理文件"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择代理文件",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if file_path:
                imported_count = self.proxy_manager.import_from_file(file_path)
                self.update_proxy_tree()
                self.log_message("INFO", f"成功导入 {imported_count} 个代理")
                messagebox.showinfo("成功", f"成功导入 {imported_count} 个代理")
        except (IOError, OSError) as e:
            self.log_message("ERROR", f"读取代理文件失败: {str(e)}")
            messagebox.showerror("错误", f"导入代理失败: {str(e)}")
        except ValueError as e:
            self.log_message("ERROR", f"代理文件格式错误: {str(e)}")
            messagebox.showerror("错误", f"代理文件格式错误: {str(e)}")
        except Exception as e:
            self.log_message("ERROR", f"导入代理文件时发生未知错误: {str(e)}")
            messagebox.showerror("错误", f"导入代理失败: {str(e)}")
    
    def validate_proxies(self):
        """验证代理有效性"""
        def validate_thread():
            try:
                self.log_message("INFO", "开始验证代理有效性...")
                valid_count, invalid_count = self.proxy_manager.validate_all_proxies()
                self.update_proxy_tree()
                self.log_message("INFO", f"代理验证完成 - 有效: {valid_count}, 无效: {invalid_count}")
                
                # 在主线程中显示消息框
                self.root.after(0, lambda: messagebox.showinfo("验证完成", 
                    f"代理验证完成\n有效: {valid_count}\n无效: {invalid_count}"))
            except Exception as e:
                self.log_message("ERROR", f"代理验证失败: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"代理验证失败: {str(e)}"))
        
        # 在后台线程中执行验证
        threading.Thread(target=validate_thread, daemon=True).start()
    
    def clean_invalid_proxies(self):
        """清理无效代理"""
        try:
            removed_count = self.proxy_manager.remove_invalid_proxies()
            self.update_proxy_tree()
            self.log_message("INFO", f"已清理 {removed_count} 个无效代理")
            messagebox.showinfo("清理完成", f"已清理 {removed_count} 个无效代理")
        except Exception as e:
            self.log_message("ERROR", f"清理代理失败: {str(e)}")
            messagebox.showerror("错误", f"清理代理失败: {str(e)}")
    
    def add_api_proxy(self):
        """添加API代理配置"""
        try:
            name = self.api_name_entry.get().strip()
            url = self.api_url_entry.get().strip()
            key = self.api_key_entry.get().strip()
            
            if not name or not url:
                messagebox.showerror("错误", "API名称和URL不能为空")
                return
            
            success = self.proxy_manager.add_api_proxy(name, url, key)
            if success:
                self.log_message("INFO", f"成功添加API代理: {name}")
                # 清空输入框
                self.api_name_entry.delete(0, tk.END)
                self.api_url_entry.delete(0, tk.END)
                self.api_key_entry.delete(0, tk.END)
                messagebox.showinfo("成功", f"API代理 '{name}' 添加成功")
            else:
                messagebox.showerror("错误", "添加API代理失败")
            
        except Exception as e:
            self.log_message("ERROR", f"添加API代理失败: {str(e)}")
            messagebox.showerror("错误", f"添加失败: {str(e)}")
    
    def fetch_api_proxies(self):
        """从API获取代理列表"""
        def fetch_thread():
            try:
                self.log_message("INFO", "开始从API获取代理列表...")
                api_proxies = self.proxy_manager.get_api_proxy_list()
                
                if api_proxies:
                    # 将API代理添加到主代理列表
                    for proxy in api_proxies:
                        self.proxy_manager.proxies.append(proxy)
                    
                    self.proxy_manager.save_proxies()
                    self.update_proxy_tree()
                    self.log_message("INFO", f"成功获取 {len(api_proxies)} 个API代理")
                    messagebox.showinfo("成功", f"获取到 {len(api_proxies)} 个代理")
                else:
                    self.log_message("WARNING", "未获取到任何代理")
                    messagebox.showwarning("提示", "未获取到任何代理")
                    
            except Exception as e:
                self.log_message("ERROR", f"获取API代理失败: {str(e)}")
                messagebox.showerror("错误", f"获取失败: {str(e)}")
        
        # 在后台线程执行
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()
    
    def update_proxy_tree(self):
        """更新代理树形视图"""
        # 清空现有项目
        for item in self.proxy_tree.get_children():
            self.proxy_tree.delete(item)
        
        # 添加代理项目
        proxies = self.proxy_manager.get_all_proxies()
        for proxy in proxies:
            status = "有效" if proxy.get('valid', False) else "未验证"
            self.proxy_tree.insert("", tk.END, values=(
                proxy.get('type', ''),
                proxy.get('host', ''),
                proxy.get('port', ''),
                proxy.get('username', ''),
                proxy.get('password', ''),
                status
            ))
        
        # 更新统计
        total = len(proxies)
        valid = sum(1 for p in proxies if p.get('valid', False))
        invalid = sum(1 for p in proxies if p.get('valid') is False)
        
        self.proxy_stats_label.config(text=f"总计: {total}, 有效: {valid}, 无效: {invalid}")
    
    def start_automation(self) -> None:
        """开始自动化播放"""
        try:
            # 获取配置
            urls = self.get_video_urls()
            if not urls:
                messagebox.showerror("错误", "请先添加视频URL")
                return
            
            proxies = self.proxy_manager.get_valid_proxies()
            if not proxies:
                messagebox.showerror("错误", "没有有效的代理服务器")
                return
            
            window_count = int(self.window_count_var.get())
            
            # 更新状态（线程安全）
            with self._status_lock:
                self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # 启动自动化线程
            self.automation_thread = threading.Thread(
                target=self.run_automation,
                args=(urls, proxies, window_count),
                daemon=True
            )
            self.automation_thread.start()
            
            self.log_message("INFO", f"开始自动化播放 - 窗口数: {window_count}")
            
        except Exception as e:
            self.log_message("ERROR", f"启动自动化失败: {str(e)}")
            messagebox.showerror("错误", f"启动失败: {str(e)}")
    
    def stop_automation(self) -> None:
        """停止自动化播放"""
        try:
            with self._status_lock:
                self.is_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            # 关闭所有窗口
            self.window_manager.close_all_windows()
            
            # 记录行为洞察
            self.log_behavior_insights()
            
            self.log_message("INFO", "已停止自动化播放")
            
        except Exception as e:
            self.log_message("ERROR", f"停止自动化失败: {str(e)}")
    
    def toggle_pause(self):
        """暂停/恢复播放"""
        try:
            # 获取所有活跃窗口并暂停/恢复
            windows = self.window_manager.get_all_windows()
            for window in windows:
                if window.status.value == 'active' or window.status.value == 'playing':
                    self.window_manager.pause_window(window.window_id)
                    self.log_message("INFO", f"暂停窗口: {window.window_id[:8]}...")
                elif window.status.value == 'paused':
                    self.window_manager.resume_window(window.window_id)
                    self.log_message("INFO", f"恢复窗口: {window.window_id[:8]}...")
        
        except Exception as e:
            self.log_message("ERROR", f"暂停/恢复操作失败: {str(e)}")
    
    def get_video_urls(self):
        """获取视频URL列表"""
        urls_text = self.url_text.get(1.0, tk.END).strip()
        if not urls_text:
            return []
        
        urls = []
        for line in urls_text.split('\n'):
            line = line.strip()
            if line and line.startswith('http'):
                urls.append(line)
        
        return urls
    
    def run_automation(self, urls, proxies, window_count):
        """运行自动化流程"""
        try:
            self.start_time = datetime.now()
            with self._count_lock:
                self.played_videos_count = 0
            
            # 获取运行模式
            headless_mode = self.mode_var.get() == "headless"
            self.log_message("INFO", f"运行模式: {'无头模式' if headless_mode else '可视模式'}")
            
            # 检查是否使用代理
            use_proxy = len(proxies) > 0
            if not use_proxy:
                self.log_message("INFO", "不使用代理直接播放视频")
            
            # 启动多个窗口
            for i in range(window_count):
                with self._status_lock:
                    if not self.is_running:
                        break
                
                # 分配代理和指纹
                proxy = None
                if use_proxy:
                    proxy = self.proxy_manager.get_next_proxy()
                    if not proxy and use_proxy:
                        self.log_message("WARNING", f"无法获取代理，跳过窗口 {i+1}")
                        continue
                
                fingerprint = self.fingerprint_engine.generate_fingerprint()
                
                # 随机选择URL
                url = urls[i % len(urls)] if urls else "https://example.com"
                
                # 获取平台信息
                selected_platform = self.get_selected_platform()
                earnvids_strategy = self.get_selected_earnvids_strategy() if selected_platform == PlatformType.EARNVIDS else 1
                
                # 创建窗口
                window_id = self.window_manager.create_window(
                    proxy=proxy,
                    fingerprint=fingerprint,
                    url=url,
                    browser_automation=self.browser_automation,
                    video_player=self.video_player,
                    humanizer=self.humanization,
                    session_manager=self.session_manager,
                    proxy_manager=self.proxy_manager,
                    fingerprint_engine=self.fingerprint_engine,
                    platform_config=self.platform_config,
                    selected_platform=selected_platform,
                    earnvids_strategy=earnvids_strategy,
                    headless=headless_mode  # 传递无头模式设置
                )
                
                if window_id:
                    self.log_message("INFO", f"创建窗口成功: {window_id[:8]}...")
                else:
                    self.log_message("ERROR", f"创建窗口失败")
                
                # 随机延迟启动
                time.sleep(random.uniform(2, 8))
        
        except Exception as e:
            self.log_message("ERROR", f"自动化运行失败: {str(e)}")
    
    def on_window_status_update(self, status_update: Dict):
        """窗口状态更新回调"""
        try:
            window_id = status_update.get('window_id', '')
            status = status_update.get('status', '')
            message = status_update.get('message', '')
            
            # 记录状态变化
            self.log_message("INFO", f"窗口 {window_id[:8]}... 状态: {status} - {message}")
            
            # 如果是播放完成，增加计数
            if "播放完成" in message:
                with self._count_lock:
                    self.played_videos_count += 1
        
        except Exception as e:
            self.log_message("ERROR", f"处理窗口状态更新失败: {str(e)}")
    
    def log_behavior_insights(self):
        """记录行为洞察"""
        try:
            if hasattr(self.humanization, 'get_behavior_insights'):
                insights = self.humanization.get_behavior_insights()
                if insights:
                    self.logger.info("行为分析报告:")
                    self.logger.info(f"  - 疲劳度: {insights.get('fatigue_level', 0):.2f}")
                    self.logger.info(f"  - 学习曲线: {insights.get('learning_curve', 0):.2f}")
                    self.logger.info(f"  - 错误次数: {insights.get('error_count', 0)}")
                    self.logger.info(f"  - 行为一致性: {insights.get('behavior_consistency', 0):.2f}")
                    
        except Exception as e:
            self.logger.debug(f"行为洞察记录失败: {str(e)}")
    
    def update_status_display(self):
        """更新状态显示"""
        try:
            # 更新活跃窗口数量
            active_count = self.window_manager.get_active_windows_count()
            max_count = self.window_manager.max_windows
            self.active_windows_label.config(text=f"{active_count}/{max_count}")
            
            # 更新播放视频数量（线程安全）
            with self._count_lock:
                played_count = self.played_videos_count
            self.played_videos_label.config(text=str(played_count))
            
            # 更新运行时间
            if self.start_time:
                runtime = datetime.now() - self.start_time
                hours, remainder = divmod(runtime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.runtime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # 更新窗口状态树
            self.update_window_tree()
            
            # 继续定时更新
            self.root.after(1000, self.update_status_display)
        
        except Exception as e:
            self.log_message("ERROR", f"更新状态显示失败: {str(e)}")
            # 即使出错也要继续定时更新
            self.root.after(1000, self.update_status_display)
    
    def update_window_tree(self):
        """更新窗口状态树"""
        try:
            # 清空现有项目
            for item in self.window_tree.get_children():
                self.window_tree.delete(item)
            
            # 获取窗口信息
            windows = self.window_manager.get_all_windows()
            
            for window in windows:
                # 格式化显示信息
                proxy_info = f"{window.proxy_info.get('host', 'N/A')}:{window.proxy_info.get('port', 'N/A')}"
                fingerprint_info = window.fingerprint_info.get('fingerprint_id', 'N/A')[:16] + "..."
                current_url = window.current_url[:50] + "..." if len(window.current_url) > 50 else window.current_url
                
                self.window_tree.insert("", tk.END, values=(
                    window.window_id[:8] + "...",
                    proxy_info,
                    fingerprint_info,
                    current_url,
                    window.status.value,
                    str(window.play_count)
                ))
        
        except Exception as e:
            self.log_message("ERROR", f"更新窗口树失败: {str(e)}")
    
    def log_message(self, level: str, message: str) -> None:
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 添加到队列
        self.log_queue.put((level, log_entry))
        
        # 添加到文件日志
        if hasattr(self, 'logger'):
            getattr(self.logger, level.lower())(message)
    
    def process_log_queue(self):
        """处理日志队列"""
        try:
            while not self.log_queue.empty():
                level, message = self.log_queue.get_nowait()
                
                # 检查日志级别过滤
                current_level = self.log_level_var.get()
                level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
                
                if level_priority.get(level, 1) >= level_priority.get(current_level, 1):
                    self.log_text.insert(tk.END, message + "\n", level)
                    self.log_text.see(tk.END)
        
        except queue.Empty:
            pass
        
        # 继续检查队列
        self.root.after(100, self.process_log_queue)
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("INFO", "日志已清空")
    
    def save_logs(self):
        """保存日志"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存日志文件",
                defaultextension=".log",
                filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if file_path:
                logs = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(logs)
                
                self.log_message("INFO", f"日志已保存到: {file_path}")
        except Exception as e:
            self.log_message("ERROR", f"保存日志失败: {str(e)}")
    
    def run(self):
        """运行主程序"""
        try:
            # 应用样式
            style = ttk.Style()
            style.theme_use('clam')
            
            # 配置样式
            style.configure("Accent.TButton", foreground="white", background="#0078d4")
            
            # 设置关闭窗口处理
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            self.root.mainloop()
        except Exception as e:
            print(f"程序运行错误: {str(e)}")
            self.logger.error(f"程序运行错误: {str(e)}")
    
    def on_closing(self):
        """程序关闭处理"""
        try:
            with self._status_lock:
                if self.is_running:
                    self.stop_automation()
            
            # 关闭窗口管理器
            self.window_manager.shutdown()
            
            # 关闭浏览器自动化
            self.browser_automation.close_all_drivers()
            
            self.root.destroy()
        
        except Exception as e:
            print(f"关闭程序时发生错误: {str(e)}")
            self.root.destroy()

def main() -> None:
    """主函数"""
    # 创建必要的目录（使用配置）
    os.makedirs(config.logs_dir, exist_ok=True)
    os.makedirs(config.data_dir, exist_ok=True)
    
    # 启动应用
    app = VideoAutomationTool()
    app.run()

if __name__ == "__main__":
    main()
