"""
Worker 单元测试

测试内容:
- TaskPoller 智能轮询算法
- 图片上传顺序保证
- 任务取消机制
"""

import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

from packages.scraper.worker.worker import (
    TaskPoller,
    TaskCancelledException,
    WorkerConfig,
    CrawlerWorker,
)


class TestTaskPoller:
    """智能轮询算法测试"""

    def test_initial_interval(self):
        """初始间隔：第一次无任务调用应用退避"""
        poller = TaskPoller(min_interval=1.0, max_interval=30.0)
        # 第一次调用，无任务，应用退避因子
        interval = poller.get_interval(has_tasks=False)
        # 实现: min_interval * backoff_factor = 1.0 * 1.5 = 1.5
        assert interval == 1.5

    def test_exponential_backoff(self):
        """空闲时应指数增长"""
        poller = TaskPoller(min_interval=1.0, max_interval=30.0, backoff_factor=1.5)
        intervals = []
        for _ in range(10):
            intervals.append(poller.get_interval(has_tasks=False))

        # 验证递增: 1.5 -> 2.25 -> 3.375 -> 5.0625 -> ...
        assert intervals[0] < intervals[4] < intervals[8]

        # 验证指数增长 (从 min_interval * factor 开始)
        # intervals[0] = 1.0 * 1.5 = 1.5
        # intervals[1] = 1.5 * 1.5 = 2.25
        # intervals[2] = 2.25 * 1.5 = 3.375
        # intervals[3] = 3.375 * 1.5 = 5.0625
        assert intervals[0] == pytest.approx(1.5, rel=0.01)
        assert intervals[1] == pytest.approx(2.25, rel=0.01)
        assert intervals[2] == pytest.approx(3.375, rel=0.01)
        assert intervals[3] == pytest.approx(5.0625, rel=0.01)

    def test_max_interval_cap(self):
        """不应超过最大间隔"""
        poller = TaskPoller(min_interval=1.0, max_interval=30.0, backoff_factor=2.0)
        interval = 0
        for _ in range(100):
            interval = poller.get_interval(has_tasks=False)

        assert interval <= 30.0

    def test_reset_on_task(self):
        """有任务时应重置为最小值"""
        poller = TaskPoller(min_interval=1.0, max_interval=30.0)

        # 先让间隔增长
        for _ in range(10):
            poller.get_interval(has_tasks=False)

        # 有任务时重置
        interval = poller.get_interval(has_tasks=True)
        assert interval == 1.0

        # 再次无任务，从最小值开始
        next_interval = poller.get_interval(has_tasks=False)
        assert next_interval == 1.5  # min_interval * backoff_factor

    def test_consecutive_empty_count(self):
        """连续空闲计数应正确"""
        poller = TaskPoller(min_interval=1.0, max_interval=30.0)

        assert poller.consecutive_empty == 0

        poller.get_interval(has_tasks=False)
        assert poller.consecutive_empty == 1

        poller.get_interval(has_tasks=False)
        assert poller.consecutive_empty == 2

        # 有任务，重置
        poller.get_interval(has_tasks=True)
        assert poller.consecutive_empty == 0

    def test_reset_method(self):
        """reset 方法应重置所有状态"""
        poller = TaskPoller(min_interval=1.0, max_interval=30.0)

        for _ in range(10):
            poller.get_interval(has_tasks=False)

        assert poller.current_interval > 1.0
        assert poller.consecutive_empty > 0

        poller.reset()

        assert poller.current_interval == 1.0
        assert poller.consecutive_empty == 0


class TestImageUploadOrder:
    """图片上传顺序测试"""

    def test_executor_map_preserves_order(self):
        """验证 executor.map() 保持顺序"""
        images = [
            {'index': 0, 'value': 'a'},
            {'index': 1, 'value': 'b'},
            {'index': 2, 'value': 'c'},
            {'index': 3, 'value': 'd'},
        ]

        def process(img):
            # 模拟不同处理时间
            time.sleep(0.01 * (4 - img['index']))  # 反向延迟
            return {'index': img['index'], 'result': img['value'].upper()}

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process, images))

        # 验证顺序保持
        assert [r['index'] for r in results] == [0, 1, 2, 3]
        assert [r['result'] for r in results] == ['A', 'B', 'C', 'D']

    def test_upload_order_with_varying_delays(self):
        """不同上传延迟时顺序仍保持"""
        images = [
            {'index': 0, 'type': 'main', 'delay': 0.05},
            {'index': 1, 'type': 'detail', 'delay': 0.01},
            {'index': 2, 'type': 'detail', 'delay': 0.03},
            {'index': 3, 'type': 'spec', 'delay': 0.02},
        ]

        def mock_upload(img):
            time.sleep(img['delay'])
            return {
                'index': img['index'],
                'type': img['type'],
                'status': 'saved'
            }

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(mock_upload, images))

        # 验证顺序
        assert [r['index'] for r in results] == [0, 1, 2, 3]
        assert results[0]['type'] == 'main'  # 主图在最前

    def test_main_image_always_first(self):
        """主图应始终在最前（按原始顺序）"""
        images = [
            {'index': 0, 'type': 'main'},
            {'index': 1, 'type': 'detail'},
            {'index': 2, 'type': 'detail'},
        ]

        def mock_upload(img):
            return {'index': img['index'], 'type': img['type']}

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(mock_upload, images))

        assert results[0]['type'] == 'main'


