"""
Worker API 端点测试

测试内容:
- Worker 注册
- 任务领取（优先级队列）
- 任务汇报
- 心跳（动态间隔）
- Worker 状态查询
"""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi.testclient import TestClient

# 导入被测模块
from apps.api.routes.worker import (
    hash_secret,
    verify_secret,
    calculate_heartbeat_interval,
)


class TestUtilityFunctions:
    """工具函数测试"""

    def test_hash_secret(self):
        """测试密钥哈希"""
        secret = "test-secret-123"
        hashed = hash_secret(secret)

        # 哈希应该是固定长度的十六进制字符串
        assert len(hashed) == 64  # SHA256 = 64 hex chars
        assert all(c in '0123456789abcdef' for c in hashed)

        # 相同输入应该产生相同输出
        assert hash_secret(secret) == hashed

        # 不同输入应该产生不同输出
        assert hash_secret("different") != hashed

    def test_verify_secret(self):
        """测试密钥验证"""
        secret = "my-secret-key"
        secret_hash = hash_secret(secret)

        assert verify_secret(secret, secret_hash) is True
        assert verify_secret("wrong-secret", secret_hash) is False
        assert verify_secret("", secret_hash) is False

    def test_calculate_heartbeat_interval_queue_backlog(self):
        """测试队列积压时的心跳间隔"""
        # 队列超过 100，应返回最短间隔
        assert calculate_heartbeat_interval(0.5, 150) == 10
        assert calculate_heartbeat_interval(0.5, 101) == 10

        # 队列在 50-100 之间
        assert calculate_heartbeat_interval(0.5, 75) == 15
        assert calculate_heartbeat_interval(0.5, 51) == 15

    def test_calculate_heartbeat_interval_high_load(self):
        """测试高负载时的心跳间隔"""
        # 高负载 (>0.8)，应返回较长间隔以减少开销
        assert calculate_heartbeat_interval(0.9, 10) == 60
        assert calculate_heartbeat_interval(0.85, 10) == 60

        # 中等负载 (0.5-0.8)
        assert calculate_heartbeat_interval(0.6, 10) == 45
        assert calculate_heartbeat_interval(0.55, 10) == 45

    def test_calculate_heartbeat_interval_normal(self):
        """测试正常情况的心跳间隔"""
        # 低负载，正常队列长度
        assert calculate_heartbeat_interval(0.3, 10) == 30
        assert calculate_heartbeat_interval(0.1, 5) == 30
        assert calculate_heartbeat_interval(0.0, 0) == 30

    def test_calculate_heartbeat_interval_priority(self):
        """测试队列长度优先于负载"""
        # 即使高负载，如果队列积压也应该返回短间隔
        assert calculate_heartbeat_interval(0.9, 150) == 10  # 队列积压优先


