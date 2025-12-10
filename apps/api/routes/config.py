from fastapi import APIRouter, HTTPException, Query, Depends
import logging
from typing import Optional, List

from apps.api.schemas.config import (
    ConfigCreate,
    ConfigUpdate,
    ConfigResponse,
    TestAPIKeyRequest,
    TestAPIKeyResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.config_service import ConfigService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/configs",
    response_model=List[ConfigResponse],
    summary="查询配置列表",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_READ))]
)
async def list_configs(
    config_type: Optional[str] = Query(None, description="配置类型过滤")
):
    """
    查询配置列表

    Args:
        config_type: 配置类型（agent/algorithm/api/system）

    Returns:
        List[ConfigResponse]: 配置列表
    """
    try:
        config_service = ConfigService()
        configs = config_service.list_configs(config_type=config_type)

        return [ConfigResponse(**config) for config in configs]

    except Exception as e:
        logger.error(f"查询配置列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get(
    "/configs/{config_key}",
    response_model=ConfigResponse,
    summary="获取配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_READ))]
)
async def get_config(config_key: str):
    """
    获取配置

    Args:
        config_key: 配置键

    Returns:
        ConfigResponse: 配置信息

    Raises:
        HTTPException: 配置不存在
    """
    try:
        config_service = ConfigService()
        config = config_service.get_config(config_key)

        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")

        return ConfigResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post(
    "/configs",
    response_model=ConfigResponse,
    summary="创建配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_CREATE))]
)
async def create_config(
    config_data: ConfigCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONFIG_CREATE))
):
    """
    创建配置

    Args:
        config_data: 配置数据

    Returns:
        ConfigResponse: 创建的配置

    Raises:
        HTTPException: 配置键已存在
    """
    try:
        config_service = ConfigService()

        config = config_service.create_config(
            config_key=config_data.config_key,
            config_value=config_data.config_value,
            config_type=config_data.config_type,
            description=config_data.description,
            is_encrypted=config_data.is_encrypted
        )

        logger.info(
            f"配置创建成功: key={config_data.config_key}, "
            f"user={current_user.username}"
        )

        return ConfigResponse(**config)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put(
    "/configs/{config_key}",
    response_model=ConfigResponse,
    summary="更新配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_UPDATE))]
)
async def update_config(
    config_key: str,
    config_data: ConfigUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONFIG_UPDATE))
):
    """
    更新配置

    Args:
        config_key: 配置键
        config_data: 更新数据

    Returns:
        ConfigResponse: 更新后的配置

    Raises:
        HTTPException: 配置不存在
    """
    try:
        config_service = ConfigService()

        config = config_service.update_config(
            config_key=config_key,
            config_value=config_data.config_value,
            description=config_data.description
        )

        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")

        logger.info(f"配置更新成功: key={config_key}, user={current_user.username}")

        return ConfigResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete(
    "/configs/{config_key}",
    status_code=204,
    summary="删除配置",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_DELETE))]
)
async def delete_config(
    config_key: str,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONFIG_DELETE))
):
    """
    删除配置

    Args:
        config_key: 配置键

    Raises:
        HTTPException: 配置不存在
    """
    try:
        config_service = ConfigService()

        success = config_service.delete_config(config_key)

        if not success:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")

        logger.info(f"配置删除成功: key={config_key}, user={current_user.username}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post(
    "/configs/test-api-key",
    response_model=TestAPIKeyResponse,
    summary="测试 API 密钥",
    dependencies=[Depends(require_permission(PermissionEnum.CONFIG_TEST))]
)
async def test_api_key(request: TestAPIKeyRequest):
    """
    测试 API 密钥有效性

    Args:
        request: 测试请求

    Returns:
        TestAPIKeyResponse: 测试结果
    """
    try:
        config_service = ConfigService()

        result = config_service.test_api_key(
            api_provider=request.api_provider,
            api_key=request.api_key
        )

        return TestAPIKeyResponse(**result)

    except Exception as e:
        logger.error(f"测试 API 密钥失败: {e}", exc_info=True)
        return TestAPIKeyResponse(
            valid=False,
            message=f"测试失败: {str(e)}"
        )
