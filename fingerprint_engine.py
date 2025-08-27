#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备指纹生成引擎
Device Fingerprint Generation Engine

生成真实的设备指纹，包括：
- User-Agent字符串
- 屏幕分辨率
- 时区设置
- 语言设置
- WebGL指纹
- Canvas指纹
- 音频指纹
"""

import json
import random
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import base64
from advanced_fingerprint import AdvancedFingerprintEngine

class FingerprintEngine:
    """设备指纹生成引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 加载指纹数据库
        self.user_agents = self._load_user_agents()
        self.screen_resolutions = self._load_screen_resolutions()
        self.timezones = self._load_timezones()
        self.languages = self._load_languages()
        self.webgl_vendors = self._load_webgl_vendors()
        self.webgl_renderers = self._load_webgl_renderers()
        
        # 高级指纹引擎
        self.advanced_engine = AdvancedFingerprintEngine()
        
        # 缓存生成的指纹
        self.fingerprint_cache = {}
    
    def generate_fingerprint(self) -> Dict:
        """生成完整的设备指纹"""
        try:
            # 选择基础操作系统和浏览器
            browser_info = self._select_browser_info()
            
            fingerprint = {
                'user_agent': browser_info['user_agent'],
                'platform': browser_info['platform'],
                'browser': browser_info['browser'],
                'browser_version': browser_info['version'],
                
                # 屏幕信息
                'screen': self._generate_screen_info(),
                
                # 时区和语言
                'timezone': self._select_timezone(),
                'languages': self._select_languages(),
                
                # WebGL指纹
                'webgl': self._generate_webgl_fingerprint(),
                
                # Canvas指纹
                'canvas': self._generate_canvas_fingerprint(),
                
                # 音频指纹
                'audio': self._generate_audio_fingerprint(),
                
                # 插件信息
                'plugins': self._generate_plugins(browser_info['browser']),
                
                # 字体信息
                'fonts': self._generate_fonts(),
                
                # 硬件信息
                'hardware': self._generate_hardware_info(),
                
                # 网络信息
                'network': self._generate_network_info(),
                
                # 媒体设备信息
                'media_devices': self._generate_media_devices(),
                
                # 浏览器特征
                'browser_features': self._generate_browser_features(),
                
                # 行为特征
                'behavioral': self._generate_behavioral_patterns(),
                
                # 其他属性
                'do_not_track': random.choice([None, '1', 'unspecified']),
                'cookie_enabled': True,
                'java_enabled': random.choice([True, False]),
                'local_storage': True,
                'session_storage': True,
                'indexed_db': True,
                
                # 指纹ID和时间戳
                'fingerprint_id': self._generate_fingerprint_id(),
                'created_at': datetime.now().isoformat()
            }
            
            # 集成高级指纹
            try:
                advanced_fingerprint = self.advanced_engine.generate_comprehensive_fingerprint()
                fingerprint.update({
                    'advanced': advanced_fingerprint,
                    'fingerprint_version': '2.0_enhanced'
                })
                self.logger.debug("成功集成高级指纹特征")
            except Exception as e:
                self.logger.warning(f"高级指纹生成失败，使用基础指纹: {str(e)}")
                fingerprint.update({
                    'fingerprint_version': '1.0_basic'
                })
            
            # 确保指纹的一致性
            self._ensure_consistency(fingerprint)
            
            return fingerprint
        
        except Exception as e:
            self.logger.error(f"生成设备指纹失败: {str(e)}")
            return self._get_default_fingerprint()
    
    def _generate_network_info(self) -> Dict:
        """生成网络信息"""
        connection_types = ['wifi', 'ethernet', 'cellular']
        effective_types = ['4g', '3g', 'slow-2g', '2g']
        
        return {
            'connection_type': random.choice(connection_types),
            'effective_type': random.choice(effective_types),
            'downlink': round(random.uniform(1.0, 50.0), 1),
            'rtt': random.randint(50, 300),
            'save_data': random.choice([True, False])
        }
    
    def _generate_media_devices(self) -> Dict:
        """生成媒体设备信息"""
        audio_inputs = random.randint(0, 2)
        video_inputs = random.randint(0, 1)
        audio_outputs = random.randint(1, 3)
        
        devices = []
        
        # 音频输入设备
        for i in range(audio_inputs):
            devices.append({
                'kind': 'audioinput',
                'label': f'Default - Microphone ({i+1})',
                'deviceId': self._generate_device_id()
            })
        
        # 视频输入设备
        for i in range(video_inputs):
            devices.append({
                'kind': 'videoinput', 
                'label': f'Integrated Camera ({i+1})',
                'deviceId': self._generate_device_id()
            })
        
        # 音频输出设备
        for i in range(audio_outputs):
            devices.append({
                'kind': 'audiooutput',
                'label': f'Default - Speaker ({i+1})',
                'deviceId': self._generate_device_id()
            })
        
        return {
            'devices': devices,
            'permissions': {
                'camera': random.choice(['granted', 'denied', 'prompt']),
                'microphone': random.choice(['granted', 'denied', 'prompt'])
            }
        }
    
    def _generate_device_id(self) -> str:
        """生成设备ID"""
        return hashlib.md5(f"{random.random()}{time.time()}".encode()).hexdigest()
    
    def _generate_browser_features(self) -> Dict:
        """生成浏览器特征"""
        return {
            'webgl_version': random.choice(['WebGL 1.0', 'WebGL 2.0']),
            'webgl2_support': random.choice([True, False]),
            'webrtc_support': True,
            'geolocation_support': True,
            'notification_support': True,
            'service_worker_support': True,
            'push_manager_support': True,
            'battery_api_support': random.choice([True, False]),
            'gamepad_support': random.choice([True, False]),
            'vibration_support': random.choice([True, False]),
            'webgl_extensions': self._generate_webgl_extensions(),
            'css_features': self._generate_css_features(),
            'js_heap_size_limit': random.randint(2000000000, 4000000000),
            'max_touch_points': random.choice([0, 5, 10]),
            'pointer_events': random.choice([True, False])
        }
    
    def _generate_webgl_extensions(self) -> List[str]:
        """生成WebGL扩展列表"""
        extensions = [
            'ANGLE_instanced_arrays',
            'EXT_blend_minmax', 
            'EXT_color_buffer_half_float',
            'EXT_disjoint_timer_query',
            'EXT_float_blend',
            'EXT_frag_depth',
            'EXT_shader_texture_lod',
            'EXT_texture_filter_anisotropic',
            'WEBKIT_EXT_texture_filter_anisotropic',
            'EXT_sRGB',
            'OES_element_index_uint',
            'OES_standard_derivatives',
            'OES_texture_float',
            'OES_texture_float_linear',
            'OES_texture_half_float',
            'OES_texture_half_float_linear',
            'OES_vertex_array_object',
            'WEBGL_color_buffer_float',
            'WEBGL_compressed_texture_s3tc',
            'WEBGL_debug_renderer_info',
            'WEBGL_debug_shaders',
            'WEBGL_depth_texture',
            'WEBGL_draw_buffers',
            'WEBGL_lose_context'
        ]
        
        # 随机选择一些扩展
        num_extensions = random.randint(15, len(extensions))
        return random.sample(extensions, num_extensions)
    
    def _generate_css_features(self) -> Dict:
        """生成CSS特征支持"""
        return {
            'css_grid': True,
            'css_flexbox': True,
            'css_variables': True,
            'css_animations': True,
            'css_transforms': True,
            'css_filters': True,
            'css_backdrop_filter': random.choice([True, False]),
            'css_clip_path': True,
            'css_mask': random.choice([True, False])
        }
    
    def _generate_behavioral_patterns(self) -> Dict:
        """生成行为模式特征"""
        return {
            'mouse_movement_entropy': round(random.uniform(0.7, 0.95), 3),
            'keystroke_dynamics': {
                'avg_dwell_time': random.randint(80, 150),
                'avg_flight_time': random.randint(50, 120),
                'rhythm_consistency': round(random.uniform(0.6, 0.9), 3)
            },
            'scroll_behavior': {
                'avg_scroll_speed': random.randint(200, 800),
                'scroll_acceleration': round(random.uniform(1.2, 2.5), 2),
                'scroll_momentum': round(random.uniform(0.8, 1.2), 2)
            },
            'click_patterns': {
                'avg_click_duration': random.randint(80, 200),
                'double_click_interval': random.randint(250, 500),
                'click_pressure_variance': round(random.uniform(0.1, 0.3), 2)
            },
            'focus_patterns': {
                'avg_focus_duration': random.randint(2000, 15000),
                'tab_switch_frequency': round(random.uniform(0.1, 2.0), 2),
                'window_idle_time': random.randint(5000, 30000)
            }
        }
    
    def _load_user_agents(self) -> List[Dict]:
        """加载User-Agent数据"""
        return [
            # Chrome Windows
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'browser': 'chrome',
                'version': '120.0.0.0',
                'platform': 'Windows NT 10.0; Win64; x64',
                'os': 'windows'
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'browser': 'chrome',
                'version': '119.0.0.0',
                'platform': 'Windows NT 10.0; Win64; x64',
                'os': 'windows'
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'browser': 'chrome',
                'version': '118.0.0.0',
                'platform': 'Windows NT 10.0; Win64; x64',
                'os': 'windows'
            },
            
            # Chrome macOS
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'browser': 'chrome',
                'version': '120.0.0.0',
                'platform': 'Macintosh; Intel Mac OS X 10_15_7',
                'os': 'macos'
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'browser': 'chrome',
                'version': '119.0.0.0',
                'platform': 'Macintosh; Intel Mac OS X 10_15_7',
                'os': 'macos'
            },
            
            # Firefox Windows
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'browser': 'firefox',
                'version': '120.0',
                'platform': 'Windows NT 10.0; Win64; x64',
                'os': 'windows'
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
                'browser': 'firefox',
                'version': '119.0',
                'platform': 'Windows NT 10.0; Win64; x64',
                'os': 'windows'
            },
            
            # Edge Windows
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'browser': 'edge',
                'version': '120.0.0.0',
                'platform': 'Windows NT 10.0; Win64; x64',
                'os': 'windows'
            }
        ]
    
    def _load_screen_resolutions(self) -> List[Tuple[int, int]]:
        """加载常见屏幕分辨率"""
        return [
            (1920, 1080),  # Full HD
            (1366, 768),   # HD
            (1440, 900),   # WXGA+
            (1536, 864),   # HD+
            (1600, 900),   # HD+
            (1680, 1050),  # WSXGA+
            (1920, 1200),  # WUXGA
            (2560, 1440),  # QHD
            (2560, 1600),  # WQXGA
            (3840, 2160),  # 4K UHD
            (1280, 720),   # HD Ready
            (1024, 768),   # XGA
            (1280, 1024),  # SXGA
            (1920, 1080),  # Full HD (重复增加权重)
            (1366, 768),   # HD (重复增加权重)
        ]
    
    def _load_timezones(self) -> List[str]:
        """加载时区列表"""
        return [
            'America/New_York',
            'America/Los_Angeles',
            'America/Chicago',
            'America/Denver',
            'Europe/London',
            'Europe/Paris',
            'Europe/Berlin',
            'Europe/Rome',
            'Asia/Tokyo',
            'Asia/Shanghai',
            'Asia/Seoul',
            'Asia/Kolkata',
            'Australia/Sydney',
            'Australia/Melbourne',
            'Pacific/Auckland',
            'America/Toronto',
            'America/Vancouver',
            'Europe/Amsterdam',
            'Europe/Madrid',
            'Asia/Singapore',
            'Asia/Hong_Kong',
            'Asia/Bangkok'
        ]
    
    def _load_languages(self) -> List[List[str]]:
        """加载语言设置"""
        return [
            ['en-US', 'en'],
            ['zh-CN', 'zh'],
            ['en-GB', 'en'],
            ['ja-JP', 'ja'],
            ['ko-KR', 'ko'],
            ['de-DE', 'de'],
            ['fr-FR', 'fr'],
            ['es-ES', 'es'],
            ['it-IT', 'it'],
            ['pt-BR', 'pt'],
            ['ru-RU', 'ru'],
            ['en-US', 'en', 'zh-CN'],
            ['en-US', 'en', 'es'],
            ['en-US', 'en', 'fr'],
        ]
    
    def _load_webgl_vendors(self) -> List[str]:
        """加载WebGL供应商"""
        return [
            'Google Inc. (NVIDIA)',
            'Google Inc. (Intel)',
            'Google Inc. (AMD)',
            'Google Inc. (Qualcomm)',
            'Mozilla',
            'Microsoft Corporation',
            'Apple Inc.'
        ]
    
    def _load_webgl_renderers(self) -> List[str]:
        """加载WebGL渲染器"""
        return [
            'ANGLE (NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)',
            'WebKit WebGL',
            'Mozilla WebGL',
            'ANGLE (Qualcomm Adreno 640 Direct3D11 vs_5_0 ps_5_0)'
        ]
    
    def _select_browser_info(self) -> Dict:
        """选择浏览器信息"""
        return random.choice(self.user_agents)
    
    def _generate_screen_info(self) -> Dict:
        """生成屏幕信息"""
        width, height = random.choice(self.screen_resolutions)
        
        # 计算可用区域（减去任务栏等）
        available_width = width
        available_height = height - random.randint(30, 80)
        
        # 颜色深度
        color_depth = random.choice([24, 32])
        pixel_depth = color_depth
        
        return {
            'width': width,
            'height': height,
            'available_width': available_width,
            'available_height': available_height,
            'color_depth': color_depth,
            'pixel_depth': pixel_depth,
            'device_pixel_ratio': random.choice([1, 1.25, 1.5, 2])
        }
    
    def _select_timezone(self) -> str:
        """选择时区"""
        return random.choice(self.timezones)
    
    def _select_languages(self) -> List[str]:
        """选择语言设置"""
        return random.choice(self.languages)
    
    def _generate_webgl_fingerprint(self) -> Dict:
        """生成WebGL指纹"""
        vendor = random.choice(self.webgl_vendors)
        renderer = random.choice(self.webgl_renderers)
        
        # 生成一些WebGL参数
        return {
            'vendor': vendor,
            'renderer': renderer,
            'version': 'WebGL 1.0',
            'shading_language_version': 'WebGL GLSL ES 1.0',
            'max_texture_size': random.choice([4096, 8192, 16384]),
            'max_viewport_dims': [16384, 16384],
            'max_vertex_attribs': 16,
            'max_vertex_uniform_vectors': random.choice([256, 512, 1024]),
            'max_fragment_uniform_vectors': random.choice([256, 512, 1024]),
            'max_varying_vectors': random.choice([8, 15, 31]),
            'aliased_line_width_range': [1, 1],
            'aliased_point_size_range': [1, 64]
        }
    
    def _generate_canvas_fingerprint(self) -> str:
        """生成Canvas指纹"""
        # 模拟Canvas指纹生成
        text = "BrowserFingerprint,1.0"
        base_hash = hashlib.md5(text.encode()).hexdigest()
        
        # 添加一些随机性
        random_suffix = random.randint(1000, 9999)
        return f"{base_hash[:16]}{random_suffix}"
    
    def _generate_audio_fingerprint(self) -> str:
        """生成音频指纹"""
        # 模拟音频指纹
        audio_data = [
            random.uniform(-1, 1) for _ in range(10)
        ]
        
        audio_str = ','.join([f"{x:.6f}" for x in audio_data])
        return hashlib.sha256(audio_str.encode()).hexdigest()[:16]
    
    def _generate_plugins(self, browser: str) -> List[Dict]:
        """生成插件列表"""
        base_plugins = []
        
        if browser == 'chrome':
            base_plugins = [
                {
                    'name': 'Portable Document Format',
                    'filename': 'internal-pdf-viewer',
                    'description': 'Portable Document Format'
                },
                {
                    'name': 'Chromium PDF Plugin',
                    'filename': 'internal-pdf-viewer',
                    'description': 'Portable Document Format'
                }
            ]
        elif browser == 'firefox':
            base_plugins = [
                {
                    'name': 'PDF.js',
                    'filename': 'pdf.js',
                    'description': 'Portable Document Format'
                }
            ]
        
        # 随机添加一些其他插件
        additional_plugins = [
            {
                'name': 'Microsoft Office Live Plug-in',
                'filename': 'npOLW.dll',
                'description': 'Office Live'
            },
            {
                'name': 'Java Deployment Toolkit',
                'filename': 'npDeployJava1.dll',
                'description': 'Java'
            }
        ]
        
        # 随机选择是否包含额外插件
        for plugin in additional_plugins:
            if random.choice([True, False]):
                base_plugins.append(plugin)
        
        return base_plugins
    
    def _generate_fonts(self) -> List[str]:
        """生成字体列表"""
        common_fonts = [
            'Arial', 'Arial Black', 'Arial Narrow', 'Book Antiqua',
            'Bookman Old Style', 'Calibri', 'Cambria', 'Century',
            'Century Gothic', 'Comic Sans MS', 'Consolas', 'Courier',
            'Courier New', 'Garamond', 'Georgia', 'Helvetica',
            'Impact', 'Lucida Console', 'Lucida Sans Unicode',
            'Microsoft Sans Serif', 'Palatino Linotype', 'Symbol',
            'Tahoma', 'Times', 'Times New Roman', 'Trebuchet MS',
            'Verdana', 'Webdings', 'Wingdings'
        ]
        
        # 随机选择字体数量
        font_count = random.randint(20, len(common_fonts))
        return random.sample(common_fonts, font_count)
    
    def _generate_hardware_info(self) -> Dict:
        """生成硬件信息"""
        return {
            'cpu_cores': random.choice([4, 6, 8, 12, 16]),
            'memory_gb': random.choice([8, 16, 32, 64]),
            'max_touch_points': random.choice([0, 1, 2, 5, 10]),
            'pointer': random.choice(['fine', 'coarse', 'none']),
            'hover': random.choice(['hover', 'none']),
            'orientation_angle': random.choice([0, 90, 180, 270]),
            'orientation_type': random.choice(['landscape-primary', 'portrait-primary'])
        }
    
    def _generate_fingerprint_id(self) -> str:
        """生成唯一指纹ID"""
        timestamp = str(int(time.time() * 1000))
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        return f"{timestamp}_{random_str}"
    
    def _ensure_consistency(self, fingerprint: Dict):
        """确保指纹的一致性"""
        # 确保语言和时区的匹配
        languages = fingerprint['languages']
        timezone = fingerprint['timezone']
        
        # 根据时区调整语言
        if 'America/' in timezone:
            if 'en' not in languages[0]:
                fingerprint['languages'] = ['en-US', 'en']
        elif 'Asia/Shanghai' in timezone or 'Asia/Hong_Kong' in timezone:
            if 'zh' not in languages[0]:
                fingerprint['languages'] = ['zh-CN', 'zh']
        elif 'Asia/Tokyo' in timezone:
            if 'ja' not in languages[0]:
                fingerprint['languages'] = ['ja-JP', 'ja']
        
        # 确保WebGL和Canvas指纹匹配操作系统
        if 'Windows' in fingerprint['platform']:
            if 'ANGLE' not in fingerprint['webgl']['renderer']:
                fingerprint['webgl']['renderer'] = random.choice([
                    r for r in self.webgl_renderers if 'ANGLE' in r
                ])
        
        # 确保屏幕分辨率合理
        screen = fingerprint['screen']
        if screen['width'] < screen['height']:
            # 交换宽高（通常桌面是横屏）
            screen['width'], screen['height'] = screen['height'], screen['width']
            screen['available_width'] = screen['width']
            screen['available_height'] = screen['height'] - random.randint(30, 80)
    
    def _get_default_fingerprint(self) -> Dict:
        """获取默认指纹"""
        return {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'platform': 'Windows NT 10.0; Win64; x64',
            'browser': 'chrome',
            'browser_version': '120.0.0.0',
            'screen': {
                'width': 1920,
                'height': 1080,
                'available_width': 1920,
                'available_height': 1040,
                'color_depth': 24,
                'pixel_depth': 24,
                'device_pixel_ratio': 1
            },
            'timezone': 'America/New_York',
            'languages': ['en-US', 'en'],
            'webgl': {
                'vendor': 'Google Inc. (NVIDIA)',
                'renderer': 'ANGLE (NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)',
                'version': 'WebGL 1.0'
            },
            'canvas': 'default_canvas_hash',
            'audio': 'default_audio_hash',
            'plugins': [],
            'fonts': ['Arial', 'Times New Roman', 'Helvetica'],
            'hardware': {
                'cpu_cores': 8,
                'memory_gb': 16
            },
            'fingerprint_id': f"default_{int(time.time())}",
            'created_at': datetime.now().isoformat()
        }
    
    def get_browser_options(self, fingerprint: Dict) -> Dict:
        """根据指纹生成浏览器选项"""
        options = {
            'user_agent': fingerprint['user_agent'],
            'viewport': {
                'width': fingerprint['screen']['width'],
                'height': fingerprint['screen']['height']
            },
            'timezone': fingerprint['timezone'],
            'locale': fingerprint['languages'][0],
            'device_scale_factor': fingerprint['screen']['device_pixel_ratio']
        }
        
        return options
    
    def apply_fingerprint_to_driver(self, driver, fingerprint: Dict):
        """将指纹应用到WebDriver"""
        try:
            # 执行JavaScript来设置指纹
            js_script = f"""
            // 重写navigator属性
            Object.defineProperty(navigator, 'userAgent', {{
                get: function() {{ return '{fingerprint['user_agent']}'; }}
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: function() {{ return '{fingerprint['platform']}'; }}
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: function() {{ return {json.dumps(fingerprint['languages'])}; }}
            }});
            
            Object.defineProperty(navigator, 'language', {{
                get: function() {{ return '{fingerprint['languages'][0]}'; }}
            }});
            
            // 重写screen属性
            Object.defineProperty(screen, 'width', {{
                get: function() {{ return {fingerprint['screen']['width']}; }}
            }});
            
            Object.defineProperty(screen, 'height', {{
                get: function() {{ return {fingerprint['screen']['height']}; }}
            }});
            
            Object.defineProperty(screen, 'availWidth', {{
                get: function() {{ return {fingerprint['screen']['available_width']}; }}
            }});
            
            Object.defineProperty(screen, 'availHeight', {{
                get: function() {{ return {fingerprint['screen']['available_height']}; }}
            }});
            
            Object.defineProperty(screen, 'colorDepth', {{
                get: function() {{ return {fingerprint['screen']['color_depth']}; }}
            }});
            
            Object.defineProperty(screen, 'pixelDepth', {{
                get: function() {{ return {fingerprint['screen']['pixel_depth']}; }}
            }});
            
            // 重写WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{fingerprint['webgl']['vendor']}';
                }}
                if (parameter === 37446) {{
                    return '{fingerprint['webgl']['renderer']}';
                }}
                return getParameter.call(this, parameter);
            }};
            """
            
            # 执行脚本
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': js_script
            })
            
        except Exception as e:
            self.logger.warning(f"应用指纹失败: {str(e)}")

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建指纹引擎
    engine = FingerprintEngine()
    
    # 生成指纹
    fingerprint = engine.generate_fingerprint()
    
    # 打印指纹信息
    print(f"指纹ID: {fingerprint['fingerprint_id']}")
    print(f"User-Agent: {fingerprint['user_agent']}")
    print(f"屏幕分辨率: {fingerprint['screen']['width']}x{fingerprint['screen']['height']}")
    print(f"时区: {fingerprint['timezone']}")
    print(f"语言: {fingerprint['languages']}")
    print(f"WebGL: {fingerprint['webgl']['vendor']} - {fingerprint['webgl']['renderer']}")
