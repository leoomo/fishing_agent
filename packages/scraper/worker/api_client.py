"""
Worker Client for apps/api

适配 apps/api 的 /api/v1/worker/* API 端点
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ApiWorkerClient:
    """
    Worker客户端 - 适配 apps/api 的 /api/v1/worker/* API

    API端点:
    - POST /api/v1/worker/register - 注册获取 token
    - POST /api/v1/worker/claim - 领取任务
    - POST /api/v1/worker/report - 汇报进度
    - POST /api/v1/worker/heartbeat - 心跳
    """

    def __init__(
        self,
        server_url: str,
        worker_id: Optional[str] = None,
        worker_name: Optional[str] = None,
        supported_types: List[str] = None,
        max_concurrent: int = 1,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        初始化Worker客户端

        Args:
            server_url: 服务器地址 (如 http://localhost:8000)
            worker_id: Worker ID (注册后返回)
            worker_name: Worker 名称
            supported_types: 支持的任务类型
            max_concurrent: 最大并发数
            timeout: 请求超时(秒)
            max_retries: 最大重试次数
        """
        self.server_url = server_url.rstrip('/')
        self.worker_id = worker_id
        self.worker_name = worker_name or 'Worker'
        self.supported_types = supported_types or ['taobao', 'jd', 'forum']
        self.max_concurrent = max_concurrent
        self.timeout = timeout

        # 认证 Token (格式: worker_id:api_key)
        self.token: Optional[str] = None

        # HTTP Session (带重试)
        self.session = self._create_session(max_retries)

    def _create_session(self, max_retries: int) -> requests.Session:
        """创建带重试机制的 HTTP Session"""
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['X-Worker-Token'] = self.token
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> requests.Response:
        """发送HTTP请求"""
        url = f'{self.server_url}/api/v1/worker{endpoint}'

        if 'headers' not in kwargs:
            kwargs['headers'] = {}

        # 添加认证头
        kwargs['headers'].update(self._get_headers())

        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    # ========== 注册 ==========

    def register(self) -> bool:
        """
        注册Worker

        Returns:
            是否成功
        """
        try:
            payload = {
                'worker_id': self.worker_id,
                'worker_name': self.worker_name,
                'supported_types': self.supported_types,
                'max_concurrent': self.max_concurrent,
            }

            response = self.session.post(
                f'{self.server_url}/api/v1/worker/register',
                json=payload,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            self.token = data.get('token')
            self.worker_id = data.get('worker_id', self.worker_id)

            logger.info(f"注册成功: worker_id={self.worker_id}")
            return True

        except requests.RequestException as e:
            logger.error(f"注册失败: {e}")
            return False

    # ========== 心跳 ==========

    def heartbeat(
        self,
        current_tasks: List[int] = None,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
    ) -> Optional[Dict]:
        """
        发送心跳

        Args:
            current_tasks: 当前执行的任务ID列表
            cpu_usage: CPU使用率
            memory_usage: 内存使用率

        Returns:
            响应数据，包含 commands 列表
        """
        try:
            payload = {
                'worker_id': self.worker_id,
                'current_tasks': current_tasks or [],
            }
            if cpu_usage is not None:
                payload['cpu_usage'] = cpu_usage
            if memory_usage is not None:
                payload['memory_usage'] = memory_usage

            response = self._request('POST', '/heartbeat', json=payload)
            return response.json()

        except requests.RequestException as e:
            logger.error(f"心跳失败: {e}")
            return None

    # ========== 任务操作 ==========

    def claim_tasks(self, max_tasks: int = 1) -> List[Dict]:
        """
        领取任务

        Args:
            max_tasks: 最多领取任务数

        Returns:
            任务列表
        """
        try:
            payload = {
                'worker_id': self.worker_id,
                'supported_types': self.supported_types,
                'max_tasks': max_tasks,
            }

            response = self._request('POST', '/claim', json=payload)
            data = response.json()

            tasks = data.get('tasks', [])
            if tasks:
                logger.info(f"领取到 {len(tasks)} 个任务")

            return tasks

        except requests.RequestException as e:
            logger.error(f"领取任务失败: {e}")
            return []

    def report_progress(
        self,
        task_id: int,
        status: str,
        progress: int = 0,
        message: str = '',
        success_items: int = 0,
        failed_items: int = 0,
        total_items: int = 0,
        error_message: Optional[str] = None,
        result_data: Optional[Dict] = None,
    ) -> bool:
        """
        汇报任务进度

        Args:
            task_id: 任务ID
            status: 状态 (running/success/failed)
            progress: 进度 0-100
            message: 消息
            success_items: 成功数量
            failed_items: 失败数量
            total_items: 总数量
            error_message: 错误信息
            result_data: 结果数据

        Returns:
            是否成功
        """
        try:
            payload = {
                'task_id': task_id,
                'worker_id': self.worker_id,
                'status': status,
                'progress': progress,
                'message': message,
                'success_items': success_items,
                'failed_items': failed_items,
                'total_items': total_items,
            }

            if error_message:
                payload['error_message'] = error_message
            if result_data:
                payload['result_data'] = result_data

            self._request('POST', '/report', json=payload)
            return True

        except requests.RequestException as e:
            logger.error(f"汇报失败: {e}")
            return False

    # ========== 图片上传 ==========

    def upload_images(
        self,
        task_id: int,
        products: List[Dict],
        image_files: List[tuple],
    ) -> Optional[Dict]:
        """
        上传产品图片

        Args:
            task_id: 任务ID
            products: 产品元数据列表
                [{"product_id", "brand_name", "product_name", "source_url", "image_count", "equipment_type"}]
            image_files: 图片文件列表，元素为 (filename, file_object)
                文件名格式: {product_index}_{image_index}.{ext}

        Returns:
            上传结果
        """
        try:
            # 构造 multipart/form-data
            # image_files 格式: [(filename, file_obj), ...]
            files = [('files', (filename, file_obj)) for filename, file_obj in image_files]
            data = {
                'task_id': str(task_id),
                'products': json.dumps(products, ensure_ascii=False),
            }

            logger.info(f"开始上传: task_id={task_id}, products={len(products)}, files={len(image_files)}")

            # 使用 Worker 专用上传端点
            url = f'{self.server_url}/api/v1/worker/upload-images'

            # 构建 headers（不设置 Content-Type，让 requests 自动生成 multipart 边界）
            headers = {}
            if self.token:
                headers['X-Worker-Token'] = self.token

            response = self.session.post(
                url,
                files=files,
                data=data,
                headers=headers,  # 只设置认证头，不设置 Content-Type
                timeout=120,  # 上传可能需要更长时间
            )

            # 打印响应状态
            logger.info(f"上传响应: status={response.status_code}")

            response.raise_for_status()

            result = response.json()
            logger.info(
                f"上传完成: task_id={task_id}, "
                f"uploaded={result.get('uploaded_count')}, "
                f"skipped={result.get('skipped_count')}, "
                f"failed={result.get('failed_count')}"
            )

            return result

        except requests.RequestException as e:
            logger.error(f"图片上传失败: {e}")
            # 尝试读取响应内容
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"响应内容: {e.response.text}")
            return None
