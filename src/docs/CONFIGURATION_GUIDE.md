# 智能钓鱼助手 - 完整配置指南 v2.2.0

## 📋 概述

本指南将帮助您配置智能钓鱼助手v2.2.0所需的所有API服务，包括天气数据、坐标服务和LLM提供商。项目采用**极简架构**，配置过程简单直接。

## 🔧 环境变量配置 (v2.2.0)

### 1. 快速配置

```bash
# 1. 安装依赖
uv sync

# 2. 复制配置模板
cp .env.example .env

# 3. 编辑配置文件，添加您的API密钥
```

### 2. 必需配置项

编辑 `.env` 文件，配置以下必需的API服务：

```bash
# === 必需的API服务 ===

# 彩云天气 API 密钥 (必需)
# 获取方式: https://www.caiyunapp.com/
# 免费注册后可获得 API 密钥，支持一定次数的免费调用
CAIYUN_API_KEY=your-caiyun-api-key-here

# 高德地图 API 密钥 (必需)
# 获取方式: https://console.amap.com/dev/key/app
# 注册成为开发者并创建 Web 服务 API 应用
AMAP_API_KEY=your-amap-api-key-here

# === LLM提供商 (至少配置一个) ===

# 智谱AI GLM API 密钥 (推荐)
# 获取方式: https://open.bigmodel.cn/
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# 或者配置其他LLM提供商：
# 通义千问 API 密钥
# DASHSCOPE_API_KEY=your-qwen-api-key-here

# === 可选配置 ===

# 日志级别 (可选)
LOG_LEVEL=INFO

# 缓存过期时间 (秒，可选)
CACHE_TTL=3600
```

### 3. API密钥获取指南

#### 🌤️ 彩云天气 API (必需)

