"""
文字区域检测器

基于 PaddleOCR 的文字检测模型（DBNet），精准检测图片中的文字区域坐标。
支持两种裁剪策略：
1. "最大包围盒"策略 (Union Box) - 把所有文字看作整体，裁剪四周留白
2. "多区域切片"策略 (Multi-Region) - 分别切出分散的文字块

作者: Claude Code
版本: 1.0.0
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# 延迟导入，避免启动时加载大模型
_ocr_instance = None
_cv2 = None
_np = None


def _lazy_import():
    """延迟导入依赖"""
    global _cv2, _np
    if _cv2 is None:
        import cv2
        import numpy as np
        _cv2 = cv2
        _np = np
    return _cv2, _np


def _get_ocr_instance(with_rec: bool = False):
    """获取 PaddleOCR 单例实例

    Args:
        with_rec: 是否启用文字识别（默认只检测位置）
    """
    global _ocr_instance

    # 如果需要识别功能，创建新实例
    if with_rec:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(
            use_angle_cls=False,
            lang="ch",
            show_log=False,
            use_gpu=False,
            det=True,
            rec=True,  # 启用识别
            cls=False
        )
        logger.info("PaddleOCR 检测+识别模型已加载")
        return ocr

    # 只检测模式（单例）
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(
            use_angle_cls=False,
            lang="ch",
            show_log=False,
            use_gpu=False,
            det=True,
            rec=False,
            cls=False
        )
        logger.info("PaddleOCR 检测模型已加载")
    return _ocr_instance


@dataclass
class TextBox:
    """文字框"""
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    confidence: float = 1.0
    text: str = ""  # 识别的文字内容
    char_count: int = 0  # 文字数量

    @property
    def width(self) -> int:
        return self.x_max - self.x_min

    @property
    def height(self) -> int:
        return self.y_max - self.y_min

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x_min + self.x_max) // 2, (self.y_min + self.y_max) // 2)


@dataclass
class HorizontalRegion:
    """横向区域（按y坐标分组的文字行）"""
    y_min: int
    y_max: int
    text_boxes: List[TextBox]
    total_chars: int = 0  # 该行总文字数

    @property
    def height(self) -> int:
        return self.y_max - self.y_min

    @property
    def center_y(self) -> int:
        return (self.y_min + self.y_max) // 2


@dataclass
class CropRegion:
    """裁剪区域"""
    x1: int
    y1: int
    x2: int
    y2: int
    text_boxes: List[TextBox]

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1


class TextRegionDetector:
    """
    文字区域检测器

    使用 PaddleOCR 的 DBNet 检测模型精准定位文字区域。
    """

    def __init__(
        self,
        padding: int = 10,
        min_text_area: int = 100,
        dilation_kernel_size: Tuple[int, int] = (20, 10),
        dilation_iterations: int = 3
    ):
        """
        初始化文字区域检测器

        Args:
            padding: 裁剪时保留的边距（像素）
            min_text_area: 最小文字区域面积，过滤噪点
            dilation_kernel_size: 膨胀核大小 (宽, 高)，用于多区域策略
            dilation_iterations: 膨胀迭代次数
        """
        self.padding = padding
        self.min_text_area = min_text_area
        self.dilation_kernel_size = dilation_kernel_size
        self.dilation_iterations = dilation_iterations

    def detect_text_boxes(self, image_path: str) -> List[TextBox]:
        """
        检测图片中所有文字框的坐标

        Args:
            image_path: 图片路径

        Returns:
            List[TextBox]: 文字框列表
        """
        cv2, np = _lazy_import()
        ocr = _get_ocr_instance()

        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"无法读取图片: {image_path}")
            return []

        # 运行 OCR 检测
        result = ocr.ocr(img, det=True, rec=False, cls=False)

        if not result or result[0] is None:
            logger.info(f"未检测到文字: {image_path}")
            return []

        boxes = result[0]
        text_boxes = []

        for box in boxes:
            # box 格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            points = np.array(box).astype(np.int32)

            # 计算边界框
            x_min = int(np.min(points[:, 0]))
            y_min = int(np.min(points[:, 1]))
            x_max = int(np.max(points[:, 0]))
            y_max = int(np.max(points[:, 1]))

            text_box = TextBox(
                x_min=x_min,
                y_min=y_min,
                x_max=x_max,
                y_max=y_max
            )

            # 过滤太小的区域
            if text_box.area >= self.min_text_area:
                text_boxes.append(text_box)

        logger.info(f"检测到 {len(text_boxes)} 个文字框: {Path(image_path).name}")
        return text_boxes

    def detect_text_with_content(self, image_path: str) -> List[TextBox]:
        """
        检测图片中所有文字框并识别文字内容

        Args:
            image_path: 图片路径

        Returns:
            List[TextBox]: 包含文字内容的文字框列表
        """
        cv2, np = _lazy_import()
        ocr = _get_ocr_instance(with_rec=True)  # 启用识别

        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"无法读取图片: {image_path}")
            return []

        # 运行 OCR 检测+识别
        result = ocr.ocr(img, det=True, rec=True, cls=False)

        if not result or result[0] is None:
            logger.info(f"未检测到文字: {image_path}")
            return []

        text_boxes = []

        for item in result[0]:
            # item 格式: [box, (text, confidence)]
            box = item[0]
            text_info = item[1]
            text = text_info[0] if text_info else ""
            confidence = text_info[1] if text_info and len(text_info) > 1 else 1.0

            points = np.array(box).astype(np.int32)
            x_min = int(np.min(points[:, 0]))
            y_min = int(np.min(points[:, 1]))
            x_max = int(np.max(points[:, 0]))
            y_max = int(np.max(points[:, 1]))

            text_box = TextBox(
                x_min=x_min,
                y_min=y_min,
                x_max=x_max,
                y_max=y_max,
                confidence=confidence,
                text=text,
                char_count=len(text)
            )

            if text_box.area >= self.min_text_area:
                text_boxes.append(text_box)

        logger.info(f"检测到 {len(text_boxes)} 个文字框（含内容）: {Path(image_path).name}")
        return text_boxes

    def analyze_horizontal_regions(
        self,
        text_boxes: List[TextBox],
        image_height: int,
        row_merge_threshold: int = 30
    ) -> List[HorizontalRegion]:
        """
        分析横向区域，按y坐标将文字框分组成行

        Args:
            text_boxes: 文字框列表（需包含文字内容）
            image_height: 图片高度
            row_merge_threshold: 行合并阈值，y坐标差小于此值认为是同一行

        Returns:
            List[HorizontalRegion]: 横向区域列表（按y坐标排序）
        """
        if not text_boxes:
            return []

        # 按y坐标排序
        sorted_boxes = sorted(text_boxes, key=lambda b: b.y_min)

        regions = []
        current_boxes = [sorted_boxes[0]]
        current_y_min = sorted_boxes[0].y_min
        current_y_max = sorted_boxes[0].y_max

        for box in sorted_boxes[1:]:
            # 判断是否属于同一行
            if box.y_min <= current_y_max + row_merge_threshold:
                # 同一行，合并
                current_boxes.append(box)
                current_y_max = max(current_y_max, box.y_max)
            else:
                # 新行，保存当前行
                total_chars = sum(b.char_count for b in current_boxes)
                regions.append(HorizontalRegion(
                    y_min=current_y_min,
                    y_max=current_y_max,
                    text_boxes=current_boxes,
                    total_chars=total_chars
                ))
                # 开始新行
                current_boxes = [box]
                current_y_min = box.y_min
                current_y_max = box.y_max

        # 保存最后一行
        if current_boxes:
            total_chars = sum(b.char_count for b in current_boxes)
            regions.append(HorizontalRegion(
                y_min=current_y_min,
                y_max=current_y_max,
                text_boxes=current_boxes,
                total_chars=total_chars
            ))

        logger.info(f"分析出 {len(regions)} 个横向区域")
        return regions

    def find_sparse_text_regions(
        self,
        image_path: str,
        min_chars: int = 5
    ) -> Dict[str, Any]:
        """
        查找文字数量少于指定值的横向区域

        Args:
            image_path: 图片路径
            min_chars: 最小文字数量阈值

        Returns:
            Dict: {
                "sparse_regions": List[HorizontalRegion],  # 文字少的区域
                "dense_regions": List[HorizontalRegion],   # 文字多的区域
                "all_regions": List[HorizontalRegion],     # 所有区域
                "image_size": (width, height),
                "total_chars": int
            }
        """
        cv2, np = _lazy_import()

        img = cv2.imread(image_path)
        if img is None:
            return {"error": f"无法读取图片: {image_path}"}

        h, w = img.shape[:2]

        # 检测文字内容
        text_boxes = self.detect_text_with_content(image_path)

        if not text_boxes:
            return {
                "sparse_regions": [],
                "dense_regions": [],
                "all_regions": [],
                "image_size": (w, h),
                "total_chars": 0
            }

        # 分析横向区域
        regions = self.analyze_horizontal_regions(text_boxes, h)

        # 按文字数量分类
        sparse_regions = [r for r in regions if r.total_chars < min_chars]
        dense_regions = [r for r in regions if r.total_chars >= min_chars]

        total_chars = sum(r.total_chars for r in regions)

        logger.info(f"文字稀疏区域: {len(sparse_regions)}, 文字密集区域: {len(dense_regions)}")

        return {
            "sparse_regions": sparse_regions,
            "dense_regions": dense_regions,
            "all_regions": regions,
            "image_size": (w, h),
            "total_chars": total_chars
        }

    def get_union_box(
        self,
        text_boxes: List[TextBox],
        image_size: Tuple[int, int]
    ) -> Optional[CropRegion]:
        """
        计算所有文字框的最大外包矩形（最大包围盒策略）

        Args:
            text_boxes: 文字框列表
            image_size: 图片尺寸 (width, height)

        Returns:
            CropRegion: 裁剪区域，如果没有文字则返回 None
        """
        if not text_boxes:
            return None

        w, h = image_size

        # 找到所有文字框的边界
        x_min = min(box.x_min for box in text_boxes)
        y_min = min(box.y_min for box in text_boxes)
        x_max = max(box.x_max for box in text_boxes)
        y_max = max(box.y_max for box in text_boxes)

        # 应用 padding 并防止越界
        x1 = max(0, x_min - self.padding)
        y1 = max(0, y_min - self.padding)
        x2 = min(w, x_max + self.padding)
        y2 = min(h, y_max + self.padding)

        return CropRegion(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            text_boxes=text_boxes
        )

    def get_multi_regions(
        self,
        text_boxes: List[TextBox],
        image_size: Tuple[int, int],
        image_path: str
    ) -> List[CropRegion]:
        """
        获取多个分散的文字区域（多区域切片策略）

        使用形态学膨胀将邻近的文字块连接，然后分别提取各个区域。

        Args:
            text_boxes: 文字框列表
            image_size: 图片尺寸 (width, height)
            image_path: 图片路径（用于创建掩膜）

        Returns:
            List[CropRegion]: 裁剪区域列表
        """
        if not text_boxes:
            return []

        cv2, np = _lazy_import()

        w, h = image_size

        # 创建掩膜
        mask = np.zeros((h, w), dtype=np.uint8)

        # 将文字区域涂成白色
        for box in text_boxes:
            points = np.array([
                [box.x_min, box.y_min],
                [box.x_max, box.y_min],
                [box.x_max, box.y_max],
                [box.x_min, box.y_max]
            ], dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)

        # 膨胀操作，将邻近的文字块连接
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            self.dilation_kernel_size
        )
        dilated = cv2.dilate(mask, kernel, iterations=self.dilation_iterations)

        # 查找轮廓
        contours, _ = cv2.findContours(
            dilated,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        regions = []
        for contour in contours:
            x, y, rect_w, rect_h = cv2.boundingRect(contour)

            # 过滤太小的区域
            if rect_w * rect_h < self.min_text_area:
                continue

            # 应用 padding
            x1 = max(0, x - self.padding)
            y1 = max(0, y - self.padding)
            x2 = min(w, x + rect_w + self.padding)
            y2 = min(h, y + rect_h + self.padding)

            # 找出属于这个区域的文字框
            region_boxes = [
                box for box in text_boxes
                if (box.x_min >= x - self.padding and
                    box.x_max <= x + rect_w + self.padding and
                    box.y_min >= y - self.padding and
                    box.y_max <= y + rect_h + self.padding)
            ]

            regions.append(CropRegion(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                text_boxes=region_boxes
            ))

        # 按 y 坐标排序（从上到下）
        regions.sort(key=lambda r: r.y1)

        logger.info(f"识别出 {len(regions)} 个独立文字区域")
        return regions

    def has_text_in_region(
        self,
        text_boxes: List[TextBox],
        region: Tuple[float, float, float, float],
        image_size: Tuple[int, int]
    ) -> Tuple[bool, float]:
        """
        检测指定区域是否有文字

        Args:
            text_boxes: 文字框列表
            region: (x_min, y_min, x_max, y_max) 相对坐标 (0-1)
            image_size: 图片尺寸 (width, height)

        Returns:
            Tuple[bool, float]: (是否有文字, 置信度)
        """
        if not text_boxes:
            return False, 0.0

        w, h = image_size
        rx_min, ry_min, rx_max, ry_max = region

        # 转换为像素坐标
        px_min = int(rx_min * w)
        py_min = int(ry_min * h)
        px_max = int(rx_max * w)
        py_max = int(ry_max * h)

        # 检查有多少文字框与区域重叠
        overlapping_boxes = []
        for box in text_boxes:
            # 计算重叠区域
            overlap_x_min = max(box.x_min, px_min)
            overlap_y_min = max(box.y_min, py_min)
            overlap_x_max = min(box.x_max, px_max)
            overlap_y_max = min(box.y_max, py_max)

            if overlap_x_min < overlap_x_max and overlap_y_min < overlap_y_max:
                overlap_area = (overlap_x_max - overlap_x_min) * (overlap_y_max - overlap_y_min)
                box_area = box.area
                overlap_ratio = overlap_area / box_area if box_area > 0 else 0

                if overlap_ratio > 0.3:  # 重叠超过30%认为在区域内
                    overlapping_boxes.append(box)

        has_text = len(overlapping_boxes) > 0
        confidence = min(1.0, len(overlapping_boxes) / 3)  # 3个以上框认为高置信度

        return has_text, confidence


class TextRegionCropper:
    """
    文字区域裁剪器

    基于 PaddleOCR 检测结果裁剪图片中的文字区域。
    """

    def __init__(
        self,
        padding: int = 10,
        strategy: str = "union",
        min_text_area: int = 100
    ):
        """
        初始化裁剪器

        Args:
            padding: 裁剪边距
            strategy: 裁剪策略 "union" 或 "multi"
            min_text_area: 最小文字区域面积
        """
        self.detector = TextRegionDetector(
            padding=padding,
            min_text_area=min_text_area
        )
        self.strategy = strategy
        self.padding = padding

    def crop_text_area(
        self,
        image_path: str,
        output_path: str,
        strategy: str = None
    ) -> Dict[str, Any]:
        """
        裁剪图片中的文字区域

        Args:
            image_path: 输入图片路径
            output_path: 输出图片路径
            strategy: 裁剪策略，覆盖初始化时的设置

        Returns:
            Dict: {
                "success": bool,
                "original_size": (width, height),
                "cropped_size": (width, height),
                "regions_count": int,
                "output_files": List[str],
                "error": Optional[str]
            }
        """
        cv2, np = _lazy_import()

        strategy = strategy or self.strategy

        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            return {
                "success": False,
                "error": f"无法读取图片: {image_path}"
            }

        h, w = img.shape[:2]
        original_size = (w, h)

        # 检测文字框
        text_boxes = self.detector.detect_text_boxes(image_path)

        if not text_boxes:
            return {
                "success": False,
                "original_size": original_size,
                "error": "未检测到文字"
            }

        output_files = []

        if strategy == "union":
            # 最大包围盒策略
            region = self.detector.get_union_box(text_boxes, (w, h))
            if region:
                cropped = img[region.y1:region.y2, region.x1:region.x2]
                cv2.imwrite(output_path, cropped)
                output_files.append(output_path)

                logger.info(
                    f"裁剪完成: {w}x{h} -> {region.width}x{region.height}"
                )

                return {
                    "success": True,
                    "original_size": original_size,
                    "cropped_size": (region.width, region.height),
                    "regions_count": 1,
                    "output_files": output_files,
                    "text_boxes_count": len(text_boxes)
                }

        else:
            # 多区域切片策略
            regions = self.detector.get_multi_regions(text_boxes, (w, h), image_path)

            if not regions:
                return {
                    "success": False,
                    "original_size": original_size,
                    "error": "未识别出有效区域"
                }

            # 生成输出文件名
            output_dir = Path(output_path).parent
            output_stem = Path(output_path).stem
            output_ext = Path(output_path).suffix

            for i, region in enumerate(regions):
                cropped = img[region.y1:region.y2, region.x1:region.x2]

                if len(regions) == 1:
                    out_path = output_path
                else:
                    out_path = str(output_dir / f"{output_stem}_part{i+1}{output_ext}")

                cv2.imwrite(out_path, cropped)
                output_files.append(out_path)

                logger.info(f"裁剪区域 {i+1}: {region.width}x{region.height}")

            return {
                "success": True,
                "original_size": original_size,
                "cropped_size": (regions[0].width, regions[0].height) if len(regions) == 1 else None,
                "regions_count": len(regions),
                "output_files": output_files,
                "text_boxes_count": len(text_boxes)
            }

        return {
            "success": False,
            "original_size": original_size,
            "error": "处理失败"
        }

    def crop_batch(
        self,
        image_paths: List[str],
        output_dir: str,
        strategy: str = None
    ) -> Dict[str, Any]:
        """
        批量裁剪图片

        Args:
            image_paths: 输入图片路径列表
            output_dir: 输出目录
            strategy: 裁剪策略

        Returns:
            Dict: 批量处理结果
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        success_count = 0
        error_count = 0
        all_output_files = []

        for image_path in image_paths:
            filename = Path(image_path).stem
            ext = Path(image_path).suffix
            output_path = str(output_dir / f"{filename}_cropped{ext}")

            result = self.crop_text_area(image_path, output_path, strategy)
            results.append({
                "input": image_path,
                **result
            })

            if result["success"]:
                success_count += 1
                all_output_files.extend(result.get("output_files", []))
            else:
                error_count += 1

        return {
            "success": error_count == 0,
            "total": len(image_paths),
            "success_count": success_count,
            "error_count": error_count,
            "output_files": all_output_files,
            "results": results
        }


# 便捷函数
def crop_text_area(
    image_path: str,
    output_path: str,
    padding: int = 10,
    strategy: str = "union"
) -> Dict[str, Any]:
    """
    便捷函数：裁剪图片中的文字区域

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径
        padding: 边距
        strategy: 策略 "union" 或 "multi"

    Returns:
        Dict: 处理结果
    """
    cropper = TextRegionCropper(padding=padding, strategy=strategy)
    return cropper.crop_text_area(image_path, output_path)


def detect_text_boxes(image_path: str) -> List[TextBox]:
    """
    便捷函数：检测图片中的文字框

    Args:
        image_path: 图片路径

    Returns:
        List[TextBox]: 文字框列表
    """
    detector = TextRegionDetector()
    return detector.detect_text_boxes(image_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python text_region_detector.py <input_image> <output_image> [strategy]")
        print("  strategy: union (default) or multi")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    strategy = sys.argv[3] if len(sys.argv) > 3 else "union"

    result = crop_text_area(input_path, output_path, padding=20, strategy=strategy)

    if result["success"]:
        print(f"裁剪成功！")
        print(f"原图尺寸: {result['original_size']}")
        print(f"输出文件: {result['output_files']}")
    else:
        print(f"裁剪失败: {result.get('error')}")
