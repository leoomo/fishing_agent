"""
WeChat login service
"""

import logging
import json
import requests
from typing import Optional, Dict, Any
from datetime import datetime

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository
from packages.agent_fishing.tools.lure.orm.repositories.wechat_user_repo import WeChatUserRepository
from ..auth.jwt import create_access_token

logger = logging.getLogger(__name__)


class WeChatService:
    """WeChat login service"""

    def __init__(self):
        self.app_id = None
        self.app_secret = None
        self.api_url = None
        self.auto_create_user = True
        self.default_role = "readonly"

    def initialize(self):
        """Initialize WeChat configuration from environment"""
        import os

        self.app_id = os.getenv("WECHAT_APP_ID") or os.getenv("WECHAT_APPID")
        self.app_secret = os.getenv("WECHAT_APP_SECRET") or os.getenv("WECHAT_SECRET")
        self.api_url = os.getenv("WECHAT_API_URL", "https://api.weixin.qq.com")
        self.auto_create_user = os.getenv("WECHAT_AUTO_CREATE_USER", "true").lower() == "true"
        self.default_role = os.getenv("WECHAT_DEFAULT_ROLE", "readonly")

        if not self.app_id or not self.app_secret:
            raise ValueError("微信配置缺失：请设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET 环境变量")

    async def code2session(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange code for session info

        Args:
            code: WeChat login code

        Returns:
            Dict containing openid, session_key, unionid (if available) or None if failed
        """
        url = f"{self.api_url}/sns/jscode2session"
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Check for error
            if "errcode" in data:
                error_msg = data.get("errmsg", "未知错误")
                logger.error(f"微信code2session失败: {data}")
                raise Exception(f"微信登录失败: {error_msg}")

            return {
                "openid": data.get("openid"),
                "session_key": data.get("session_key"),
                "unionid": data.get("unionid")
            }

        except requests.RequestException as e:
            logger.error(f"请求微信API失败: {e}")
            raise Exception("网络错误，请稍后重试")
        except Exception as e:
            logger.error(f"微信登录失败: {e}")
            raise

    async def login_or_create_user(
        self,
        code: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        gender: int = 0,
        city: Optional[str] = None,
        province: Optional[str] = None,
        country: Optional[str] = None,
        language: str = "zh_CN"
    ) -> Dict[str, Any]:
        """
        WeChat login or create user

        Args:
            code: WeChat login code
            nickname: User nickname (optional)
            avatar_url: Avatar URL (optional)
            gender: Gender (0=unknown, 1=male, 2=female)
            city: City (optional)
            province: Province (optional)
            country: Country (optional)
            language: Language (default: zh_CN)

        Returns:
            Dict containing access_token and user info
        """
        # Exchange code for session info
        session_info = await self.code2session(code)
        if not session_info or not session_info.get("openid"):
            raise Exception("获取微信用户信息失败")

        openid = session_info["openid"]
        session_key = session_info.get("session_key")
        unionid = session_info.get("unionid")

        with get_db_session() as db_session:
            wechat_repo = WeChatUserRepository(db_session)
            admin_repo = AdminUserRepository(db_session)

            # Create or update WeChat user
            wechat_user = wechat_repo.create_or_update_wechat_user(
                openid=openid,
                unionid=unionid,
                session_key=session_key,
                nickname=nickname,
                avatar_url=avatar_url,
                gender=gender,
                city=city,
                province=province,
                country=country,
                language=language,
                extra_info={
                    "login_time": datetime.utcnow().isoformat(),
                    "source": "wechat_miniprogram"
                }
            )

            # Check if WeChat user is bound to admin user
            admin_user = None
            if wechat_user.admin_user_id:
                admin_user = admin_repo.get(wechat_user.admin_user_id)
            elif self.auto_create_user and unionid:
                # Try to find admin user by unionid
                admin_user = self._find_admin_by_unionid(admin_repo, unionid)
                if admin_user:
                    # Bind WeChat user to admin user
                    wechat_repo.bind_admin_user(openid, admin_user.id)
                    wechat_user.admin_user_id = admin_user.id

            # If no admin user found and auto-create is enabled, create new admin user
            if not admin_user and self.auto_create_user:
                admin_user = self._create_admin_user(
                    admin_repo,
                    openid,
                    nickname,
                    avatar_url
                )
                # Bind WeChat user to admin user
                wechat_repo.bind_admin_user(openid, admin_user.id)
                wechat_user.admin_user_id = admin_user.id

            if not admin_user:
                raise Exception("用户账号未配置，请联系管理员")

            # Update last login time for admin user
            admin_repo.update_last_login(admin_user.id)

            # Generate JWT token
            token_data = {
                "user_id": admin_user.id,
                "username": admin_user.username,
                "role": admin_user.role,
                "openid": openid,
                "login_type": "wechat"
            }
            access_token = create_access_token(token_data)

            # Commit all changes
            db_session.commit()

            logger.info(f"微信登录成功: openid={openid}, admin_user_id={admin_user.id}")

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "user_id": admin_user.id,
                    "username": admin_user.username,
                    "email": admin_user.email,
                    "role": admin_user.role,
                    "full_name": admin_user.full_name,
                    "is_active": admin_user.is_active,
                    "last_login": admin_user.last_login,
                    "created_at": admin_user.created_at.isoformat() if admin_user.created_at else None,
                    "login_type": "wechat"
                },
                "wechat_info": {
                    "openid": openid,
                    "nickname": nickname,
                    "avatar_url": avatar_url
                }
            }

    def _find_admin_by_unionid(self, admin_repo: AdminUserRepository, unionid: str):
        """Find admin user by unionid"""
        # This would require adding wechat_unionid field to admin_users table
        # For now, return None
        # TODO: Implement after adding wechat_unionid field to admin_users
        return None

    def _create_admin_user(
        self,
        admin_repo: AdminUserRepository,
        openid: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None
    ):
        """Create admin user from WeChat info"""
        import bcrypt

        # Generate random password for WeChat users
        import secrets
        random_password = secrets.token_urlsafe(32)
        password_hash = bcrypt.hashpw(random_password.encode(), bcrypt.gensalt()).decode()

        # Generate unique username
        base_username = nickname or f"wx_{openid[:8]}"
        username = base_username
        counter = 1

        # Ensure username is unique
        while admin_repo.get_by_username(username):
            username = f"{base_username}_{counter}"
            counter += 1

        # Generate unique email
        email = f"wx_{openid}@wechat.local"
        counter_email = 1
        while admin_repo.get_by_email(email):
            email = f"wx_{openid}_{counter_email}@wechat.local"
            counter_email += 1

        # Create admin user
        admin_user = admin_repo.create_admin_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role=self.default_role,
            full_name=nickname,
            is_active=True
        )

        logger.info(f"为微信用户创建管理员账号: {username}")
        return admin_user

    async def bind_wechat_to_admin(
        self,
        admin_user_id: int,
        code: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bind WeChat to existing admin user

        Args:
            admin_user_id: Admin user ID
            code: WeChat login code
            nickname: User nickname (optional)
            avatar_url: Avatar URL (optional)

        Returns:
            Dict containing binding result
        """
        # Exchange code for session info
        session_info = await self.code2session(code)
        if not session_info or not session_info.get("openid"):
            raise Exception("获取微信用户信息失败")

        openid = session_info["openid"]
        session_key = session_info.get("session_key")
        unionid = session_info.get("unionid")

        with get_db_session() as db_session:
            wechat_repo = WeChatUserRepository(db_session)
            admin_repo = AdminUserRepository(db_session)

            # Check if admin user exists
            admin_user = admin_repo.get(admin_user_id)
            if not admin_user:
                raise Exception("管理员用户不存在")

            # Check if WeChat user is already bound
            existing_binding = wechat_repo.get_by_openid(openid)
            if existing_binding and existing_binding.admin_user_id:
                if existing_binding.admin_user_id != admin_user_id:
                    raise Exception("该微信账号已绑定其他用户")
                else:
                    # Already bound to this user
                    return {"message": "微信账号已绑定", "bound": True}

            # Create or update WeChat user and bind to admin
            wechat_user = wechat_repo.create_or_update_wechat_user(
                openid=openid,
                unionid=unionid,
                session_key=session_key,
                nickname=nickname,
                avatar_url=avatar_url
            )

            # Bind to admin user
            wechat_repo.bind_admin_user(openid, admin_user_id)

            # Update admin user with unionid if available
            if unionid and not admin_user.wechat_unionid:
                admin_user.wechat_unionid = unionid

            db_session.commit()

            logger.info(f"微信绑定成功: openid={openid}, admin_user_id={admin_user_id}")

            return {
                "message": "微信账号绑定成功",
                "bound": True,
                "wechat_info": {
                    "openid": openid,
                    "nickname": nickname,
                    "avatar_url": avatar_url
                }
            }


# Global instance
wechat_service = WeChatService()