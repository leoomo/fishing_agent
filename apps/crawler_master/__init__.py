"""
Crawler Master Service Entry Point

分布式爬虫Master服务入口
"""

from packages.scraper.master import create_app

app = create_app()

__all__ = ["app"]
