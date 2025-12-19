"""
WeChat User Repository for WeChat login management
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..repository import BaseRepository
from ...models.wechat_user import WeChatUser


class WeChatUserRepository(BaseRepository[WeChatUser]):
    """Repository for WeChatUser with specialized queries"""

    def __init__(self, session: Session):
        super().__init__(session, WeChatUser)

    def get_by_openid(self, openid: str) -> Optional[WeChatUser]:
        """
        Get WeChat user by OpenID

        Args:
            openid: WeChat OpenID

        Returns:
            WeChatUser instance or None if not found
        """
        return (
            self.session.query(WeChatUser)
            .filter(WeChatUser.openid == openid)
            .first()
        )

    def get_by_unionid(self, unionid: str) -> Optional[WeChatUser]:
        """
        Get WeChat user by UnionID

        Args:
            unionid: WeChat UnionID

        Returns:
            WeChatUser instance or None if not found
        """
        return (
            self.session.query(WeChatUser)
            .filter(WeChatUser.unionid == unionid)
            .first()
        )

    def get_by_admin_user_id(self, admin_user_id: int) -> Optional[WeChatUser]:
        """
        Get WeChat user by bound admin user ID

        Args:
            admin_user_id: Admin user ID

        Returns:
            WeChatUser instance or None if not found
        """
        return (
            self.session.query(WeChatUser)
            .filter(WeChatUser.admin_user_id == admin_user_id)
            .first()
        )

    def create_or_update_wechat_user(
        self,
        openid: str,
        unionid: Optional[str] = None,
        session_key: Optional[str] = None,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        gender: int = 0,
        city: Optional[str] = None,
        province: Optional[str] = None,
        country: Optional[str] = None,
        language: str = "zh_CN",
        extra_info: Optional[Dict[str, Any]] = None
    ) -> WeChatUser:
        """
        Create or update a WeChat user

        Args:
            openid: WeChat OpenID
            unionid: WeChat UnionID (optional)
            session_key: WeChat session key (optional)
            nickname: WeChat nickname (optional)
            avatar_url: WeChat avatar URL (optional)
            gender: Gender (0=unknown, 1=male, 2=female)
            city: City (optional)
            province: Province (optional)
            country: Country (optional)
            language: Language (default: zh_CN)
            extra_info: Additional info in dictionary (optional)

        Returns:
            WeChatUser: Created or updated user instance
        """
        # Check if user exists
        wechat_user = self.get_by_openid(openid)

        if wechat_user is None:
            # Create new user
            wechat_user = WeChatUser(
                openid=openid,
                unionid=unionid,
                session_key=session_key,
                session_expires_at=datetime.utcnow() + timedelta(hours=24),  # WeChat session key expires in 24 hours
                nickname=nickname,
                avatar_url=avatar_url,
                gender=gender,
                city=city,
                province=province,
                country=country,
                language=language,
                login_count=1,
                last_login_at=datetime.utcnow(),
                extra_info=str(extra_info) if extra_info else None
            )
            self.session.add(wechat_user)
        else:
            # Update existing user
            if unionid:
                wechat_user.unionid = unionid
            if session_key:
                wechat_user.session_key = session_key
                wechat_user.session_expires_at = datetime.utcnow() + timedelta(hours=24)
            if nickname:
                wechat_user.nickname = nickname
            if avatar_url:
                wechat_user.avatar_url = avatar_url
            if gender:
                wechat_user.gender = gender
            if city:
                wechat_user.city = city
            if province:
                wechat_user.province = province
            if country:
                wechat_user.country = country
            if language:
                wechat_user.language = language

            # Update login tracking
            wechat_user.login_count = (wechat_user.login_count or 0) + 1
            wechat_user.last_login_at = datetime.utcnow()

            # Update extra info if provided
            if extra_info:
                import json
                current_info = {}
                if wechat_user.extra_info:
                    try:
                        current_info = json.loads(wechat_user.extra_info)
                    except:
                        pass
                current_info.update(extra_info)
                wechat_user.extra_info = json.dumps(current_info)

        self.session.flush()
        return wechat_user

    def bind_admin_user(self, openid: str, admin_user_id: int) -> bool:
        """
        Bind WeChat user to admin user

        Args:
            openid: WeChat OpenID
            admin_user_id: Admin user ID to bind

        Returns:
            bool: True if bound successfully, False if user not found
        """
        wechat_user = self.get_by_openid(openid)
        if wechat_user is None:
            return False

        wechat_user.admin_user_id = admin_user_id
        self.session.flush()
        return True

    def unbind_admin_user(self, openid: str) -> bool:
        """
        Unbind WeChat user from admin user

        Args:
            openid: WeChat OpenID

        Returns:
            bool: True if unbound successfully, False if user not found
        """
        wechat_user = self.get_by_openid(openid)
        if wechat_user is None:
            return False

        wechat_user.admin_user_id = None
        self.session.flush()
        return True

    def deactivate_wechat_user(self, openid: str) -> bool:
        """
        Deactivate WeChat user

        Args:
            openid: WeChat OpenID

        Returns:
            bool: True if deactivated, False if user not found
        """
        wechat_user = self.get_by_openid(openid)
        if wechat_user is None:
            return False

        wechat_user.is_active = False
        self.session.flush()
        return True

    def activate_wechat_user(self, openid: str) -> bool:
        """
        Activate WeChat user

        Args:
            openid: WeChat OpenID

        Returns:
            bool: True if activated, False if user not found
        """
        wechat_user = self.get_by_openid(openid)
        if wechat_user is None:
            return False

        wechat_user.is_active = True
        self.session.flush()
        return True

    def is_session_valid(self, openid: str) -> bool:
        """
        Check if WeChat session is still valid

        Args:
            openid: WeChat OpenID

        Returns:
            bool: True if session is valid, False if expired or not found
        """
        wechat_user = self.get_by_openid(openid)
        if wechat_user is None or wechat_user.session_expires_at is None:
            return False

        return wechat_user.session_expires_at > datetime.utcnow()