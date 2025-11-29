"""
Chat API Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., description="用户查询内容")
    model_provider: str = Field(default="zhipu", description="LLM 提供商")


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str = Field(..., description="Agent 回复内容")
    status: str = Field(default="success", description="响应状态")
    error: Optional[str] = Field(default=None, description="错误信息")
