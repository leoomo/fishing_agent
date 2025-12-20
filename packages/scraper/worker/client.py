"""
Worker Client SDK

Worker与Master通信的HTTP客户端
"""

import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class WorkerClient:
    """
    Worker与Master通信的HTTP客户端

    Features:
    - 自动重试机制
    - Token自动刷新
    - 离线数据缓存
    - 图片上传（单张和批量）
    """

    def __init__(
        self,
        master_url: str,
        node_id: str,
        node_secret: str,
        cache_dir: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        初始化WorkerClient

        Args:
            master_url: Master服务地址
            node_id: 节点ID
            node_secret: 节点密钥
            cache_dir: 离线缓存目录
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.master_url = master_url.rstrip('/')
        self.node_id = node_id
        self.node_secret = node_secret
        self.timeout = timeout
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # 离线缓存目录
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(f'~/.crawler_worker/{node_id}').expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 配置HTTP会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> requests.Response:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: requests参数

        Returns:
            Response对象

        Raises:
            requests.RequestException: 请求失败
        """
        url = f'{self.master_url}/api/v1/nodes/{self.node_id}{endpoint}'

        if 'headers' not in kwargs:
            kwargs['headers'] = {}

        # 添加认证头（非multipart请求）
        if self.token and 'files' not in kwargs:
            kwargs['headers']['Authorization'] = f'Bearer {self.token}'
        elif self.token:
            kwargs['headers']['Authorization'] = f'Bearer {self.token}'

        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        response = self.session.request(method, url, **kwargs)

        # 处理认证过期
        if response.status_code == 401:
            logger.warning("Token expired, re-authenticating...")
            if self.authenticate():
                # 更新认证头并重试
                if 'files' not in kwargs:
                    kwargs['headers']['Authorization'] = f'Bearer {self.token}'
                else:
                    kwargs['headers']['Authorization'] = f'Bearer {self.token}'
                response = self.session.request(method, url, **kwargs)

        response.raise_for_status()
        return response

    # ========== 认证 ==========

    def authenticate(self) -> bool:
        """
        获取访问Token

        Returns:
            True if authenticated successfully
        """
        try:
            url = f'{self.master_url}/api/v1/nodes/auth/token'
            response = self.session.post(
                url,
                json={
                    'node_id': self.node_id,
                    'node_secret': self.node_secret,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            self.token = data['token']
            self.token_expires_at = datetime.fromisoformat(
                data['expires_at'].replace('Z', '+00:00')
            )

            logger.info(f"Authenticated successfully, token expires at {self.token_expires_at}")
            return True

        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def is_token_valid(self) -> bool:
        """检查Token是否有效"""
        if not self.token or not self.token_expires_at:
            return False
        # 提前5分钟刷新
        return datetime.utcnow() < self.token_expires_at.replace(tzinfo=None)

    def ensure_authenticated(self) -> bool:
        """确保已认证"""
        if not self.is_token_valid():
            return self.authenticate()
        return True

    # ========== 心跳 ==========

    def heartbeat(
        self,
        current_tasks: int = 0,
        running_task_ids: Optional[List[int]] = None,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        disk_usage: Optional[float] = None,
        worker_version: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        发送心跳

        Args:
            current_tasks: 当前运行任务数
            running_task_ids: 正在运行的任务ID列表
            cpu_usage: CPU使用率
            memory_usage: 内存使用率
            disk_usage: 磁盘使用率
            worker_version: Worker版本号

        Returns:
            心跳响应或None
        """
        try:
            self.ensure_authenticated()

            payload = {
                'current_tasks': current_tasks,
                'running_task_ids': running_task_ids or [],
            }
            if cpu_usage is not None:
                payload['cpu_usage'] = cpu_usage
            if memory_usage is not None:
                payload['memory_usage'] = memory_usage
            if disk_usage is not None:
                payload['disk_usage'] = disk_usage
            if worker_version:
                payload['worker_version'] = worker_version

            response = self._request('POST', '/heartbeat', json=payload)
            data = response.json()

            # 心跳成功，同步缓存数据
            self.sync_cached_results()
            self.sync_cached_images()

            return data

        except requests.RequestException as e:
            logger.error(f"Heartbeat failed: {e}")
            return None

    # ========== 任务操作 ==========

    def get_tasks(self, limit: int = 10) -> List[Dict]:
        """
        获取可用任务列表

        Returns:
            任务列表
        """
        try:
            self.ensure_authenticated()
            response = self._request('GET', f'/tasks?limit={limit}')
            data = response.json()
            return data.get('tasks', [])
        except requests.RequestException as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

    def claim_task(self, task_id: int) -> Optional[Dict]:
        """
        认领任务

        Args:
            task_id: 任务ID

        Returns:
            任务信息或None
        """
        try:
            self.ensure_authenticated()
            response = self._request('POST', f'/tasks/{task_id}/claim')
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to claim task {task_id}: {e}")
            return None

    def report_progress(
        self,
        task_id: int,
        progress: int,
        message: Optional[str] = None,
        current_items: Optional[int] = None,
        total_items: Optional[int] = None,
    ) -> bool:
        """
        上报任务进度

        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
            current_items: 当前处理项数
            total_items: 总项数

        Returns:
            是否成功
        """
        try:
            self.ensure_authenticated()

            payload = {'progress': progress}
            if message:
                payload['message'] = message
            if current_items is not None:
                payload['current_items'] = current_items
            if total_items is not None:
                payload['total_items'] = total_items

            self._request('PUT', f'/tasks/{task_id}/progress', json=payload)
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to report progress for task {task_id}: {e}")
            return False

    def complete_task(
        self,
        task_id: int,
        success_items: int = 0,
        failed_items: int = 0,
        total_items: int = 0,
        duplicate_items: int = 0,
        result_summary: Optional[Dict] = None,
        result_data: Optional[List[Dict]] = None,
        image_stats: Optional[Dict] = None,
    ) -> bool:
        """
        上报任务完成

        支持离线缓存
        """
        payload = {
            'success_items': success_items,
            'failed_items': failed_items,
            'total_items': total_items,
            'duplicate_items': duplicate_items,
        }
        if result_summary:
            payload['result_summary'] = result_summary
        if result_data:
            payload['result_data'] = result_data
        if image_stats:
            payload['image_stats'] = image_stats

        try:
            self.ensure_authenticated()
            self._request('POST', f'/tasks/{task_id}/complete', json=payload)
            logger.info(f"Task {task_id} completed successfully")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            # 缓存到本地
            self._cache_result(task_id, 'complete', payload)
            return False

    def fail_task(
        self,
        task_id: int,
        error_message: str,
        error_details: Optional[Dict] = None,
        should_retry: bool = True,
    ) -> bool:
        """
        上报任务失败

        支持离线缓存
        """
        payload = {
            'error_message': error_message,
            'should_retry': should_retry,
        }
        if error_details:
            payload['error_details'] = error_details

        try:
            self.ensure_authenticated()
            self._request('POST', f'/tasks/{task_id}/fail', json=payload)
            logger.info(f"Task {task_id} failure reported")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to report task {task_id} failure: {e}")
            # 缓存到本地
            self._cache_result(task_id, 'fail', payload)
            return False

    # ========== 图片上传 ==========

    def upload_image(
        self,
        task_id: int,
        image_path: Path,
        image_type: str,
        original_url: str,
        equipment_name: str = "unknown",
    ) -> Optional[Dict]:
        """
        上传单张图片到Master

        Args:
            task_id: 任务ID
            image_path: 本地图片路径
            image_type: 图片类型 (main/detail/spec)
            original_url: 原始图片URL (用于去重)
            equipment_name: 装备名称

        Returns:
            上传结果或None
        """
        try:
            self.ensure_authenticated()

            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/jpeg')}
                data = {
                    'image_type': image_type,
                    'original_url': original_url,
                    'equipment_name': equipment_name,
                }

                url = f'{self.master_url}/api/v1/nodes/{self.node_id}/tasks/{task_id}/images'
                headers = {'Authorization': f'Bearer {self.token}'}

                response = self.session.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.timeout * 2,  # 图片上传给更长超时
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            # 缓存到本地
            self._cache_image(task_id, image_path, image_type, original_url, equipment_name)
            return None

    def upload_images_batch(
        self,
        task_id: int,
        images: List[Dict],
    ) -> Optional[Dict]:
        """
        批量上传图片

        Args:
            task_id: 任务ID
            images: 图片列表 [{"path": Path, "type": "main", "url": "...", "name": "..."}]

        Returns:
            批量上传结果或None
        """
        try:
            self.ensure_authenticated()

            files = []
            metadata = []

            for img in images:
                img_path = Path(img['path'])
                if not img_path.exists():
                    logger.warning(f"Image not found: {img_path}")
                    continue

                with open(img_path, 'rb') as f:
                    content = f.read()
                    files.append(('files', (img_path.name, content, 'image/jpeg')))
                    metadata.append({
                        'image_type': img.get('type', 'detail'),
                        'original_url': img.get('url', ''),
                        'equipment_name': img.get('name', 'unknown'),
                    })

            if not files:
                return {'total': 0, 'saved': 0, 'duplicates': 0, 'errors': 0, 'images': []}

            data = {'metadata': json.dumps(metadata)}

            url = f'{self.master_url}/api/v1/nodes/{self.node_id}/tasks/{task_id}/images/batch'
            headers = {'Authorization': f'Bearer {self.token}'}

            response = self.session.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout * 3,  # 批量上传给更长超时
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Batch image upload failed: {e}")
            # 降级为逐个缓存
            for img in images:
                self._cache_image(
                    task_id,
                    Path(img['path']),
                    img.get('type', 'detail'),
                    img.get('url', ''),
                    img.get('name', 'unknown'),
                )
            return None

    # ========== 离线缓存 ==========

    def _cache_result(self, task_id: int, action: str, payload: Dict):
        """缓存任务结果"""
        cache_file = self.cache_dir / 'results' / f'task_{task_id}_{action}.json'
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({
            'task_id': task_id,
            'action': action,
            'payload': payload,
            'cached_at': datetime.utcnow().isoformat(),
        }))
        logger.info(f"Result cached locally: {cache_file}")

    def sync_cached_results(self):
        """同步缓存的结果"""
        results_dir = self.cache_dir / 'results'
        if not results_dir.exists():
            return

        for f in results_dir.glob('task_*.json'):
            try:
                data = json.loads(f.read_text())
                task_id = data['task_id']
                action = data['action']
                payload = data['payload']

                if action == 'complete':
                    self._request('POST', f'/tasks/{task_id}/complete', json=payload)
                elif action == 'fail':
                    self._request('POST', f'/tasks/{task_id}/fail', json=payload)

                f.unlink()
                logger.info(f"Synced cached result: task {task_id} {action}")

            except Exception as e:
                logger.warning(f"Failed to sync cached result {f}: {e}")

    def _cache_image(
        self,
        task_id: int,
        image_path: Path,
        image_type: str,
        original_url: str,
        equipment_name: str,
    ):
        """缓存上传失败的图片"""
        cache_dir = self.cache_dir / 'images' / str(task_id)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # 复制图片到缓存目录
        cached_path = cache_dir / image_path.name
        if image_path.exists():
            shutil.copy2(image_path, cached_path)

            # 保存元数据
            meta_file = cache_dir / f'{image_path.stem}.meta.json'
            meta_file.write_text(json.dumps({
                'image_type': image_type,
                'original_url': original_url,
                'equipment_name': equipment_name,
                'cached_at': datetime.utcnow().isoformat(),
            }))
            logger.info(f"Image cached locally: {cached_path}")

    def sync_cached_images(self):
        """同步缓存的图片（在心跳时调用）"""
        images_cache = self.cache_dir / 'images'
        if not images_cache.exists():
            return

        for task_dir in images_cache.iterdir():
            if not task_dir.is_dir():
                continue

            task_id = int(task_dir.name)

            for meta_file in list(task_dir.glob('*.meta.json')):
                image_name = meta_file.stem.replace('.meta', '')
                image_file = None

                # 查找对应的图片文件
                for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    candidate = task_dir / f'{image_name}{ext}'
                    if candidate.exists():
                        image_file = candidate
                        break

                if not image_file:
                    meta_file.unlink()
                    continue

                try:
                    meta = json.loads(meta_file.read_text())
                    result = self.upload_image(
                        task_id,
                        image_file,
                        meta['image_type'],
                        meta['original_url'],
                        meta['equipment_name'],
                    )

                    if result and result.get('status') in ['saved', 'duplicate']:
                        image_file.unlink()
                        meta_file.unlink()
                        logger.info(f"Synced cached image: {image_file}")

                except Exception as e:
                    logger.warning(f"Failed to sync cached image {image_file}: {e}")

            # 如果目录为空，删除它
            if not any(task_dir.iterdir()):
                task_dir.rmdir()
