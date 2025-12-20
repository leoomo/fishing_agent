"""
Crawler Master Service Main Entry

启动命令:
    uv run uvicorn apps.crawler_master.main:app --host 0.0.0.0 --port 8100 --reload
"""

import logging
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from packages.scraper.master import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.crawler_master.main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
    )
