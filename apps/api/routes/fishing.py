"""
钓鱼 Agent API 路由
"""
from fastapi import APIRouter, HTTPException
from packages.agents.fishing import create_agent
from ..schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与钓鱼助手对话

    Args:
        request: 聊天请求，包含查询内容、模型提供商和用户ID（可选）

    Returns:
        ChatResponse: Agent 的回复
    """
    try:
        agent = create_agent(model_provider=request.model_provider)

        # 如果提供了 user_id，注入到查询上下文
        query = request.query
        if request.user_id:
            query = f"[USER_ID:{request.user_id}] {query}"

        response = agent.run(query)
        return ChatResponse(response=response, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """
    列出所有可用工具

    Returns:
        工具列表
    """
    from packages.agents.fishing import get_all_tools

    tools = get_all_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in tools
        ]
    }
