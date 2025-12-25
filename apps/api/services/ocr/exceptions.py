"""
OCR 服务异常类

定义OCR相关的自定义异常
"""


class OCRError(Exception):
    """OCR 错误基类"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class SiliconFlowError(OCRError):
    """SiliconFlow API 相关错误"""
    pass


class OllamaError(OCRError):
    """Ollama 相关错误"""
    pass


class BaiduError(OCRError):
    """百度 OCR 相关错误"""
    pass


class OCRProviderNotAvailableError(OCRError):
    """OCR 提供商不可用错误"""
    pass


class OCRConfigurationError(OCRError):
    """OCR 配置错误"""
    pass


class OCRModelNotFoundError(OCRError):
    """OCR 模型未找到错误"""
    pass


class OCRProcessingError(OCRError):
    """OCR 处理错误"""
    pass