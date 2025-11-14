# LangChain 智能体日志中间件

## 📋 概述

`AgentLoggingMiddleware` 是一个为 LangChain 智能体设计的全面日志记录和监控中间件，提供详细的执行追踪、性能分析和工具调用监控功能。

## ✨ 主要功能

### 🔍 完整执行日志
- 记录用户输入和AI回复
- 模型调用详细信息
- 工具调用参数和结果
- 错误和异常追踪

### ⚡ 性能监控
- 响应时间统计
- Token使用量监控
- 模型调用次数统计
- 工具调用性能分析

### 🛠️ 工具调用追踪
- 每个工具的调用详情
- 参数和结果记录
- 执行耗时统计
- 成功/失败状态

### 🔐 安全特性
- 自动过滤敏感信息（API密钥、密码等）
- 可配置的日志级别
- 安全的日志文件输出

### 📊 统计分析
- 会话级别的执行统计
- 实时性能指标
- 可重置的统计计数
- JSON格式的详细报告

## 🚀 快速开始

### 1. 基础使用

```python
from modern_langchain_agent import ModernLangChainAgent

# 启用日志中间件（使用默认配置）
agent = ModernLangChainAgent(
    model_provider="anthropic",
    enable_logging=True
)

# 正常使用智能体
response = agent.run("北京今天天气怎么样？")
print(response)

# 获取执行统计
summary = agent.get_execution_summary()
print(f"模型调用次数: {summary['metrics']['model_calls_count']}")
```

### 2. 自定义配置

```python
from modern_langchain_agent import ModernLangChainAgent
from services.middleware import MiddlewareConfig

# 创建自定义配置
config = MiddlewareConfig(
    log_level="DEBUG",                      # 详细日志
    log_to_console=True,                    # 控制台输出
    log_to_file=True,                       # 文件输出
    log_file_path="logs/agent.log",         # 日志文件路径
    enable_performance_monitoring=True,     # 性能监控
    enable_tool_tracking=True,              # 工具追踪
    max_log_length=1000                     # 日志最大长度
)

# 使用自定义配置
agent = ModernLangChainAgent(
    model_provider="anthropic",
    enable_logging=True,
    middleware_config=config
)
```

### 3. 环境变量配置

在 `.env` 文件中设置：

```bash
# 日志级别
AGENT_LOG_LEVEL=INFO

# 输出方式
AGENT_LOG_CONSOLE=true
AGENT_LOG_FILE=true
AGENT_LOG_FILE_PATH=logs/agent.log

# 功能开关
AGENT_PERF_MONITOR=true
AGENT_TOOL_TRACKING=true
AGENT_SENSITIVE_FILTER=true
```

### 4. 交互式使用

```python
agent = ModernLangChainAgent(enable_logging=True)
agent.interactive_chat()

# 在聊天中：
# - 输入 "stats" 查看执行统计
# - 输入 "reset" 重置统计指标
# - 输入 "quit" 退出
```

## 📊 执行统计

### 获取统计信息

```python
summary = agent.get_execution_summary()

# 访问各项指标
metrics = summary['metrics']
print(f"总耗时: {metrics['total_duration_ms']:.2f}ms")
print(f"模型调用次数: {metrics['model_calls_count']}")
print(f"工具调用次数: {metrics['tool_calls_count']}")
print(f"错误次数: {metrics['errors_count']}")
print(f"Token使用: {metrics['token_usage']}")

# 查看工具调用详情
tool_calls = summary['tool_calls']
for tc in tool_calls:
    print(f"{tc.tool_name}: {tc.duration_ms:.2f}ms ({'成功' if tc.success else '失败'})")
```

### 重置统计

```python
agent.reset_session_metrics()
print("统计指标已重置")
```

## 🛠️ 配置选项

### MiddlewareConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `log_level` | str | "INFO" | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `log_to_console` | bool | True | 控制台输出 |
| `log_to_file` | bool | False | 文件输出 |
| `log_file_path` | str | "logs/agent.log" | 日志文件路径 |
| `enable_performance_monitoring` | bool | True | 性能监控 |
| `enable_tool_tracking` | bool | True | 工具调用追踪 |
| `enable_sensitive_filter` | bool | True | 敏感信息过滤 |
| `max_log_length` | int | 2000 | 最大日志长度 |
| `session_id_generator` | str | "uuid" | 会话ID生成方式 |

### 环境变量

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `AGENT_LOG_LEVEL` | 日志级别 | `DEBUG` |
| `AGENT_LOG_CONSOLE` | 控制台输出 | `true` |
| `AGENT_LOG_FILE` | 文件输出 | `true` |
| `AGENT_LOG_FILE_PATH` | 日志文件路径 | `logs/agent.log` |
| `AGENT_PERF_MONITOR` | 性能监控 | `true` |
| `AGENT_TOOL_TRACKING` | 工具追踪 | `true` |
| `AGENT_SENSITIVE_FILTER` | 敏感信息过滤 | `true` |
| `AGENT_MAX_LOG_LENGTH` | 最大日志长度 | `2000` |

