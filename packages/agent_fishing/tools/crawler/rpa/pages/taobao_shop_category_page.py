"""淘宝店铺分类页面对象"""

import logging
import time
import re
from typing import List, Optional
from playwright.sync_api import Page, Locator

from .taobao_shop_page import TaobaoShopPage
from ..core.base_page import retry_operation
from ..config import RPAConfig
from ..utils.scroll_helper import scroll_to_load_all

logger = logging.getLogger(__name__)


class TaobaoShopCategoryPage(TaobaoShopPage):
    """淘宝店铺分类页面，负责分类交互和商品定位"""

    def __init__(self, page: Page, config: Optional[RPAConfig] = None, timeout: int = 30000):
        """
        初始化店铺分类页面

        Args:
            page: Playwright Page 对象
            config: RPA配置
            timeout: 超时时间（毫秒）
        """
        super().__init__(page, timeout)
        self.config = config or RPAConfig.from_env()

    def navigate_to_shop(self, shop_url: str) -> bool:
        """
        导航到店铺页面

        Args:
            shop_url: 店铺URL

        Returns:
            是否成功进入店铺
        """
        self.logger.info(f"正在进入店铺页面: {shop_url}")

        try:
            # 使用父类的导航方法
            if not self.navigate_to_url(shop_url):
                return False

            # 等待页面加载
            time.sleep(3)

            # 检查是否成功进入店铺
            if "taobao.com" not in self.page.url:
                self.logger.error("页面跳转失败，未进入淘宝店铺")
                return False

            self.logger.info("✅ 成功进入店铺页面")
            return True

        except Exception as e:
            self.logger.error(f"进入店铺页面时发生错误: {e}", exc_info=True)
            return False

    @retry_operation(max_attempts=3, delay=1.0)
    def click_category(self, category_name: str) -> bool:
        """
        点击指定分类

        Args:
            category_name: 分类名称（如"路亚竿"）

        Returns:
            是否成功点击分类
        """
        self.logger.info(f"开始点击'{category_name}'分类...")

        # 使用语义定位器（优先策略）
        strategies = [
            # 策略1：精确文本匹配（最优）
            lambda: self.get_element_by_text(category_name, exact=True).click(),

            # 策略2：链接角色匹配
            lambda: self.get_element_by_role("link", name=category_name, exact=True).click(),

            # 策略3：模糊文本匹配
            lambda: self.get_element_by_text(category_name, exact=False).click(),

            # 策略4：自定义选择器（后备方案）
            lambda: self._click_category_by_selectors(category_name),
        ]

        for i, strategy in enumerate(strategies, 1):
            try:
                strategy()
                self.logger.info(f"✅ 成功点击'{category_name}'分类（策略{i}）")
                time.sleep(3)  # 等待页面加载
                return True
            except Exception as e:
                self.logger.debug(f"策略{i}失败: {e}")
                continue

        self.logger.error(f"❌ 未找到'{category_name}'分类")
        return False

    def _click_category_by_selectors(self, category_name: str) -> bool:
        """使用自定义选择器点击分类（后备方案）"""
        selectors = [
            f"a:has-text('{category_name}')",
            f".shop-category a:has-text('{category_name}')",
            f".cat-tree a:has-text('{category_name}')",
            f".side-cate a:has-text('{category_name}')",
            f".category-list a:has-text('{category_name}')",
        ]

        for selector in selectors:
            elements = self.page.locator(selector).all()
            for elem in elements:
                if elem.is_visible(timeout=2000):
                    elem.click()
                    return True

        raise Exception(f"所有选择器都未找到分类: {category_name}")

    def wait_for_category_loaded(self, timeout: int = 30) -> bool:
        """
        等待分类页面加载完成

        Args:
            timeout: 最大等待时间（秒）

        Returns:
            是否成功加载
        """
        self.logger.info("等待分类页面加载完成...")

        start_time = time.time()
        wait_interval = 2

        # 商品元素指示器
        product_indicators = [
            "[data-spm='product_shelf']",
            "[data-spm-anchor-id*='product_shelf']",
            ".item",
            ".product",
            ".Card--doubleCard",
        ]

        while (time.time() - start_time) < timeout:
            try:
                for indicator in product_indicators:
                    elements = self.page.locator(indicator).all()
                    if elements and len(elements) > 0:
                        self.logger.info(f"✅ 分类页面加载完成，检测到 {len(elements)} 个商品元素")
                        return True

                time.sleep(wait_interval)
                self.logger.debug(f"等待分类加载... ({int(time.time() - start_time)}s)")

            except Exception as e:
                self.logger.debug(f"检查加载状态时发生错误: {e}")
                time.sleep(wait_interval)

        self.logger.warning("分类页面加载超时，但继续执行")
        return True

    def scroll_to_load_products(self) -> bool:
        """
        滚动页面加载所有商品

        Returns:
            是否成功完成滚动
        """
        self.logger.info("开始滚动加载所有商品...")

        # 使用通用滚动工具
        return scroll_to_load_all(self.page, self.config, self.logger)

    def find_product_elements(self) -> List[Locator]:
        """
        查找商品元素

        Returns:
            商品元素列表
        """
        self.logger.info("查找商品元素...")

        # 商品选择器配置（按优先级排序）
        product_selectors = [
            # 优先级1：精确的XPath
            "xpath=//div//div[@data-spm='product_shelf']/div[contains(@class, 'container--')]/div[contains(@class,'cardContainer--')]",

            # 优先级2：Data属性
            "[data-spm='product_shelf']",
            "[data-spm-anchor-id*='product_shelf']",

            # 优先级3：通用类名
            ".Card--doubleCard",
            "[class*='cardContainer']",
            ".item",
        ]

        for selector in product_selectors:
            try:
                # 区分XPath和CSS选择器
                if selector.startswith("xpath="):
                    elements = self.page.locator(selector).all()
                else:
                    elements = self.page.locator(selector).all()

                if elements:
                    self.logger.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个商品元素")
                    return elements

            except Exception as e:
                self.logger.debug(f"选择器 '{selector}' 失败: {e}")
                continue

        self.logger.warning("未找到商品元素")
        return []

    def open_first_product_detail(self) -> Optional[Page]:
        """
        打开第一个商品的详情页

        Returns:
            新打开的详情页Page对象，失败返回None
        """
        self.logger.info("开始打开第一个商品详情...")

        # 查找商品元素
        elements = self.find_product_elements()
        if not elements:
            self.logger.warning("未找到商品元素")
            return None

        self.logger.info(f"找到 {len(elements)} 个商品，打开第一个")

        try:
            # 监听新页面打开
            with self.page.expect_popup() as popup_info:
                elements[0].click()

            # 获取新打开的页面
            new_page = popup_info.value
            self.logger.info("新标签页已打开，等待页面加载...")
            new_page.wait_for_load_state('domcontentloaded', timeout=10000)
            time.sleep(3)

            self.logger.info(f"✅ 成功打开商品详情页: {new_page.url}")
            return new_page

        except Exception as e:
            self.logger.error(f"打开商品详情页失败: {e}", exc_info=True)
            return None

    def extract_product_id_from_url(self, url: str) -> Optional[str]:
        """
        从URL中提取商品ID

        Args:
            url: 商品详情页URL

        Returns:
            商品ID，失败返回None
        """
        try:
            # 从URL中提取id参数
            patterns = [
                r'id=(\d+)',  # 标准模式
                r'item\.htm\?id=(\d+)',  # 淘宝商品详情页
                r'detail\.tmall\.com/item\.htm\?id=(\d+)',  # 天猫详情页
            ]

            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

            return None

        except Exception as e:
            self.logger.error(f"从URL提取商品ID失败: {e}", exc_info=True)
            return None
