"""
登录管理器
"""

import time
import logging
from typing import Optional

from playwright.sync_api import Page, BrowserContext

from .config import RPAConfig
from .session_storage import SessionStorage
from .captcha_solver import CaptchaSolver

logger = logging.getLogger(__name__)


class LoginManager:
    """淘宝登录管理器"""

    def __init__(self, config: RPAConfig):
        """
        初始化

        Args:
            config: RPA 配置
        """
        self.config = config
        self.storage = SessionStorage(config.cookie_path)
        self.captcha_solver = CaptchaSolver(config)

        logger.info(f"初始化登录管理器: {config.cookie_path}")

    def ensure_logged_in(self, page: Page, context: BrowserContext) -> bool:
        """
        确保已登录（核心方法）

        Args:
            page: Page 对象
            context: BrowserContext 对象

        Returns:
            是否登录成功
        """
        logger.info("检查登录状态...")

        # 1. 尝试加载 Cookie
        if self.storage.exists() and self.storage.is_valid():
            logger.info("发现已保存的 Session，尝试加载...")

            # 加载 Cookie
            cookies = self.storage.get_cookies()
            if cookies:
                try:
                    context.add_cookies(cookies)
                    logger.debug(f"已添加 {len(cookies)} 个 Cookie")
                except Exception as e:
                    logger.error(f"添加 Cookie 失败: {e}")

            # 验证有效性
            if self.is_session_valid(page):
                logger.info("✅ Session 有效，已登录")
                return True
            else:
                logger.warning("Session 已失效")
                self.storage.mark_invalid()

        # 2. 需要重新登录
        logger.info("需要重新登录...")
        return self.login(page, context)

    def is_session_valid(self, page: Page) -> bool:
        """
        检测 Session 是否有效

        Args:
            page: Page 对象

        Returns:
            是否有效
        """
        try:
            # 访问淘宝首页
            page.goto("https://www.taobao.com/", timeout=15000, wait_until="domcontentloaded")

            # 等待页面稳定
            time.sleep(2)

            # 检测用户昵称元素（登录后才会显示）
            user_selectors = [
                ".site-nav-user",  # 用户昵称区域
                ".site-nav-login-info-nick",  # 用户昵称
                "a[href*='member1.taobao.com']",  # 会员链接
            ]

            for selector in user_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        element = page.locator(selector).first
                        if element.is_visible(timeout=3000):
                            # 提取用户名
                            user_name = element.inner_text().strip()
                            if user_name and user_name not in ["请登录", "登录", "亲，请登录"]:
                                logger.info(f"检测到登录用户: {user_name}")
                                return True
                except:
                    continue

            logger.debug("未检测到登录状态")
            return False

        except Exception as e:
            logger.warning(f"登录检测失败: {e}")
            return False

    def login(self, page: Page, context: BrowserContext) -> bool:
        """
        扫码登录

        Args:
            page: Page 对象
            context: BrowserContext 对象

        Returns:
            是否成功
        """
        logger.info("开始扫码登录流程...")

        try:
            # 1. 访问登录页
            logger.info("访问淘宝登录页...")
            page.goto("https://login.taobao.com/", timeout=30000, wait_until="domcontentloaded")

            # 等待页面加载
            time.sleep(3)

            # 2. 点击"扫码登录"标签（如果有多个登录方式）
            try:
                # 查找扫码登录标签
                qr_tab_selectors = [
                    ".login-form-qrcode-title",  # 二维码标签
                    'a[data-type="qrcode"]',  # 二维码链接
                    'a:has-text("扫码登录")',  # 文本匹配
                ]

                for selector in qr_tab_selectors:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click()
                        logger.debug("已切换到扫码登录")
                        time.sleep(1)
                        break

            except:
                logger.debug("未找到扫码登录标签，继续...")

            # 3. 等待二维码加载
            qr_selectors = [
                "#login .qrcode-img",  # 二维码图片
                ".qrcode-img",
                'img[src*="qrcode"]',
            ]

            qr_loaded = False
            for selector in qr_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    qr_loaded = True
                    logger.debug(f"二维码已加载: {selector}")
                    break
                except:
                    continue

            if not qr_loaded:
                logger.error("❌ 二维码加载失败")
                return False

            # 4. 截图保存二维码
            qr_screenshot = "shared/data/cookies/taobao_qrcode.png"
            try:
                page.screenshot(path=qr_screenshot)
                logger.info(f"📸 二维码截图: {qr_screenshot}")
            except Exception as e:
                logger.warning(f"截图失败: {e}")
                qr_screenshot = "（截图失败）"

            # 5. 提示用户扫码
            print("\n" + "=" * 60)
            print("📱 请使用淘宝/手机淘宝APP扫描二维码登录")
            print("=" * 60)
            print(f"二维码截图: {qr_screenshot}")

            if not self.config.headless:
                print("浏览器窗口中也可直接扫码")

            print("等待扫码中...")
            print("=" * 60 + "\n")

            # 6. 轮询检测登录状态（最多60秒）
            for i in range(60):
                time.sleep(2)

                # 检查是否登录成功（通过 URL 跳转判断）
                current_url = page.url

                # 登录成功后会跳转离开 login.taobao.com
                if "login.taobao.com" not in current_url:
                    logger.info(f"✅ 检测到页面跳转: {current_url}")
                    print("\n✅ 登录成功！正在验证...\n")

                    # 再次验证登录状态（此时才跳转到首页验证）
                    time.sleep(1)
                    if self.is_session_valid(page):
                        logger.info("✅ 扫码登录验证成功！")

                        # 7. 保存 Cookie
                        self._save_cookies(page, context)
                        return True
                    else:
                        logger.warning("登录验证失败，继续等待...")

                # 每10秒提示一次
                if (i + 1) % 5 == 0:
                    logger.info(f"等待扫码... ({(i + 1) * 2}/120秒)")
                    print(f"⏳ 等待中... ({(i + 1) * 2}/120秒)")

            # 超时
            logger.error("❌ 扫码登录超时（120秒）")
            print("\n❌ 登录超时，请重试\n")
            return False

        except Exception as e:
            logger.error(f"登录流程失败: {e}", exc_info=True)
            return False

    def _save_cookies(self, page: Page, context: BrowserContext):
        """
        保存 Cookie

        Args:
            page: Page 对象
            context: BrowserContext 对象
        """
        try:
            # 获取所有 Cookie
            cookies = context.cookies()

            # 提取账号信息（从用户昵称）
            account = "unknown"
            try:
                user_elem = page.locator(".site-nav-login-info-nick").first
                if user_elem.is_visible(timeout=2000):
                    account = user_elem.inner_text().strip()
            except:
                pass

            # 构建 Session 数据
            session_data = {
                "account": account,
                "cookies": cookies,
                "is_valid": True,
            }

            # 保存
            self.storage.save(session_data)
            logger.info(f"✅ Cookie 已保存 (账号: {account})")

        except Exception as e:
            logger.error(f"保存 Cookie 失败: {e}", exc_info=True)
