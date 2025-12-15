"""
通用滚动加载工具

提供可复用的页面滚动逻辑，适用于各种RPA爬虫场景。
"""

import time
import random
import logging
from playwright.sync_api import Page

from ..config import RPAConfig

logger = logging.getLogger(__name__)


def scroll_to_load_all(
    page: Page,
    config: RPAConfig,
    custom_logger: logging.Logger = None
) -> bool:
    """
    竖向滚动页面直到加载完所有内容

    使用渐进式滚动模拟人类浏览行为，支持懒加载内容。

    Args:
        page: Playwright Page 对象
        config: RPA配置（包含滚动参数）
        custom_logger: 自定义日志记录器（可选）

    Returns:
        是否成功完成滚动
    """
    _logger = custom_logger or logger

    max_scrolls = config.scroll_max_attempts
    scroll_count = 0
    no_change_count = 0

    try:
        # 获取初始页面高度
        last_height = page.evaluate("document.body.scrollHeight")
        _logger.debug(f"初始页面高度: {last_height}")

        while scroll_count < max_scrolls:
            # 计算滚动步长（随机化，模拟人类行为）
            viewport_height = page.evaluate("window.innerHeight")
            current_scroll_position = page.evaluate("window.pageYOffset")

            scroll_step = random.uniform(
                config.scroll_step_min,
                config.scroll_step_max
            ) * viewport_height
            next_scroll_position = current_scroll_position + scroll_step

            # 执行平滑滚动
            page.evaluate(f"""
                window.scrollTo({{
                    top: {next_scroll_position},
                    behavior: 'smooth'
                }});
            """)

            # 等待内容加载（随机延迟）
            wait_time = random.uniform(config.scroll_wait_min, config.scroll_wait_max)
            _logger.debug(f"等待 {wait_time:.1f}s 让内容加载...")
            time.sleep(wait_time)

            # 检测是否到达页面底部
            at_bottom = page.evaluate("""
                () => {
                    const scrollTop = window.pageYOffset;
                    const windowHeight = window.innerHeight;
                    const documentHeight = document.documentElement.scrollHeight;
                    return scrollTop + windowHeight >= documentHeight - 100;
                }
            """)

            # 检查页面高度变化
            new_height = page.evaluate("document.body.scrollHeight")

            if at_bottom:
                _logger.debug("已到达页面底部")

                if new_height == last_height:
                    no_change_count += 1
                    _logger.debug(f"到底部后页面高度未变化，无变化计数: {no_change_count}")

                    if no_change_count >= config.scroll_completion_threshold:
                        _logger.info("✅ 检测到页面内容加载完成")
                        break
                else:
                    no_change_count = 0
                    last_height = new_height
                    _logger.debug(f"到底部后页面高度增加: {new_height}")
            else:
                # 未到底部，检查高度变化
                if new_height > last_height:
                    no_change_count = 0
                    last_height = new_height
                    _logger.debug(f"页面高度更新: {last_height}")

            scroll_count += 1
            _logger.debug(f"滚动进度: {scroll_count}/{max_scrolls}")

            # 如果连续多次滚动都没有变化，可能已完成
            if scroll_count > 10 and no_change_count > 3:
                _logger.info("✅ 检测到页面滚动趋于稳定，可能已加载完成")
                break

        _logger.info(f"滚动完成，总滚动次数: {scroll_count}")
        return True

    except Exception as e:
        _logger.error(f"滚动操作失败: {e}", exc_info=True)
        return False