1. 访问 [彩云天气官网](https://www.caiyunapp.com/)
2. 注册账号并登录
3. 进入开发者控制台
4. 创建应用并获取 API 密钥
5. 将 `CAIYUN_API_KEY` 填入 `.env` 文件

#### 🗺️ 高德地图 API (必需)

1. 访问 [高德开放平台](https://console.amap.com/dev/key/app)
2. 注册成为开发者
3. 创建 Web 服务 API 应用
4. 获取 API 密钥
5. 将 `AMAP_API_KEY` 填入 `.env` 文件

#### 🤖 智谱AI GLM (推荐LLM)

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并实名认证
3. 获取 API Token
4. 将 `ANTHROPIC_AUTH_TOKEN` 填入 `.env` 文件

#### 🔄 阿里巴巴通义千问 (可选LLM)

1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 开通服务并获取API-KEY
3. 将 `DASHSCOPE_API_KEY` 填入 `.env` 文件

### 4. 验证配置 (v2.2.0)

运行以下命令验证配置是否正确：

```bash
# v2.2.0 简化验证测试

# 1. 测试工具接口
uv run python -c "
from src.tools import get_all_tools
tools = get_all_tools()
print(f'✅ 工具加载成功: {len(tools)} 个工具')
"

# 2. 测试天气API (需要CAIYUN_API_KEY)
uv run python -c "
from src.tools.weather_tools import get_current_weather
try:
    result = get_current_weather.invoke({'place': '北京', 'date': '今天'})
    print(f'✅ 天气API测试成功: {result[:100]}...')
except Exception as e:
    print(f'❌ 天气API测试失败: {e}')
"

# 3. 测试智能体 (需要LLM API)
uv run python -c "
from src.agent import create_optimized_fishing_agent
try:
    agent = create_optimized_fishing_agent()
    result = agent.run('现在几点了？')
    print(f'✅ 智能体测试成功: {result[:100]}...')
except Exception as e:
    print(f'❌ 智能体测试失败: {e}')
"

# 4. 运行完整测试套件
uv run pytest src/tests/ -v
```

如果配置正确，您将看到所有测试都显示"✅ 成功"。

## 📁 配置文件详解 (v2.2.0)

### `.env` 文件完整结构

```bash
# === 数据API服务 (必需) ===
CAIYUN_API_KEY=your-caiyun-api-key-here      # 彩云天气API
AMAP_API_KEY=your-amap-api-key-here          # 高德地图API

# === LLM提供商 (至少配置一个) ===
ANTHROPIC_AUTH_TOKEN=your-zhipu-token-here   # 智谱AI GLM (推荐)
DASHSCOPE_API_KEY=your-qwen-key-here         # 阿里通义千问
OPENAI_API_KEY=your-openai-key-here          # OpenAI GPT
ANTHROPIC_API_KEY=your-claude-key-here       # Anthropic Claude

# === 可选配置 ===
LOG_LEVEL=INFO                               # 日志级别
CACHE_TTL=3600                               # 缓存过期时间(秒)
```

### 环境变量详细说明

| 变量名 | 必需 | 描述 | 推荐程度 | 获取方式 |
|--------|------|------|----------|----------|
| `CAIYUN_API_KEY` | ✅ 是 | 彩云天气 API 密钥 | 核心必需 | https://www.caiyunapp.com/ |
| `AMAP_API_KEY` | ✅ 是 | 高德地图 API 密钥 | 核心必需 | https://console.amap.com/dev/key/app |
| `ANTHROPIC_AUTH_TOKEN` | ⚠️ 推荐 | 智谱AI GLM API | 推荐首选 | https://open.bigmodel.cn/ |
| `DASHSCOPE_API_KEY` | ⚠️ 推荐 | 通义千问 API | 备选方案 | https://bailian.console.aliyun.com/ |
| `LOG_LEVEL` | ❌ 否 | 日志级别 | 可选 | INFO/WARNING/ERROR |

## 🚀 使用方法 (v2.2.0)

### 基本使用

```python
# 方式1: 直接使用工具
from src.tools.weather_tools import get_current_weather
from src.tools.fishing_tools import query_fishing_recommendation

# 获取天气信息
weather_info = get_current_weather.invoke({
    'place': '北京',
    'date': '今天'
})

# 获取钓鱼推荐
fishing_advice = query_fishing_recommendation.invoke({
    'location': '杭州',
    'date': '明天'
})

# 方式2: 使用智能体
from src.agent import create_optimized_fishing_agent

agent = create_optimized_fishing_agent(model_provider="zhipu")
response = agent.run("明天北京适合钓鱼吗？")
print(weather_info)
```

### 在智能体中使用

```python
from modern_langchain_agent import ModernLangChainAgent

# 创建智能体 (会自动使用环境变量中的 API 密钥)
agent = ModernLangChainAgent(model_provider="zhipu")

# 查询天气
result = agent.run("北京今天天气怎么样？")
print(result)
```

## 🛠️ 故障排除

### 常见问题

#### 1. API 密钥未生效
**问题**: 仍然使用模拟数据
**解决方案**:
- 确认 `.env` 文件在项目根目录
- 检查 API 密钥是否正确复制
- 重启 Python 程序

#### 2. 环境变量未加载
**问题**: `CAIYUN_API_KEY` 为空
**解决方案**:
- 安装 `python-dotenv`: `uv add python-dotenv`
- 确认在代码中调用 `load_dotenv()`

#### 3. API 调用失败
**问题**: API 返回错误
**解决方案**:
- 检查 API 密钥是否有效
- 确认 API 配额是否充足
- 查看网络连接是否正常

### 调试命令

```bash
# 检查环境变量
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('彩云天气 API 密钥:', os.getenv('CAIYUN_API_KEY', '未设置'))
"

# 测试 API 连接
uv run python -c "
from weather_service import get_weather_info
print(get_weather_info('北京'))
"
```

## 🔒 安全注意事项

1. **不要提交 .env 文件到版本控制系统**
   ```bash
   # .gitignore 应包含
   .env
   ```

2. **定期轮换 API 密钥**
   - 建议每 3-6 个月更换一次 API 密钥

3. **监控 API 使用量**
   - 定期检查彩云天气控制台的 API 调用统计

4. **生产环境配置**
   - 使用环境变量或密钥管理服务
   - 不要在代码中硬编码 API 密钥

## 📊 功能特性

### 支持的城市
目前支持中国 15+ 主要城市：
- 北京、上海、广州、深圳、杭州
- 成都、西安、武汉、南京、重庆
- 天津、苏州、青岛、大连、厦门

### 数据格式
返回的天气数据包含：
- 温度和体感温度
- 湿度和气压
- 风速和风向
- 天气状况描述

### 错误处理
- API 不可用时自动降级到模拟数据
- 无效城市返回友好的错误信息
- 网络异常时提供重试机制

## 📞 技术支持

如果遇到配置问题，请：

1. 查看本指南的故障排除部分
2. 检查彩云天气官方文档
3. 运行测试脚本诊断问题

---

**配置完成后，您的智能体将能够提供准确的实时天气信息！** 🌤️