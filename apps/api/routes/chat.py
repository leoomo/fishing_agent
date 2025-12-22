"""
Chat API Routes - Adapting to mobile app expected endpoints

Endpoints:
- POST /message           -> Non-streaming message
- POST /message/stream    -> SSE streaming message
- GET  /sessions          -> List sessions
- POST /sessions          -> Create session
- GET  /sessions/{id}     -> Get session
- PUT  /sessions/{id}     -> Update session
- DELETE /sessions/{id}   -> Delete session
- GET  /sessions/{id}/messages -> Get messages
- DELETE /sessions/{id}/messages -> Clear messages
- GET  /suggestions       -> Get suggested questions
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from ..auth.dependencies import get_current_user, CurrentUser
from ..schemas.chat_session import (
    MessageRequest,
    MessageResponse,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    MessageListResponse,
    SuggestionsResponse,
    SuggestedQuestion
)
from ..services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instance for non-LLM operations
chat_service = ChatService()

# ============ Message Endpoints ============

@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Send a message and get AI response (non-streaming)

    This endpoint is for platforms that don't support SSE.
    """
    try:
        # Create chat service instance for this user
        service = ChatService(
            model_provider=request.model_provider,
            user_id=current_user.user_id,
            session_id=request.session_id
        )

        result = service.chat(
            message=request.message,
            session_id=request.session_id,
            user_id=current_user.user_id  # 使用认证用户ID
        )

        return MessageResponse(
            id=result["assistant_message"]["id"],
            session_id=result["session_id"],
            role="assistant",
            content=result["assistant_message"]["content"],
            created_at=result["assistant_message"]["created_at"]
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/stream")
async def send_message_stream(
    request: MessageRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Send a message and get AI response (streaming via SSE)

    This is the primary endpoint for mobile app chat.
    Returns Server-Sent Events with format:
        data: {"content": "accumulated", "delta": "new chunk"}
        data: [DONE]
    """
    # 捕获用户ID以在生成器中使用
    user_id = current_user.user_id

    async def generate():
        try:
            # Create chat service instance for this user
            service = ChatService(
                model_provider=request.model_provider,
                user_id=current_user.user_id,
                session_id=request.session_id
            )

            for chunk in service.chat_stream(
                message=request.message,
                session_id=request.session_id,
                user_id=user_id  # 使用认证用户ID
            ):
                if chunk.get("done"):
                    yield "data: [DONE]\n\n"
                else:
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============ Session Endpoints ============

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    List chat sessions for current user
    """
    result = chat_service.list_sessions(user_id=current_user.user_id, limit=limit, offset=offset)
    return SessionListResponse(
        sessions=[SessionResponse(**s) for s in result["sessions"]],
        total=result["total"]
    )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new chat session for current user
    """
    result = chat_service.create_session(
        user_id=current_user.user_id,  # 使用认证用户ID
        title=request.title or "新对话"
    )
    return SessionResponse(**result)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get session by ID (with ownership verification)
    """
    result = chat_service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    # 验证会话归属
    if result.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    return SessionResponse(**result)


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    request: SessionUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update session title (with ownership verification)
    """
    # 先验证会话归属
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权修改此会话")

    result = chat_service.update_session(session_id, request.title)
    return SessionResponse(**result)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a session (soft delete, with ownership verification)
    """
    # 先验证会话归属
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权删除此会话")

    success = chat_service.delete_session(session_id)
    return {"success": True, "message": "Session deleted"}


# ============ Message History Endpoints ============

@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get messages for a session (with ownership verification)
    """
    # Verify session exists and ownership
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    result = chat_service.get_messages(session_id, limit=limit, offset=offset)
    return MessageListResponse(
        messages=[MessageResponse(**m) for m in result["messages"]],
        total=result["total"]
    )


@router.delete("/sessions/{session_id}/messages")
async def clear_session_messages(
    session_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Clear all messages in a session (with ownership verification)
    """
    # Verify session exists and ownership
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权操作此会话")

    success = chat_service.clear_messages(session_id)
    return {"success": success, "message": "Messages cleared" if success else "No messages to clear"}


# ============ Suggestions Endpoint ============

@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get suggested questions for the chat

    Categories: fishing, weather, equipment, technique
    """
    suggestions = chat_service.get_suggestions(category)
    return SuggestionsResponse(
        suggestions=[SuggestedQuestion(**s) for s in suggestions]
    )
