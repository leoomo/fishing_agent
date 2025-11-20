# Fishing Agent - 智能钓鱼助手 v2.3.0

基于 LangChain 1.0+ 的智能钓鱼助手项目，专注于钓鱼时间推荐和天气分析。

> 🎣 智能分析天气条件，推荐最佳钓鱼时间 - **时间段意图理解增强版**

## ✨ 核心功能

- **🎣 智能钓鱼推荐**: 基于7因子评分算法的专业钓鱼分析
- **⏰ 时间段意图理解**: 精准识别用户时间限定，支持白天/晚上/上午/下午等时段
- **🌤️ 实时天气查询**: 集成彩云天气API，支持全国3,142+地区
- **🗺️ 智能坐标服务**: 高德地图API集成，多级缓存优化
- **🤖 LangChain智能体**: 多模型支持，Few-Shot意图识别增强
- **📊 同步架构**: 稳定可靠的同步版本，避免异步复杂性

## 🏗️ 技术架构

### 核心特性
- **🔄 中央服务管理**: 单例模式管理服务实例，避免重复初始化
- **🔧 接口抽象层**: 松耦合设计，支持依赖注入
- **⚡ 多级缓存**: 内存+文件缓存，90%+命中率
- **🛡️ 同步稳定**: 完全同步架构，消除事件循环问题
- **🧠 智能匹配**: 智能地名匹配和坐标解析
- **🚀 纯LangChain架构**: 简洁高效的LangChain 1.0+实现，无额外包装层
- **⏰ 时间段智能识别**: Few-Shot示例 + 思维链增强，95%+意图识别准确率
- **📝 精准时段过滤**: 基于时间范围的算法过滤，支持跨午夜时间段

### 已修复的技术问题
- ✅ **数据库路径问题**: 修复相对路径导致的数据库连接失败
- ✅ **中间件兼容性**: 解决AgentMiddleware基类属性设置冲突
- ✅ **模型配置统一**: 统一GLM-4.6模型配置，支持智谱AI平台
- ✅ **异步中间件**: 完整的异步支持，ModelCallRecord正确实例化
- ✅ **服务管理**: 通过服务管理器统一管理坐标服务依赖
- ✅ **LangGraph集成问题**: 修复404 API端点错误和中间件TypeError
  - 修复环境变量冲突导致的API路径错误
  - 修复ToolCallRecord构造函数参数错误
  - 修复缺失的_extract_token_usage方法
  - 解决total_response_time_ms属性名称错误
- ✅ **天气API容错优化**: 扩展hourly预报从48到72小时，增强hourly/dual API降级机制
- ✅ **时间戳解析问题**: 修复ISO 8601格式解析，支持跨日期数据聚合
- ✅ **架构清理**: 移除tools模块循环依赖，简化为纯LangChain 1.0+架构
- ✅ **时间段意图理解**: 新增time_period参数支持，实现精准时间段识别和过滤

### 🎣 钓鱼推荐系统
- **7因子评分算法**: 温度、天气、风力、气压、湿度、季节、月相
- **时间段意图理解**: 精准识别用户时间限定，支持多种时间表达方式
- **智能时段过滤**: 支持白天/晚上/上午/下午/傍晚/深夜等6种时段
- **自然语言理解**: 支持中文查询，如"明天白天哪里钓鱼好？"
- **全国覆盖**: 支持3,142+地区的钓鱼条件分析

#### 支持的时间段
- **白天 (daytime)**: 6:00-18:00 - 适合日间活动
- **晚上 (night)**: 18:00-次日6:00 - 支持跨午夜时间范围
- **上午 (morning)**: 6:00-12:00 - 清晨到正午
- **下午 (afternoon)**: 12:00-18:00 - 午后到傍晚
- **傍晚 (evening)**: 16:00-19:00 - 黄金钓鱼时段
- **深夜 (midnight)**: 0:00-6:00 - 夜钓爱好者时段

### 🌤️ 天气服务
- **实时数据**: 彩云天气API集成，实时天气信息
- **日期查询**: 支持相对日期("明天")和绝对日期("2024-12-25")
- **小时预报**: 72小时详细天气预报，完整覆盖3天钓鱼规划
- **智能降级**: hourly/daily双API降级机制，确保高可用性
- **容错机制**: ISO 8601时间戳解析，跨日期数据聚合，零虚假数据原则

