"""
监控主模块

整合指标收集和告警系统，提供统一的监控接口
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from packages.agent_fishing.tools.crawler.executor.task_queue import CrawlerTaskQueue
from packages.agent_fishing.tools.crawler.workflow.engine import WorkflowEngine
from .metrics import metrics_collector
from .alerts import alert_manager, AlertLevel, Alert

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    监控服务

    整合指标收集和告警功能
    """

    def __init__(self, task_queue: Optional[CrawlerTaskQueue] = None,
                 workflow_engine: Optional[WorkflowEngine] = None):
        """
        初始化监控服务

        Args:
            task_queue: 任务队列实例
            workflow_engine: 工作流引擎实例
        """
        self.task_queue = task_queue
        self.workflow_engine = workflow_engine
        self.running = False
        self._monitor_thread = None

        # 注册自定义指标收集器
        self._setup_custom_collectors()

    def _setup_custom_collectors(self):
        """设置自定义指标收集器"""
        # 如果有任务队列，定期收集队列指标
        if self.task_queue:
            def collect_queue_metrics():
                stats = self.task_queue.get_stats()
                metrics_collector.record_queue_metrics(
                    depth=stats.get("queue_depth", 0),
                    running=stats.get("running_tasks", 0)
                )

            # 添加到后台收集
            self._add_periodic_collector(collect_queue_metrics, interval=10)

    def _add_periodic_collector(self, collector_func, interval: int):
        """添加周期性收集器"""
        def collector_loop():
            while self.running:
                try:
                    collector_func()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"周期性收集器异常: {e}")
                    time.sleep(interval * 2)  # 出错后延长间隔

        thread = threading.Thread(target=collector_loop, daemon=True)
        thread.start()
        logger.info(f"启动周期性收集器，间隔: {interval}秒")

    def start(self):
        """启动监控服务"""
        if self.running:
            logger.warning("监控服务已经在运行")
            return

        self.running = True

        # 启动监控线程
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info("监控服务已启动")

    def stop(self):
        """停止监控服务"""
        if not self.running:
            return

        self.running = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

        logger.info("监控服务已停止")

    def _monitor_loop(self):
        """监控主循环"""
        while self.running:
            try:
                # 检查告警
                alert_manager.check_alerts()

                # 清理过期数据
                metrics_collector.cleanup_old_metrics(days=7)

                # 短暂休眠
                time.sleep(30)  # 每30秒检查一次

            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(60)  # 出错后等待1分钟

    def record_task_event(self, event_type: str, task_id: int, **kwargs):
        """
        记录任务事件

        Args:
            event_type: 事件类型 (start, complete, fail, etc.)
            task_id: 任务ID
            **kwargs: 事件参数
        """
        if event_type == "start":
            task_type = kwargs.get("task_type", "unknown")
            metrics_collector.record_task_start(task_id, task_type)

        elif event_type == "complete":
            status = kwargs.get("status", "unknown")
            items_processed = kwargs.get("items_processed", 0)
            items_success = kwargs.get("items_success", 0)
            items_failed = kwargs.get("items_failed", 0)
            error_message = kwargs.get("error_message")

            metrics_collector.record_task_complete(
                task_id, status, items_processed,
                items_success, items_failed, error_message
            )

        else:
            logger.debug(f"未知的任务事件类型: {event_type}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        # 当前指标
        current_metrics = metrics_collector.get_current_metrics()

        # 队列状态
        queue_status = None
        if self.task_queue:
            queue_status = self.task_queue.get_stats()

        # 工作流状态
        workflow_status = None
        if self.workflow_engine:
            running_workflows = len(self.workflow_engine.active_workflows)
            workflow_status = {
                "running_count": running_workflows,
                "workflows": [
                    {
                        "id:": wf_id,
                        "name": wf.name,
                        "status": wf.status
                    }
                    for wf_id, wf in self.workflow_engine.active_workflows.items()
                ]
            }

        # 告警摘要
        alert_summary = alert_manager.get_alert_summary()

        # 任务类型统计
        task_type_stats = metrics_collector.get_task_type_stats()

        # 系统指标趋势（最近1小时）
        system_metrics = metrics_collector.get_system_metrics(minutes=60)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_metrics": current_metrics,
            "queue_status": queue_status,
            "workflow_status": workflow_status,
            "alert_summary": alert_summary,
            "task_type_stats": task_type_stats,
            "system_metrics": system_metrics
        }

    def get_task_report(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务报告

        Args:
            task_id: 任务ID

        Returns:
            任务报告
        """
        task_metric = metrics_collector.get_task_metrics(task_id)
        if not task_metric:
            return None

        return {
            "task_id": task_metric.task_id,
            "task_type": task_metric.task_type,
            "status": task_metric.status,
            "start_time": task_metric.start_time.isoformat() if task_metric.start_time else None,
            "end_time": task_metric.end_time.isoformat() if task_metric.end_time else None,
            "duration": task_metric.duration,
            "items_processed": task_metric.items_processed,
            "items_success": task_metric.items_success,
            "items_failed": task_metric.items_failed,
            "error_message": task_metric.error_message
        }

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        current_metrics = metrics_collector.get_current_metrics()
        alerts = alert_manager.get_recent_alerts(hours=1)

        # 计算健康评分
        health_score = 100

        # CPU使用率影响
        cpu_usage = current_metrics.get("gauges", {}).get("cpu_usage", 0)
        if cpu_usage > 90:
            health_score -= 20
        elif cpu_usage > 70:
            health_score -= 10

        # 内存使用率影响
        memory_usage = current_metrics.get("gauges", {}).get("memory_usage", 0)
        if memory_usage > 90:
            health_score -= 20
        elif memory_usage > 70:
            health_score -= 10

        # 成功率影响
        success_rate = current_metrics.get("gauges", {}).get("success_rate", 100)
        if success_rate < 80:
            health_score -= 30
        elif success_rate < 90:
            health_score -= 15

        # 队列深度影响
        queue_depth = current_metrics.get("gauges", {}).get("queue_depth", 0)
        if queue_depth > 100:
            health_score -= 20
        elif queue_depth > 50:
            health_score -= 10

        # 活跃错误告警影响
        error_alerts = [a for a in alerts if a["level"] in ["error", "critical"]]
        if error_alerts:
            health_score -= min(len(error_alerts) * 5, 25)

        health_score = max(0, health_score)

        # 确定健康状态
        if health_score >= 90:
            health_status = "healthy"
        elif health_score >= 70:
            health_status = "warning"
        elif health_score >= 50:
            health_status = "degraded"
        else:
            health_status = "critical"

        return {
            "status": health_status,
            "score": health_score,
            "checks": {
                "cpu_usage": {
                    "value": cpu_usage,
                    "status": "ok" if cpu_usage < 70 else "warning" if cpu_usage < 90 else "critical"
                },
                "memory_usage": {
                    "value": memory_usage,
                    "status": "ok" if memory_usage < 70 else "warning" if memory_usage < 90 else "critical"
                },
                "success_rate": {
                    "value": success_rate,
                    "status": "ok" if success_rate > 95 else "warning" if success_rate > 80 else "critical"
                },
                "queue_depth": {
                    "value": queue_depth,
                    "status": "ok" if queue_depth < 50 else "warning" if queue_depth < 100 else "critical"
                },
                "active_alerts": {
                    "value": len(error_alerts),
                    "status": "ok" if len(error_alerts) == 0 else "warning" if len(error_alerts) < 3 else "critical"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def add_custom_alert_rule(self, rule):
        """添加自定义告警规则"""
        alert_manager.add_rule(rule)

    def get_alerts(self, hours: int = 24, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取告警列表"""
        alert_level = AlertLevel(level) if level else None
        return alert_manager.get_recent_alerts(hours, alert_level)

    def enable_alerts(self):
        """启用告警"""
        alert_manager.enable()

    def disable_alerts(self):
        """禁用告警"""
        alert_manager.disable()

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        return alert_manager.resolve_alert(alert_id)


# 全局监控服务实例
monitoring_service: Optional[MonitoringService] = None


def initialize_monitoring(task_queue: Optional[CrawlerTaskQueue] = None,
                         workflow_engine: Optional[WorkflowEngine] = None) -> MonitoringService:
    """
    初始化监控服务

    Args:
        task_queue: 任务队列实例
        workflow_engine: 工作流引擎实例

    Returns:
        监控服务实例
    """
    global monitoring_service
    monitoring_service = MonitoringService(task_queue, workflow_engine)
    monitoring_service.start()
    return monitoring_service


def get_monitoring_service() -> Optional[MonitoringService]:
    """获取监控服务实例"""
    return monitoring_service


def shutdown_monitoring():
    """关闭监控服务"""
    global monitoring_service
    if monitoring_service:
        monitoring_service.stop()
        monitoring_service = None