## 📁 文件结构

```
services/middleware/
├── __init__.py                 # 模块初始化
├── config.py                  # 配置管理
└── logging_middleware.py      # 核心中间件实现

测试和示例文件:
├── test_logging_middleware.py # 功能测试
├── example_logging_middleware.py # 使用示例
├── verify_logging_middleware.py # 集成验证
└── .env.middleware.example   # 环境变量示例

日志输出:
└── logs/                       # 日志文件目录
    └── agent.log              # 默认日志文件
```

## 🔧 高级用法

### 自定义敏感数据过滤

```python
from services.middleware.logging_middleware import SensitiveDataFilter

# 创建自定义过滤器
class CustomFilter(SensitiveDataFilter):
    SENSITIVE_PATTERNS = [
        ('api_key', r'(?i)api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\\s]{10,})'),
        # 添加更多自定义模式...
    ]

# 在配置中使用
config = MiddlewareConfig(enable_sensitive_filter=True)
```

### 性能监控示例

```python
# 启用详细性能监控
config = MiddlewareConfig(
    log_level="DEBUG",
    enable_performance_monitoring=True,
    enable_tool_tracking=True
)

agent = ModernLangChainAgent(
    enable_logging=True,
    middleware_config=config
)

# 执行复杂任务
response = agent.run("明天杭州适合钓鱼吗？需要查天气、计算最佳时间")

# 查看性能分析
summary = agent.get_execution_summary()
print("性能分析:")
print(f"  总耗时: {summary['metrics']['total_duration_ms']:.2f}ms")
print(f"  平均每次模型调用: {summary['metrics']['total_duration_ms'] / summary['metrics']['model_calls_count']:.2f}ms")

for tool_call in summary['tool_calls']:
    print(f"  {tool_call['tool_name']}: {tool_call['duration_ms']:.2f}ms")
```

### 错误追踪

```python
# 启用详细错误日志
config = MiddlewareConfig(
    log_level="DEBUG",
    enable_tool_tracking=True
)

agent = ModernLangChainAgent(enable_logging=True, middleware_config=config)

# 尝试可能出错的操作
try:
    response = agent.run("计算 1/0")  # 会产生除零错误
except Exception as e:
    print(f"处理错误: {e}")

# 查看错误统计
summary = agent.get_execution_summary()
print(f"记录的错误次数: {summary['metrics']['errors_count']}")
```

## 🧪 测试

### 运行完整测试套件

```bash
# 验证集成
uv run python verify_logging_middleware.py

# 功能测试
uv run python test_logging_middleware.py

# 使用示例
uv run python example_logging_middleware.py
```

### 单独测试功能

```python
# 测试基础功能
from test_logging_middleware import test_basic_logging
test_basic_logging()

# 测试自定义配置
from test_logging_middleware import test_custom_config
test_custom_config()

# 测试性能监控
from test_logging_middleware import test_performance_monitoring
test_performance_monitoring()
```

## 📈 性能影响

日志中间件的设计考虑了性能影响：

- **异步日志记录**: 避免阻塞主执行流程
- **可配置级别**: 生产环境可减少日志量
- **智能截断**: 防止日志过长
- **缓存优化**: 减少重复计算

典型性能开销：1-5ms 每次调用

## 🔍 故障排除

### 常见问题

1. **日志文件未生成**
   - 检查 `AGENT_LOG_FILE=true`
   - 确保目录权限正确
   - 验证文件路径有效

2. **日志级别不生效**
   - 确认环境变量设置正确
   - 检查配置加载顺序

3. **敏感信息泄露**
   - 启用 `AGENT_SENSITIVE_FILTER=true`
   - 添加自定义过滤规则

4. **性能影响过大**
   - 调整日志级别为 `INFO` 或 `WARNING`
   - 禁用工具追踪：`AGENT_TOOL_TRACKING=false`

### 调试模式

```python
# 启用详细调试
config = MiddlewareConfig(
    log_level="DEBUG",
    enable_performance_monitoring=True,
    enable_tool_tracking=True,
    max_log_length=5000
)

agent = ModernLangChainAgent(
    enable_logging=True,
    middleware_config=config
)
```

## 📚 API 参考

### AgentLoggingMiddleware

主要的日志中间件类。

**方法:**

- `get_execution_summary()` -> `Dict[str, Any]`: 获取执行统计
- `reset_session_metrics()`: 重置统计指标

### MiddlewareConfig

配置管理类。

**方法:**

- `from_env()` -> `MiddlewareConfig`: 从环境变量创建配置
- `validate()` -> `bool`: 验证配置有效性
- `to_dict()` -> `Dict[str, Any]`: 转换为字典格式

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进日志中间件功能。

## 📄 许可证

本项目采用 MIT 许可证。