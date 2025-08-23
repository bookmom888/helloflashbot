#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块
Logger Utility Module

提供统一的日志配置和管理
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional

def setup_logger(name: str, level: str = "INFO", 
                log_file: Optional[str] = None) -> logging.Logger:
    """设置日志记录器"""
    
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if not log_file:
        log_file = f"logs/{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
