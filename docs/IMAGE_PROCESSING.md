# 图片处理系统文档

## 概述

智能图片处理系统是智能钓鱼助手的核心功能之一，专门用于自动检测和合并带有文字说明的图片。系统支持本地和云端双OCR提供商，可根据需求灵活配置。

### 核心特性
- **多OCR提供商支持**：支持Ollama本地OCR和SiliconFlow云端OCR
- **智能文字检测**：基于图像特征和文件名规则的双重检测机制
- **完全本地化处理**（使用Ollama时）：保护数据隐私，无API调用成本
- **高效批处理**：支持多线程并行处理和智能分组
- **灵活配置**：丰富的配置选项，适应不同使用场景

## 核心功能

### 1. 智能文字检测
- **图像特征分析**：分析图片底部区域的像素分布，识别可能的文字区域
- **文件名规则识别**：基于文件名中的数字编号判断是否需要合并
- **置信度评估**：综合多种因素计算检测结果的置信度

### 2. 批量智能合并
- **自动分组**：根据检测结果智能决定哪些图片需要合并
- **并行处理**：支持多线程并行检测，提高处理效率
- **元数据管理**：自动生成详细的处理报告和统计信息

### 3. 高质量输出
- **格式支持**：支持JPEG、PNG等多种图片格式
- **质量配置**：可配置输出图片质量（1-100）
- **尺寸控制**：支持最大宽度限制，自动调整图片尺寸

## 架构设计

### 核心组件

```
图片处理系统架构：
├── OCR服务层 (apps/api/services/ocr/)
│   ├── base.py              # OCR提供商抽象基类
│   ├── factory.py           # OCR提供商工厂
│   ├── siliconflow_provider.py  # SiliconFlow云端OCR实现
│   ├── ollama_provider.py   # Ollama本地OCR实现
│   └── exceptions.py        # OCR异常定义
├── 图片合并层 (packages/agent_fishing/tools/lure/)
│   ├── image_merger.py      # 图片合并核心模块
│   │   ├── ImageMerger      # 图片合并器类
│   │   ├── merge_vertically()  # 垂直合并方法
│   │   └── merge_with_text_overlay() # 带文字覆盖的合并
│   └── batch_merge_processor.py  # 批量智能合并处理器
│       ├── BatchMergeProcessor # 批处理管理器
│       ├── MergeGroup       # 合并组数据结构
│       └── 智能检测算法实现
└── 服务集成层 (apps/api/services/)
    └── ocr_service.py       # OCR服务集成和封装
```

### 检测算法详解

#### 1. 底部区域文字检测

```python
def _detect_text_by_image_features(self, image_path: str) -> dict:
    """
    基于图像特征检测底部是否有文字

    步骤：
    1. 裁剪图片底部20%区域
    2. 转换为灰度图
    3. 计算暗像素比例（< 180的像素）
    4. 计算标准差（评估像素变化）
    5. 综合判断是否有文字
    """
```

**判断规则：**
- 暗像素比例超过 5%
- 或标准差大于 25（表示有明显变化）

#### 2. 文件名规则检测

```python
def _detect_text_by_filename(self, image_path: str) -> dict:
    """
    基于文件名规则检测

    规则：奇数编号的文件通常需要与下一张合并
    例如：img_001.jpg -> 需要与 img_002.jpg 合并
    """
```

#### 3. 置信度计算

```python
# 对于检测到文字的情况
confidence = min(0.8, dark_ratio * 8 + std_dev / 40)

# 对于未检测到文字的情况
confidence = max(0.2, 1.0 - (dark_ratio * 5 + std_dev / 50))
```

## OCR提供商配置

### 1. Ollama本地OCR（推荐）

**优势**：
- 完全本地处理，保护数据隐私
- 无API调用成本
- 可自定义模型

**配置**：
```bash
# .env 文件
OCR_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-ocr
OLLAMA_TIMEOUT=120
OLLAMA_MAX_SIZE=20971520  # 20MB
```

**前提条件**：
```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载OCR模型
ollama pull deepseek-ocr
```

### 2. SiliconFlow云端OCR

**优势**：
- 识别精度高
- 无需本地计算资源
- 快速部署

