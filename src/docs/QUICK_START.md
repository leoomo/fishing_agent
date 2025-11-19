# 智能钓鱼助手 - 快速开始指南

本指南帮助您快速开始使用基于 LangChain 1.0+ 的智能钓鱼助手系统。

## 🚀 5分钟快速体验

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd fishing_agent

# 安装依赖
uv sync

# 配置环境变量 (复制示例文件)
cp .env.example .env
# 编辑 .env 文件，添加API密钥
```

### 2. 运行智能钓鱼助手

```bash
# 启动简化架构的智能体
uv run python src/agent.py
```

这将演示智能钓鱼助手的完整功能：
- 🎣 智能钓鱼推荐：基于天气的专业建议
- 🌤️ 实时天气查询：全国3,142+地区覆盖
- ⏰ 时间查询：支持复杂时间表达
- 🔢 计算功能：基本数学运算

### 3. 单独使用工具

```bash
# 天气工具
uv run python -c "
from tools.weather_tools import get_current_weather
print(get_current_weather('北京'))
"

# 钓鱼推荐工具
uv run python -c "
from tools.fishing_tools import query_fishing_recommendation
print(query_fishing_recommendation('余杭区', '明天'))
"

# 时间工具
uv run python -c "
from tools.basic_tools import get_current_time
print(get_current_time())
"

# 计算工具
uv run python -c "
from tools.basic_tools import calculate
print(calculate('123 * 456'))
"
```

## 📋 工具概览

| 工具 | 功能 | 快速命令 |
|------|------|----------|
| **天气工具** | 实时天气查询 | `uv run python -c "from tools.weather_tools import get_current_weather; print(get_current_weather('上海'))"` |
| **钓鱼工具** | 智能钓鱼推荐 | `uv run python -c "from tools.fishing_tools import query_fishing_recommendation; print(query_fishing_recommendation('杭州', '明天'))"` |
| **时间工具** | 时间查询 | `uv run python -c "from tools.basic_tools import get_current_time; print(get_current_time())"` |
| **计算工具** | 数学运算 | `uv run python -c "from tools.basic_tools import calculate; print(calculate('12 * 8'))"` |

## 🛠️ 基础使用示例

### Python 脚本示例

```python
from tools.weather_tools import get_current_weather, get_weather_forecast
from tools.fishing_tools import query_fishing_recommendation
from tools.basic_tools import get_current_time, calculate

def main():
    # 1. 获取当前时间
    time_result = get_current_time()
    print(f"🕐 当前时间: {time_result}")

    # 2. 数学计算
    math_result = calculate("123 * 456")
    print(f"🔢 计算结果: {math_result}")

    # 3. 查询天气
    weather_result = get_current_weather("北京")
    print(f"🌤️ 北京天气: {weather_result}")

    # 4. 智能钓鱼推荐
    fishing_result = query_fishing_recommendation("余杭区", "明天")
    print(f"🎣 钓鱼建议: {fishing_result[:200]}...")

if __name__ == "__main__":
    main()
```

### 运行脚本

```bash
# 保存为 quick_demo.py 并运行
uv run python quick_demo.py
```

## 🔧 高级功能

### 1. 工具组合使用

```python
from tools.weather_tools import get_current_weather
from tools.fishing_tools import query_fishing_recommendation
from tools.basic_tools import get_current_time, calculate

def advanced_example():
    # 智能钓鱼决策系统
    time_result = get_current_time()
    current_hour = int(time_result.split(":")[0]) if ":" in time_result else 12

    # 计算最佳钓鱼时间段
    remaining_hours = 24 - current_hour

    # 根据时间段和天气推荐钓鱼策略
    weather_result = get_current_weather("杭州")

    # 智能钓鱼建议
    if 5 <= current_hour <= 9:  # 早晨黄金时段
        fishing_result = query_fishing_recommendation("杭州", "今天")
        print("🎯 早晨是钓鱼黄金时段！")
        print(f"📊 综合建议: {fishing_result[:150]}...")
    elif 17 <= current_hour <= 21:  # 傍晚黄金时段
        fishing_result = query_fishing_recommendation("杭州", "今天")
        print("🌅 傍晚是钓鱼黄金时段！")
        print(f"📊 综合建议: {fishing_result[:150]}...")
    else:
        print(f"⏰ 当前时段一般，建议等待 {max(0, 5-current_hour)} 小时后再钓鱼")

        # 计算下次钓鱼时间
        next_fishing_hours = max(0, 5 - current_hour) if current_hour < 5 else max(0, 17 - current_hour)
        next_fishing_minutes = calculate(f"{next_fishing_hours} * 60")
        print(f"📝 距离下次最佳钓鱼时间还有: {next_fishing_minutes} 分钟")

advanced_example()
```

### 2. 使用智能体完整功能

```python
from agent import create_optimized_fishing_agent

def agent_example():
    # 创建智能钓鱼助手
    agent = create_optimized_fishing_agent(model_provider='zhipu')

    # 智能对话示例
    queries = [
        "明天余杭区钓鱼怎么样？",
        "现在几点了？",
        "计算 15 * 8",
        "杭州未来三天天气如何？"
    ]

    for query in queries:
        print(f"🤔 用户: {query}")
        result = agent.run(query)
        print(f"🤖 助手: {result[:200]}...")
        print("-" * 50)

agent_example()
```

### 3. 错误处理和降级模式

```python
from agent import create_optimized_fishing_agent

def error_handling_example():
    # 创建智能体（包含降级机制）
    agent = create_optimized_fishing_agent(model_provider='zhipu')

    # 检查系统健康状态
    health = agent.health_check()
    print(f"🏥 系统状态: {health['status']}")

    for check, status in health['checks'].items():
        print(f"  {check}: {status}")

    # 获取详细统计信息
    stats = agent.get_llm_stats()
    print(f"📊 模型调用统计: {stats['total_model_calls']}次, 错误率: {100-stats['success_rate']:.1f}%")

error_handling_example()
```

## 📚 更多资源

- **[工具使用指南](TOOLS_GUIDE.md)** - 详细的使用文档
- **[API文档](API.md)** - 完整的API参考
- **[项目README](README.md)** - 项目概述和架构
- **[更新日志](CHANGELOG.md)** - 版本更新信息

## 🆘 获取帮助

如果遇到问题：

1. **检查环境配置**：`uv sync`
2. **验证API密钥**：确保 `.env` 文件中的密钥正确配置
3. **查看健康状态**：
   ```bash
   uv run python -c "
   from agent import create_optimized_fishing_agent
   agent = create_optimized_fishing_agent()
   health = agent.health_check()
   print('系统状态:', health)
   "
   ```
4. **阅读文档**：查看 `src/docs/` 目录下的完整文档
5. **检查日志**：系统会记录详细的错误信息和降级状态

## 🎉 开始探索

现在您已经掌握了基础用法，可以：

- 🎣 **智能钓鱼**：查询任意地区的钓鱼建议和天气条件
- 🌤️ **天气监控**：实时获取全国3,142+地区的天气信息
- 🤖 **智能对话**：使用自然语言与助手交互
- 🛠️ **工具开发**：基于LangChain 1.0+创建自定义工具
- 📊 **数据分析**：结合天气和时间数据进行决策

## 🔥 核心特性

- **伦理数据约束**：绝不编造虚假天气数据
- **架构简化**：从75+文件简化到5个核心文件
- **全国覆盖**：支持95%+中国行政区划
- **降级机制**：API失效时优雅降级，提供基础建议
- **同步架构**：稳定可靠的同步调用设计

祝您钓鱼愉快！🎣🐟