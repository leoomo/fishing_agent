# LangChain Agents 中间件

此目录用于存放 LangChain Agents 中间件组件。

> **注意**：本项目使用 `langchain>=0.3.0`（LangChain 1.0+）。中间件是基于 **LangChain Agents** 的钩子系统，而不是 Runnable 包装器。

## 什么是中间件？

在 LangChain Agents 中，中间件是在代理执行流程特定点运行的**钩子（hooks）**，用于：

- **日志记录和监控**：记录模型调用、工具执行
- **重试和错误处理**：自动重试失败的调用
- **状态验证和控制流**：限制消息数量、提前退出
- **动态提示词生成**：根据上下文调整系统提示
- **工具选择和过滤**：动态选择相关工具

## 中间件类型

### Node-style Hooks（节点钩子）

在执行流程的特定点按顺序运行：

- **`before_agent`** - 代理开始前执行（每次调用一次）
- **`before_model`** - 每次模型调用前执行
- **`after_model`** - 每次模型响应后执行
- **`after_agent`** - 代理完成后执行（每次调用一次）

### Wrap-style Hooks（包装钩子）

拦截执行并控制何时调用处理器：

- **`wrap_model_call`** - 包装每次模型调用
- **`wrap_tool_call`** - 包装每次工具调用

## 实现方式

### 装饰器方式（简单快速）

适用于单一钩子、无复杂配置的场景：

```python
from langchain.agents.middleware import before_model, after_model
from langchain.agents.middleware import AgentState
from langgraph.runtime import Runtime
from typing import Any

@before_model
def log_input(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"输入: {state['messages'][-1].content}")
    return None

@after_model
def log_output(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"输出: {state['messages'][-1].content}")
    return None
```

### 类方式（复杂场景）

适用于多个钩子、需要配置的场景：

```python
from langchain.agents.middleware import AgentMiddleware, AgentState
from langgraph.runtime import Runtime
from typing import Any

class LoggingMiddleware(AgentMiddleware):
    def __init__(self, verbose: bool = True):
        super().__init__()
        self.verbose = verbose

    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        if self.verbose:
            print(f"模型调用前: {len(state['messages'])} 条消息")
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        if self.verbose:
            print(f"模型返回: {state['messages'][-1].content}")
        return None
```

## 使用中间件

通过 `create_agent()` 的 `middleware` 参数传递中间件：

```python
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[log_input, log_output, LoggingMiddleware()],
)
```

## 实用示例

### 示例 1：日志中间件

记录每次模型调用的输入输出：

```python
from langchain.agents.middleware import before_model, after_model

@before_model
def log_request(state, runtime):
    last_msg = state['messages'][-1]
    print(f"[请求] {last_msg.content[:50]}...")
    return None

@after_model
def log_response(state, runtime):
    last_msg = state['messages'][-1]
    print(f"[响应] {last_msg.content[:50]}...")
    return None
```

### 示例 2：重试中间件

自动重试失败的模型调用：

```python
from langchain.agents.middleware import wrap_model_call
from langchain.agents.middleware import ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def retry_on_error(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """重试最多 3 次"""
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"重试 {attempt + 1}/3，错误: {e}")
```

### 示例 3：工具监控中间件

监控工具调用和结果：

```python
from langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    tool_name = request.tool_call['name']
    print(f"[工具] 执行: {tool_name}")
    try:
        result = handler(request)
        print(f"[工具] {tool_name} 成功")
        return result
    except Exception as e:
        print(f"[工具] {tool_name} 失败: {e}")
        raise
```

### 示例 4：消息限制中间件

限制对话消息数量，超过限制时提前退出：

```python
from langchain.agents.middleware import before_model, hook_config
from langchain.messages import AIMessage

@before_model
@hook_config(can_jump_to=["end"])
def check_message_limit(state, runtime):
    """限制对话不超过 50 条消息"""
    if len(state["messages"]) >= 50:
        return {
            "messages": [AIMessage("对话消息已达上限，请开始新对话。")],
            "jump_to": "end"
        }
    return None
```

### 示例 5：钓鱼查询日志（项目集成）

基于 `src/fishing_agent/core.py` 的实际使用示例：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import before_model, after_model
from src.tools import get_all_tools
from src.fishing_agent.model_factory import ModelFactory
from src.fishing_agent.prompts import get_system_prompt

@before_model
def log_fishing_query(state, runtime):
    """记录钓鱼相关查询"""
    user_query = state['messages'][-1].content
    if any(keyword in user_query for keyword in ['钓鱼', '天气', '路亚']):
        print(f"[钓鱼查询] {user_query}")
    return None