**配置**：
```bash
# .env 文件
OCR_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-api-key-here
SILICONFLOW_OCR_TIMEOUT=30
SILICONFLOW_OCR_MAX_SIZE=10485760  # 10MB
```

### 3. 使用示例

```python
from apps.api.services.ocr_service import OCRService

# 创建OCR服务（自动使用配置的提供商）
service = OCRService()

# 单图识别
result = service.recognize_table("image.jpg", verbose=True)

# 批量识别（自动合并）
result = service.recognize_table_from_paths(
    ["img1.jpg", "img2.jpg"],
    verbose=True
)
```

## 图片合并使用指南

### 基本用法

```python
from packages.agent_fishing.tools.lure import BatchMergeProcessor

# 创建批处理器
processor = BatchMergeProcessor(
    source_dir="./input_images",    # 输入目录
    output_dir="./merged_images",   # 输出目录
    quality=95,                     # 输出质量
    bottom_detection_ratio=0.2,     # 底部检测区域比例
    ocr_confidence_threshold=0.5,   # 置信度阈值
    parallel_detection=True,        # 启用并行检测
    max_workers=4                  # 最大线程数
)

# 执行批处理
result = processor.process()

if result["success"]:
    print(f"处理成功!")
    print(f"原始图片: {result['statistics']['total_images']}")
    print(f"输出图片: {result['statistics']['output_count']}")
    print(f"文字检测: {result['statistics']['text_detections']}")
else:
    print(f"处理失败: {result['error']}")
```

### 高级配置

```python
# 自定义配置处理器
processor = BatchMergeProcessor(
    source_dir="./images",
    output_dir="./output",
    quality=98,                      # 更高的输出质量
    bottom_detection_ratio=0.15,     # 检测底部15%区域
    ocr_confidence_threshold=0.6,    # 更严格的置信度要求
    min_text_length=3,              # 最小文字长度
    parallel_detection=True,
    max_workers=8                   # 更多线程
)
```

### 单独使用图片合并器

```python
from packages.agent_fishing.tools.lure import ImageMerger

# 创建合并器
merger = ImageMerger(
    quality=95,
    background_color=(255, 255, 255),  # 白色背景
    max_width=1200,                     # 最大宽度
    spacing=10                          # 图片间距
)

# 合并图片
success = merger.merge_vertically(
    image_paths=["img1.jpg", "img2.jpg"],
    output_path="merged_output.jpg",
    output_format="JPEG"
)
```

## 配置参数详解

### BatchMergeProcessor 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source_dir` | str | - | 源图片目录（必需） |
| `output_dir` | str | "source_dir/merged" | 输出目录 |
| `quality` | int | 95 | JPEG输出质量 (1-100) |
| `bottom_detection_ratio` | float | 0.2 | 底部检测区域比例 (0-1) |
| `ocr_confidence_threshold` | float | 0.5 | OCR置信度阈值 (0-1) |
| `min_text_length` | int | 2 | 最小文字长度 |
| `parallel_detection` | bool | True | 是否启用并行检测 |
| `max_workers` | int | 4 | 并行检测最大线程数 |

### ImageMerger 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `quality` | int | 95 | JPEG输出质量 (1-100) |
| `background_color` | tuple | (255,255,255) | 背景色 (R,G,B) |
| `max_width` | int/None | None | 最大宽度限制 |
| `spacing` | int | 0 | 图片间距（像素） |

## 输出文件命名规则

### 单张图片（无需合并）
```
merge_001.jpg    # 原始第1张图片
merge_002.jpg    # 原始第2张图片
...
```

### 多张图片合并
```
merge_001_002.jpg  # 合并第1-2张图片
merge_003_004.jpg  # 合并第3-4张图片
...
```

## 元数据文件

处理完成后会在输出目录生成 `merge_metadata.json` 文件，包含：

```json
{
  "timestamp": "2024-12-16T10:30:00",
  "source_directory": "/path/to/input",
  "output_directory": "/path/to/output",
  "configuration": {
    "quality": 95,
    "bottom_detection_ratio": 0.2,
    "ocr_confidence_threshold": 0.5
  },
  "statistics": {
    "total_images": 100,
    "merge_groups": 75,
    "original_count": 100,
    "output_count": 75,
    "reduction_ratio": 0.25,
    "smart_grouping_enabled": true,
    "text_detections": 25,
    "cache_hits": 0
  },
  "merge_groups": [
    {
      "group_id": 1,
      "output_file": "merge_001_002.jpg",
      "source_files": ["img_001.jpg", "img_002.jpg"],
      "file_count": 2,
      "indices": [0, 1],
      "reason": "smart merge: image 1 has text below, merging with image 2"
    }
  ]
}
```

