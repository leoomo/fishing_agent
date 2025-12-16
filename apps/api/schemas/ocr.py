"""
OCR API 数据模型

用于图片表格识别功能的请求和响应模型。
"""

from typing import Optional
from pydantic import BaseModel, Field


class OCRMetadata(BaseModel):
    """OCR识别元数据"""
    model: str = Field(default="deepseek-ai/DeepSeek-OCR", description="使用的模型")
    processing_time_ms: int = Field(..., description="处理时间（毫秒）")
    images_merged: int = Field(default=1, description="合并的图片数量")
    image_size_bytes: Optional[int] = Field(None, description="图片大小（字节）")


class OCRRecognizeResponse(BaseModel):
    """OCR识别响应"""
    success: bool = Field(..., description="是否成功")
    markdown: Optional[str] = Field(None, description="识别结果（Markdown格式）")
    metadata: Optional[OCRMetadata] = Field(None, description="元数据")
    error: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "markdown": "| 参数 | 数值 |\n|---|---|\n| 长度 | 2.1m |\n| 调性 | M |",
                "metadata": {
                    "model": "deepseek-ai/DeepSeek-OCR",
                    "processing_time_ms": 1234,
                    "images_merged": 2,
                    "image_size_bytes": 102400
                }
            }
        }
