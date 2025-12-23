"""
Chat-related models for session and message management
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ChatSession(Base, TimestampMixin):
    """Chat session model for storing conversation sessions"""

    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="User ID (can be null for anonymous)")
    title = Column(String(200), default="新对话", comment="Session title")
    is_active = Column(Boolean, default=True, comment="Whether session is active")

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title='{self.title}')>"

    def to_dict(self, include_messages=False):
        """Convert to dictionary representation"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_messages:
            result['messages'] = [msg.to_dict() for msg in self.messages]

        return result


class ChatMessage(Base, TimestampMixin):
    """Chat message model for storing individual messages"""

    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey('chat_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Parent session ID"
    )
    role = Column(String(20), nullable=False, comment="Message role: 'user' or 'assistant'")
    content = Column(Text, nullable=False, comment="Message content")
    tool_calls = Column(Text, nullable=True, comment="Tool calls JSON (for assistant messages)")

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<ChatMessage(id={self.id}, role='{self.role}', content='{content_preview}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'tool_calls': self.tool_calls,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