class TestTaskCancellation:
    """任务取消机制测试"""

    def test_cancel_event_creation(self):
        """取消事件应正确创建"""
        event = threading.Event()
        assert not event.is_set()

        event.set()
        assert event.is_set()

    def test_task_cancelled_exception(self):
        """TaskCancelledException 应能正确抛出和捕获"""
        def task_with_cancel_check(cancel_event: threading.Event):
            if cancel_event.is_set():
                raise TaskCancelledException("Task was cancelled")
            return "completed"

        # 未取消
        event = threading.Event()
        result = task_with_cancel_check(event)
        assert result == "completed"

        # 已取消
        event.set()
        with pytest.raises(TaskCancelledException):
            task_with_cancel_check(event)

    def test_cancel_during_execution(self):
        """执行过程中取消应能检测到"""
        cancel_event = threading.Event()
        results = []

        def long_running_task():
            for i in range(10):
                if cancel_event.is_set():
                    results.append('cancelled')
                    return
                results.append(i)
                time.sleep(0.01)

        # 启动任务
        thread = threading.Thread(target=long_running_task)
        thread.start()

        # 中途取消
        time.sleep(0.03)
        cancel_event.set()

        thread.join()

        # 应该被取消了
        assert 'cancelled' in results
        assert len(results) < 10  # 未完成所有步骤

    @patch('packages.scraper.worker.worker.WorkerClient')
    def test_worker_cancel_task_method(self, mock_client):
        """Worker.cancel_task 方法应正确设置取消事件"""
        config = WorkerConfig(master_url="http://localhost:8000")
        worker = CrawlerWorker(config)

        # 模拟有一个任务在运行
        task_id = 123
        worker.cancel_events[task_id] = threading.Event()

        assert not worker.cancel_events[task_id].is_set()

        # 取消任务
        result = worker.cancel_task(task_id)

        assert result is True
        assert worker.cancel_events[task_id].is_set()

    @patch('packages.scraper.worker.worker.WorkerClient')
    def test_cancel_nonexistent_task(self, mock_client):
        """取消不存在的任务应返回 False"""
        config = WorkerConfig(master_url="http://localhost:8000")
        worker = CrawlerWorker(config)

        result = worker.cancel_task(999)
        assert result is False


class TestWorkerConfig:
    """WorkerConfig 测试"""

    def test_default_values(self):
        """默认值应正确设置"""
        config = WorkerConfig(master_url="http://localhost:8000")

        assert config.master_url == "http://localhost:8000"
        assert config.node_id is None
        assert config.node_secret is None
        assert config.node_name == "Worker Node"
        assert config.capabilities == ["all"]
        assert config.max_concurrent_tasks == 1
        assert config.heartbeat_interval == 30
        assert config.headless is True

    def test_from_dict(self):
        """从字典创建配置"""
        data = {
            'master_url': 'http://example.com:8000',
            'node_id': 'test-node',
            'node_secret': 'test-secret',
            'node_name': 'Test Worker',
            'capabilities': ['taobao', 'jd'],
            'max_concurrent_tasks': 3,
        }

        config = WorkerConfig.from_dict(data)

        assert config.master_url == 'http://example.com:8000'
        assert config.node_id == 'test-node'
        assert config.capabilities == ['taobao', 'jd']
        assert config.max_concurrent_tasks == 3

    def test_to_dict(self):
        """转换为字典"""
        config = WorkerConfig(
            master_url="http://localhost:8000",
            node_name="Test",
            max_concurrent_tasks=2
        )

        data = config.to_dict()

        assert data['master_url'] == "http://localhost:8000"
        assert data['node_name'] == "Test"
        assert data['max_concurrent_tasks'] == 2


class TestDynamicHeartbeatInterval:
    """动态心跳间隔测试（针对后端 API）"""

    def test_calculate_heartbeat_interval(self):
        """测试心跳间隔计算"""
        from apps.api.routes.worker import calculate_heartbeat_interval

        # 队列积压
        assert calculate_heartbeat_interval(0.5, 150) == 10
        assert calculate_heartbeat_interval(0.5, 75) == 15

        # 高负载
        assert calculate_heartbeat_interval(0.9, 10) == 60
        assert calculate_heartbeat_interval(0.6, 10) == 45

        # 正常
        assert calculate_heartbeat_interval(0.3, 10) == 30
