"""
钓鱼 Agent API 路由
"""
from fastapi import APIRouter, HTTPException
from packages.agent_fishing import create_agent
from ..schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与钓鱼助手对话

    Args:
        request: 聊天请求，包含查询内容和模型提供商

    Returns:
        ChatResponse: Agent 的回复
    """
    try:
        agent = create_agent(model_provider=request.model_provider)
        response = agent.run(request.query)
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
    from packages.agent_fishing import get_all_tools

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