@after_model
def log_fishing_response(state, runtime):
    """记录钓鱼推荐结果"""
    response = state['messages'][-1].content
    if '推荐' in response or '评分' in response:
        print(f"[推荐结果] 已生成")
    return None

# 创建带中间件的代理
model_factory = ModelFactory()
agent = create_agent(
    model=model_factory.create(),
    tools=get_all_tools(),
    middleware=[log_fishing_query, log_fishing_response],
    system_prompt=get_system_prompt()
)
```

## 执行顺序

当使用多个中间件时，执行顺序如下：

```python
agent = create_agent(
    model="gpt-4o",
    middleware=[middleware1, middleware2, middleware3],
    tools=[...],
)
```

**执行流程**：

1. `middleware1.before_agent()`
2. `middleware2.before_agent()`
3. `middleware3.before_agent()`
4. **代理循环开始**
5. `middleware1.before_model()`
6. `middleware2.before_model()`
7. `middleware3.before_model()`
8. `middleware1.wrap_model_call()` → `middleware2.wrap_model_call()` → `middleware3.wrap_model_call()` → **模型调用**
9. `middleware3.after_model()`
10. `middleware2.after_model()`
11. `middleware1.after_model()`
12. **代理循环结束**
13. `middleware3.after_agent()`
14. `middleware2.after_agent()`
15. `middleware1.after_agent()`

**关键规则**：
- `before_*` 钩子：按顺序执行（第一个到最后一个）
- `after_*` 钩子：反向执行（最后一个到第一个）
- `wrap_*` 钩子：嵌套执行（第一个中间件包装所有其他中间件）

## Agent Jumps（提前退出）

从中间件提前退出，返回包含 `jump_to` 的字典：

**可用的跳转目标**：
- `'end'` - 跳转到代理执行结束（或第一个 `after_agent` 钩子）
- `'tools'` - 跳转到工具节点
- `'model'` - 跳转到模型节点（或第一个 `before_model` 钩子）

```python
from langchain.agents.middleware import after_model, hook_config
from langchain.messages import AIMessage

@after_model
@hook_config(can_jump_to=["end"])
def check_blocked_content(state, runtime):
    """检测被屏蔽的内容"""
    last_message = state["messages"][-1]
    if "BLOCKED" in last_message.content:
        return {
            "messages": [AIMessage("抱歉，无法回应该请求。")],
            "jump_to": "end"
        }
    return None
```

## 中间件 vs 工具类

**重要区别**：

| 特性 | 中间件（middleware/） | 工具类（utils/） |
|------|---------------------|-----------------|
| **用途** | 拦截代理执行流程 | 独立辅助功能 |
| **参与执行** | 是（钩子系统） | 否 |
| **典型场景** | 日志、重试、验证、控制流 | 日期处理、坐标转换、数据验证 |
| **依赖** | 依赖 LangChain Agents | 独立模块 |

**判断标准**：
- 需要在模型调用前后执行逻辑？ → **中间件**
- 需要拦截工具调用？ → **中间件**
- 需要修改代理状态或提前退出？ → **中间件**
- 独立的辅助函数或数据处理？ → **工具类（utils/）**

## 最佳实践

1. **单一职责** - 每个中间件专注做好一件事
2. **优雅错误处理** - 不要让中间件错误导致代理崩溃
3. **选择合适的钩子类型**：
   - Node-style 用于顺序逻辑（日志、验证）
   - Wrap-style 用于控制流（重试、回退、缓存）
4. **清晰文档** - 说明任何自定义状态属性
5. **独立测试** - 集成前单独测试中间件
6. **考虑执行顺序** - 将关键中间件放在列表前面
7. **优先使用内置中间件** - 可用时使用 LangChain 内置中间件

## 当前状态

目前此目录为空，预留给未来可能需要的 LangChain Agents 中间件实现。

项目当前使用 `FishingAgentCallback` 回调系统进行日志记录和统计。未来可以考虑迁移到中间件系统以获得更强大的功能。

## 参考资源

- [LangChain Agents 中间件官方文档](https://python.langchain.com/docs/langchain/middleware/custom)
- [Built-in 中间件](https://python.langchain.com/docs/langchain/middleware/built-in)
- [Middleware API Reference](https://reference.langchain.com/python/langchain/middleware/)
- [LangChain Agents 文档](https://python.langchain.com/docs/langchain/agents)
