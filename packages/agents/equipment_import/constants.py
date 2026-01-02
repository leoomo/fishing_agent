"""
装备导入常量定义

配置常量和类型定义的唯一位置
"""

# 有效的装备类型
EQUIPMENT_TYPES = ["鱼竿", "渔轮", "鱼线", "拟饵", "路亚竿"]

# 来源类型
SOURCE_TYPES = ["ecommerce", "official", "forum", "unknown"]

# 置信度阈值
CONFIDENCE_THRESHOLD_LOW = 0.3      # 低于此值认为提取不可靠
CONFIDENCE_THRESHOLD_HIGH = 0.7     # 高于此值认为提取可靠

# 默认模型提供商
DEFAULT_MODEL_PROVIDER = "zhipu"

# 文本压缩配置
COMPRESSION_MIN_LENGTH = 2000       # 触发压缩的最小文本长度

# 批量处理配置
BATCH_OCR_TEXT_LIMIT = 1000         # 批量保存时原文限制字符数