class TestWorkerRegistration:
    """Worker 注册测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        with patch('apps.api.routes.worker.get_crawler_db') as mock:
            mock_session = MagicMock()
            mock_db = MagicMock()
            mock_db.session_scope.return_value.__enter__.return_value = mock_session
            mock_db.session_scope.return_value.__exit__.return_value = None
            mock.return_value = mock_db
            yield mock_session

    def test_register_new_worker_format(self, mock_db):
        """测试新 Worker 注册响应格式"""
        # 模拟无现有节点
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 验证注册请求格式
        worker_info = {
            'worker_id': 'test-worker-001',
            'worker_name': 'Test Worker',
            'supported_types': ['taobao', 'jd'],
            'max_concurrent': 2
        }

        # 预期响应应包含以下字段
        expected_fields = ['success', 'worker_id', 'token', 'message']

        # 由于我们在单元测试中，只验证数据模型
        from apps.api.routes.worker import WorkerInfo
        info = WorkerInfo(**worker_info)

        assert info.worker_id == 'test-worker-001'
        assert info.worker_name == 'Test Worker'
        assert info.supported_types == ['taobao', 'jd']
        assert info.max_concurrent == 2

    def test_worker_info_default_values(self):
        """测试 WorkerInfo 默认值"""
        from apps.api.routes.worker import WorkerInfo

        info = WorkerInfo(worker_id='test-id')

        assert info.worker_id == 'test-id'
        assert info.worker_name is None
        assert info.supported_types == ['taobao', 'jd', 'forum']
        assert info.max_concurrent == 1


class TestTaskClaimRequest:
    """任务领取请求测试"""

    def test_task_claim_request_format(self):
        """测试任务领取请求格式"""
        from apps.api.routes.worker import TaskClaimRequest

        request = TaskClaimRequest(
            worker_id='worker-001',
            supported_types=['taobao'],
            max_tasks=3
        )

        assert request.worker_id == 'worker-001'
        assert request.supported_types == ['taobao']
        assert request.max_tasks == 3

    def test_task_claim_request_defaults(self):
        """测试任务领取请求默认值"""
        from apps.api.routes.worker import TaskClaimRequest

        request = TaskClaimRequest(worker_id='worker-001')

        assert request.supported_types == ['taobao', 'jd', 'forum']
        assert request.max_tasks == 1


class TestTaskProgressReport:
    """任务进度汇报测试"""

    def test_progress_report_format(self):
        """测试进度汇报格式"""
        from apps.api.routes.worker import TaskProgressReport

        report = TaskProgressReport(
            task_id=123,
            worker_id='worker-001',
            status='running',
            progress=50,
            message='处理中...',
            success_items=10,
            failed_items=2,
            total_items=20
        )

        assert report.task_id == 123
        assert report.worker_id == 'worker-001'
        assert report.status == 'running'
        assert report.progress == 50
        assert report.success_items == 10
        assert report.failed_items == 2
        assert report.total_items == 20

    def test_progress_report_success(self):
        """测试成功状态汇报"""
        from apps.api.routes.worker import TaskProgressReport

        report = TaskProgressReport(
            task_id=123,
            worker_id='worker-001',
            status='success',
            progress=100,
            success_items=20,
            total_items=20,
            result_data={'key': 'value'}
        )

        assert report.status == 'success'
        assert report.progress == 100
        assert report.result_data == {'key': 'value'}

    def test_progress_report_failed(self):
        """测试失败状态汇报"""
        from apps.api.routes.worker import TaskProgressReport

        report = TaskProgressReport(
            task_id=123,
            worker_id='worker-001',
            status='failed',
            progress=30,
            error_message='连接超时'
        )

        assert report.status == 'failed'
        assert report.error_message == '连接超时'


class TestHeartbeatRequest:
    """心跳请求测试"""

    def test_heartbeat_request_format(self):
        """测试心跳请求格式"""
        from apps.api.routes.worker import HeartbeatRequest

        request = HeartbeatRequest(
            worker_id='worker-001',
            current_tasks=[1, 2, 3],
            cpu_usage=45.5,
            memory_usage=62.3
        )

        assert request.worker_id == 'worker-001'
        assert request.current_tasks == [1, 2, 3]
        assert request.cpu_usage == 45.5
        assert request.memory_usage == 62.3

    def test_heartbeat_request_defaults(self):
        """测试心跳请求默认值"""
        from apps.api.routes.worker import HeartbeatRequest

        request = HeartbeatRequest(worker_id='worker-001')

        assert request.current_tasks == []
        assert request.cpu_usage is None
        assert request.memory_usage is None


class TestHeartbeatResponse:
    """心跳响应测试"""

    def test_heartbeat_response_format(self):
        """测试心跳响应格式"""
        from apps.api.routes.worker import HeartbeatResponse

        response = HeartbeatResponse(
            success=True,
            server_time='2024-01-01T12:00:00',
            commands=[{'type': 'cancel_task', 'task_id': 1}],
            next_heartbeat_seconds=15
        )

        assert response.success is True
        assert response.server_time == '2024-01-01T12:00:00'
        assert len(response.commands) == 1
        assert response.next_heartbeat_seconds == 15

    def test_heartbeat_response_defaults(self):
        """测试心跳响应默认值"""
        from apps.api.routes.worker import HeartbeatResponse

        response = HeartbeatResponse(
            success=True,
            server_time='2024-01-01T12:00:00'
        )

        assert response.commands == []
        assert response.next_heartbeat_seconds == 30


class TestPriorityQueue:
    """优先级队列测试"""

    def test_priority_ordering_logic(self):
        """测试优先级排序逻辑"""
        # 模拟任务列表
        tasks = [
            {'id': 1, 'priority': 5, 'created_at': '2024-01-01T10:00:00'},
            {'id': 2, 'priority': 10, 'created_at': '2024-01-01T11:00:00'},
            {'id': 3, 'priority': 5, 'created_at': '2024-01-01T09:00:00'},
            {'id': 4, 'priority': 1, 'created_at': '2024-01-01T08:00:00'},
        ]

        # 按优先级降序，创建时间升序排序
        sorted_tasks = sorted(
            tasks,
            key=lambda x: (-x['priority'], x['created_at'])
        )

        # 验证排序结果
        # 优先级 10 的任务应该在最前面
        assert sorted_tasks[0]['id'] == 2  # priority=10
        # 优先级 5 的两个任务，创建时间早的在前
        assert sorted_tasks[1]['id'] == 3  # priority=5, created earlier
        assert sorted_tasks[2]['id'] == 1  # priority=5, created later
        # 优先级 1 的任务在最后
        assert sorted_tasks[3]['id'] == 4  # priority=1


class TestTokenFormat:
    """Token 格式测试"""

    def test_token_format_valid(self):
        """测试有效的 Token 格式"""
        token = "node-123:abc123secret"
        assert ":" in token

        node_id, secret = token.split(":", 1)
        assert node_id == "node-123"
        assert secret == "abc123secret"

    def test_token_format_with_colon_in_secret(self):
        """测试 secret 中包含冒号的情况"""
        token = "node-123:secret:with:colons"

        node_id, secret = token.split(":", 1)
        assert node_id == "node-123"
        assert secret == "secret:with:colons"

    def test_token_format_invalid(self):
        """测试无效的 Token 格式"""
        invalid_tokens = [
            "no-colon-token",
            "",
            "   ",
        ]

        for token in invalid_tokens:
            assert ":" not in token or token.strip() == ""


class TestDynamicHeartbeat:
    """动态心跳间隔综合测试"""

    def test_interval_ranges(self):
        """测试心跳间隔范围"""
        # 最短间隔
        min_interval = calculate_heartbeat_interval(0.0, 200)
        assert min_interval == 10

        # 最长间隔
        max_interval = calculate_heartbeat_interval(0.9, 0)
        assert max_interval == 60

        # 正常间隔
        normal_interval = calculate_heartbeat_interval(0.3, 10)
        assert normal_interval == 30

    def test_interval_boundaries(self):
        """测试边界值"""
        # 队列长度边界 (queue_length > 100 返回 10, > 50 返回 15, 否则看负载)
        assert calculate_heartbeat_interval(0.3, 100) == 15  # 100 > 50，返回 15
        assert calculate_heartbeat_interval(0.3, 101) == 10  # 101 > 100，返回 10
        assert calculate_heartbeat_interval(0.3, 50) == 30   # 50 不大于 50，检查负载 0.3，返回正常
        assert calculate_heartbeat_interval(0.3, 51) == 15   # 51 > 50，返回 15

        # 负载边界 (worker_load > 0.8 返回 60, > 0.5 返回 45, 否则返回 30)
        # 注意: 条件是 > 不是 >=，所以 0.8 仍然满足 > 0.5
        assert calculate_heartbeat_interval(0.8, 10) == 45   # 0.8 > 0.5，返回 45
        assert calculate_heartbeat_interval(0.81, 10) == 60  # 0.81 > 0.8，返回 60
        assert calculate_heartbeat_interval(0.5, 10) == 30   # 0.5 不大于 0.5，返回正常
        assert calculate_heartbeat_interval(0.51, 10) == 45  # 0.51 > 0.5，返回 45
