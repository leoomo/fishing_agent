from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ConfigCreate(BaseModel):
    """创建配置请求"""
    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: str = Field(..., description="配置值（JSON字符串）")
    config_type: str = Field(
        ...,
        pattern="^(agent|algorithm|api|system)$",
        description="配置类型"
    )
    description: Optional[str] = Field(None, description="描述")
    is_encrypted: bool = Field(default=False, description="是否加密")


class ConfigUpdate(BaseModel):
    """更新配置请求"""
    config_value: str = Field(..., description="配置值（JSON字符串）")
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    """配置响应"""
    id: int
    config_key: str
    config_value: Any  # 已解析的 JSON
    config_type: str
    description: Optional[str] = None
    is_encrypted: bool
    created_at: str
    updated_at: str


class TestAPIKeyRequest(BaseModel):
    """测试 API 密钥请求"""
    api_provider: str = Field(
        ...,
        pattern="^(dashscope|caiyun|amap)$",
        description="API 提供商"
    )
    api_key: str = Field(..., description="API 密钥")


class TestAPIKeyResponse(BaseModel):
    """测试 API 密钥响应"""
    valid: bool
    message: str
