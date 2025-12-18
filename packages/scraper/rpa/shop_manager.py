"""
店铺配置管理器
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ShopManager:
    """淘宝店铺配置管理"""

    def __init__(self, config_path: str = "shared/data/shops/shops.json"):
        """
        初始化

        Args:
            config_path: 店铺配置文件路径
        """
        self.config_path = Path(config_path)

        # 确保父目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化配置文件
        if not self.config_path.exists():
            self._init_config()

        logger.info(f"初始化 ShopManager: {self.config_path}")

    def _init_config(self):
        """初始化空配置文件"""
        initial_data = {"shops": []}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        logger.info(f"创建店铺配置文件: {self.config_path}")

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {"shops": []}

    def _save_config(self, data: Dict):
        """保存配置文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

    def add_shop(
        self,
        shop_url: str,
        shop_name: str,
        shop_id: Optional[str] = None,
        categories: Optional[List[str]] = None,
        is_default: bool = False,
    ) -> bool:
        """
        添加店铺

        Args:
            shop_url: 店铺URL
            shop_name: 店铺名称
            shop_id: 店铺ID（可选，自动提取）
            categories: 店铺分类列表（可选）
            is_default: 是否为默认店铺

        Returns:
            是否成功
        """
        # 提取店铺ID
        if not shop_id:
            shop_id = self._extract_shop_id(shop_url)

        # 检查是否已存在
        config = self._load_config()
        for shop in config["shops"]:
            if shop["shop_id"] == shop_id:
                logger.warning(f"店铺已存在: {shop_name} ({shop_id})")
                return False

        # 构建店铺数据
        shop_data = {
            "shop_id": shop_id,
            "shop_name": shop_name,
            "shop_url": shop_url,
            "categories": categories or [],
            "is_default": is_default,
            "created_at": datetime.now().isoformat(),
            "last_crawled": None,
        }

        # 添加到配置
        config["shops"].append(shop_data)
        self._save_config(config)

        logger.info(f"✅ 添加店铺: {shop_name} ({shop_id})")
        return True

    def remove_shop(self, shop_id: str) -> bool:
        """
        删除店铺

        Args:
            shop_id: 店铺ID

        Returns:
            是否成功
        """
        config = self._load_config()
        original_count = len(config["shops"])

        config["shops"] = [s for s in config["shops"] if s["shop_id"] != shop_id]

        if len(config["shops"]) < original_count:
            self._save_config(config)
            logger.info(f"✅ 删除店铺: {shop_id}")
            return True
        else:
            logger.warning(f"店铺不存在: {shop_id}")
            return False

    def update_shop(
        self,
        shop_id: str,
        shop_name: Optional[str] = None,
        categories: Optional[List[str]] = None,
        is_default: Optional[bool] = None,
    ) -> bool:
        """
        更新店铺信息

        Args:
            shop_id: 店铺ID
            shop_name: 新的店铺名称（可选）
            categories: 新的分类列表（可选）
            is_default: 新的默认状态（可选）

        Returns:
            是否成功
        """
        config = self._load_config()

        for shop in config["shops"]:
            if shop["shop_id"] == shop_id:
                if shop_name is not None:
                    shop["shop_name"] = shop_name
                if categories is not None:
                    shop["categories"] = categories
                if is_default is not None:
                    shop["is_default"] = is_default

                self._save_config(config)
                logger.info(f"✅ 更新店铺: {shop_id}")
                return True

        logger.warning(f"店铺不存在: {shop_id}")
        return False

    def mark_crawled(self, shop_id: str):
        """
        标记店铺已爬取

        Args:
            shop_id: 店铺ID
        """
        config = self._load_config()

        for shop in config["shops"]:
            if shop["shop_id"] == shop_id:
                shop["last_crawled"] = datetime.now().isoformat()
                self._save_config(config)
                logger.debug(f"标记店铺已爬取: {shop_id}")
                return

    def get_shop(self, shop_id: str) -> Optional[Dict]:
        """
        获取店铺信息

        Args:
            shop_id: 店铺ID

        Returns:
            店铺数据字典或None
        """
        config = self._load_config()

        for shop in config["shops"]:
            if shop["shop_id"] == shop_id:
                return shop

        return None

    def get_shop_by_url(self, shop_url: str) -> Optional[Dict]:
        """
        通过URL获取店铺信息

        Args:
            shop_url: 店铺URL

        Returns:
            店铺数据字典或None
        """
        shop_id = self._extract_shop_id(shop_url)
        return self.get_shop(shop_id)

    def list_shops(self, default_only: bool = False) -> List[Dict]:
        """
        列出所有店铺

        Args:
            default_only: 仅列出默认店铺

        Returns:
            店铺列表
        """
        config = self._load_config()

        if default_only:
            return [s for s in config["shops"] if s.get("is_default", False)]

        return config["shops"]

    def _extract_shop_id(self, shop_url: str) -> str:
        """
        从URL提取店铺ID

        Args:
            shop_url: 店铺URL

        Returns:
            店铺ID
        """
        import re

        # 提取淘宝店铺ID（从URL中提取）
        # 例如: https://xxx.taobao.com -> xxx
        # 例如: https://shop123456.taobao.com -> shop123456
        match = re.search(r"https?://([^.]+)\.taobao\.com", shop_url)
        if match:
            return match.group(1)

        # 如果无法提取，使用URL作为ID（截断）
        return shop_url[:50]