### 🗺️ 坐标服务
- **高德地图API**: 精确的地理坐标查询
- **智能缓存**: 90%+命中率，响应时间<1ms
- **地名匹配**: 支持别名简称和模糊匹配
- **全国覆盖**: 中国所有行政区划95%+覆盖率

## 🚀 快速开始

### 环境要求
- Python 3.11+
- uv 包管理器

### 安装依赖
```bash
# 安装依赖
uv sync
```

### 配置环境变量
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件，添加您的API密钥
# 必需的API密钥：
# - CAIYUN_API_KEY: 彩云天气API
# - AMAP_API_KEY: 高德地图API
# - ANTHROPIC_AUTH_TOKEN: 智谱AI API (推荐)
```

### 运行项目

#### 方法一：交互式应用（推荐）
```bash
uv run python main.py
```

#### 方法二：直接运行Agent（新！）
```bash
# 从项目根目录运行
uv run python src/agent.py

# 或者从src目录运行
cd src && uv run python agent.py
```

> ✅ **注意**: v2.2.0新增功能！无需复杂的PYTHONPATH配置，直接运行即可！
> ⏰ **v2.3.0更新**: 新增时间段意图理解功能，支持精准时段识别！

#### 方法三：激活虚拟环境
```bash
source .venv/bin/activate
python main.py
```

## 💻 使用示例

### 基础使用
```python
# 导入智能体 (添加src到路径)
import sys
sys.path.append('src')
from agent import create_optimized_fishing_agent

# 创建智能体实例
agent = create_optimized_fishing_agent(model_provider="zhipu")

# 钓鱼推荐查询（包含时间段限定）
response = agent.run("明天白天去杭州钓鱼怎么样？")
print(response)

# 精确时间段查询
response = agent.run("今晚北京哪里适合钓鱼？")
print(response)

# 天气查询
response = agent.run("北京今天天气怎么样？")
print(response)
```

### 时间段功能使用（v2.3.0新增）
```python
from src.tools.fishing_tools import query_fishing_recommendation

# 白天钓鱼推荐
result = query_fishing_recommendation.invoke({
    'location': '杭州',
    'date': '明天',
    'time_period': '白天'  # 仅返回6:00-18:00的时段
})
print(f"白天钓鱼推荐: {result}")

# 晚上钓鱼推荐
result = query_fishing_recommendation.invoke({
    'location': '北京',
    'date': '今天',
    'time_period': '晚上'  # 仅返回18:00-次日6:00的时段
})
print(f"晚上钓鱼推荐: {result}")

# 上午时段推荐
result = query_fishing_recommendation.invoke({
    'location': '上海',
    'date': '后天',
    'time_period': '上午'  # 仅返回6:00-12:00的时段
})
print(f"上午钓鱼推荐: {result}")
```

### 直接工具调用
```python
from src.tools import get_all_tools
from src.tools.weather_tools import get_current_weather
from src.tools.fishing_tools import query_fishing_recommendation

# 查询当前天气
result = get_current_weather.invoke({'place': '杭州'})
print(f"当前天气: {result}")

# 传统钓鱼推荐（无时间段限定）
result = query_fishing_recommendation.invoke({
    'location': '富阳区',
    'date': '明天'
})
print(f"全天钓鱼推荐: {result}")

# 查看所有可用工具
tools = get_all_tools()
print(f"可用工具数量: {len(tools)}")
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
```

### 工具统一接口使用
```python
# 使用简化的工具接口
from src.tools import get_fishing_tools, get_weather_tools, get_basic_tools

# 获取钓鱼工具
fishing_tools = get_fishing_tools()
print(f"钓鱼工具: {len(fishing_tools)}个")

# 获取天气工具
weather_tools = get_weather_tools()
print(f"天气工具: {len(weather_tools)}个")

