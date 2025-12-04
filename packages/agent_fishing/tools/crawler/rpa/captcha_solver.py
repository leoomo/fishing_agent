"""
验证码处理器
"""

import time
import logging
from typing import Optional
from pathlib import Path

from playwright.sync_api import Page

from .config import RPAConfig

logger = logging.getLogger(__name__)


class CaptchaSolver:
    """验证码处理器（人工介入模式）"""

    def __init__(self, config: RPAConfig):
        """
        初始化

        Args:
            config: RPA 配置
        """
        self.config = config
        logger.info(f"初始化验证码处理器: {config.captcha_solver} 模式")

    def solve_slider(self, page: Page, screenshot_dir: Optional[str] = None) -> bool:
        """
        处理滑块验证码

        Args:
            page: Page 对象
            screenshot_dir: 截图保存目录（默认使用 cookies 目录）

        Returns:
            是否成功
        """
        # 检测滑块
        if not self._detect_slider(page):
            logger.debug("未检测到滑块验证码")
            return True  # 无验证码

        logger.warning("⚠️  检测到滑块验证码，需要人工完成")

        # 截图保存
        screenshot_path = self._take_screenshot(page, screenshot_dir)
        logger.info(f"📸 验证码截图: {screenshot_path}")

        # 检查是否为 headless 模式
        if self.config.headless:
            logger.error(
                "❌ 当前为 headless 模式，无法手动完成验证码\n"
                "请设置环境变量: PLAYWRIGHT_HEADLESS=false\n"
                "然后重新运行爬虫"
            )
            return False

        # 提示用户
        print("\n" + "=" * 60)
        print("⚠️  请在浏览器中手动完成滑块验证")
        print("=" * 60)
        print(f"截图已保存: {screenshot_path}")
        print("请完成验证后，爬虫将自动继续...")
        print("=" * 60 + "\n")

        # 轮询等待验证完成（60秒超时）
        for i in range(60):
            time.sleep(1)

            # 检查验证码是否消失
            if not self._detect_slider(page):
                logger.info("✅ 验证码已完成")
                print("\n✅ 验证码验证成功！继续爬取...\n")
                return True

            # 每10秒提示一次
            if (i + 1) % 10 == 0:
                logger.info(f"等待验证码完成... ({i + 1}/60秒)")

        # 超时
        logger.error("❌ 验证码验证超时（60秒）")
        print("\n❌ 验证码验证超时，请重试\n")
        return False

    def _detect_slider(self, page: Page) -> bool:
        """
        检测滑块验证码元素

        Args:
            page: Page 对象

        Returns:
            是否存在滑块
        """
        # 淘宝常见滑块选择器
        selectors = [
            "#nc_1_n1z",  # 淘宝滑块
            ".nc-lang-cnt",  # 通用滑块
            'iframe[src*="captcha"]',  # 验证码 iframe
            ".baxia-dialog",  # 阿里云盾
            "#baxia-dialog-content",  # 阿里云盾内容
        ]

        for selector in selectors:
            try:
                if page.locator(selector).count() > 0:
                    if page.locator(selector).first.is_visible(timeout=1000):
                        logger.debug(f"检测到滑块元素: {selector}")
                        return True
            except:
                continue

        return False

    def _take_screenshot(self, page: Page, screenshot_dir: Optional[str] = None) -> str:
        """
        截图保存

        Args:
            page: Page 对象
            screenshot_dir: 截图目录

        Returns:
            截图文件路径
        """
        # 默认保存到 cookies 目录
        if screenshot_dir is None:
            screenshot_dir = "shared/data/cookies"

        # 确保目录存在
        Path(screenshot_dir).mkdir(parents=True, exist_ok=True)

        # 生成文件名（带时间戳）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{screenshot_dir}/captcha_{timestamp}.png"

        try:
            page.screenshot(path=screenshot_path)
            logger.debug(f"截图已保存: {screenshot_path}")
            return screenshot_path

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return "（截图失败）"
