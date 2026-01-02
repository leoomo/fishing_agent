"""
压缩规则 - 定义文本压缩的正则模式

删除冗余内容，保留核心信息（规格表、型号描述、技术特色等）。
"""

import re
from typing import List

# ============================================================
# 删除模式（单行匹配）
# ============================================================

REMOVE_LINE_PATTERNS: List[str] = [
    # 图片标题
    r'^## merge_\d+.*\.jpg\s*$',

    # 分隔符
    r'^---+\s*$',

    # 纯英文大写行（营销语）- 但排除含有型号的行
    r'^[A-Z][A-Z\s,\.\'&\-\#]+$',

    # 图表说明
    r'^Figure \d+\..*$',

    # 纯英文加粗标题
    r'^\*\*[A-Z][A-Z\s\-]+\*\*\s*$',

    # 星号/评分行
    r'^[\*★]+\s*$',

    # 纯数字行
    r'^\d+\s*$',

    # 空的 markdown 标题
    r'^#+\s*$',

    # Innovation by Chemistry 等口号
    r'^Innovation by Chemistry.*$',

    # 纯英文短句（无中文，少于50字符）
    r'^[A-Za-z\s,\.\'&\-\#\!\?]+$',
]

# 编译正则
REMOVE_LINE_COMPILED = [re.compile(p, re.MULTILINE) for p in REMOVE_LINE_PATTERNS]


# ============================================================
# 删除块模式（多行匹配）
# ============================================================

REMOVE_BLOCK_PATTERNS: List[str] = [
    # 售后服务说明块
    r'#\s*Gold medal after sales service[\s\S]*?联系我们！',
    r'#\s*售后服务说明[\s\S]*?联系我们！',

    # 价格说明块
    r'价格说明：[\s\S]*?以商家的表述为准。',

    # 消费提醒块
    r'#\s*消费提醒[\s\S]*?\[绿网计划\]',

    # 技术原理图说明（Figure + 曲线数据）
    r'Figure \d+\.[\s\S]*?(?=\n#|\n\||\Z)',

    # 树脂技术详细说明（保留关键词但删除详细说明）
    r'Resin [AB][\s\S]*?Flexural modulus',

    # 重复的技术说明块（图示文字）
    r'###\s*图示文字[\s\S]*?(?=\n#|\n---|\Z)',
]

# 编译正则
REMOVE_BLOCK_COMPILED = [re.compile(p, re.MULTILINE | re.DOTALL) for p in REMOVE_BLOCK_PATTERNS]


# ============================================================
# 保留模式（优先级高于删除）
# ============================================================

KEEP_PATTERNS: List[str] = [
    # 表格行（规格参数）
    r'\|.*\|',

    # 型号标题 (# C661M, # S681M+)
    r'^#+ [CS]\d+[A-Z0-9\-\+]+',

    # 产品描述关键词
    r'竿型特点|适用钓组|适用场景|设计理念|建议搭配|作钓环境',

    # 碳布材质
    r'T1100G|M40X|M40JB|T40|T30|TORAYCA|NANOALLOY',

    # 导环配置
    r'富士|FUJI|SiC|SIC|TORZITE|ECS轮座|导环',

    # 代言人/钓手
    r'国内.*钓手|设计师|著名.*钓手|知名.*钓手',

    # 系列名
    r'轻鸿|知境|GNOMIC|灵感|信号|STATE',

    # 品牌名
    r'DOOP|K·F',

    # 详细参数标题
    r'详细参数|产品参数|规格',
]

# 编译正则
KEEP_COMPILED = [re.compile(p, re.MULTILINE) for p in KEEP_PATTERNS]


# ============================================================
# 元信息提取模式
# ============================================================

# 品牌名提取
BRAND_PATTERNS: List[str] = [
    r'DOOP',
    r'K·F',
]

# 系列名提取
SERIES_PATTERNS: List[str] = [
    r'轻鸿',
    r'知境|GNOMIC|STATE',
    r'灵感',
    r'信号',
]

# 型号提取（用于统计）
MODEL_PATTERN = re.compile(r'[CS]\d{2,3}[A-Z0-9\-\+]+(?:-ST)?', re.IGNORECASE)


def should_keep_line(line: str) -> bool:
    """检查行是否应该保留"""
    for pattern in KEEP_COMPILED:
        if pattern.search(line):
            return True
    return False


def should_remove_line(line: str) -> bool:
    """检查行是否应该删除"""
    # 先检查是否应该保留
    if should_keep_line(line):
        return False

    # 检查删除模式
    for pattern in REMOVE_LINE_COMPILED:
        if pattern.match(line.strip()):
            return True

    return False
