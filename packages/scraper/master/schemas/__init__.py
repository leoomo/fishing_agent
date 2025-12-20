"""
Master Service Schemas

请求/响应数据模型
"""

from .node import (
    NodeRegisterRequest,
    NodeRegisterResponse,
    NodeAuthRequest,
    NodeAuthResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    NodeInfo,
    NodeListResponse,
    NodeUpdateRequest,
    TaskClaimRequest,
    TaskProgressRequest,
    TaskCompleteRequest,
    TaskFailRequest,
    TaskInfo,
    TaskListResponse,
    ImageUploadResponse,
    ImageBatchUploadResponse,
)

__all__ = [
    "NodeRegisterRequest",
    "NodeRegisterResponse",
    "NodeAuthRequest",
    "NodeAuthResponse",
    "HeartbeatRequest",
    "HeartbeatResponse",
    "NodeInfo",
    "NodeListResponse",
    "NodeUpdateRequest",
    "TaskClaimRequest",
    "TaskProgressRequest",
    "TaskCompleteRequest",
    "TaskFailRequest",
    "TaskInfo",
    "TaskListResponse",
    "ImageUploadResponse",
    "ImageBatchUploadResponse",
]
