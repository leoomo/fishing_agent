"""
OCR - 文字检测模块
"""

from .text_detector import (
    TextRegionDetector,
    TextRegionCropper,
    TextBox,
    CropRegion,
    HorizontalRegion,
    crop_text_area,
    detect_text_boxes
)
from .ocr_processor import (
    OCRMergeProcessor,
    ProcessedImage,
    ProcessingResult,
    create_ocr_merge_processor
)

__all__ = [
    # Text Detector
    "TextRegionDetector",
    "TextRegionCropper",
    "TextBox",
    "CropRegion",
    "HorizontalRegion",
    "crop_text_area",
    "detect_text_boxes",
    # OCR Processor
    "OCRMergeProcessor",
    "ProcessedImage",
    "ProcessingResult",
    "create_ocr_merge_processor",
]
