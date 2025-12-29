# 装备导入指南 v5.0.2

详细介绍智能钓鱼助手v5.0.2的装备信息提取、导入和管理功能。

## 📋 目录

- [功能概览](#功能概览)
- [文本提取技术](#文本提取技术)
- [智能压缩算法](#智能压缩算法)
- [批量导入流程](#批量导入流程)
- [数据清洗](#数据清洗)
- [API接口使用](#api接口使用)
- [质量控制](#质量控制)
- [常见问题](#常见问题)

## 🎯 功能概览

### 核心能力
- **智能提取**：从各种文本源提取装备信息
- **文本压缩**：自动压缩冗余文本，提高处理效率
- **批量处理**：支持大规模批量导入操作
- **质量控制**：数据验证和去重处理
- **来源追溯**：保留数据来源和导入记录

### 应用场景
- **电商商品**：从电商网站提取装备信息
- **论坛帖子**：从钓鱼论坛收集装备讨论
- **评测文章**：从专业评测文章提取装备参数
- **用户分享**：处理用户分享的装备信息

## 🔍 文本提取技术

### 提取器架构
```python
# packages/agents/equipment_import/core/extractors/custom_extractor.py
from typing import List, Dict, Optional
import re

class CustomExtractor:
    def __init__(self):
        # 品牌词典
        self.brands = {
            "光威", "达亿瓦", "禧玛诺", "阿布", "Shimano", "Daiwa",
            "宝丽", "科尼", "佳钓尼", "钓鱼王", "化氏", "老鬼"
        }
        
        # 类别映射
        self.categories = {
            "路亚竿": ["竿", "路亚竿", "鱼竿"],
            "纺车轮": ["轮", "纺车轮", "渔轮"],
            "拟饵": ["饵", "拟饵", "crank", "minnow", "spinnerbait"],
            "鱼线": ["线", "鱼线", "尼龙线", "碳线", "pe线"]
        }
        
        # 价格模式
        self.price_patterns = [
            r'￥(\d+\.?\d*)',           # 人民币符号
            r'(\d+)元',                 # 元
            r'\$(\d+\.?\d*)',           # 美元符号
            r'¥(\d+\.?\d*)',            # 人民币符号(全角)
        ]
        
        # 规格模式
        self.spec_patterns = {
            "length": r'(\d+\.?\d*)[米m]',
            "weight": r'(\d+\.?\d*)[克g]',
            "action": r'(L|M|H|UL|XUL)'
        }

    def extract(self, text: str) -> List[Dict]:
        """主提取方法"""
        # 1. 文本分段
        segments = self._split_segments(text)
        
        equipment_list = []
        
        for segment in segments:
            equipment = self._extract_single_equipment(segment)
            if self._is_valid_equipment(equipment):
                equipment_list.append(equipment)
        
        return equipment_list
    
    def _split_segments(self, text: str) -> List[str]:
        """智能分段"""
        # 按标点符号分段
        segments = re.split(r'[。！？\n\r]+', text)
        
        # 过滤空段和短段
        segments = [seg.strip() for seg in segments if len(seg.strip()) > 10]
        
        return segments
    
    def _extract_single_equipment(self, text: str) -> Dict:
        """提取单个装备信息"""
        equipment = {
            "brand": self._extract_brand(text),
            "model": self._extract_model(text),
            "category": self._detect_category(text),
            "price": self._extract_price(text),
            "specs": self._extract_specs(text),
            "description": text[:200]  # 保留前200字符作为描述
        }
        
        return equipment
    
    def _extract_brand(self, text: str) -> Optional[str]:
        """提取品牌"""
        for brand in self.brands:
            if brand in text:
                return brand
        return None
    
    def _extract_model(self, text: str) -> Optional[str]:
        """提取型号"""
        # 常见型号模式
        model_patterns = [
            r'([A-Z]{2,4}\d{2,4}[A-Z]*)',  # 大写字母+数字
            r'(\d{2,4}[A-Z]{2,4})',     # 数字+大写字母
            r'([A-Z]\d{3,4}-\w+)',        # A123-XXX格式
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None
    
    def _detect_category(self, text: str) -> Optional[str]:
        """检测类别"""
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        return None
    
    def _extract_price(self, text: str) -> float:
        """提取价格"""
        for pattern in self.price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return 0.0
    
    def _extract_specs(self, text: str) -> Dict:
        """提取规格"""
        specs = {}
        
        for spec_type, pattern in self.spec_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                specs[spec_type] = matches[0]
        
        return specs
    
    def _is_valid_equipment(self, equipment: Dict) -> bool:
        """验证装备信息有效性"""
        # 至少要有品牌或型号
        return bool(equipment.get("brand") or equipment.get("model"))
```

### 提取示例
```python
# 使用示例
from packages.agents.equipment_import.core import EquipmentImportAgent

# 创建导入Agent
agent = EquipmentImportAgent(
    model_provider="zhipu",
    enable_compression=True
)

# 示例文本
text = """
光威赤刃 GT602L-M 路亚竿，碳纤维材质，超轻硬设计，
适合淡水作钓，长度2.4米，自重120g，售价299元。
禧玛诺斯特拉 C3000 纺车轮，金属机身，12轴承，
线容量：0.20mm/150m，0.25mm/120m，价格450元。
"""

# 执行提取
results = agent.extract_and_save(
    text=text,
    source_type="forum",
    source_url="https://forum.example.com/post/123"
)

print(f"提取到 {len(results)} 个装备信息")
for result in results:
    print(f"品牌: {result.data.get('brand')}")
    print(f"型号: {result.data.get('model')}")
    print(f"类别: {result.data.get('category')}")
    print(f"价格: {result.data.get('price')}")
```

## 🗜️ 智能压缩算法

### 压缩策略
```python
# packages/agents/equipment_import/core/compressor.py
class TextCompressor:
    def __init__(self):
        # 冗余词汇列表
        self.redundant_words = [
            "的", "了", "和", "在", "是", "有", "我", "你", "他", "她",
            "这个", "那个", "一些", "一种", "可以", "能够", "应该"
        ]
        
        # 保留的关键词
        self.keep_words = {
            "光威", "达亿瓦", "禧玛诺", "路亚竿", "纺车轮", 
            "拟饵", "碳纤维", "超轻", "金属", "价格", "元"
        }

    def compress(self, text: str) -> CompressionResult:
        """压缩文本"""
        if len(text) <= 500:
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                compression_ratio=1.0,
                removed_chars=0
            )
        
        # 1. 去除冗余内容
        cleaned = self._remove_redundant(text)
        
        # 2. 提取核心信息
        core_info = self._extract_core(cleaned)
        
        # 3. 重建压缩文本
        compressed = self._rebuild_text(core_info)
        
        # 4. 优化长度
        if len(compressed) > 2000:
            compressed = self._further_compress(compressed)
        
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            compression_ratio=len(text) / len(compressed),
            removed_chars=len(text) - len(compressed)
        )
    
    def _remove_redundant(self, text: str) -> str:
        """去除冗余内容"""
        # 去除重复句子
        sentences = text.split('。')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in seen:
                unique_sentences.append(sentence)
                seen.add(sentence)
        
        return '。'.join(unique_sentences)
    
    def _extract_core(self, text: str) -> List[str]:
        """提取核心信息"""
        # 分词
        words = text.split()
        
        # 保留关键词和品牌型号信息
        core_words = []
        for word in words:
            # 检查是否为关键词
            if word in self.keep_words:
                core_words.append(word)
            # 检查是否为品牌或型号
            elif self._is_brand_or_model(word):
                core_words.append(word)
            # 检查是否为数字或规格
            elif self._is_spec_info(word):
                core_words.append(word)
        
        return core_words
    
    def _is_brand_or_model(self, word: str) -> bool:
        """判断是否为品牌或型号"""
        # 大写字母开头的词可能是品牌或型号
        if word[0].isupper() and len(word) > 1:
            return True
        return False
    
    def _is_spec_info(self, word: str) -> bool:
        """判断是否为规格信息"""
        # 包含数字和单位的词
        return bool(re.search(r'\d+(米|mm|g|kg|L|M|H|UL)', word))
    
    def _rebuild_text(self, core_words: List[str]) -> str:
        """重建压缩文本"""
        if not core_words:
            return ""
        
        # 按逻辑顺序重建
        text = ' '.join(core_words)
        
        # 确保基本可读性
        text = text.replace('。', '。').replace('，', '，')
        
        return text
    
    def _further_compress(self, text: str) -> str:
        """进一步压缩"""
        # 截取前2000字符
        compressed = text[:2000]
        
        # 确保在句子边界截取
        if compressed[-1] not in ('。！？'):
            last_sentence = compressed.rfind('。')
            if last_sentence > 0:
                compressed = compressed[:last_sentence + 1]
        
        return compressed


class CompressionResult:
    def __init__(self, original_text: str, compressed_text: str, 
                 compression_ratio: float, removed_chars: int):
        self.original_text = original_text
        self.compressed_text = compressed_text
        self.compression_ratio = compression_ratio
        self.removed_chars = removed_chars
        self.compressed_size = len(compressed_text)
        self.original_size = len(original_text)
    
    def __str__(self):
        return f"压缩比: {self.compression_ratio:.2f}, 压缩大小: {self.compressed_size}/{self.original_size}"
```

## 📦 批量导入流程

### 批量处理架构
```python
# packages/agents/equipment_import/core/batch_processor.py
class BatchImportProcessor:
    def __init__(self, batch_size: int = 50, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.extractor = CustomExtractor()
        self.compressor = TextCompressor()

    async def process_batch(self, texts: List[str], 
                           source_type: str = "batch") -> List[ImportResult]:
        """批量处理文本"""
        results = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_results = await self._process_single_batch(batch, source_type)
            results.extend(batch_results)
            
            # 进度回调
            progress = (i + len(batch)) / len(texts)
            await self._on_progress(progress)
        
        return results
    
    async def _process_single_batch(self, texts: List[str], 
                                   source_type: str) -> List[ImportResult]:
        """处理单个批次"""
        tasks = []
        
        # 创建异步任务
        for text in texts:
            task = self._process_text(text, source_type)
            tasks.append(task)
        
        # 并发执行
        return await asyncio.gather(*tasks)
    
    async def _process_text(self, text: str, source_type: str) -> ImportResult:
        """处理单个文本"""
        try:
            # 1. 文本压缩
            if len(text) > 500:
                compression_result = self.compressor.compress(text)
                processed_text = compression_result.compressed_text
            else:
                processed_text = text
                compression_result = None
            
            # 2. 信息提取
            equipment_list = self.extractor.extract(processed_text)
            
            # 3. 构建结果
            result = ImportResult(
                original_text=text,
                processed_text=processed_text,
                compression_result=compression_result,
                equipment_list=equipment_list,
                source_type=source_type,
                success=True
            )
            
            return result
            
        except Exception as e:
            return ImportResult(
                original_text=text,
                processed_text=None,
                compression_result=None,
                equipment_list=[],
                source_type=source_type,
                success=False,
                error=str(e)
            )
    
    async def _on_progress(self, progress: float):
        """进度回调"""
        print(f"处理进度: {progress:.1%}")
        # 这里可以添加WebSocket推送或进度队列更新


@dataclass
class ImportResult:
    original_text: str
    processed_text: Optional[str]
    compression_result: Optional[CompressionResult]
    equipment_list: List[Dict]
    source_type: str
    success: bool
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
```

### 批量导入示例
```python
# 批量导入示例
async def main():
    # 示例文本列表（实际应用中可能来自文件、数据库等）
    texts = [
        "光威赤刃 GT602L-M 路亚竿，碳纤维材质，售价299元",
        "达亿瓦纺车轮 3000C，12轴承，金属机身，价格450元",
        # ... 更多文本
    ]
    
    # 创建批量处理器
    processor = BatchImportProcessor(
        batch_size=20,
        max_workers=4
    )
    
    # 执行批量处理
    results = await processor.process_batch(
        texts=texts,
        source_type="ecommerce"
    )
    
    # 统计结果
    success_count = sum(1 for r in results if r.success)
    total_equipment = sum(len(r.equipment_list) for r in results)
    
    print(f"处理完成: {success_count}/{len(results)} 成功")
    print(f"提取装备: {total_equipment} 个")

# 运行批量导入
if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 数据清洗

### 数据验证规则
```python
# packages/agents/equipment_import/core/validator.py
class EquipmentValidator:
    def __init__(self):
        self.brand_whitelist = {
            "光威", "达亿瓦", "禧玛诺", "阿布", "宝丽", "科尼",
            "佳钓尼", "钓鱼王", "化氏", "老鬼", "大和"
        }
        
        self.category_whitelist = {
            "路亚竿", "纺车轮", "水滴轮", "拟饵", "鱼线", 
            "鱼钩", "浮漂", "竿架", "钓鱼箱"
        }
    
    def validate(self, equipment: Dict) -> ValidationResult:
        """验证装备信息"""
        errors = []
        warnings = []
        
        # 品牌验证
        if equipment.get("brand"):
            if equipment["brand"] not in self.brand_whitelist:
                warnings.append(f"未知品牌: {equipment['brand']}")
        else:
            errors.append("缺少品牌信息")
        
        # 价格验证
        price = equipment.get("price", 0)
        if price <= 0:
            errors.append("价格信息无效")
        elif price > 50000:
            warnings.append(f"价格异常高: ¥{price}")
        
        # 规格验证
        specs = equipment.get("specs", {})
        if specs.get("length"):
            length = float(specs["length"])
            if length <= 0 or length > 10:
                warnings.append(f"长度异常: {length}米")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
```

### 去重处理
```python
# packages/agents/equipment_import/core/deduplicator.py
class EquipmentDeduplicator:
    def __init__(self):
        self.existing_equipment = set()
        
    def deduplicate(self, equipment_list: List[Dict]) -> List[Dict]:
        """去重处理"""
        unique_equipment = []
        
        for equipment in equipment_list:
            # 生成唯一标识
            signature = self._generate_signature(equipment)
            
            if signature not in self.existing_equipment:
                self.existing_equipment.add(signature)
                unique_equipment.append(equipment)
        
        return unique_equipment
    
    def _generate_signature(self, equipment: Dict) -> str:
        """生成装备唯一标识"""
        brand = equipment.get("brand", "")
        model = equipment.get("model", "")
        category = equipment.get("category", "")
        
        # 标准化处理
        brand = brand.upper().strip()
        model = model.upper().strip()
        category = category.strip()
        
        return f"{brand}_{model}_{category}"
```

## 🌐 API接口使用

### RESTful API
```python
# 单个提取接口
POST /api/v1/equipment/import/extract
Content-Type: application/json
Authorization: Bearer {token}

{
    "text": "光威赤刃 GT602L-M 路亚竿，价格299元",
    "source_type": "forum",
    "enable_compression": true
}

# 批量提取接口
POST /api/v1/equipment/import/batch
Content-Type: application/json
Authorization: Bearer {token}

{
    "texts": [
        "文本1...",
        "文本2...",
        "文本3..."
    ],
    "source_type": "ecommerce",
    "enable_compression": true,
    "enable_validation": true
}

# 上传文件接口
POST /api/v1/equipment/import/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

files: [
    (binary file)
]
source_type: file_upload
enable_compression: true
```

### Python SDK
```python
# 安装依赖
pip install fishing-agent-sdk

# 使用SDK
from fishing_agent_sdk import EquipmentImportClient

# 创建客户端
client = EquipmentImportClient(
    base_url="https://api.fishing-agent.com",
    api_key="your-api-key"
)

# 单个提取
result = client.extract_equipment(
    text="光威赤刃 GT602L-M 路亚竿，价格299元",
    source_type="forum"
)

# 批量提取
texts = ["文本1", "文本2", "文本3"]
results = client.batch_extract(texts, source_type="ecommerce")

# 文件上传
results = client.upload_file(
    file_path="./equipment.txt",
    source_type="file_upload"
)
```

## ⚡ 性能优化

### 并发处理
```python
import asyncio
import concurrent.futures
from typing import List, Callable

class ConcurrentProcessor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        
    async def process_concurrent(self, 
                                   texts: List[str], 
                                   process_func: Callable) -> List:
        """并发处理"""
        loop = asyncio.get_event_loop()
        
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 创建任务
            tasks = []
            for text in texts:
                task = loop.run_in_executor(
                    executor, process_func, text
                )
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks)
            
        return results
```

### 缓存优化
```python
import hashlib
import pickle
from pathlib import Path
import time

class CacheManager:
    def __init__(self, cache_dir: str = "./cache", ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl  # 缓存过期时间(秒)
    
    def get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get_cached_result(self, text: str) -> Optional[List]:
        """获取缓存结果"""
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            # 检查缓存是否过期
            file_time = cache_file.stat().st_mtime
            if time.time() - file_time > self.ttl:
                cache_file.unlink()
                return None
            
            # 读取缓存
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    
    def cache_result(self, text: str, result: List):
        """缓存结果"""
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            print(f"缓存失败: {e}")
```

## ❓ 常见问题

### Q: 提取精度不高怎么办？

**A**: 
1. 优化品牌和型号词典
2. 调整提取算法参数
3. 增加样本训练数据
4. 使用多层验证机制

### Q: 批量处理速度慢？

**A**: 
1. 增加并发处理数量
2. 启用文本压缩减少处理量
3. 使用缓存避免重复处理
4. 优化算法复杂度

### Q: 如何处理特殊字符？

**A**: 
1. 添加字符编码转换
2. 使用Unicode标准化
3. 过滤特殊符号和表情
4. 统一数据格式

### Q: 去重效果不理想？

**A**: 
1. 改进唯一标识生成算法
2. 增加模糊匹配功能
3. 考虑相似性阈值
4. 手动合并相似数据

---

**指南版本**: v5.0.2  
**最后更新**: 2024-12-20  
**相关功能**: 智能提取、文本压缩、批量处理