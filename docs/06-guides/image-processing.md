# 图片处理指南 v5.0.2

智能钓鱼助手v5.0.2的图片处理功能，包括OCR识别、图片合并、文字检测等。

## 📋 目录

- [功能概览](#功能概览)
- [OCR多提供商](#ocr多提供商)
- [智能图片合并](#智能图片合并)
- [文字区域检测](#文字区域检测)
- [图片预处理](#图片预处理)
- [性能优化](#性能优化)
- [常见问题](#常见问题)

## 🎯 功能概览

### 核心功能
- **OCR文字识别**: 支持多种OCR提供商
- **智能图片合并**: 自动检测相关图片并合并
- **文字区域检测**: 精确定位图片中的文字区域
- **批量处理**: 支持大规模图片批量处理
- **结果优化**: 自动优化识别结果和格式

### 技术特点
- **多提供商支持**: Ollama本地OCR + SiliconFlow云端OCR + 百度OCR
- **智能分组算法**: 基于图像内容的自动分组
- **格式转换**: 支持多种输入输出格式
- **容错机制**: 处理失败时的自动重试和降级

## 🔍 OCR多提供商

### 提供商对比

| 提供商 | 类型 | 优势 | 缺点 | 适用场景 |
|--------|------|------|------|----------|
| **Ollama** | 本地 | 隐私保护、无延迟 | 需要GPU、模型文件大 | 敏感数据、高频调用 |
| **SiliconFlow** | 云端 | 高精度、无需资源 | 网络依赖、产生费用 | 精度要求高、处理量大 |
| **百度OCR** | 云端 | 中文识别强、稳定 | 需要配额、网络依赖 | 中文场景、表格识别 |

### 配置Ollama本地OCR

```python
from packages.data_processing.ocr import OCRMergeProcessor

# 配置本地OCR
processor = OCRMergeProcessor(provider="ollama")

# 设置OCR模型
processor.ollama_model = "deepseek-ocr"
processor.ollama_base_url = "http://localhost:11434"

# 执行识别
result = await processor.recognize_table(["image1.jpg", "image2.jpg"])
```

### 配置SiliconFlow云端OCR

```python
from packages.data_processing.ocr import OCRMergeProcessor

# 配置云端OCR
processor = OCRMergeProcessor(provider="siliconflow")
processor.api_key = "your-siliconflow-api-key"

# 执行识别
result = await processor.recognize_table(["image1.jpg", "image2.jpg"])
```

### 配置百度OCR

```python
from packages.data_processing.ocr import OCRMergeProcessor

# 配置百度OCR
processor = OCRMergeProcessor(provider="baidu")
processor.api_key = "your-baidu-api-key"
processor.secret_key = "your-baidu-secret-key"

# 执行识别
result = await processor.recognize_table(["image1.jpg", "image2.jpg"])
```

### 自动降级策略

```python
class HybridOCRProcessor:
    def __init__(self, primary="ollama", fallback="siliconflow"):
        self.primary = OCRMergeProcessor(provider=primary)
        self.fallback = OCRMergeProcessor(provider=fallback)
    
    async def recognize_with_fallback(self, images):
        try:
            # 尝试主要提供商
            return await self.primary.recognize_table(images)
        except Exception as e:
            # 降级到备用提供商
            return await self.fallback.recognize_table(images)
```

## 🖼️ 智能图片合并

### 合并流程
```
图片输入 → 预处理 → 特征提取 → 相似度计算 → 智能分组 → 合并处理 → 结果输出
```

### 批量合并处理

```python
from packages.data_processing.image import BatchMergeProcessor

# 创建批量处理器
processor = BatchMergeProcessor(
    source_dir="./images",
    output_dir="./merged",
    similarity_threshold=0.8
)

# 执行批量处理
results = processor.process()

# 输出结果
for result in results:
    print(f"合并组: {result.group_id}")
    print(f"源图片: {result.source_images}")
    print(f"合并结果: {result.merged_path}")
```

### 智能分组算法

```python
from packages.data_processing.image.detector import TextRegionDetector

# 创建文字区域检测器
detector = TextRegionDetector()

# 检测图片中的文字区域
regions = detector.detect_text_regions("image.jpg")

# 基于文字区域相似度分组
similar_images = detector.find_similar_images(
    images=["img1.jpg", "img2.jpg", "img3.jpg"],
    regions_list=[regions1, regions2, regions3]
)
```

### 合并策略配置

```python
# 水平合并
horizontal_merge = {
    "direction": "horizontal",
    "spacing": 10,
    "alignment": "top"
}

# 垂直合并
vertical_merge = {
    "direction": "vertical", 
    "spacing": 15,
    "alignment": "left"
}

# 网格合并
grid_merge = {
    "rows": 2,
    "cols": 3,
    "spacing": 5,
    "background_color": "white"
}
```

## 🔍 文字区域检测

### 检测算法

```python
from packages.data_processing.ocr.text_detector import TextRegionDetector

# 创建检测器
detector = TextRegionDetector(
    min_text_area=100,  # 最小文字区域面积
    min_text_height=10,  # 最小文字高度
    merge_threshold=0.5   # 合并相邻区域的阈值
)

# 检测文字区域
regions = detector.detect("image.jpg")

for i, region in enumerate(regions):
    print(f"区域 {i+1}:")
    print(f"  坐标: ({region.x}, {region.y})")
    print(f"  尺寸: {region.width} x {region.height}")
    print(f"  置信度: {region.confidence}")
```

### 区域优化处理

```python
# 区域合并
merged_regions = detector.merge_nearby_regions(
    regions, 
    distance_threshold=20
)

# 区域过滤
filtered_regions = detector.filter_regions(
    regions,
    min_confidence=0.8,
    min_area_ratio=0.1
)

# 区域排序
sorted_regions = detector.sort_regions_by_position(regions)
```

### 表格结构识别

```python
# 表格检测
table_detector = TableDetector()

# 检测表格结构
table_info = table_detector.detect_table("image_with_table.jpg")

# 解析表格内容
table_content = table_detector.parse_table_content(
    table_info,
    ocr_result=ocr_result
)
```

## 🛠️ 图片预处理

### 基础预处理

```python
from PIL import Image, ImageEnhance
import cv2

def preprocess_image(image_path):
    # 加载图片
    img = Image.open(image_path)
    
    # 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    enhanced = enhancer.enhance(2.0)
    
    # 锐化处理
    sharpener = ImageEnhance.Sharpness(enhanced)
    sharpened = sharpener.enhance(1.5)
    
    return sharpened
```

### 降噪处理

```python
import cv2
import numpy as np

def denoise_image(image_path):
    # 读取图片
    img = cv2.imread(image_path)
    
    # 高斯滤波去噪
    denoised = cv2.GaussianBlur(img, (5, 5), 0)
    
    # 中值滤波去椒盐噪声
    denoised = cv2.medianBlur(denoised, 3)
    
    return denoised
```

### 尺寸标准化

```python
def standardize_image(image_path, target_size=(800, 600)):
    img = Image.open(image_path)
    
    # 计算缩放比例
    width, height = img.size
    ratio = min(target_size[0]/width, target_size[1]/height)
    
    # 等比缩放
    new_size = (int(width * ratio), int(height * ratio))
    resized = img.resize(new_size, Image.LANCZOS)
    
    # 添加白色边框到目标尺寸
    padded = Image.new('RGB', target_size, 'white')
    offset = ((target_size[0] - new_size[0]) // 2,
              (target_size[1] - new_size[1]) // 2)
    padded.paste(resized, offset)
    
    return padded
```

## ⚡ 性能优化

### 并行处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def batch_process_images(image_paths, max_workers=4):
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = []
        for image_path in image_paths:
            task = loop.run_in_executor(
                executor, 
                process_single_image, 
                image_path
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
    
    return results

def process_single_image(image_path):
    processor = OCRMergeProcessor()
    return processor.recognize_text(image_path)
```

### 缓存机制

```python
import hashlib
import pickle
from pathlib import Path

class CachedOCRProcessor:
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, image_path):
        # 基于文件内容和路径生成缓存键
        with open(image_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    
    async def recognize_with_cache(self, image_path):
        cache_key = self.get_cache_key(image_path)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # 检查缓存
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        # 执行OCR
        processor = OCRMergeProcessor()
        result = await processor.recognize_text(image_path)
        
        # 保存到缓存
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
        
        return result
```

### 内存优化

```python
import gc

class MemoryEfficientProcessor:
    def __init__(self, max_batch_size=10):
        self.max_batch_size = max_batch_size
    
    async def process_large_dataset(self, image_paths):
        results = []
        
        # 分批处理
        for i in range(0, len(image_paths), self.max_batch_size):
            batch = image_paths[i:i + self.max_batch_size]
            
            # 处理当前批次
            batch_results = await self.process_batch(batch)
            results.extend(batch_results)
            
            # 强制垃圾回收
            gc.collect()
        
        return results
```

## 🚀 API接口使用

### 单图片OCR识别

```python
import requests

# 识别单张图片
with open("equipment.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/ocr/recognize-text",
        files={"file": f},
        headers={"Authorization": "Bearer your-token"}
    )

result = response.json()
print(f"识别结果: {result['text']}")
```

### 批量表格识别

```python
# 批量识别表格
files = []
for image_path in ["table1.jpg", "table2.jpg", "table3.jpg"]:
    files.append(("files", open(image_path, "rb")))

response = requests.post(
    "http://localhost:8000/api/v1/ocr/recognize-table",
    files=files,
    headers={"Authorization": "Bearer your-token"}
)

results = response.json()
for i, result in enumerate(results):
    print(f"表格 {i+1}: {result['markdown']}")
```

### 智能合并处理

```python
# 触发智能合并
response = requests.post(
    "http://localhost:8000/api/v1/image/intelligent-merge",
    json={
        "source_dir": "./images",
        "merge_strategy": "auto",
        "output_format": "markdown"
    },
    headers={"Authorization": "Bearer your-token"}
)

result = response.json()
print(f"合并任务ID: {result['task_id']}")
```

## ❓ 常见问题

### Q: OCR识别准确率低怎么办？

**A**: 
1. 检查图片质量和清晰度
2. 使用适当的预处理增强对比度
3. 尝试不同的OCR提供商
4. 调整检测参数和阈值

### Q: 图片合并效果不理想？

**A**:
1. 调整相似度计算阈值
2. 优化文字区域检测参数
3. 尝试不同的合并策略
4. 手动调整合并顺序

### Q: 处理大量图片时内存溢出？

**A**:
1. 使用分批处理
2. 启用内存缓存限制
3. 定期进行垃圾回收
4. 降低图片分辨率

### Q: 本地OCR模型加载慢？

**A**:
1. 预加载模型到内存
2. 使用SSD存储模型文件
3. 增加系统内存
4. 考虑使用云端OCR

### Q: 如何处理不同格式的图片？

**A**:
1. 使用PIL库进行格式转换
2. 统一预处理流程
3. 支持常见格式：JPG, PNG, BMP, TIFF
4. 转换时保持质量

## 🔧 高级配置

### 环境变量配置
```bash
# OCR配置
OCR_PROVIDER=ollama                    # ollama/siliconflow/baidu
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-ocr
SILICONFLOW_API_KEY=your-api-key
BAIDU_API_KEY=your-baidu-api-key
BAIDU_SECRET_KEY=your-baidu-secret-key

# 图片处理配置
IMAGE_MAX_SIZE=10MB                  # 最大图片大小
IMAGE_BATCH_SIZE=20                   # 批量处理大小
IMAGE_CACHE_ENABLED=true              # 启用缓存
IMAGE_CACHE_TTL=3600                   # 缓存过期时间(秒)
```

### 配置文件示例
```python
# image_config.py
IMAGE_CONFIG = {
    "ocr": {
        "provider": "ollama",
        "fallback_provider": "siliconflow",
        "confidence_threshold": 0.8,
        "max_retry_count": 3
    },
    "merge": {
        "similarity_threshold": 0.8,
        "min_group_size": 2,
        "max_group_size": 10
    },
    "preprocessing": {
        "enhance_contrast": true,
        "sharpen_image": true,
        "denoise": true,
        "standardize_size": (800, 600)
    }
}
```

## 📚 相关资源

### 技术文档
- [Ollama文档](https://ollama.com/documentation) - 本地AI模型
- [SiliconFlow文档](https://siliconflow.cn/docs) - 云端AI服务
- [OpenCV文档](https://opencv.org/docs/) - 计算机视觉
- [Pillow文档](https://pillow.readthedocs.io/) - 图片处理

### 代码示例
- [示例代码仓库](https://github.com/fishing-agent/image-processing-examples)
- [Jupyter Notebook教程](./notebooks/image_processing_tutorial.ipynb)

---

**指南版本**: v5.1.0
**最后更新**: 2026-01-17
**相关功能**: OCR识别、图片合并、文字检测