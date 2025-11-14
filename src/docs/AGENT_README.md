# LangChain 1.0+ 智能体使用指南

本项目基于最新的 LangChain 1.0+ API 创建了一个现代化的智能体，展示了当前推荐的智能体开发模式，**默认使用智谱AI GLM-4.6 模型**。

## 🆕 LangChain 1.0+ 主要特性

- **新的 `create_agent` API**: 替代了旧版本的 `createReactAgent`
- **简化的工具集成**: 使用 `@tool` 装饰器定义工具
- **基于 LangGraph**: 智能体底层使用 LangGraph 实现，提供更好的执行能力
- **标准化消息格式**: 统一的消息传递接口
- **多模型支持**: 支持智谱AI、Anthropic Claude、OpenAI GPT

## 📁 项目文件

- `modern_langchain_agent.py` - 主要的智能体实现
- `test_agent_structure.py` - 代码结构测试（无需 API 密钥）
- `.env.example` - 环境变量示例文件

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 设置环境变量

复制示例环境文件并配置 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置 API 密钥：

```env
# 智谱AI (默认使用)
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# 或者使用其他模型
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. 获取智谱AI API 密钥

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录账号
3. 在控制台获取 API Token
4. 将 Token 设置为 `ANTHROPIC_AUTH_TOKEN` 环境变量

### 4. 测试代码结构

首先运行结构测试（无需 API 密钥）：

```bash
uv run python test_agent_structure.py
```

### 5. 启动智能体

设置好 API 密钥后，运行主程序：

```bash
uv run python modern_langchain_agent.py
```

## 🛠️ 智能体工具

智能体内置了以下工具：

1. **get_current_time()** - 获取当前时间和日期
2. **calculate(expression)** - 计算数学表达式
3. **get_weather(city)** - 查询城市天气信息（模拟数据）
4. **search_information(query)** - 搜索信息（模拟搜索）

## 🤖 支持的模型

### 智谱AI (默认)
- **模型**: GLM-4.6
- **环境变量**: `ANTHROPIC_AUTH_TOKEN`
- **特点**: 中文优化，性价比高

### Anthropic Claude
- **模型**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- **环境变量**: `ANTHROPIC_API_KEY`
- **特点**: 推理能力强，对话质量高

### OpenAI GPT
- **模型**: GPT-4o-mini
- **环境变量**: `OPENAI_API_KEY`
- **特点**: 速度快，成本较低

### 切换模型

如需切换模型，修改 `modern_langchain_agent.py` 中的 `model_provider` 参数：

```python
# 使用智谱AI (默认)
agent = ModernLangChainAgent(model_provider="zhipu")

# 使用 Claude
agent = ModernLangChainAgent(model_provider="anthropic")

# 使用 OpenAI
agent = ModernLangChainAgent(model_provider="openai")
```

## 💡 使用示例

### 基本查询

```
用户: 现在几点了？
智能体: 当前时间: 2025-11-03 17:53:22 (星期日)

用户: 帮我计算 123 * 456
智能体: 计算结果: 123 * 456 = 56088

用户: 北京天气怎么样？
智能体: 北京天气: 晴天，温度 25°C，湿度 60%
```

### 复杂查询

```
用户: 今天是什么日子？如果下雨的话，提醒我带伞
智能体: 当前时间: 2025-11-03 17:53:22 (星期日)。今天是星期日。关于下雨提醒，我可以帮您查询天气，目前北京是晴天，不需要带伞。
```

## 🔧 代码特点

### 使用最新 API

```python
# LangChain 1.0+ 新语法
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

# 支持多种模型初始化方式
# 智谱AI (使用 init_chat_model)
model = init_chat_model(
    model="glm-4.6",
    model_provider="openai",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    api_key=api_key,
)

# 或者使用传统方式
from langchain_anthropic import ChatAnthropic
model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# 创建智能体
agent = create_agent(
    model=model,
    tools=[tool1, tool2],
    system_prompt="你是一个智能助手..."
)

# 标准调用格式
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "你好"}
    ]
})
```

### 现代工具定义

```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """工具描述"""
    return f"处理结果: {param}"
```

### 智谱AI 集成示例

```python
from langchain.chat_models import init_chat_model

# 使用 init_chat_model 集成智谱AI
zhipu_model = init_chat_model(
    model="glm-4.6",
    model_provider="openai",  # 使用 OpenAI 兼容接口
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
)
```

## 📚 相关文档

- [LangChain 官方文档](https://docs.langchain.com)
- [LangChain 1.0 迁移指南](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [工具开发指南](https://docs.langchain.com/oss/python/contributing/implement-langchain)

## 🧪 测试和调试

### 运行测试

```bash
# 结构测试
uv run python test_agent_structure.py

# 完整功能测试（需要 API 密钥）
uv run python modern_langchain_agent.py
```

### 启用 LangSmith 追踪（可选）

在 `.env` 文件中添加：

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=langchain-agent-demo
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个智能体示例！

## 📄 许可证

本项目仅供学习和参考使用。