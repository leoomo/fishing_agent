"""
WeChat user model for WeChat login integration
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin


class WeChatUser(Base, TimestampMixin):
    """WeChat user model for WeChat login integration"""

    __tablename__ = 'wechat_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), unique=True, nullable=False, index=True, comment="WeChat OpenID")
    unionid = Column(String(100), index=True, comment="WeChat UnionID (for cross-app integration)")
    nickname = Column(String(100), comment="WeChat nickname")
    avatar_url = Column(String(500), comment="WeChat avatar URL")
    gender = Column(Integer, default=0, comment="Gender: 0=unknown, 1=male, 2=female")
    city = Column(String(50), comment="City")
    province = Column(String(50), comment="Province")
    country = Column(String(50), comment="Country")
    language = Column(String(20), default="zh_CN", comment="Language")

    # Session information
    session_key = Column(String(100), comment="WeChat session key")
    session_expires_at = Column(DateTime, comment="Session key expiration time")

    # User binding
    admin_user_id = Column(Integer, ForeignKey('admin_users.id'), comment="Bound admin user ID")
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether WeChat login is active")

    # Login tracking
    last_login_at = Column(DateTime, comment="Last login time")
    login_count = Column(Integer, default=0, comment="Total login count")

    # Additional WeChat information (JSON format)
    extra_info = Column(Text, comment="Additional WeChat user info in JSON format")

    # Relationships
    admin_user = relationship("AdminUser", backref="wechat_bindings", lazy='noload')

    def __repr__(self):
        return f"<WeChatUser(id={self.id}, openid='{self.openid}', nickname='{self.nickname}')>"

    def to_dict(self, include_session=False, include_extra=False):
        """Convert to dictionary representation"""
        result = {
            'id': self.id,
            'openid': self.openid,
            'unionid': self.unionid,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'gender': self.gender,
            'city': self.city,
            'province': self.province,
            'country': self.country,
            'language': self.language,
            'admin_user_id': self.admin_user_id,
            'is_active': self.is_active,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_session:
            result['session_key'] = self.session_key
            result['session_expires_at'] = self.session_expires_at.isoformat() if self.session_expires_at else None

        if include_extra:
            result['extra_info'] = self.extra_info

        return result