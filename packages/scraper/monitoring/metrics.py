"""
监控指标模块

定义系统监控的各项指标
"""

import time
import threading
import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class TaskMetric:
    """任务指标"""
    task_id: int
    task_type: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    items_processed: int = 0
    items_success: int = 0
    items_failed: int = 0
    error_message: Optional[str] = None


@dataclass
class QueueMetric:
    """队列指标"""
    depth: int = 0
    running_tasks: int = 0
    completed_per_minute: float = 0
    failed_per_minute: float = 0
    avg_wait_time: float = 0


@dataclass
class SystemMetric:
    """系统指标"""
    timestamp: datetime
    cpu_usage: float = 0
    memory_usage: float = 0
    active_tasks: int = 0
    total_tasks: int = 0
    success_rate: float = 0
    avg_task_duration: float = 0


class MetricsCollector:
    """
    指标收集器

    收集和管理系统运行指标
    """

    def __init__(self, history_size: int = 1000):
        """
        初始化指标收集器

        Args:
            history_size: 历史数据保留数量
        """
        self.history_size = history_size
        self._lock = threading.Lock()

        # 任务指标（按ID索引）
        self.task_metrics: Dict[int, TaskMetric] = {}

        # 队列指标历史
        self.queue_history: deque = deque(maxlen=history_size)

        # 系统指标历史
        self.system_history: deque = deque(maxlen=history_size)

        # 统计计数器
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = defaultdict(float)

        # 启动后台收集线程
        self._start_collection()

    def record_task_start(self, task_id: int, task_type: str):
        """记录任务开始"""
        with self._lock:
            metric = TaskMetric(
                task_id=task_id,
                task_type=task_type,
                status="running",
                start_time=datetime.utcnow()
            )
            self.task_metrics[task_id] = metric
            self.counters["tasks_started"] += 1
            self.gauges["active_tasks"] += 1

    def record_task_complete(self, task_id: int, status: str,
                          items_processed: int = 0,
                          items_success: int = 0,
                          items_failed: int = 0,
                          error_message: Optional[str] = None):
        """记录任务完成"""
        with self._lock:
            metric = self.task_metrics.get(task_id)
            if not metric:
                logger.warning(f"未找到任务 {task_id} 的指标")
                return

            metric.status = status
            metric.end_time = datetime.utcnow()
            metric.items_processed = items_processed
            metric.items_success = items_success
            metric.items_failed = items_failed
            metric.error_message = error_message

            if metric.start_time:
                metric.duration = (metric.end_time - metric.start_time).total_seconds()
                self.timers["task_duration"].append(metric.duration)

            if status == "success":
                self.counters["tasks_completed"] += 1
            elif status == "failed":
                self.counters["tasks_failed"] += 1

            self.gauges["active_tasks"] -= 1

    def record_queue_metrics(self, depth: int, running: int):
        """记录队列指标"""
        with self._lock:
            timestamp = datetime.utcnow()

            # 计算速率（最近1分钟）
            recent_completed = sum(
                1 for m in self.task_metrics.values()
                if m.end_time and (timestamp - m.end_time).total_seconds() <= 60
                and m.status == "success"
            )
            recent_failed = sum(
                1 for m in self.task_metrics.values()
                if m.end_time and (timestamp - m.end_time).total_seconds() <= 60
                and m.status == "failed"
            )

            metric = QueueMetric(
                depth=depth,
                running_tasks=running,
                completed_per_minute=recent_completed,
                failed_per_minute=recent_failed
            )

            self.queue_history.append((timestamp, metric))
            self.gauges["queue_depth"] = depth
            self.gauges["running_tasks"] = running

    def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # 尝试导入psutil
            try:
                import psutil
                has_psutil = True
            except ImportError:
                has_psutil = False
                logger.warning("psutil模块未安装，跳过系统资源监控")

            cpu_usage = 0
            memory_usage = 0

            if has_psutil:
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                memory_usage = memory.percent

            # 计算任务相关指标
            total_tasks = len(self.task_metrics)
            active_tasks = len([m for m in self.task_metrics.values() if m.status == "running"])

            completed_tasks = [m for m in self.task_metrics.values() if m.status == "success"]
            failed_tasks = [m for m in self.task_metrics.values() if m.status == "failed"]

            success_rate = 0
            if completed_tasks or failed_tasks:
                success_rate = len(completed_tasks) / (len(completed_tasks) + len(failed_tasks)) * 100

            avg_duration = 0
            if completed_tasks:
                durations = [m.duration for m in completed_tasks if m.duration]
                if durations:
                    avg_duration = sum(durations) / len(durations)

            metric = SystemMetric(
                timestamp=datetime.utcnow(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                active_tasks=active_tasks,
                total_tasks=total_tasks,
                success_rate=success_rate,
                avg_task_duration=avg_duration
            )

            with self._lock:
                self.system_history.append(metric)
                self.gauges["cpu_usage"] = cpu_usage
                self.gauges["memory_usage"] = memory_usage
                self.gauges["success_rate"] = success_rate
                self.gauges["avg_task_duration"] = avg_duration

        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")

    def _start_collection(self):
        """启动后台收集线程"""
        def collect_loop():
            while True:
                try:
                    self.collect_system_metrics()
                    time.sleep(30)  # 每30秒收集一次
                except Exception as e:
                    logger.error(f"系统指标收集异常: {e}")
                    time.sleep(60)  # 出错后等待1分钟再重试

        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()
        logger.info("系统指标收集线程已启动")

    def get_task_metrics(self, task_id: Optional[int] = None) -> Any:
        """
        获取任务指标

        Args:
            task_id: 任务ID，None表示返回所有任务

        Returns:
            任务指标或指标列表
        """
        with self._lock:
            if task_id:
                return self.task_metrics.get(task_id)
            else:
                return list(self.task_metrics.values())

    def get_queue_metrics(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """
        获取队列指标历史

        Args:
            minutes: 获取最近N分钟的数据

        Returns:
            队列指标列表
        """
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

            metrics = []
            for timestamp, metric in self.queue_history:
                if timestamp >= cutoff_time:
                    metrics.append({
                        "timestamp": timestamp.isoformat(),
                        "depth": metric.depth,
                        "running_tasks": metric.running_tasks,
                        "completed_per_minute": metric.completed_per_minute,
                        "failed_per_minute": metric.failed_per_minute
                    })

            return metrics

    def get_system_metrics(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """
        获取系统指标历史

        Args:
            minutes: 获取最近N分钟的数据

        Returns:
            系统指标列表
        """
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

            metrics = []
            for metric in self.system_history:
                if metric.timestamp >= cutoff_time:
                    metrics.append({
                        "timestamp": metric.timestamp.isoformat(),
                        "cpu_usage": metric.cpu_usage,
                        "memory_usage": metric.memory_usage,
                        "active_tasks": metric.active_tasks,
                        "total_tasks": metric.total_tasks,
                        "success_rate": metric.success_rate,
                        "avg_task_duration": metric.avg_task_duration
                    })

            return metrics

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前实时指标"""
        with self._lock:
            return {
                # 计数器
                "counters": dict(self.counters),

                # 仪表盘
                "gauges": dict(self.gauges),

                # 任务统计
                "task_stats": {
                    "total": len(self.task_metrics),
                    "running": len([m for m in self.task_metrics.values() if m.status == "running"]),
                    "success": len([m for m in self.task_metrics.values() if m.status == "success"]),
                    "failed": len([m for m in self.task_metrics.values() if m.status == "failed"]),
                },

                # 时间统计
                "timer_stats": {
                    "avg_task_duration": sum(self.timers["task_duration"]) / len(self.timers["task_duration"])
                                      if self.timers["task_duration"] else 0,
                    "max_task_duration": max(self.timers["task_duration"])
                                      if self.timers["task_duration"] else 0,
                    "min_task_duration": min(self.timers["task_duration"])
                                      if self.timers["task_duration"] else 0,
                }
            }

    def get_task_type_stats(self) -> Dict[str, Dict[str, Any]]:
        """按任务类型统计"""
        with self._lock:
            stats = defaultdict(lambda: {"count": 0, "success": 0, "failed": 0, "avg_duration": 0})

            for metric in self.task_metrics.values():
                task_type = metric.task_type
                stats[task_type]["count"] += 1

                if metric.status == "success":
                    stats[task_type]["success"] += 1
                elif metric.status == "failed":
                    stats[task_type]["failed"] += 1

                if metric.duration:
                    # 简单的移动平均
                    current_avg = stats[task_type]["avg_duration"]
                    count = stats[task_type]["count"]
                    stats[task_type]["avg_duration"] = (current_avg * (count - 1) + metric.duration) / count

            return dict(stats)

    def cleanup_old_metrics(self, days: int = 7):
        """清理旧指标数据"""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # 清理任务指标
            old_task_ids = [
                task_id for task_id, metric in self.task_metrics.items()
                if metric.end_time and metric.end_time < cutoff_time
            ]

            for task_id in old_task_ids:
                del self.task_metrics[task_id]

            logger.info(f"清理了 {len(old_task_ids)} 条旧任务指标")


# 全局指标收集器实例
metrics_collector = MetricsCollector()

# 导出类
__all__ = [
    'TaskMetric',
    'QueueMetric',
    'SystemMetric',
    'MetricsCollector',
    'metrics_collector'
]