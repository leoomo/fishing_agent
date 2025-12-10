import json
import logging
from typing import Dict, Optional, List

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import SystemConfig
from apps.api.utils.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)


class ConfigService:
    """配置管理服务"""

    def list_configs(self, config_type: Optional[str] = None) -> List[Dict]:
        """
        查询配置列表

        Args:
            config_type: 配置类型过滤

        Returns:
            list: 配置列表
        """
        with get_db_session() as session:
            query = session.query(SystemConfig)

            if config_type:
                query = query.filter(SystemConfig.config_type == config_type)

            configs = query.all()

            result = []
            for config in configs:
                # 解密配置值（如果加密）
                config_value = config.config_value
                if config.is_encrypted:
                    try:
                        config_value = decrypt_value(config_value)
                    except:
                        config_value = "***加密内容***"

                # 解析 JSON
                try:
                    config_value = json.loads(config_value)
                except:
                    pass  # 保持字符串

                result.append({
                    "id": config.id,
                    "config_key": config.config_key,
                    "config_value": config_value,
                    "config_type": config.config_type,
                    "description": config.description,
                    "is_encrypted": config.is_encrypted,
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat()
                })

            return result

    def get_config(self, config_key: str) -> Optional[Dict]:
        """
        获取配置

        Args:
            config_key: 配置键

        Returns:
            dict: 配置信息
        """
        configs = self.list_configs()
        return next((c for c in configs if c["config_key"] == config_key), None)

    def create_config(
        self,
        config_key: str,
        config_value: str,
        config_type: str,
        description: Optional[str] = None,
        is_encrypted: bool = False
    ) -> Dict:
        """
        创建配置

        Args:
            config_key: 配置键
            config_value: 配置值（JSON字符串）
            config_type: 配置类型
            description: 描述
            is_encrypted: 是否加密

        Returns:
            dict: 创建的配置

        Raises:
            ValueError: 配置键已存在
        """
        with get_db_session() as session:
            # 检查是否存在
            existing = session.query(SystemConfig).filter_by(
                config_key=config_key
            ).first()

            if existing:
                raise ValueError(f"配置键已存在: {config_key}")

            # 加密配置值（如果需要）
            stored_value = config_value
            if is_encrypted:
                stored_value = encrypt_value(config_value)

            # 创建配置
            config = SystemConfig(
                config_key=config_key,
                config_value=stored_value,
                config_type=config_type,
                description=description,
                is_encrypted=is_encrypted
            )

            session.add(config)
            session.commit()
            session.refresh(config)

            # 返回解密后的值
            return self.get_config(config_key)

    def update_config(
        self,
        config_key: str,
        config_value: str,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        更新配置

        Args:
            config_key: 配置键
            config_value: 配置值
            description: 描述

        Returns:
            dict: 更新后的配置
        """
        with get_db_session() as session:
            config = session.query(SystemConfig).filter_by(
                config_key=config_key
            ).first()

            if not config:
                return None

            # 加密配置值（如果需要）
            stored_value = config_value
            if config.is_encrypted:
                stored_value = encrypt_value(config_value)

            # 更新
            config.config_value = stored_value
            if description is not None:
                config.description = description

            session.commit()

            return self.get_config(config_key)

    def delete_config(self, config_key: str) -> bool:
        """
        删除配置

        Args:
            config_key: 配置键

        Returns:
            bool: 是否成功
        """
        with get_db_session() as session:
            config = session.query(SystemConfig).filter_by(
                config_key=config_key
            ).first()

            if not config:
                return False

            session.delete(config)
            session.commit()

            return True

    def test_api_key(self, api_provider: str, api_key: str) -> Dict:
        """
        测试 API 密钥有效性

        Args:
            api_provider: API 提供商
            api_key: API 密钥

        Returns:
            dict: 测试结果
        """
        try:
            if api_provider == "dashscope":
                # 测试通义千问 API
                import requests
                response = requests.get(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5
                )
                valid = response.status_code != 401

            elif api_provider == "caiyun":
                # 测试彩云天气 API
                import requests
                response = requests.get(
                    f"https://api.caiyunapp.com/v2.6/{api_key}/120.0,30.0/realtime",
                    timeout=5
                )
                valid = response.status_code == 200

            elif api_provider == "amap":
                # 测试高德地图 API
                import requests
                response = requests.get(
                    f"https://restapi.amap.com/v3/geocode/geo?key={api_key}&address=北京",
                    timeout=5
                )
                valid = response.status_code == 200 and response.json().get("status") == "1"

            else:
                return {"valid": False, "message": f"不支持的 API 提供商: {api_provider}"}

            return {
                "valid": valid,
                "message": "API 密钥有效" if valid else "API 密钥无效"
            }

        except Exception as e:
            return {
                "valid": False,
                "message": f"测试失败: {str(e)}"
            }
