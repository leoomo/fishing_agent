# Fishing Agent - 智能钓鱼助手

基于 LangChain 1.0+ 和 LangGraph 的智能钓鱼助手项目，专注于钓鱼时间推荐和天气分析。

> 🎣 智能分析天气条件，推荐最佳钓鱼时间

## ✨ 核心功能

- **🎣 智能钓鱼推荐**: 基于7因子评分算法的专业钓鱼分析
- **🌤️ 实时天气查询**: 集成彩云天气API，支持全国3,142+地区
- **🗺️ 智能坐标服务**: 高德地图API集成，多级缓存优化
- **🤖 LangChain智能体**: 多模型支持，自然语言交互
- **📊 同步架构**: 稳定可靠的同步版本，避免异步复杂性

## 🏗️ 技术架构

### 核心特性
- **🔄 中央服务管理**: 单例模式管理服务实例，避免重复初始化
- **🔧 接口抽象层**: 松耦合设计，支持依赖注入
- **⚡ 多级缓存**: 内存+文件缓存，90%+命中率
- **🛡️ 同步稳定**: 完全同步架构，消除事件循环问题
- **🧠 智能匹配**: 智能地名匹配和坐标解析

### 🎣 钓鱼推荐系统
- **7因子评分算法**: 温度、天气、风力、气压、湿度、季节、月相
- **智能时间段推荐**: 解决传统"86分问题"，提供最佳钓鱼时间
- **自然语言理解**: 支持中文查询，如"明天哪里钓鱼好？"
- **全国覆盖**: 支持3,142+地区的钓鱼条件分析

### 🌤️ 天气服务
- **实时数据**: 彩云天气API集成，实时天气信息
- **日期查询**: 支持相对日期("明天")和绝对日期("2024-12-25")
- **小时预报**: 24小时详细天气预报
- **智能降级**: API不可用时自动使用模拟数据

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
# 创建环境配置文件
cat > .env << 'EOF'
# 彩云天气 API 密钥 (必需)
# 获取方式: https://www.caiyunapp.com/
CAIYUN_API_KEY=your-caiyun-api-key-here

# 高德地图 API 密钥 (必需)
# 获取方式: https://console.amap.com/dev/key/app
AMAP_API_KEY=your-amap-api-key-here

# 智谱AI GLM API 密钥 (推荐)
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# OpenAI API 密钥 (可选)
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic API 密钥 (可选)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
EOF
```

### 运行项目
```bash
# 运行主程序
uv run python main.py

# 或激活虚拟环境后运行
source .venv/bin/activate
python main.py
```

## 💻 使用示例

### 基础使用
```python
# 导入智能体
from src.agent import create_agent

# 创建智能体实例
agent = create_agent(model_provider="zhipu")

# 钓鱼推荐查询
response = agent.run("明天什么时段去杭州钓鱼比较好？")
print(response)

# 天气查询
response = agent.run("北京今天天气怎么样？")
print(response)
```

### 直接工具调用
```python
from src.tools.langchain_weather_tools_sync import (
    query_current_weather,
    query_fishing_recommendation
)

# 查询当前天气
result = query_current_weather.invoke({'place': '杭州'})
print(f"当前天气: {result}")

# 钓鱼推荐
result = query_fishing_recommendation.invoke({
    'location': '富阳区',
    'date': '明天'
})
print(f"钓鱼推荐: {result}")
```

### 坐标服务使用
```python
from src.services.coordinate.amap_coordinate_service import AmapCoordinateService

service = AmapCoordinateService()
coords = service.get_coordinate("河桥镇")
print(f"坐标: {coords}")
```

## 📁 项目结构

```
fishing-agent/
├── src/                          # 源代码目录
│   ├── agent.py                  # 🤖 LangChain智能体主入口
│   ├── core/                     # 🏗️ 核心架构
│   │   ├── interfaces.py         # 📋 接口定义
│   │   ├── base_tool.py          # 🔧 工具基类
│   │   ├── base_agent.py         # 🤖 智能体基类
│   │   └── registry.py           # 📊 注册器
│   ├── tools/                    # 🛠️ 工具模块
│   │   ├── langchain_weather_tools_sync.py  # 天气工具
│   │   ├── fishing_analyzer_sync.py         # 钓鱼分析器
│   │   └── enhanced_fishing_scorer.py       # 增强评分器
│   ├── services/                 # 🌐 服务层
│   │   ├── service_manager.py    # 🔄 服务管理器
│   │   ├── coordinate/           # 📍 坐标服务
│   │   ├── weather/              # 🌤️ 天气服务
│   │   ├── matching/             # 🧠 匹配服务
│   │   └── middleware/           # 📝 中间件
│   ├── interfaces/               # 🔧 服务接口
│   ├── config/                   # ⚙️ 配置管理
│   └── tests/                    # 🧪 测试套件
├── main.py                       # 🚀 程序入口
├── pyproject.toml                # 📦 项目配置
├── CLAUDE.md                     # 📖 Claude开发指南
└── README.md                     # 📋 项目说明
```

## 🧪 测试

```bash
# 运行测试套件
uv run pytest src/tests/

# 运行特定测试
uv run python src/tests/test_enhanced_fishing_scorer.py

# 运行集成测试
uv run python src/tests/integration/verify_national_integration.py
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

> 🎣 智能分析，精准钓鱼！