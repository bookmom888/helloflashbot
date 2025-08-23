#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器自动化模块
Browser Automation Module

提供反检测的浏览器自动化功能：
- 多浏览器支持（Chrome、Firefox、Edge）
- 反检测配置
- 代理集成
- 设备指纹应用
- 窗口管理
"""

import os
import sys
import random
import logging
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from .anti_detection_advanced import AdvancedAntiDetection

class BrowserAutomation:
    """浏览器自动化管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_drivers = []
        self.temp_dirs = []
        
        # 高级反检测引擎
        self.anti_detection = AdvancedAntiDetection()
        
        # 反检测配置
        self.stealth_config = {
            'disable_blink_features': True,
            'disable_extensions': False,
            'disable_plugins': False,
            'disable_default_apps': True,
            'disable_background_timer_throttling': True,
            'disable_backgrounding_occluded_windows': True,
            'disable_renderer_backgrounding': True,
            'disable_features': [
                'VizDisplayCompositor',
                'TranslateUI',
                'BlinkGenPropertyTrees'
            ]
        }
    
    def create_browser(self, proxy: Dict = None, fingerprint: Dict = None, 
                      config: Dict = None) -> Optional[webdriver.Chrome]:
        """创建浏览器实例"""
        try:
            config = config or {}
            browser_type = config.get('browser', 'chrome')
            
            if browser_type == 'chrome':
                driver = self._create_chrome_driver(proxy, fingerprint, config)
            elif browser_type == 'firefox':
                driver = self._create_firefox_driver(proxy, fingerprint, config)
            elif browser_type == 'edge':
                driver = self._create_edge_driver(proxy, fingerprint, config)
            else:
                raise ValueError(f"不支持的浏览器类型: {browser_type}")
            
            if driver:
                self.active_drivers.append(driver)
                self.logger.info(f"成功创建 {browser_type} 浏览器实例")
                
                # 应用指纹
                if fingerprint:
                    self._apply_fingerprint(driver, fingerprint)
                
                # 应用高级反检测
                try:
                    self.anti_detection.apply_advanced_stealth(driver)
                    self.anti_detection.apply_memory_protection(driver)
                    self.logger.debug("成功应用高级反检测措施")
                except Exception as e:
                    self.logger.warning(f"高级反检测应用失败: {str(e)}")
                
                return driver
            
            return None
        
        except Exception as e:
            self.logger.error(f"创建浏览器失败: {str(e)}")
            return None
    
    def _create_chrome_driver(self, proxy: Dict = None, fingerprint: Dict = None, 
                             config: Dict = None) -> Optional[webdriver.Chrome]:
        """创建Chrome浏览器"""
        try:
            # 创建临时用户目录
            temp_dir = tempfile.mkdtemp(prefix="chrome_profile_")
            self.temp_dirs.append(temp_dir)
            
            # Chrome选项
            options = ChromeOptions()
            
            # 基础配置
            if config and config.get('headless', False):
                options.add_argument('--headless')
            
            # 反检测配置
            if config and config.get('stealth', True):
                self._add_stealth_options(options)
            
            # 代理配置
            if proxy:
                proxy_arg = self._format_proxy_for_chrome(proxy)
                if proxy_arg:
                    options.add_argument(proxy_arg)
            
            # 用户数据目录
            options.add_argument(f'--user-data-dir={temp_dir}')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            
            # 窗口大小
            if fingerprint and 'screen' in fingerprint:
                width = fingerprint['screen']['width']
                height = fingerprint['screen']['height']
                options.add_argument(f'--window-size={width},{height}')
            
            # 语言设置
            if fingerprint and 'languages' in fingerprint:
                lang = fingerprint['languages'][0]
                options.add_argument(f'--lang={lang}')
                options.add_experimental_option('prefs', {
                    'intl.accept_languages': ','.join(fingerprint['languages'])
                })
            
            # User-Agent
            if fingerprint and 'user_agent' in fingerprint:
                options.add_argument(f'--user-agent={fingerprint["user_agent"]}')
            
            # 时区
            if fingerprint and 'timezone' in fingerprint:
                options.add_argument(f'--timezone={fingerprint["timezone"]}')
            
            # 禁用功能
            if config and config.get('disable_images', False):
                prefs = options.experimental_options.get('prefs', {})
                prefs['profile.managed_default_content_settings.images'] = 2
                options.add_experimental_option('prefs', prefs)
            
            if config and config.get('disable_js', False):
                prefs = options.experimental_options.get('prefs', {})
                prefs['profile.managed_default_content_settings.javascript'] = 2
                options.add_experimental_option('prefs', prefs)
            
            # 使用undetected-chromedriver
            driver = uc.Chrome(options=options, version_main=None)
            
            # 设置窗口位置
            if fingerprint and 'screen' in fingerprint:
                width = fingerprint['screen']['width']
                height = fingerprint['screen']['height']
                driver.set_window_size(width, height)
                
                # 随机窗口位置
                x = random.randint(0, 100)
                y = random.randint(0, 100)
                driver.set_window_position(x, y)
            
            return driver
        
        except Exception as e:
            self.logger.error(f"创建Chrome驱动失败: {str(e)}")
            return None
    
    def _create_firefox_driver(self, proxy: Dict = None, fingerprint: Dict = None, 
                              config: Dict = None) -> Optional[webdriver.Firefox]:
        """创建Firefox浏览器"""
        try:
            # Firefox选项
            options = FirefoxOptions()
            
            # 基础配置
            if config and config.get('headless', False):
                options.add_argument('--headless')
            
            # 创建临时profile
            profile = webdriver.FirefoxProfile()
            
            # 代理配置
            if proxy:
                self._configure_firefox_proxy(profile, proxy)
            
            # User-Agent
            if fingerprint and 'user_agent' in fingerprint:
                profile.set_preference("general.useragent.override", fingerprint['user_agent'])
            
            # 语言设置
            if fingerprint and 'languages' in fingerprint:
                lang = fingerprint['languages'][0]
                profile.set_preference("intl.accept_languages", ','.join(fingerprint['languages']))
                profile.set_preference("intl.locale.requested", lang)
            
            # 时区设置
            if fingerprint and 'timezone' in fingerprint:
                profile.set_preference("intl.regional_prefs.use_os_locales", False)
            
            # 禁用功能
            if config and config.get('disable_images', False):
                profile.set_preference("permissions.default.image", 2)
            
            if config and config.get('disable_js', False):
                profile.set_preference("javascript.enabled", False)
            
            # 反检测设置
            if config and config.get('stealth', True):
                profile.set_preference("dom.webdriver.enabled", False)
                profile.set_preference('useAutomationExtension', False)
                profile.set_preference("marionette.enabled", True)
            
            # 创建驱动
            service = webdriver.FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options, firefox_profile=profile)
            
            # 设置窗口大小
            if fingerprint and 'screen' in fingerprint:
                width = fingerprint['screen']['width']
                height = fingerprint['screen']['height']
                driver.set_window_size(width, height)
            
            return driver
        
        except Exception as e:
            self.logger.error(f"创建Firefox驱动失败: {str(e)}")
            return None
    
    def _create_edge_driver(self, proxy: Dict = None, fingerprint: Dict = None, 
                           config: Dict = None) -> Optional[webdriver.Edge]:
        """创建Edge浏览器"""
        try:
            # Edge选项
            options = EdgeOptions()
            
            # 基础配置
            if config and config.get('headless', False):
                options.add_argument('--headless')
            
            # 反检测配置
            if config and config.get('stealth', True):
                self._add_stealth_options(options)
            
            # 代理配置
            if proxy:
                proxy_arg = self._format_proxy_for_chrome(proxy)  # Edge使用Chromium内核
                if proxy_arg:
                    options.add_argument(proxy_arg)
            
            # User-Agent
            if fingerprint and 'user_agent' in fingerprint:
                options.add_argument(f'--user-agent={fingerprint["user_agent"]}')
            
            # 窗口大小
            if fingerprint and 'screen' in fingerprint:
                width = fingerprint['screen']['width']
                height = fingerprint['screen']['height']
                options.add_argument(f'--window-size={width},{height}')
            
            # 语言设置
            if fingerprint and 'languages' in fingerprint:
                lang = fingerprint['languages'][0]
                options.add_argument(f'--lang={lang}')
            
            # 创建驱动
            service = webdriver.EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            
            return driver
        
        except Exception as e:
            self.logger.error(f"创建Edge驱动失败: {str(e)}")
            return None
    
    def _add_stealth_options(self, options):
        """添加反检测选项"""
        stealth_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions-file-access-check',
            '--disable-extensions-http-throttling',
            '--disable-extensions-except',
            '--disable-default-apps',
            '--disable-component-extensions-with-background-pages',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-back-forward-cache',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--no-first-run',
            '--no-service-autorun',
            '--no-default-browser-check',
            '--password-store=basic',
            '--use-mock-keychain',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-sandbox'
        ]
        
        for arg in stealth_args:
            options.add_argument(arg)
        
        # 实验性选项（暂时禁用以避免兼容性问题）
        # experimental_options = {
        #     'useAutomationExtension': False
        # }
        # 
        # for key, value in experimental_options.items():
        #     options.add_experimental_option(key, value)
    
    def _format_proxy_for_chrome(self, proxy: Dict) -> Optional[str]:
        """格式化代理用于Chrome"""
        try:
            proxy_type = proxy.get('type', 'http').lower()
            host = proxy.get('host')
            port = proxy.get('port')
            username = proxy.get('username')
            password = proxy.get('password')
            
            if not host or not port:
                return None
            
            if proxy_type in ['http', 'https']:
                if username and password:
                    return f'--proxy-server=http://{username}:{password}@{host}:{port}'
                else:
                    return f'--proxy-server=http://{host}:{port}'
            elif proxy_type == 'socks4':
                return f'--proxy-server=socks4://{host}:{port}'
            elif proxy_type == 'socks5':
                if username and password:
                    return f'--proxy-server=socks5://{username}:{password}@{host}:{port}'
                else:
                    return f'--proxy-server=socks5://{host}:{port}'
            
            return None
        
        except Exception as e:
            self.logger.error(f"格式化代理失败: {str(e)}")
            return None
    
    def _configure_firefox_proxy(self, profile, proxy: Dict):
        """配置Firefox代理"""
        try:
            proxy_type = proxy.get('type', 'http').lower()
            host = proxy.get('host')
            port = proxy.get('port')
            username = proxy.get('username')
            password = proxy.get('password')
            
            if proxy_type in ['http', 'https']:
                profile.set_preference("network.proxy.type", 1)
                profile.set_preference("network.proxy.http", host)
                profile.set_preference("network.proxy.http_port", port)
                profile.set_preference("network.proxy.ssl", host)
                profile.set_preference("network.proxy.ssl_port", port)
            elif proxy_type == 'socks4':
                profile.set_preference("network.proxy.type", 1)
                profile.set_preference("network.proxy.socks", host)
                profile.set_preference("network.proxy.socks_port", port)
                profile.set_preference("network.proxy.socks_version", 4)
            elif proxy_type == 'socks5':
                profile.set_preference("network.proxy.type", 1)
                profile.set_preference("network.proxy.socks", host)
                profile.set_preference("network.proxy.socks_port", port)
                profile.set_preference("network.proxy.socks_version", 5)
            
            # 认证
            if username and password:
                profile.set_preference("network.proxy.socks_username", username)
                profile.set_preference("network.proxy.socks_password", password)
        
        except Exception as e:
            self.logger.error(f"配置Firefox代理失败: {str(e)}")
    
    def _apply_fingerprint(self, driver, fingerprint: Dict):
        """应用设备指纹"""
        try:
            # 准备JavaScript代码
            js_scripts = []
            
            # User-Agent
            if 'user_agent' in fingerprint:
                js_scripts.append(f"""
                Object.defineProperty(navigator, 'userAgent', {{
                    get: function() {{ return '{fingerprint["user_agent"]}'; }}
                }});
                """)
            
            # Platform
            if 'platform' in fingerprint:
                js_scripts.append(f"""
                Object.defineProperty(navigator, 'platform', {{
                    get: function() {{ return '{fingerprint["platform"]}'; }}
                }});
                """)
            
            # Languages
            if 'languages' in fingerprint:
                languages_json = str(fingerprint['languages']).replace("'", '"')
                js_scripts.append(f"""
                Object.defineProperty(navigator, 'languages', {{
                    get: function() {{ return {languages_json}; }}
                }});
                Object.defineProperty(navigator, 'language', {{
                    get: function() {{ return '{fingerprint['languages'][0]}'; }}
                }});
                """)
            
            # Screen properties
            if 'screen' in fingerprint:
                screen = fingerprint['screen']
                js_scripts.append(f"""
                Object.defineProperty(screen, 'width', {{
                    get: function() {{ return {screen['width']}; }}
                }});
                Object.defineProperty(screen, 'height', {{
                    get: function() {{ return {screen['height']}; }}
                }});
                Object.defineProperty(screen, 'availWidth', {{
                    get: function() {{ return {screen['available_width']}; }}
                }});
                Object.defineProperty(screen, 'availHeight', {{
                    get: function() {{ return {screen['available_height']}; }}
                }});
                Object.defineProperty(screen, 'colorDepth', {{
                    get: function() {{ return {screen['color_depth']}; }}
                }});
                Object.defineProperty(screen, 'pixelDepth', {{
                    get: function() {{ return {screen['pixel_depth']}; }}
                }});
                """)
            
            # WebGL fingerprint
            if 'webgl' in fingerprint:
                webgl = fingerprint['webgl']
                js_scripts.append(f"""
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{
                        return '{webgl["vendor"]}';
                    }}
                    if (parameter === 37446) {{
                        return '{webgl["renderer"]}';
                    }}
                    return getParameter.call(this, parameter);
                }};
                """)
            
            # Canvas fingerprint
            if 'canvas' in fingerprint:
                js_scripts.append(f"""
                const toDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {{
                    return toDataURL.apply(this, arguments) + '{fingerprint["canvas"]}';
                }};
                """)
            
            # Hardware concurrency
            if 'hardware' in fingerprint and 'cpu_cores' in fingerprint['hardware']:
                js_scripts.append(f"""
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: function() {{ return {fingerprint['hardware']['cpu_cores']}; }}
                }});
                """)
            
            # Device memory
            if 'hardware' in fingerprint and 'memory_gb' in fingerprint['hardware']:
                memory_gb = fingerprint['hardware']['memory_gb']
                js_scripts.append(f"""
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: function() {{ return {memory_gb}; }}
                }});
                """)
            
            # Timezone
            if 'timezone' in fingerprint:
                js_scripts.append(f"""
                const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
                Date.prototype.getTimezoneOffset = function() {{
                    return new Date().getTimezoneOffset();
                }};
                
                Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                    value: function() {{
                        const options = Object.getOwnPropertyDescriptor(Intl.DateTimeFormat.prototype, 'resolvedOptions').value.call(this);
                        options.timeZone = '{fingerprint["timezone"]}';
                        return options;
                    }}
                }});
                """)
            
            # 执行所有脚本
            combined_script = '\n'.join(js_scripts)
            
            if hasattr(driver, 'execute_cdp_cmd'):
                # Chrome/Edge支持CDP
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': combined_script
                })
            else:
                # Firefox等其他浏览器
                driver.execute_script(combined_script)
            
            self.logger.debug("设备指纹应用成功")
        
        except Exception as e:
            self.logger.error(f"应用设备指纹失败: {str(e)}")
    
    def navigate_safely(self, driver, url: str, timeout: int = 30) -> bool:
        """安全导航到URL"""
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            
            # 等待页面加载完成
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            self.logger.debug(f"成功导航到: {url}")
            return True
        
        except TimeoutException:
            self.logger.warning(f"页面加载超时: {url}")
            return False
        except Exception as e:
            self.logger.error(f"导航失败: {url} - {str(e)}")
            return False
    
    def close_driver(self, driver):
        """关闭浏览器驱动"""
        try:
            if driver in self.active_drivers:
                self.active_drivers.remove(driver)
            
            driver.quit()
            self.logger.debug("浏览器驱动已关闭")
        
        except Exception as e:
            self.logger.error(f"关闭浏览器驱动失败: {str(e)}")
    
    def close_all_drivers(self):
        """关闭所有浏览器驱动"""
        for driver in self.active_drivers.copy():
            self.close_driver(driver)
        
        # 清理临时目录
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        self.temp_dirs.clear()
        self.logger.info("所有浏览器驱动已关闭")
    
    def get_current_ip(self, driver) -> Optional[str]:
        """获取当前IP地址"""
        try:
            driver.get("http://httpbin.org/ip")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "pre"))
            )
            
            import json
            response_text = driver.find_element(By.TAG_NAME, "pre").text
            response_data = json.loads(response_text)
            
            return response_data.get('origin', '').split(',')[0].strip()
        
        except Exception as e:
            self.logger.error(f"获取IP地址失败: {str(e)}")
            return None
    
    def check_detection(self, driver) -> Dict:
        """检查是否被检测"""
        try:
            detection_results = {
                'webdriver_detected': False,
                'automation_detected': False,
                'stealth_score': 100
            }
            
            # 检查webdriver属性
            webdriver_result = driver.execute_script("""
                return {
                    webdriver: navigator.webdriver,
                    permissions: navigator.permissions,
                    chrome: window.chrome,
                    automation: window.navigator.webdriver
                };
            """)
            
            if webdriver_result.get('webdriver') is True:
                detection_results['webdriver_detected'] = True
                detection_results['stealth_score'] -= 30
            
            if webdriver_result.get('automation') is True:
                detection_results['automation_detected'] = True
                detection_results['stealth_score'] -= 20
            
            # 检查其他检测标志
            other_checks = driver.execute_script("""
                return {
                    phantomjs: window.callPhantom || window._phantom,
                    selenium: window.__selenium_unwrapped || window.__webdriver_evaluate,
                    chromedriver: window.domAutomation || window.domAutomationController
                };
            """)
            
            if any(other_checks.values()):
                detection_results['stealth_score'] -= 25
            
            return detection_results
        
        except Exception as e:
            self.logger.error(f"检测检查失败: {str(e)}")
            return {'webdriver_detected': True, 'automation_detected': True, 'stealth_score': 0}
    
    def get_active_windows_count(self) -> int:
        """获取活跃窗口数量"""
        return len(self.active_drivers)

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建浏览器自动化管理器
    browser_automation = BrowserAutomation()
    
    try:
        # 测试创建浏览器
        config = {'headless': False, 'stealth': True}
        driver = browser_automation.create_browser(config=config)
        
        if driver:
            print("浏览器创建成功")
            
            # 测试导航
            if browser_automation.navigate_safely(driver, "https://httpbin.org/ip"):
                print("导航成功")
                
                # 获取IP
                ip = browser_automation.get_current_ip(driver)
                print(f"当前IP: {ip}")
                
                # 检查检测
                detection = browser_automation.check_detection(driver)
                print(f"检测结果: {detection}")
            
            # 关闭浏览器
            browser_automation.close_driver(driver)
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
    
    finally:
        browser_automation.close_all_drivers()
