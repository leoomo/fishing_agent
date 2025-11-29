#!/usr/bin/env python3
"""
智能钓鱼助手主程序入口

CLI 入口委托到 apps/cli/main.py
"""

import sys

# 确保项目根目录在 Python 路径中
sys.path.insert(0, ".")

from apps.cli.main import main

if __name__ == "__main__":
    main()
