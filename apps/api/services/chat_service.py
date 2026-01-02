"""
Chat Service - Business logic for chat sessions and messages
"""
import logging
from typing import Dict, Optional, List, Generator
from datetime import datetime

from apps.api.orm.session import get_db_session
from apps.api.models.chat import ChatSession, ChatMessage
from packages.agents.fishing import create_agent
from packages.agents.agent_component.monitoring import MonitoringCallback

logger = logging.getLogger(__name__)


# Default suggested questions for fishing assistant
DEFAULT_SUGGESTIONS = [
    {"id": 1, "question": "今天杭州钓鱼怎么样？", "category": "fishing"},
    {"id": 2, "question": "明天的天气适合路亚吗？", "category": "weather"},
    {"id": 3, "question": "推荐一款适合新手的路亚竿", "category": "equipment"},
    {"id": 4, "question": "钓鲈鱼用什么饵料最好？", "category": "technique"},
    {"id": 5, "question": "这周末哪天最适合出钓？", "category": "fishing"},
    {"id": 6, "question": "帮我对比几款渔轮", "category": "equipment"},
]


class ChatService:
    """Chat service for managing sessions and messages"""

    def __init__(self, model_provider: str = "qwen", user_id: Optional[int] = None, session_id: Optional[int] = None):
        self.model_provider = model_provider
        self.user_id = user_id
        self.session_id = session_id
        self._agent = None

    @property
    def agent(self):
        """Lazy load agent"""
        if self._agent is None:
            self._agent = create_agent(
                model_provider=self.model_provider,
                enable_monitoring=True,
                user_id=self.user_id,
                session_id=self.session_id,
                verbose_callbacks=False
            )
        return self._agent

    # ============ Session Operations ============

    def create_session(self, user_id: Optional[int] = None, title: str = "新对话") -> Dict:
        """
        Create a new chat session

        Args:
            user_id: User ID (optional)
            title: Session title

        Returns:
            dict: Created session info
        """
        with get_db_session() as session:
            chat_session = ChatSession(
                user_id=user_id or 0,
                title=title,
                is_active=True
            )
            session.add(chat_session)
            session.flush()

            result = chat_session.to_dict()
            logger.info(f"Created session: {chat_session.id}")
            return result

    def get_session(self, session_id: int) -> Optional[Dict]:
        """
        Get session by ID

        Args:
            session_id: Session ID

        Returns:
            dict: Session info or None
        """
        with get_db_session() as session:
            chat_session = session.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()

            if chat_session:
                return chat_session.to_dict()
            return None

    def list_sessions(
        self,
        user_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict:
        """
        List chat sessions for a user

        Args:
            user_id: User ID filter
            limit: Max results
            offset: Pagination offset

        Returns:
            dict: Sessions list with total count
        """
        from sqlalchemy import func

        with get_db_session() as session:
            query = session.query(ChatSession).filter(ChatSession.is_active == True)

            if user_id is not None:
                query = query.filter(ChatSession.user_id == user_id)

            total = query.count()
            sessions = query.order_by(ChatSession.updated_at.desc()) \
                           .offset(offset).limit(limit).all()

            # 获取每个会话的消息数量
            session_ids = [s.id for s in sessions]
            if session_ids:
                message_counts = dict(
                    session.query(ChatMessage.session_id, func.count(ChatMessage.id))
                    .filter(ChatMessage.session_id.in_(session_ids))
                    .group_by(ChatMessage.session_id)
                    .all()
                )
            else:
                message_counts = {}

            # 将消息数量添加到会话字典中
            result_sessions = []
            for s in sessions:
                session_dict = s.to_dict()
                session_dict['message_count'] = message_counts.get(s.id, 0)
                result_sessions.append(session_dict)

            return {
                "sessions": result_sessions,
                "total": total
            }

    def cleanup_empty_sessions(self, user_id: int) -> int:
        """
        清理用户的空会话（无消息的会话）

        Args:
            user_id: 用户ID

        Returns:
            int: 清理的会话数量
        """
        from sqlalchemy import exists

        with get_db_session() as session:
            # 找出用户的空会话
            has_messages = exists().where(ChatMessage.session_id == ChatSession.id)
            empty_sessions = session.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True,
                ~has_messages
            ).all()

            count = 0
            for s in empty_sessions:
                s.is_active = False
                count += 1

            if count > 0:
                logger.info(f"Cleaned up {count} empty sessions for user {user_id}")

            return count

    def update_session(self, session_id: int, title: str) -> Optional[Dict]:
        """
        Update session title

        Args:
            session_id: Session ID
            title: New title

        Returns:
            dict: Updated session info
        """
        with get_db_session() as session:
            chat_session = session.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()

            if chat_session:
                chat_session.title = title
                session.flush()
                return chat_session.to_dict()
            return None

    def delete_session(self, session_id: int) -> bool:
        """
        Delete (soft delete) a session

        Args:
            session_id: Session ID

        Returns:
            bool: Success status
        """
        with get_db_session() as session:
            chat_session = session.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()

            if chat_session:
                chat_session.is_active = False
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    # ============ Message Operations ============

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        tool_calls: Optional[str] = None
    ) -> Dict:
        """
        Add a message to a session

        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            tool_calls: Tool calls JSON (optional)

        Returns:
            dict: Created message info
        """
        with get_db_session() as session:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                tool_calls=tool_calls
            )
            session.add(message)
            session.flush()

            # Update session timestamp
            chat_session = session.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            if chat_session:
                chat_session.updated_at = datetime.utcnow()

                # Auto-generate title from first user message
                if role == "user" and chat_session.title == "新对话":
                    chat_session.title = self._generate_title(content)

            # Convert to dict before the session closes
            result = message.to_dict()
            return result

    def get_messages(self, session_id: int, limit: int = 100, offset: int = 0) -> Dict:
        """
        Get messages for a session

        Args:
            session_id: Session ID
            limit: Max results
            offset: Pagination offset

        Returns:
            dict: Messages list with total count
        """
        with get_db_session() as session:
            query = session.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            )

            total = query.count()
            messages = query.order_by(ChatMessage.created_at.asc()) \
                           .offset(offset).limit(limit).all()

            return {
                "messages": [m.to_dict() for m in messages],
                "total": total
            }

    def clear_messages(self, session_id: int) -> bool:
        """
        Clear all messages in a session

        Args:
            session_id: Session ID

        Returns:
            bool: Success status
        """
        with get_db_session() as session:
            deleted = session.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).delete()

            logger.info(f"Cleared {deleted} messages from session {session_id}")
            return deleted > 0

    # ============ Chat Operations ============

    def chat(self, message: str, session_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict:
        """
        Send a message and get AI response (non-streaming)

        Args:
            message: User message
            session_id: Session ID (creates new if not provided)
            user_id: User ID

        Returns:
            dict: Response with session and message info
        """
        # Create or get session
        if session_id is None:
            session_data = self.create_session(user_id=user_id)
            session_id = session_data["id"]

        # Add user message
        user_msg = self.add_message(session_id, "user", message)

        # Get AI response
        query = message
        if user_id:
            query = f"[USER_ID:{user_id}] {message}"

        response = self.agent.run(query)

        # Add assistant message
        assistant_msg = self.add_message(session_id, "assistant", response)

        return {
            "session_id": session_id,
            "user_message": user_msg,
            "assistant_message": assistant_msg
        }

    def chat_stream(
        self,
        message: str,
        session_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        Send a message and get AI response (streaming)

        Args:
            message: User message
            session_id: Session ID (creates new if not provided)
            user_id: User ID

        Yields:
            dict: Streaming chunks with content and delta
        """
        # Create or get session
        if session_id is None:
            session_data = self.create_session(user_id=user_id)
            session_id = session_data["id"]

        # Add user message
        self.add_message(session_id, "user", message)

        # Get AI response stream
        query = message
        if user_id:
            query = f"[USER_ID:{user_id}] {message}"

        accumulated_content = ""

        for chunk in self.agent.stream(query):
            accumulated_content += chunk
            yield {
                "session_id": session_id,
                "content": accumulated_content,
                "delta": chunk
            }

        # Save complete response
        self.add_message(session_id, "assistant", accumulated_content)

        # Yield final done signal
        yield {"session_id": session_id, "done": True}

    # ============ Suggestions ============

    def get_suggestions(self, category: Optional[str] = None) -> List[Dict]:
        """
        Get suggested questions

        Args:
            category: Category filter

        Returns:
            list: Suggested questions
        """
        if category:
            return [q for q in DEFAULT_SUGGESTIONS if q["category"] == category]
        return DEFAULT_SUGGESTIONS

    # ============ Helpers ============

    def _generate_title(self, first_message: str) -> str:
        """Generate session title from first message"""
        # Truncate to 20 chars and add ellipsis if needed
        if len(first_message) > 20:
            return first_message[:20] + "..."
        return first_message
