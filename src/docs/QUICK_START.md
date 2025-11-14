# 快速开始指南

本指南帮助您快速开始使用 LangChain 学习项目的新工具模块。

## 🚀 5分钟快速体验

### 1. 安装依赖

```bash
uv sync
```

### 2. 运行新工具演示

```bash
uv run python demo_new_tools_agent.py
```

这将演示所有4个新工具的功能：
- ⏰ 时间工具：获取当前时间
- 🔢 数学工具：执行计算
- 🌤️ 天气工具：查询天气
- 🔍 搜索工具：信息检索

### 3. 单独使用工具

```bash
# 时间工具
uv run python -c "
import asyncio
from tools import TimeTool
asyncio.run(TimeTool().execute(operation='current_time'))
"

# 数学工具
uv run python -c "
import asyncio
from tools import MathTool
asyncio.run(MathTool().execute(operation='add', a=10, b=5))
"

# 天气工具
uv run python -c "
import asyncio
from tools import WeatherTool
asyncio.run(WeatherTool().execute(operation='current_weather', location='北京'))
"

# 搜索工具
uv run python -c "
import asyncio
from tools import SearchTool
asyncio.run(SearchTool().execute(operation='knowledge_search', query='python'))
"
```

## 📋 工具概览

| 工具 | 功能 | 快速命令 |
|------|------|----------|
| **TimeTool** | 时间管理 | `uv run python -c "import asyncio; from tools import TimeTool; asyncio.run(TimeTool().execute(operation='current_time'))"` |
| **MathTool** | 数学计算 | `uv run python -c "import asyncio; from tools import MathTool; asyncio.run(MathTool().execute(operation='multiply', a=12, b=8))"` |
| **WeatherTool** | 天气查询 | `uv run python -c "import asyncio; from tools import WeatherTool; asyncio.run(WeatherTool().execute(operation='current_weather', location='上海'))"` |
| **SearchTool** | 信息搜索 | `uv run python -c "import asyncio; from tools import SearchTool; asyncio.run(SearchTool().execute(operation='knowledge_search', query='人工智能'))"` |

## 🛠️ 基础使用示例

### Python 脚本示例

```python
import asyncio
from tools import TimeTool, MathTool, WeatherTool, SearchTool

async def main():
    # 创建工具实例
    time_tool = TimeTool()
    math_tool = MathTool()
    weather_tool = WeatherTool()
    search_tool = SearchTool()

    # 1. 获取当前时间
    time_result = await time_tool.execute(operation='current_time')
    print(f"🕐 当前时间: {time_result.data['formatted']}")

    # 2. 数学计算
    math_result = await math_tool.execute(operation='multiply', a=123, b=456)
    print(f"🔢 计算结果: {math_result.data['formatted']}")

    # 3. 查询天气
    weather_result = await weather_tool.execute(
        operation='current_weather',
        location='北京'
    )
    if weather_result.success:
        data = weather_result.data
        print(f"🌤️ 北京天气: {data['condition']} {data['temperature']}°C")

    # 4. 搜索信息
    search_result = await search_tool.execute(
        operation='knowledge_search',
        query='LangChain'
    )
    if search_result.success:
        print(f"🔍 搜索结果: 找到 {search_result.data['total_results']} 个相关结果")

if __name__ == "__main__":
    asyncio.run(main())
```

### 运行脚本

```bash
# 保存为 quick_demo.py 并运行
uv run python quick_demo.py
```

## 🔧 高级功能

### 1. 工具组合使用

```python
import asyncio
from tools import TimeTool, MathTool, WeatherTool

async def advanced_example():
    time_tool = TimeTool()
    math_tool = MathTool()
    weather_tool = WeatherTool()

    # 获取当前时间并计算剩余工作时间
    time_result = await time_tool.execute(operation='current_time')
    if time_result.success:
        current_hour = time_result.data['hour']
        remaining_hours = 24 - current_hour

        # 计算剩余分钟数
        calc_result = await math_tool.execute(
            operation='multiply',
            a=remaining_hours,
            b=60
        )

        if calc_result.success:
            remaining_minutes = calc_result.data['result']
            print(f"⏰ 今天还剩 {remaining_hours} 小时 ({remaining_minutes} 分钟)")

            # 根据时间推荐活动
            if remaining_hours > 8:
                print("🎯 建议: 还有很多时间，可以学习新技能")
            elif remaining_hours > 4:
                print("💡 建议: 可以完成一些中等任务")
            else:
                print("🌙 建议: 时间不多，适合轻松活动")

asyncio.run(advanced_example())
```

### 2. 配置化工具

```python
import asyncio
from tools import TimeTool, MathTool

async def configured_example():
    # 自定义配置
    time_config = {
        "default_timezone": "America/New_York",
        "precision": 15
    }

    math_config = {
        "precision": 20,
        "enable_cache": True
    }

    time_tool = TimeTool(time_config)
    math_tool = MathTool(math_config)

    # 使用配置后的工具
    time_result = await time_tool.execute(operation='current_time')
    print(f"🌍 纽约时间: {time_result.data['formatted']}")

    # 高精度数学计算
    calc_result = await math_tool.execute(
        operation='power',
        base=2,
        exponent=0.5
    )
    print(f"🔤 √2 = {calc_result.data['result']}")

asyncio.run(configured_example())
```

### 3. 错误处理

```python
import asyncio
from tools import TimeTool

async def error_handling_example():
    time_tool = TimeTool()

    # 尝试无效操作
    result = await time_tool.execute(operation='invalid_operation')

    if not result.success:
        print(f"❌ 错误: {result.error}")

        # 使用回退方案
        fallback_result = await time_tool.execute(operation='current_time')
        if fallback_result.success:
            print(f"✅ 回退成功: {fallback_result.data['formatted']}")

asyncio.run(error_handling_example())
```

## 📚 更多资源

- **[工具使用指南](TOOLS_GUIDE.md)** - 详细的使用文档
- **[API文档](API.md)** - 完整的API参考
- **[项目README](README.md)** - 项目概述和架构
- **[更新日志](CHANGELOG.md)** - 版本更新信息

## 🆘 获取帮助

如果遇到问题：

1. 检查环境配置：`uv sync`
2. 查看错误日志：工具会返回详细的错误信息
3. 参考示例代码：查看 `demo_new_tools_agent.py`
4. 阅读完整文档：查看 `docs/` 目录下的文档

## 🎉 开始探索

现在您已经掌握了基础用法，可以：

- 📖 深入学习每个工具的详细功能
- 🔧 组合多个工具创建复杂应用
- 🛠️ 开发自定义工具
- 🚀 集成到更大的项目中

祝您使用愉快！🎊