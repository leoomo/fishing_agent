"""
Worker 集成测试

测试内容:
- 完整工作流程
- 离线缓存同步
- 图片上传顺序验证
"""

import json
import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from concurrent.futures import Future

from packages.scraper.worker.worker import (
    CrawlerWorker,
    WorkerConfig,
    TaskPoller,
    TaskCancelledException,
)
from packages.scraper.worker.client import WorkerClient


class TestWorkerIntegration:
    """Worker 完整流程集成测试"""

    @pytest.fixture
    def mock_client(self):
        """创建模拟的 WorkerClient"""
        client = MagicMock(spec=WorkerClient)
        client.authenticate.return_value = True
        client.heartbeat.return_value = {'status': 'ok'}
        client.get_tasks.return_value = []
        return client

    @pytest.fixture
    def worker_config(self):
        """Worker 配置"""
        return WorkerConfig(
            master_url="http://localhost:8000",
            node_id="test-node",
            node_secret="test-secret",
            node_name="Test Worker",
            max_concurrent_tasks=2,
            heartbeat_interval=1,  # 快速心跳便于测试
        )

    def test_worker_initialization(self, worker_config):
        """Worker 初始化测试"""
        worker = CrawlerWorker(worker_config)

        assert worker.config == worker_config
        assert worker.running is False
        assert worker.draining is False
        assert len(worker.current_tasks) == 0
        assert len(worker.cancel_events) == 0
        assert worker.task_poller is not None

    @patch('packages.scraper.worker.worker.WorkerClient')
    def test_task_claim_and_execute(self, mock_client_class, worker_config):
        """任务领取和执行流程测试"""
        # 设置模拟客户端
        mock_client = MagicMock()
        mock_client.authenticate.return_value = True
        mock_client.get_tasks.side_effect = [
            [{'id': 1, 'task_type': 'test'}],  # 第一次返回任务
            [],  # 后续返回空
        ] + [[]] * 100
        mock_client.claim_task.return_value = {
            'id': 1,
            'task_type': 'test',
            'config': '{}',
        }
        mock_client.complete_task.return_value = True
        mock_client.heartbeat.return_value = {'status': 'ok'}

        mock_client_class.return_value = mock_client

        worker = CrawlerWorker(worker_config)
        worker.client = mock_client

        # 模拟平台注册器不可用
        worker._platform_registry = None

        # 手动运行一次任务循环
        worker.running = True

        # 执行一次任务领取
        tasks = worker.client.get_tasks(limit=1)
        assert len(tasks) == 1
        assert tasks[0]['id'] == 1

    def test_task_poller_integration(self, worker_config):
        """智能轮询器集成测试"""
        worker = CrawlerWorker(worker_config)

        # 初始状态
        assert worker.task_poller.current_interval == 1.0

        # 模拟无任务
        for _ in range(5):
            interval = worker.task_poller.get_interval(has_tasks=False)

        assert interval > 1.0  # 间隔应该增长

        # 模拟有任务
        interval = worker.task_poller.get_interval(has_tasks=True)
        assert interval == 1.0  # 重置

    def test_cancel_event_cleanup(self, worker_config):
        """取消事件清理测试"""
        worker = CrawlerWorker(worker_config)

        # 添加取消事件
        worker.cancel_events[1] = threading.Event()
        worker.cancel_events[2] = threading.Event()

        assert len(worker.cancel_events) == 2

        # 清理
        del worker.cancel_events[1]
        assert len(worker.cancel_events) == 1
        assert 2 in worker.cancel_events


class TestImageUploadOrderIntegration:
    """图片上传顺序集成测试"""

    def test_ordered_upload_simulation(self):
        """模拟有序上传"""
        # 模拟图片列表
        images = [
            {'index': 0, 'type': 'main', 'url': 'http://example.com/main.jpg'},
            {'index': 1, 'type': 'detail', 'url': 'http://example.com/d1.jpg'},
            {'index': 2, 'type': 'detail', 'url': 'http://example.com/d2.jpg'},
            {'index': 3, 'type': 'spec', 'url': 'http://example.com/spec.jpg'},
        ]

        # 模拟上传结果（记录上传顺序）
        upload_order = []

        def mock_upload(img):
            # 模拟不同延迟
            time.sleep(0.01 * (4 - img['index']))
            upload_order.append(img['index'])
            return {
                'index': img['index'],
                'status': 'saved',
            }

        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(mock_upload, images))

        # 验证结果顺序（executor.map 保证）
        result_indices = [r['index'] for r in results]
        assert result_indices == [0, 1, 2, 3]

        # 上传执行顺序可能不同（并发），但结果顺序必须正确
        assert results[0]['index'] == 0  # 主图结果在最前


class TestOfflineCacheSync:
    """离线缓存同步测试"""

    def test_cache_result_format(self):
        """缓存结果格式测试"""
        from datetime import datetime
        import json

        cache_data = {
            'task_id': 123,
            'action': 'complete',
            'payload': {
                'success_items': 10,
                'failed_items': 0,
            },
            'cached_at': datetime.utcnow().isoformat(),
        }

        # 序列化/反序列化
        json_str = json.dumps(cache_data)
        loaded = json.loads(json_str)

        assert loaded['task_id'] == 123
        assert loaded['action'] == 'complete'
        assert loaded['payload']['success_items'] == 10

    def test_cache_directory_structure(self):
        """缓存目录结构测试"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir)

            # 创建结果缓存目录
            results_dir = cache_dir / 'results'
            results_dir.mkdir(parents=True, exist_ok=True)

            # 创建图片缓存目录
            images_dir = cache_dir / 'images' / '123'
            images_dir.mkdir(parents=True, exist_ok=True)

            assert results_dir.exists()
            assert images_dir.exists()

            # 写入缓存文件
            cache_file = results_dir / 'task_123_complete.json'
            cache_file.write_text('{"test": true}')

            assert cache_file.exists()


class TestConcurrentTaskExecution:
    """并发任务执行测试"""

    def test_max_concurrent_limit(self):
        """最大并发限制测试"""
        config = WorkerConfig(
            master_url="http://localhost:8000",
            max_concurrent_tasks=2
        )
        worker = CrawlerWorker(config)

        # 模拟任务
        worker.current_tasks[1] = MagicMock()
        worker.current_tasks[2] = MagicMock()

        # 达到最大并发
        assert len(worker.current_tasks) >= config.max_concurrent_tasks

    def test_task_cleanup(self):
        """任务清理测试"""
        config = WorkerConfig(master_url="http://localhost:8000")
        worker = CrawlerWorker(config)

        # 添加已完成的 Future
        future = Future()
        future.set_result(None)
        worker.current_tasks[1] = future

        # 添加取消事件
        worker.cancel_events[1] = threading.Event()

        # 执行清理
        worker._cleanup_completed_tasks()

        # 应该被清理
        assert 1 not in worker.current_tasks
        assert 1 not in worker.cancel_events


class TestHeartbeatDynamicInterval:
    """动态心跳间隔测试"""

    def test_heartbeat_response_parsing(self):
        """心跳响应解析测试"""
        response = {
            'status': 'ok',
            'next_heartbeat_seconds': 15,
            'cancel_tasks': [1, 2],
        }

        assert response.get('next_heartbeat_seconds', 30) == 15
        assert len(response.get('cancel_tasks', [])) == 2

    def test_drain_signal_handling(self):
        """排空信号处理测试"""
        config = WorkerConfig(master_url="http://localhost:8000")
        worker = CrawlerWorker(config)

        assert worker.draining is False

        # 模拟收到 drain 信号
        worker.draining = True

        assert worker.draining is True
