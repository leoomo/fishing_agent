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

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

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

# Service instance
chat_service = ChatService()


# ============ Message Endpoints ============

@router.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """
    Send a message and get AI response (non-streaming)

    This endpoint is for platforms that don't support SSE.
    """
    try:
        result = chat_service.chat(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
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
async def send_message_stream(request: MessageRequest):
    """
    Send a message and get AI response (streaming via SSE)

    This is the primary endpoint for mobile app chat.
    Returns Server-Sent Events with format:
        data: {"content": "accumulated", "delta": "new chunk"}
        data: [DONE]
    """
    async def generate():
        try:
            for chunk in chat_service.chat_stream(
                message=request.message,
                session_id=request.session_id,
                user_id=request.user_id
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
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    List chat sessions for a user
    """
    result = chat_service.list_sessions(user_id=user_id, limit=limit, offset=offset)
    return SessionListResponse(
        sessions=[SessionResponse(**s) for s in result["sessions"]],
        total=result["total"]
    )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """
    Create a new chat session
    """
    result = chat_service.create_session(
        user_id=request.user_id,
        title=request.title or "新对话"
    )
    return SessionResponse(**result)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int):
    """
    Get session by ID
    """
    result = chat_service.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**result)


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: int, request: SessionUpdate):
    """
    Update session title
    """
    result = chat_service.update_session(session_id, request.title)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**result)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int):
    """
    Delete a session (soft delete)
    """
    success = chat_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "message": "Session deleted"}


# ============ Message History Endpoints ============

@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: int,
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get messages for a session
    """
    # Verify session exists
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = chat_service.get_messages(session_id, limit=limit, offset=offset)
    return MessageListResponse(
        messages=[MessageResponse(**m) for m in result["messages"]],
        total=result["total"]
    )


@router.delete("/sessions/{session_id}/messages")
async def clear_session_messages(session_id: int):
    """
    Clear all messages in a session
    """
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
