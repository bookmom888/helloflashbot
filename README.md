# FlashBot2 代理管理系统

一个功能强大的代理管理和自动化系统，支持多种代理类型、异步验证、数据库存储、监控告警等高级功能。

## 🚀 主要功能

### 核心功能
- **多协议支持**: HTTP/HTTPS、SOCKS4/SOCKS5 代理
- **智能验证**: 异步批量验证，支持自定义验证URL
- **数据持久化**: SQLite数据库存储，支持JSON备份
- **配置管理**: YAML配置文件 + 环境变量支持
- **监控告警**: 实时系统监控和性能指标收集
- **健康检查**: 自动代理健康状态监测
- **代理轮换**: 多种轮换策略（轮询、随机、加权）

### 高级功能
- **浏览器自动化**: Selenium集成，支持反检测
- **指纹伪造**: 高级浏览器指纹伪造技术
- **人性化操作**: 模拟真实用户行为
- **会话管理**: 智能会话保持和恢复
- **API代理**: 支持第三方代理API集成

## 📦 安装要求

### 系统要求
- Python 3.8+
- Windows/Linux/macOS
- Chrome/Chromium 浏览器

### 依赖安装
```bash
pip install -r requirements.txt
```

### 主要依赖
- `selenium`: 浏览器自动化
- `requests`: HTTP请求处理
- `pysocks`: SOCKS代理支持
- `sqlite3`: 数据库存储
- `pyyaml`: 配置文件解析
- `psutil`: 系统监控

## 🔧 配置说明

### 1. 配置文件设置

复制并编辑配置文件：
```bash
cp config/proxy_config.yaml config/proxy_config_local.yaml
```

主要配置项：
```yaml
proxy_manager:
  validation:
    timeout: 10
    max_retries: 3
    max_threads: 10
  storage:
    use_database: true
    db_path: 'data/proxies.db'
  health_check:
    interval: 300
    max_error_count: 5

monitoring:
  enabled: true
  alerts:
    thresholds:
      success_rate_min: 80
      response_time_max: 10
```

### 2. 环境变量配置

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```bash
# 数据库配置
PROXY_DB_PATH=data/proxies.db

# 监控配置
MONITORING_ENABLED=true
ALERT_SUCCESS_RATE_MIN=80

# API配置
API_PROXIES_ENABLED=false
EXAMPLE_PROVIDER_API_KEY=your_api_key_here
```

## 🚀 快速开始

### 1. 基础使用

```python
from src.proxy_manager import ProxyManager
from src.config_manager import ConfigManager

# 初始化配置管理器
config = ConfigManager('config/proxy_config.yaml')

# 创建代理管理器
proxy_manager = ProxyManager(config_manager=config)

# 添加代理
proxy_manager.add_proxy('127.0.0.1:8080', 'http')
proxy_manager.add_proxy('127.0.0.1:1080', 'socks5')

# 验证所有代理
proxy_manager.validate_all_proxies()

# 获取有效代理
valid_proxies = proxy_manager.get_valid_proxies()
print(f"有效代理数量: {len(valid_proxies)}")

# 获取统计信息
stats = proxy_manager.get_proxy_stats()
print(f"代理统计: {stats}")
```

### 2. 异步验证

```python
from src.async_proxy_validator import AsyncProxyValidator

# 创建异步验证器
validator = AsyncProxyValidator(max_concurrent=50)

# 批量验证代理
proxies = ['127.0.0.1:8080', '127.0.0.1:1080']
results = await validator.validate_proxies_batch(proxies)

for result in results:
    print(f"代理: {result['proxy']}, 状态: {result['is_valid']}")
```

### 3. 监控系统

```python
from src.monitoring_logger import MonitoringSystem

# 启动监控系统
monitoring = MonitoringSystem()
monitoring.start_monitoring()

# 获取系统指标
metrics = monitoring.get_current_metrics()
print(f"CPU使用率: {metrics['cpu_percent']}%")
print(f"内存使用率: {metrics['memory_percent']}%")

# 获取告警信息
alerts = monitoring.get_active_alerts()
for alert in alerts:
    print(f"告警: {alert['message']}")
```

## 📁 项目结构

