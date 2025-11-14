# 分层日志系统配置指南

## 🎯 概述

本项目实现了分层日志系统，支持三种日志模式和四种预设模板，能够根据使用场景动态调整日志输出的详细程度。

## 📋 环境变量配置

### 核心配置

```bash
# 日志模式 (默认: normal)
LOG_MODE=normal          # normal/debug/error

# 日志模板 (默认: production)
LOG_TEMPLATE=production  # production/development/debugging/minimal
```

### 模式说明

#### 🔸 LOG_MODE=normal (简洁模式)
- **适用场景**: 日常使用、生产环境
- **输出特点**: 只显示关键结果和重要信息
- **示例输出**:
  ```
  ✅ 北京: 晴夜, 6.76°C
  🎣 钓鱼建议: 推荐早上6-8点，评分85/100
  ```

#### 🔸 LOG_MODE=debug (调试模式)
- **适用场景**: 开发调试、问题排查
- **输出特点**: 显示详细的执行过程和性能指标
- **示例输出**:
  ```
  🚀 Agent调用 #1 [天气查询] - 耗时: 235ms
  🔧 天气工具: query_current_weather - 余杭区
  ✅ API响应成功 - 温度: 22°C, 多云
  🎣 钓鱼分析完成 - 最佳时间: 6-8点
  ```

#### 🔸 LOG_MODE=error (错误模式)
- **适用场景**: 错误排查、生产监控
- **输出特点**: 只显示异常信息和完整错误上下文
- **示例输出**:
  ```
  ❌ 天气API调用失败: HTTP 503
  📍 请求坐标: (120.2, 30.3) - 重试次数: 3
  📋 完整错误堆栈: ...
  💡 恢复建议: 使用缓存数据或切换备用API
  ```

### 模板说明

#### 🔸 production (生产模板)
- **Normal模式**: 简洁输出，只显示结果
- **Debug模式**: 显示工具执行过程和性能指标
- **Error模式**: 显示完整错误信息

#### 🔸 development (开发模板)
- **Normal模式**: 显示工具执行过程
- **Debug模式**: 显示完整调试信息
- **Error模式**: 显示完整错误上下文

#### 🔸 debugging (调试模板)
- **所有模式**: 显示最详细的调试信息
- **包含**: 事务ID、执行时间、参数传递、缓存状态等

#### 🔸 minimal (最小模板)
- **所有模式**: 只显示错误信息
- **适用**: 静默运行、CI/CD环境

## 🔧 快速配置

### 日常使用 (推荐)
```bash
export LOG_MODE=normal
export LOG_TEMPLATE=production
```

### 开发调试
```bash
export LOG_MODE=debug
export LOG_TEMPLATE=development
```

### 深度调试
```bash
export LOG_MODE=debug
export LOG_TEMPLATE=debugging
```

### 静默运行
```bash
export LOG_MODE=normal
export LOG_TEMPLATE=minimal
```

## 🔄 向后兼容

系统保持与现有配置的向后兼容性：

```bash
# 仍然支持现有的DEBUG_LOGGING配置
export DEBUG_LOGGING=true  # 等同于 LOG_MODE=debug

# 现有的Agent日志配置继续有效
export AGENT_LOG_LEVEL=INFO
export AGENT_ENHANCED_CONSOLE=true
```

## 📊 分层日志架构

```
Agent中间件层
├── 模型调用追踪
├── 性能指标统计
└── 调用目的分析

天气工具层
├── 函数执行过程
├── API调用记录
└── 缓存状态统计

底层服务层
├── 数据库查询
├── HTTP请求
└── 错误处理
```

## 🎮 动态配置

### 程序内动态切换
```python
from services.logging.hierarchical_logger import HierarchicalLogger, LogMode

# 获取logger实例
logger = HierarchicalLogger("my_component", "tool")

# 动态切换模式
logger.set_mode(LogMode.DEBUG)  # 切换到调试模式
logger.set_mode(LogMode.NORMAL) # 切换回简洁模式
```

### 配置管理
```python
from services.logging.hierarchical_logger_config import HierarchicalLoggerConfig, LogMode, LogTemplate

# 创建自定义配置
config = HierarchicalLoggerConfig(
    mode=LogMode.DEBUG,
    template=LogTemplate.DEVELOPMENT
)

# 获取层级配置
tool_config = config.get_layer_config("tool")
print(f"工具层日志级别: {tool_config.tool_level}")
print(f"显示详细信息: {tool_config.enable_tool_details}")
```

## 🚨 故障排查

### 常见问题

1. **日志输出过多**
   ```bash
   export LOG_MODE=normal
   export LOG_TEMPLATE=minimal
   ```

2. **需要详细调试信息**
   ```bash
   export LOG_MODE=debug
   export LOG_TEMPLATE=debugging
   ```

3. **只关心错误信息**
   ```bash
   export LOG_MODE=error
   export LOG_TEMPLATE=production
   ```

### 验证配置

```python
from services.logging.hierarchical_logger_config import default_hierarchical_config

# 查看当前配置
config = default_hierarchical_config
print(f"当前模式: {config.mode.value}")
print(f"当前模板: {config.template.value}")

# 查看详细配置
tool_config = config.get_layer_config("tool")
print(f"工具层配置: {tool_config}")
```

## 📝 最佳实践

1. **生产环境**: 使用 `LOG_MODE=normal` + `LOG_TEMPLATE=production`
2. **开发环境**: 使用 `LOG_MODE=debug` + `LOG_TEMPLATE=development`
3. **问题排查**: 使用 `LOG_MODE=debug` + `LOG_TEMPLATE=debugging`
4. **自动化部署**: 使用 `LOG_MODE=normal` + `LOG_TEMPLATE=minimal`

这样可以确保在正常使用时获得简洁的输出，在需要时获得详细的调试信息。