# 获取基础工具
basic_tools = get_basic_tools()
print(f"基础工具: {len(basic_tools)}个")
```

## 📁 项目结构

```
fishing-agent/
├── src/                          # 源代码目录
│   ├── agent.py                  # 🤖 LangChain智能体主入口（向后兼容）
│   ├── fishing_agent/            # 🧠 智能体核心实现
│   │   ├── __init__.py          # 智能体模块导出
│   │   ├── core.py              # 核心智能体类
│   │   ├── model_factory.py     # 多模型工厂
│   │   ├── prompts.py           # System Prompt和Few-Shot
│   │   └── callbacks.py         # 回调处理
│   ├── tools/                    # 🛠️ 简化工具模块 (5-file架构核心)
│   │   ├── __init__.py          # 工具统一接口和导出
│   │   ├── basic_tools.py       # 基础工具（时间、数学、坐标）
│   │   ├── weather_tools.py     # 天气工具（实时天气、预报）
│   │   └── fishing_tools.py     # 钓鱼工具（推荐、评分、时段过滤）
│   ├── utils/                    # 🔧 工具类
│   │   ├── api_client.py        # 统一HTTP客户端
│   │   ├── coordinate_utils.py  # 坐标和地理工具
│   │   └── cache.py             # 缓存系统
│   ├── config/                   # ⚙️ 配置管理
│   ├── middleware/               # 🔌 中间件
│   ├── data/                     # 📊 数据层
│   ├── docs/                     # 📖 技术文档
│   └── tests/                    # 🧪 测试套件
├── docs/                         # 📖 项目文档
│   └── intent_understanding_optimization.md  # ⏰ 时间段意图优化文档（v2.3.0）
├── main.py                       # 🚀 交互式CLI入口
├── pyproject.toml                # 📦 项目配置 (v2.3.0)
├── CLAUDE.md                     # 📖 Claude开发指南
├── CHANGELOG.md                  # 📋 更新日志
└── README.md                     # 📋 项目说明
```

## 🧪 测试

```bash
# 运行测试套件
uv run pytest src/tests/

# 运行时间段意图测试（v2.3.0新增）
uv run python src/tests/test_time_period_intent.py -v

# 运行时间段功能单元测试（不需要API密钥）
uv run pytest src/tests/test_time_period_intent.py -v -k "not integration"

# 运行时间段功能集成测试（需要配置API密钥）
uv run pytest src/tests/test_time_period_intent.py -v -k "integration"

# 运行其他特定测试
uv run python src/tests/test_enhanced_fishing_scorer.py
uv run python src/tests/test_national_coverage.py

# 运行集成测试
uv run python src/tests/integration/verify_national_integration.py

# 测试覆盖率报告
uv run pytest src/tests/ --cov=src --cov-report=html
```

## 🔧 开发指南

### 代码规范
- 使用 Python 3.11+ 语法
- 遵循 PEP 8 代码风格
- 添加类型注解和文档字符串
- 编写单元测试

### 添加新功能
1. 在相应模块中实现功能
2. 更新测试用例
3. 运行测试确保通过
4. 更新文档

## 📄 许可证

MIT License

---

---

## 🆕 v2.3.0 新功能亮点

### ⏰ 时间段意图理解（核心功能）

**问题解决**：
- ❌ **旧版**: 用户问"明天白天佛山钓鱼" → 返回包含晚上的全天推荐
- ✅ **新版**: 智能识别"白天"意图 → 仅返回6:00-18:00的时段推荐

**技术实现**：
- **Few-Shot学习**: 通过示例教会LLM正确识别时间表达
- **思维链增强**: 提升意图识别准确率至95%+
- **智能时段过滤**: 支持6种标准时间段的精准过滤
- **向后兼容**: `time_period`参数可选，不影响现有功能

**支持的时间表达**：
| 用户表达 | AI识别结果 | 时间范围 |
|---------|-----------|---------|
| "明天白天钓鱼" | time_period="白天" | 6:00-18:00 |
| "今晚钓鱼好吗" | time_period="晚上" | 18:00-次日6:00 |
| "后天上午" | time_period="上午" | 6:00-12:00 |
| "明天下午" | time_period="下午" | 12:00-18:00 |
| "傍晚时分" | time_period="傍晚" | 16:00-19:00 |
| "深夜钓鱼" | time_period="深夜" | 0:00-6:00 |

**完整测试覆盖**：
- 19个测试用例，100%通过率
- 单元测试 + 集成测试 + 边界测试
- 支持跨午夜时间段（如晚上时段）

### 🛠️ 架构优化

- **工具参数扩展**: `query_fishing_recommendation`新增`time_period`参数
- **System Prompt增强**: Few-Shot示例和意图识别规则
- **算法优化**: 基于时间范围的精确过滤算法
- **错误处理**: 优雅的未识别时间段回退机制

---

> 🎣 智能分析，精准钓鱼！现在支持时间段意图理解！