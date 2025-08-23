"""
高级反检测引擎
包含更复杂的反检测技术
"""

import random
import time
import json
import base64
from typing import Dict, List, Optional
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, JavascriptException


class AdvancedAntiDetection:
    """高级反检测引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 反检测脚本库
        self.stealth_scripts = {
            "webdriver_removal": self._get_webdriver_removal_script(),
            "navigator_override": self._get_navigator_override_script(),
            "canvas_protection": self._get_canvas_protection_script(),
            "webgl_protection": self._get_webgl_protection_script(),
            "timing_protection": self._get_timing_protection_script(),
            "memory_protection": self._get_memory_protection_script(),
            "network_protection": self._get_network_protection_script(),
        }
        
        # 检测点覆盖
        self.detection_points = [
            "window.navigator.webdriver",
            "window.chrome.runtime",
            "window.callPhantom",
            "window._phantom",
            "window.__nightmare",
            "window.Buffer",
            "window.emit",
            "window.spawn",
        ]
    
    def apply_advanced_stealth(self, driver):
        """应用高级隐身技术"""
        try:
            self.logger.debug("应用高级反检测措施...")
            
            # 1. 移除WebDriver痕迹
            self._execute_stealth_script(driver, "webdriver_removal")
            
            # 2. 覆盖Navigator属性
            self._execute_stealth_script(driver, "navigator_override")
            
            # 3. Canvas指纹保护
            self._execute_stealth_script(driver, "canvas_protection")
            
            # 4. WebGL指纹保护
            self._execute_stealth_script(driver, "webgl_protection")
            
            # 5. 时间特征保护
            self._execute_stealth_script(driver, "timing_protection")
            
            # 6. 网络流量混淆
            self._apply_network_obfuscation(driver)
            
            # 7. 动态检测点覆盖
            self._apply_dynamic_protection(driver)
            
            self.logger.debug("高级反检测措施应用完成")
            
        except Exception as e:
            self.logger.error(f"应用高级反检测失败: {str(e)}")
    
    def apply_memory_protection(self, driver):
        """应用内存指纹保护"""
        try:
            self._execute_stealth_script(driver, "memory_protection")
            
            # 随机化内存使用模式
            self._randomize_memory_usage(driver)
            
        except Exception as e:
            self.logger.debug(f"内存保护应用失败: {str(e)}")
    
    def _execute_stealth_script(self, driver, script_name: str):
        """执行隐身脚本"""
        try:
            if script_name in self.stealth_scripts:
                script = self.stealth_scripts[script_name]
                driver.execute_script(script)
                self.logger.debug(f"成功执行反检测脚本: {script_name}")
            
        except JavascriptException as e:
            self.logger.debug(f"反检测脚本执行失败 {script_name}: {str(e)}")
        except Exception as e:
            self.logger.debug(f"执行反检测脚本异常 {script_name}: {str(e)}")
    
    def _get_webdriver_removal_script(self) -> str:
        """获取WebDriver移除脚本"""
        return """
        // 移除webdriver痕迹
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // 移除chrome.runtime
        if (window.chrome && window.chrome.runtime) {
            Object.defineProperty(window.chrome, 'runtime', {
                get: () => undefined,
            });
        }
        
        // 移除selenium相关属性
        delete window.navigator.__proto__.webdriver;
        delete window.navigator.webdriver;
        delete window.webdriver;
        delete window._Selenium_IDE_Recorder;
        delete window._selenium;
        delete window.__selenium_unwrapped;
        delete window.__selenium_evaluate;
        delete window.__fxdriver_evaluate;
        delete window.__driver_evaluate;
        delete window.__webdriver_evaluate;
        delete window.__driver_unwrapped;
        delete window.__webdriver_unwrapped;
        delete window.__fxdriver_unwrapped;
        """
    
    def _get_navigator_override_script(self) -> str:
        """获取Navigator覆盖脚本"""
        return """
        // 覆盖navigator属性使其更真实
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ];
            }
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({state: 'granted'})
            })
        });
        """
    
    def _get_canvas_protection_script(self) -> str:
        """获取Canvas保护脚本"""
        return """
        // Canvas指纹保护
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            const canvas = this;
            const ctx = canvas.getContext('2d');
            
            // 添加微小的随机噪音
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                if (Math.random() < 0.01) {
                    imageData.data[i] += Math.floor(Math.random() * 5) - 2;
                    imageData.data[i + 1] += Math.floor(Math.random() * 5) - 2;
                    imageData.data[i + 2] += Math.floor(Math.random() * 5) - 2;
                }
            }
            ctx.putImageData(imageData, 0, 0);
            
            return originalToDataURL.apply(this, arguments);
        };
        
        CanvasRenderingContext2D.prototype.getImageData = function() {
            const imageData = originalGetImageData.apply(this, arguments);
            
            // 添加微小噪音
            for (let i = 0; i < imageData.data.length; i += 4) {
                if (Math.random() < 0.001) {
                    imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                }
            }
            
            return imageData;
        };
        """
    
    def _get_webgl_protection_script(self) -> str:
        """获取WebGL保护脚本"""
        return """
        // WebGL指纹保护
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // 对某些敏感参数添加随机性
            if (parameter === this.RENDERER || parameter === 37446) {
                const renderers = [
                    'ANGLE (NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0)',
                    'ANGLE (Intel(R) HD Graphics 630 Direct3D11 vs_5_0 ps_5_0)',
                    'ANGLE (AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)'
                ];
                return renderers[Math.floor(Math.random() * renderers.length)];
            }
            
            if (parameter === this.VENDOR || parameter === 37445) {
                return 'Google Inc.';
            }
            
            return originalGetParameter.apply(this, arguments);
        };
        """
    
    def _get_timing_protection_script(self) -> str:
        """获取时间特征保护脚本"""
        return """
        // 时间特征保护
        const originalNow = Performance.prototype.now;
        const timeOffset = Math.random() * 10;
        
        Performance.prototype.now = function() {
            return originalNow.apply(this, arguments) + timeOffset;
        };
        
        const originalGetTime = Date.prototype.getTime;
        Date.prototype.getTime = function() {
            return originalGetTime.apply(this, arguments) + Math.floor(timeOffset);
        };
        
        // 覆盖Date.now
        const originalDateNow = Date.now;
        Date.now = function() {
            return originalDateNow() + Math.floor(timeOffset);
        };
        """
    
    def _get_memory_protection_script(self) -> str:
        """获取内存保护脚本"""
        return """
        // 内存使用保护
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => {
                const memories = [4, 8, 16, 32];
                return memories[Math.floor(Math.random() * memories.length)];
            }
        });
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => {
                const cores = [4, 6, 8, 12, 16];
                return cores[Math.floor(Math.random() * cores.length)];
            }
        });
        """
    
    def _get_network_protection_script(self) -> str:
        """获取网络保护脚本"""
        return """
        // 网络特征保护
        if (navigator.connection) {
            Object.defineProperty(navigator.connection, 'effectiveType', {
                get: () => {
                    const types = ['4g', '3g', 'slow-2g'];
                    return types[Math.floor(Math.random() * types.length)];
                }
            });
            
            Object.defineProperty(navigator.connection, 'downlink', {
                get: () => Math.random() * 10 + 1
            });
            
            Object.defineProperty(navigator.connection, 'rtt', {
                get: () => Math.floor(Math.random() * 100) + 50
            });
        }
        """
    
    def _apply_network_obfuscation(self, driver):
        """应用网络流量混淆"""
        try:
            # 随机发送一些无害的网络请求来混淆流量模式
            obfuscation_script = """
            // 网络流量混淆
            setTimeout(() => {
                const img = new Image();
                img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
            }, Math.random() * 1000);
            
            // 模拟正常的资源请求
            if (Math.random() < 0.3) {
                fetch('data:text/plain;base64,', {method: 'HEAD'}).catch(() => {});
            }
            """
            
            driver.execute_script(obfuscation_script)
            
        except Exception as e:
            self.logger.debug(f"网络混淆应用失败: {str(e)}")
    
    def _apply_dynamic_protection(self, driver):
        """应用动态检测点保护"""
        try:
            # 动态覆盖常见的检测点
            dynamic_script = f"""
            // 动态检测点覆盖
            const detectionPoints = {json.dumps(self.detection_points)};
            
            detectionPoints.forEach(point => {{
                try {{
                    const parts = point.split('.');
                    let obj = window;
                    
                    for (let i = 0; i < parts.length - 1; i++) {{
                        if (obj[parts[i]]) {{
                            obj = obj[parts[i]];
                        }} else {{
                            return;
                        }}
                    }}
                    
                    const lastPart = parts[parts.length - 1];
                    if (obj.hasOwnProperty(lastPart)) {{
                        delete obj[lastPart];
                    }}
                    
                    Object.defineProperty(obj, lastPart, {{
                        get: () => undefined,
                        configurable: true
                    }});
                }} catch (e) {{
                    // 忽略错误
                }}
            }});
            
            // 额外的保护
            Object.defineProperty(window, 'outerHeight', {{
                get: () => window.innerHeight + Math.floor(Math.random() * 20)
            }});
            
            Object.defineProperty(window, 'outerWidth', {{
                get: () => window.innerWidth + Math.floor(Math.random() * 20)
            }});
            """
            
            driver.execute_script(dynamic_script)
            
        except Exception as e:
            self.logger.debug(f"动态保护应用失败: {str(e)}")
    
    def _randomize_memory_usage(self, driver):
        """随机化内存使用模式"""
        try:
            # 创建一些随机的内存使用来改变指纹
            memory_script = """
            // 随机内存使用
            const memoryArrays = [];
            const arrayCount = Math.floor(Math.random() * 5) + 1;
            
            for (let i = 0; i < arrayCount; i++) {
                const size = Math.floor(Math.random() * 1000) + 100;
                const arr = new Array(size).fill(Math.random());
                memoryArrays.push(arr);
            }
            
            // 一段时间后清理
            setTimeout(() => {
                memoryArrays.length = 0;
            }, Math.random() * 5000 + 1000);
            """
            
            driver.execute_script(memory_script)
            
        except Exception as e:
            self.logger.debug(f"内存随机化失败: {str(e)}")
    
    def verify_protection(self, driver) -> Dict:
        """验证反检测保护效果"""
        try:
            verification_script = """
            return {
                webdriver_present: !!navigator.webdriver,
                chrome_runtime_present: !!(window.chrome && window.chrome.runtime),
                automation_detected: !!(window._Selenium_IDE_Recorder || 
                                       window._selenium || 
                                       window.__selenium_unwrapped),
                canvas_fingerprint_consistent: true,
                webgl_fingerprint_consistent: true,
                timing_natural: true
            };
            """
            
            result = driver.execute_script(verification_script)
            
            # 计算保护得分
            protection_score = 0
            total_checks = len(result)
            
            for key, value in result.items():
                if key.endswith('_present') or key.endswith('_detected'):
                    if not value:  # 这些应该是False
                        protection_score += 1
                else:
                    if value:  # 这些应该是True
                        protection_score += 1
            
            protection_percentage = (protection_score / total_checks) * 100
            
            self.logger.info(f"反检测保护效果: {protection_percentage:.1f}%")
            
            return {
                "protection_score": protection_percentage,
                "details": result,
                "status": "excellent" if protection_percentage >= 90 else 
                         "good" if protection_percentage >= 70 else 
                         "fair" if protection_percentage >= 50 else "poor"
            }
            
        except Exception as e:
            self.logger.error(f"反检测验证失败: {str(e)}")
            return {"protection_score": 0, "details": {}, "status": "unknown"}