"""
淘宝商品信息提取器

配置驱动的字段提取，减少重复代码。
"""

import re
import logging
from typing import Optional, Any, Dict, List
from playwright.sync_api import Page

from packages.scraper.spider.base import CrawlItem as EquipmentData

logger = logging.getLogger(__name__)


class TaobaoProductExtractor:
    """淘宝商品信息提取器"""

    # 字段提取配置（集中管理所有选择器）
    FIELD_CONFIGS = {
        'name': {
            'selectors': [
                "xpath=//div[@id='tbpcDetail_SkuPanelBody']//span[contains(@class, 'mainTitle--')]",
                ".product-title",
                "h1.tb-main-title",
            ],
            'attribute': 'title',  # 提取 title 属性
            'required': True,
            'fallback_from_title': True,  # 失败时从页面标题提取
        },
        'price': {
            'selectors': [
                ".price",
                "[class*='price']",
                ".tm-price",
                ".tb-price",
            ],
            'parser': lambda text: re.search(r'[\d.]+', str(text)).group() if text and re.search(r'[\d.]+', str(text)) else None,
            'required': False,
        },
        'brand': {
            'selectors': [
                "[data-spm='brand']",
                ".brand",
                "[class*='brand']",
                ".tb-property",
            ],
            'max_length': 20,
            'required': False,
        },
        'description': {
            'selectors': [
                "[data-spm='description']",
                ".tb-description",
                ".description",
                "[class*='desc']",
                ".detail-desc",
            ],
            'max_length': 500,
            'min_length': 10,
            'required': False,
        },
        'images': {
            'selectors': [
                "xpath=//div[@id='imageTextInfo-content']//img",
                ".detail-gallery img",
                ".tb-gallery img",
            ],
            'attributes': ['data-src', 'src'],  # 按顺序尝试
            'multiple': True,  # 返回列表
            'required': False,
        },
    }

    def __init__(self, page: Page):
        """
        初始化提取器

        Args:
            page: Playwright Page 对象
        """
        self.page = page
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_all(self, product_id: str, product_url: str) -> Optional[EquipmentData]:
        """
        提取所有字段，返回 EquipmentData 对象

        Args:
            product_id: 商品ID
            product_url: 商品URL

        Returns:
            EquipmentData 对象，如果缺少必需字段则返回 None
        """
        self.logger.info("开始提取商品详细信息...")

        # 提取各个字段
        name = self._extract_field('name', self.FIELD_CONFIGS['name'])
        price = self._extract_field('price', self.FIELD_CONFIGS['price'])
        brand = self._extract_field('brand', self.FIELD_CONFIGS['brand'])
        description = self._extract_field('description', self.FIELD_CONFIGS['description'])
        images = self._extract_field('images', self.FIELD_CONFIGS['images'])
        specs = self._extract_specs()

        # 如果name未提取成功，尝试从页面标题获取
        if not name:
            name = self._extract_name_from_title()

        # 验证必需字段
        if not name:
            self.logger.warning("无法提取商品名称")
            return None

        # 记录提取结果
        self.logger.info(f"商品名称: {name}")
        self.logger.info(f"商品价格: {price or '未提取到'}")
        self.logger.info(f"商品品牌: {brand or '未提取到'}")
        self.logger.info(f"图片数量: {len(images) if images else 0}")
        self.logger.info(f"规格参数数量: {len(specs) if specs else 0}")

        # 解析价格
        price_min = 0.0
        if price:
            try:
                price_min = float(price)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"价格解析失败: {price}, 错误: {e}")

        # 转换图片格式为字典列表
        image_list = []
        if images:
            for img_url in images:
                if img_url:
                    image_list.append({"url": img_url, "type": "detail"})

        # 创建商品数据对象
        product_data = EquipmentData(
            name=name,
            category="鱼竿",  # 路亚竿属于鱼竿类别
            brand_name=brand or "未知品牌",
            price_min=price_min,
            source_url=product_url,
            description=description,
            images=image_list,
            specs=specs or {},
        )

        # 将商品ID保存在specs中（因为EquipmentData没有id字段）
        product_data.specs['product_id'] = product_id

        self.logger.info(f"商品信息提取完成: {name}")
        return product_data

    def _extract_field(self, field_name: str, config: Dict[str, Any]) -> Any:
        """
        通用字段提取逻辑

        Args:
            field_name: 字段名称
            config: 字段配置

        Returns:
            提取的字段值，失败返回 None 或空列表（对于 multiple=True）
        """
        is_multiple = config.get('multiple', False)
        selectors = config.get('selectors', [])

        for selector in selectors:
            try:
                if is_multiple:
                    # 提取多个元素
                    return self._extract_multiple_values(selector, config)
                else:
                    # 提取单个元素
                    return self._extract_single_value(selector, config)
            except Exception as e:
                self.logger.debug(f"选择器 '{selector}' 失败: {e}")
                continue

        # 如果是多值字段，返回空列表而非 None
        return [] if is_multiple else None

    def _extract_single_value(self, selector: str, config: Dict[str, Any]) -> Optional[Any]:
        """提取单个字段值"""
        element = self.page.locator(selector).first

        # 提取属性或文本
        if 'attribute' in config:
            value = element.get_attribute(config['attribute'], timeout=5000)
        elif 'attributes' in config:
            # 尝试多个属性
            value = None
            for attr in config['attributes']:
                value = element.get_attribute(attr, timeout=5000)
                if value:
                    break
        else:
            value = element.text_content(timeout=5000)

        if not value:
            return None

        # 应用解析器
        if 'parser' in config:
            value = config['parser'](value)

        # 验证字段值
        if value and self._validate_field(value, config):
            return value.strip() if isinstance(value, str) else value

        return None

    def _extract_multiple_values(self, selector: str, config: Dict[str, Any]) -> List[str]:
        """提取多个字段值（如图片列表）"""
        elements = self.page.locator(selector).all()
        values = []

        for element in elements:
            # 提取属性或文本
            if 'attributes' in config:
                # 按顺序尝试多个属性
                value = None
                for attr in config['attributes']:
                    value = element.get_attribute(attr)
                    if value:
                        break
            elif 'attribute' in config:
                value = element.get_attribute(config['attribute'])
            else:
                value = element.text_content()

            if value:
                # 处理相对路径（如图片URL）
                if value.startswith("//"):
                    value = "https:" + value

                if value not in values:  # 去重
                    values.append(value.strip() if isinstance(value, str) else value)

        self.logger.info(f"提取到 {len(values)} 个值")
        return values

    def _validate_field(self, value: Any, config: Dict[str, Any]) -> bool:
        """
        验证字段值

        Args:
            value: 字段值
            config: 字段配置

        Returns:
            是否通过验证
        """
        if not value:
            return False

        # 检查最大长度
        if 'max_length' in config and len(str(value)) > config['max_length']:
            self.logger.debug(f"字段值超过最大长度: {len(str(value))} > {config['max_length']}")
            return False

        # 检查最小长度
        if 'min_length' in config and len(str(value)) < config['min_length']:
            self.logger.debug(f"字段值小于最小长度: {len(str(value))} < {config['min_length']}")
            return False

        return True

    def _extract_name_from_title(self) -> Optional[str]:
        """从页面标题提取商品名称"""
        try:
            title = self.page.title()
            if title:
                # 移除淘宝相关的后缀
                for suffix in ['-淘宝网', '-tmall.com天猫', '-天猫Tmall', '-淘宝']:
                    if suffix in title:
                        title = title.split(suffix)[0]
                        break
                name = title.strip()
                if len(name) > 5:
                    self.logger.info(f"从页面标题获取商品名称: {name}")
                    return name
        except Exception as e:
            self.logger.debug(f"从标题提取名称失败: {e}")

        return None

    def _extract_specs(self) -> Optional[Dict[str, str]]:
        """提取商品规格参数"""
        specs = {}

        # 规格参数选择器
        spec_selectors = [
            "#J_AttrUL",
            ".tb-props",
            ".props",
            "[class*='spec']",
            "[class*='param']",
            "[class*='attr']",
            ".attributes",
            ".attributes-list",
        ]

        for selector in spec_selectors:
            try:
                container = self.page.locator(selector).first
                if not container.count():
                    continue

                # 提取键值对形式的规格参数
                rows = container.locator("li, tr, .item, dt, dd").all()
                for row in rows:
                    try:
                        text = row.text_content().strip()
                        if not text:
                            continue

                        # 解析键值对
                        if '：' in text:
                            key, value = text.split('：', 1)
                        elif ':' in text:
                            key, value = text.split(':', 1)
                        else:
                            continue

                        key = key.strip()
                        value = value.strip()

                        # 验证并保存
                        if key and value and len(key) < 30 and len(value) < 200:
                            specs[key] = value

                    except Exception as e:
                        self.logger.debug(f"解析规格参数失败: {e}")
                        continue

                if specs:
                    self.logger.info(f"使用选择器 {selector} 提取到 {len(specs)} 个规格参数")
                    break

            except Exception as e:
                self.logger.debug(f"提取规格参数失败 ({selector}): {e}")
                continue

        return specs if specs else None
