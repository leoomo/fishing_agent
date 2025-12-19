"""
Chat Session API Schemas - Adapting to mobile app expected format
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ Message Schemas ============

class MessageRequest(BaseModel):
    """Message request from mobile app"""
    message: str = Field(..., description="Message content")
    session_id: Optional[int] = Field(None, description="Session ID (creates new if not provided)")
    user_id: Optional[int] = Field(None, description="User ID")
    model_provider: str = Field(default="zhipu", description="LLM provider")


class MessageResponse(BaseModel):
    """Message response (for non-streaming)"""
    id: int = Field(..., description="Message ID")
    session_id: int = Field(..., description="Session ID")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Creation timestamp")


class StreamChunk(BaseModel):
    """Streaming chunk format for SSE"""
    content: str = Field(..., description="Accumulated content")
    delta: str = Field(..., description="New content chunk")


# ============ Session Schemas ============

class SessionCreate(BaseModel):
    """Create new session request"""
    title: Optional[str] = Field(default="新对话", description="Session title")
    user_id: Optional[int] = Field(None, description="User ID")


class SessionUpdate(BaseModel):
    """Update session request"""
    title: str = Field(..., description="New session title")


class SessionResponse(BaseModel):
    """Session response"""
    id: int = Field(..., description="Session ID")
    user_id: Optional[int] = Field(None, description="User ID")
    title: str = Field(..., description="Session title")
    is_active: bool = Field(default=True, description="Whether session is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Session list response"""
    sessions: List[SessionResponse] = Field(default_factory=list, description="List of sessions")
    total: int = Field(default=0, description="Total count")


class MessageListResponse(BaseModel):
    """Message list response"""
    messages: List[MessageResponse] = Field(default_factory=list, description="List of messages")
    total: int = Field(default=0, description="Total count")


# ============ Suggested Questions ============

class SuggestedQuestion(BaseModel):
    """Suggested question item"""
    id: int = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    category: str = Field(default="general", description="Question category")


class SuggestionsResponse(BaseModel):
    """Suggested questions response"""
    suggestions: List[SuggestedQuestion] = Field(default_factory=list, description="List of suggestions")
