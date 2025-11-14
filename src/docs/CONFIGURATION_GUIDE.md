# 彩云天气 API 配置指南

## 📋 概述

本指南将帮助您配置彩云天气 API，以便在 LangChain 智能体中获取真实的天气数据。

## 🔧 环境变量配置

### 1. 配置文件设置

项目使用 `.env` 文件来管理环境变量配置。配置步骤如下：

#### 步骤 1: 复制配置模板
```bash
cp .env.example .env
```

#### 步骤 2: 编辑配置文件
编辑 `.env` 文件，设置您的彩云天气 API 密钥：

```bash
# 彩云天气 API 密钥 (用于真实天气数据)
# 获取方式: https://www.caiyunapp.com/
# 免费注册后可获得 API 密钥，支持一定次数的免费调用
CAIYUN_API_KEY=your-caiyun-api-key-here

# 高德地图 API 密钥 (用于坐标查询服务)
# 获取方式: https://console.amap.com/dev/key/app
# 注册成为开发者并创建 Web 服务 API 应用
AMAP_API_KEY=your-amap-api-key-here

# 调试日志开关 (全局日志控制)
# true/false, 1/0, yes/no, on/off - 支持多种格式
# 默认值: true (开启详细调试日志)
# 生产环境建议设置为: false (关闭详细日志)
DEBUG_LOGGING=true
```

将 `your-caiyun-api-key-here` 替换为您实际的 API 密钥。

### 2. 获取彩云天气 API 密钥

1. 访问 [彩云天气官网](https://www.caiyunapp.com/)
2. 注册账号并登录
3. 进入开发者控制台
4. 创建应用并获取 API 密钥
5. 将 API 密钥填入 `.env` 文件

### 3. 验证配置

运行以下命令验证配置是否正确：

```bash
# 运行天气服务测试
uv run python weather_service.py

# 或运行完整的测试套件
uv run python test_real_weather_api.py
```

如果配置正确，您将看到真实的天气数据而不是模拟数据。

## 📁 配置文件详解

### `.env` 文件结构

```bash
# LangChain 1.0+ 智能体所需的 API 密钥

# 智谱AI GLM API 密钥 (默认使用)
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# Anthropic Claude API 密钥 (备选)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OpenAI API 密钥 (备选)
OPENAI_API_KEY=your-openai-api-key-here

# 彩云天气 API 密钥 (天气功能核心配置)
CAIYUN_API_KEY=your-caiyun-api-key-here
```

### 环境变量说明

| 变量名 | 必需 | 描述 | 获取方式 |
|--------|------|------|----------|
| `CAIYUN_API_KEY` | 是 | 彩云天气 API 密钥 | https://www.caiyunapp.com/ |
| `ANTHROPIC_AUTH_TOKEN` | 否 | 智谱AI API 密钥 | https://open.bigmodel.cn/ |
| `ANTHROPIC_API_KEY` | 否 | Anthropic API 密钥 | https://console.anthropic.com/ |
| `OPENAI_API_KEY` | 否 | OpenAI API 密钥 | https://platform.openai.com/ |

## 🚀 使用方法

### 基本使用

```python
from weather_service import get_weather_info

# 获取天气信息
weather_info = get_weather_info("北京")
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