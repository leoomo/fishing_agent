import json
import logging
from typing import Dict, Optional, List

from apps.api.orm.session import get_db_session
from apps.api.models.system import SystemConfig
from apps.api.utils.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

# 装备选项默认配置（带备注）
EQUIPMENT_OPTION_DEFAULTS = {
    'equipment.rod.power_options': {
        'value': [
            {'value': 'UL', 'note': '超轻调，适合微物钓法'},
            {'value': 'L', 'note': '轻调，适合小型鱼类'},
            {'value': 'ML', 'note': '中轻调，通用型'},
            {'value': 'M', 'note': '中调，平衡性好'},
            {'value': 'MH', 'note': '中硬调，适合中大型鱼'},
            {'value': 'H', 'note': '硬调，适合大型鱼'},
            {'value': 'XH', 'note': '超硬调，适合巨物'},
        ],
        'description': '鱼竿调性选项（从超软到超硬）',
    },
    'equipment.rod.action_options': {
        'value': [
            {'value': 'Fast', 'note': '快调，恢复迅速'},
            {'value': 'Medium', 'note': '中调，平衡性好'},
            {'value': 'Slow', 'note': '慢调，弯曲幅度大'},
        ],
        'description': '鱼竿动作选项（弯曲恢复速度）',
    },
    'equipment.rod.action_options_cn': {
        'value': [
            {'value': '慢调', 'note': '弯曲幅度大，适合溜鱼'},
            {'value': '中调', 'note': '平衡型，适用范围广'},
            {'value': '快调', 'note': '恢复快，灵敏度高'},
            {'value': '超快调', 'note': '极速恢复，精准度高'},
        ],
        'description': '鱼竿动作选项（中文表述）',
    },
    'equipment.user_level_options': {
        'value': [
            {'value': '新手', 'note': '入门级用户'},
            {'value': '进阶', 'note': '有一定经验的用户'},
            {'value': '高手', 'note': '经验丰富的专业用户'},
        ],
        'description': '装备适合的用户水平',
    },
    'equipment.category_options': {
        'value': [
            {'value': '鱼竿', 'note': '钓鱼主要工具'},
            {'value': '渔轮', 'note': '收放线装置'},
            {'value': '鱼线', 'note': '连接鱼竿和鱼钩'},
            {'value': '拟饵', 'note': '模拟饵料吸引鱼类'},
        ],
        'description': '装备分类选项',
    },
    'equipment.reel.type_options': {
        'value': [
            {'value': 'spinning', 'note': '纺车轮，适合新手'},
            {'value': 'baitcasting', 'note': '水滴轮，精准抛投'},
            {'value': 'fly', 'note': '飞蝇轮，飞蝇钓专用'},
        ],
        'description': '渔轮类型选项',
    },
    'equipment.line.type_options': {
        'value': [
            {'value': 'PE', 'note': '编织线，强度高'},
            {'value': '尼龙', 'note': '尼龙线，延展性好'},
            {'value': '碳线', 'note': '碳素线，隐蔽性强'},
            {'value': '钢丝', 'note': '钢丝线，防咬断'},
        ],
        'description': '鱼线类型选项',
    },
}


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

    def init_equipment_options(self) -> Dict[str, bool]:
        """
        初始化装备选项默认配置

        只创建不存在的配置，不覆盖已存在的配置。

        Returns:
            dict: 配置键 -> 是否创建 (True=新建, False=已存在)
        """
        results = {}

        with get_db_session() as session:
            for config_key, config_data in EQUIPMENT_OPTION_DEFAULTS.items():
                # 检查是否已存在
                existing = session.query(SystemConfig).filter_by(
                    config_key=config_key
                ).first()

                if existing:
                    results[config_key] = False
                    logger.debug(f"配置已存在，跳过: {config_key}")
                    continue

                # 创建新配置
                config = SystemConfig(
                    config_key=config_key,
                    config_value=json.dumps(config_data['value'], ensure_ascii=False),
                    config_type='system',
                    description=config_data['description'],
                    is_encrypted=False
                )
                session.add(config)
                results[config_key] = True
                logger.info(f"创建装备选项配置: {config_key}")

            session.commit()

        return results


def init_default_equipment_options():
    """
    初始化装备选项默认配置的便捷函数

    可在应用启动时调用，确保默认配置存在。
    """
    service = ConfigService()
    results = service.init_equipment_options()

    created = [k for k, v in results.items() if v]
    skipped = [k for k, v in results.items() if not v]

    if created:
        logger.info(f"创建了 {len(created)} 个装备选项配置")
    if skipped:
        logger.debug(f"跳过了 {len(skipped)} 个已存在的配置")

    return results