```
flashbot2/
├── src/                          # 源代码目录
│   ├── proxy_manager.py          # 代理管理核心
│   ├── async_proxy_validator.py  # 异步验证器
│   ├── database_manager.py       # 数据库管理
│   ├── config_manager.py         # 配置管理
│   ├── monitoring_logger.py      # 监控日志系统
│   ├── browser_automation.py     # 浏览器自动化
│   ├── fingerprint_engine.py     # 指纹伪造引擎
│   └── ...
├── config/                       # 配置文件目录
│   └── proxy_config.yaml         # 主配置文件
├── data/                         # 数据目录
│   ├── proxies.db               # 代理数据库
│   ├── proxies.json             # JSON备份
│   └── proxies.txt              # 文本格式代理
├── logs/                         # 日志目录
├── examples/                     # 示例文件
├── .env.example                  # 环境变量模板
├── requirements.txt              # 依赖列表
└── main.py                       # 主程序入口
```

## 🔍 代理格式支持

### 支持的代理格式

1. **基础格式**:
   ```
   127.0.0.1:8080
   192.168.1.100:3128
   ```

2. **带协议格式**:
   ```
   http://127.0.0.1:8080
   socks5://127.0.0.1:1080
   ```

3. **带认证格式**:
   ```
   http://username:password@127.0.0.1:8080
   socks5://user:pass@127.0.0.1:1080
   ```

### 批量导入

从文件导入代理：
```python
# 从TXT文件导入
proxy_manager.load_proxies_from_file('data/proxies.txt')

# 从JSON文件导入
proxy_manager.load_proxies_from_json('data/proxies.json')
```

## 📊 监控和告警

### 监控指标

- **系统指标**: CPU、内存、磁盘使用率
- **代理指标**: 成功率、响应时间、错误率
- **性能指标**: 验证速度、轮换频率

### 告警规则

- 代理成功率低于阈值
- 平均响应时间超过限制
- 系统资源使用率过高
- 代理验证失败率过高

### 日志系统

- **结构化日志**: JSON格式，便于分析
- **日志轮转**: 自动压缩和清理旧日志
- **多级别**: DEBUG、INFO、WARNING、ERROR
- **多输出**: 控制台 + 文件

## 🛠️ 高级用法

### 1. 自定义验证URL

```python
custom_urls = [
    'http://httpbin.org/ip',
    'https://api.ipify.org?format=json',
    'http://ip-api.com/json'
]

proxy_manager = ProxyManager(
    validation_urls=custom_urls,
    validation_timeout=15
)
```

### 2. 代理轮换策略

```python
# 轮询策略
proxy = proxy_manager.get_next_proxy(strategy='round_robin')

# 随机策略
proxy = proxy_manager.get_next_proxy(strategy='random')

# 加权策略（基于响应时间）
proxy = proxy_manager.get_next_proxy(strategy='weighted')
```

### 3. 健康检查配置

```python
proxy_manager = ProxyManager(
    health_check_interval=300,  # 5分钟检查一次
    max_error_count=5,          # 最大错误次数
    error_threshold_time=300    # 错误时间窗口
)
```

### 4. API代理集成

```python
from src.api_proxy_manager import APIProxyManager

api_manager = APIProxyManager({
    'provider_name': {
        'api_url': 'https://api.example.com/proxies',
        'api_key': 'your_api_key',
        'rate_limit': 100
    }
})

# 获取API代理
api_proxies = api_manager.fetch_proxies('provider_name')
```

## 🔧 故障排除

### 常见问题

1. **代理验证失败**
   - 检查代理格式是否正确
   - 确认代理服务器可访问
   - 调整验证超时时间

2. **数据库连接错误**
   - 检查数据库文件路径
   - 确认目录写入权限
   - 查看错误日志详情

3. **监控系统异常**
   - 检查配置文件格式
   - 确认监控权限设置
   - 查看系统资源使用情况

### 调试模式

启用调试模式获取详细信息：
```python
proxy_manager = ProxyManager(debug=True)
```

或在配置文件中设置：
```yaml
debug:
  enabled: true
  verbose_logging: true
  save_failed_requests: true
```

## 📈 性能优化

### 验证性能
- 使用异步验证提升速度
- 调整并发数量平衡性能和资源
- 启用连接池复用连接

### 存储性能
- 使用数据库存储提升查询速度
- 定期清理无效代理
- 启用索引优化查询

### 监控性能
- 调整指标收集间隔
- 限制日志文件大小
- 使用异步日志写入

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果遇到问题或需要帮助：

1. 查看 [故障排除](#故障排除) 部分
2. 检查 [Issues](../../issues) 中的已知问题
3. 创建新的 Issue 描述问题
4. 提供详细的错误日志和配置信息

---

**注意**: 请确保遵守相关法律法规，合理使用代理服务。