## 性能优化

### 1. 并行处理
- 启用 `parallel_detection` 可显著提高处理速度
- 根据 CPU 核心数调整 `max_workers`
- 建议值：CPU 核心数的 1-2 倍

### 2. 缓存机制
- 自动缓存检测结果，避免重复计算
- 基于文件修改时间的缓存失效策略

### 3. 内存管理
- 及时释放图片资源
- 支持大量图片的批处理

## 故障排除

### OCR相关

1. **Ollama服务未启动**
   ```bash
   # 启动Ollama服务
   ollama serve
   ```

2. **OCR模型未下载**
   ```bash
   # 下载deepseek-ocr模型
   ollama pull deepseek-ocr

   # 查看已安装模型
   ollama list
   ```

3. **SiliconFlow API密钥无效**
   - 检查`.env`文件中的`SILICONFLOW_API_KEY`
   - 访问 https://siliconflow.cn/ 获取有效API密钥

4. **OCR识别失败**
   - 检查图片格式是否支持（PNG/JPG/JPEG/WebP）
   - 检查图片大小是否超限
   - 查看服务日志获取详细错误信息

### 图片合并相关

1. **PIL/Pillow 未安装**
   ```bash
   uv add pillow
   ```

2. **内存不足**
   - 减少 `max_workers` 数量
   - 分批处理大量图片

3. **检测不准确**
   - 调整 `bottom_detection_ratio` (0.1-0.3)
   - 调整 `ocr_confidence_threshold` (0.3-0.7)

4. **输出质量不佳**
   - 增加 `quality` 参数 (建议 90-98)
   - 检查原始图片质量

### 调试模式

```python
import logging

# 启用详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建处理器
processor = BatchMergeProcessor("./images")
```

## 最佳实践

1. **图片准备**
   - 确保图片文件名有序（包含数字编号）
   - 建议使用统一的图片格式

2. **参数调优**
   - 根据实际图片特点调整检测参数
   - 小批量测试后再进行大批量处理

3. **结果验证**
   - 检查生成的元数据文件
   - 抽样验证合并结果

4. **性能考虑**
   - 大量图片时建议启用并行处理
   - 监控内存使用情况

## 扩展开发

### 添加自定义检测算法

```python
class CustomBatchMergeProcessor(BatchMergeProcessor):
    def _detect_text_by_custom_method(self, image_path: str) -> dict:
        """实现自定义检测算法"""
        # Your custom detection logic here
        return {
            "has_text": True/False,
            "confidence": 0.8,
            "text": "detected text",
            "error": None
        }

    def _detect_text_below_image(self, image_path: str) -> dict:
        """重写检测方法"""
        # 调用自定义算法
        return self._detect_text_by_custom_method(image_path)
```

### 集成到其他应用

```python
# FastAPI 集成示例
from fastapi import FastAPI, UploadFile, File
from packages.agent_fishing.tools.lure import BatchMergeProcessor
import tempfile
import shutil

app = FastAPI()

@app.post("/merge-images")
async def merge_images(files: List[UploadFile] = File(...)):
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 保存上传的文件
        for file in files:
            with open(f"{temp_dir}/{file.filename}", "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # 执行合并
        processor = BatchMergeProcessor(temp_dir)
        result = processor.process()

        return result
```

## 版本历史

### 图片合并功能
- **v1.0** - 基础图片合并功能
- **v1.1** - 添加智能文字检测
- **v1.2** - 支持并行处理
- **v1.3** - 优化检测算法，添加文件名规则
- **v1.4** - 完善元数据管理和错误处理

### OCR服务
- **v2.0** - 重构OCR服务架构（v5.0.2）
  - 新增多提供商支持（Ollama + SiliconFlow）
  - 实现Factory模式设计
  - 添加提供商自动检测和切换
  - 完善异常处理和错误恢复机制

## 许可证

本模块遵循项目的 MIT 许可证。