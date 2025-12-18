"""
告警系统

根据监控指标触发告警
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .metrics import metrics_collector

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警信息"""
    id: str
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertRule:
    """告警规则基类"""

    def __init__(self, name: str, level: AlertLevel, cooldown_minutes: int = 5):
        """
        初始化告警规则

        Args:
            name: 规则名称
            level: 告警级别
            cooldown_minutes: 冷却时间（分钟）
        """
        self.name = name
        self.level = level
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered = None

    def check(self) -> Optional[Alert]:
        """
        检查是否触发告警

        Returns:
            告警信息或None
        """
        # 检查冷却时间
        if self.last_triggered:
            elapsed = (datetime.utcnow() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_minutes * 60:
                return None

        # 执行检查
        alert = self._check_condition()
        if alert:
            self.last_triggered = datetime.utcnow()

        return alert

    def _check_condition(self) -> Optional[Alert]:
        """检查告警条件（子类实现）"""
        raise NotImplementedError


class QueueDepthAlertRule(AlertRule):
    """队列深度告警规则"""

    def __init__(self, threshold: int, level: AlertLevel = AlertLevel.WARNING):
        super().__init__(
            name=f"队列深度告警 (阈值: {threshold})",
            level=level
        )
        self.threshold = threshold

    def _check_condition(self) -> Optional[Alert]:
        metrics = metrics_collector.get_current_metrics()
        queue_depth = metrics.get("gauges", {}).get("queue_depth", 0)

        if queue_depth >= self.threshold:
            return Alert(
                id=f"queue_depth_{datetime.utcnow().timestamp()}",
                name=self.name,
                level=self.level,
                message=f"任务队列深度过高: {queue_depth} (阈值: {self.threshold})",
                timestamp=datetime.utcnow(),
                metadata={
                    "current_depth": queue_depth,
                    "threshold": self.threshold
                }
            )

        return None


class FailureRateAlertRule(AlertRule):
    """失败率告警规则"""

    def __init__(self, threshold: float, window_minutes: int = 10, level: AlertLevel = AlertLevel.ERROR):
        super().__init__(
            name=f"任务失败率告警 (阈值: {threshold*100:.1f}%)",
            level=level
        )
        self.threshold = threshold
        self.window_minutes = window_minutes

    def _check_condition(self) -> Optional[Alert]:
        # 获取最近的任务
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        recent_tasks = [
            m for m in metrics_collector.get_task_metrics()
            if m.end_time and m.end_time >= cutoff_time
        ]

        if not recent_tasks:
            return None

        failed_count = len([m for m in recent_tasks if m.status == "failed"])
        failure_rate = failed_count / len(recent_tasks)

        if failure_rate >= self.threshold:
            return Alert(
                id=f"failure_rate_{datetime.utcnow().timestamp()}",
                name=self.name,
                level=self.level,
                message=f"任务失败率过高: {failure_rate*100:.1f}% (阈值: {self.threshold*100:.1f}%)",
                timestamp=datetime.utcnow(),
                metadata={
                    "current_rate": failure_rate,
                    "threshold": self.threshold,
                    "window_minutes": self.window_minutes,
                    "failed_count": failed_count,
                    "total_count": len(recent_tasks)
                }
            )

        return None


class SystemResourceAlertRule(AlertRule):
    """系统资源告警规则"""

    def __init__(self, resource: str, threshold: float, level: AlertLevel = AlertLevel.WARNING):
        super().__init__(
            name=f"{resource}使用率告警 (阈值: {threshold*100:.1f}%)",
            level=level
        )
        self.resource = resource
        self.threshold = threshold

    def _check_condition(self) -> Optional[Alert]:
        metrics = metrics_collector.get_current_metrics()
        usage = metrics.get("gauges", {}).get(f"{self.resource}_usage", 0)

        if usage >= self.threshold * 100:
            return Alert(
                id=f"{self.resource}_usage_{datetime.utcnow().timestamp()}",
                name=self.name,
                level=self.level,
                message=f"{self.resource}使用率过高: {usage:.1f}% (阈值: {self.threshold*100:.1f}%)",
                timestamp=datetime.utcnow(),
                metadata={
                    "current_usage": usage,
                    "threshold": self.threshold * 100,
                    "resource": self.resource
                }
            )

        return None


class TaskTimeoutAlertRule(AlertRule):
    """任务超时告警规则"""

    def __init__(self, timeout_minutes: int, level: AlertLevel = AlertLevel.ERROR):
        super().__init__(
            name=f"任务超时告警 (阈值: {timeout_minutes}分钟)",
            level=level
        )
        self.timeout_minutes = timeout_minutes

    def _check_condition(self) -> Optional[Alert]:
        timeout_threshold = datetime.utcnow() - timedelta(minutes=self.timeout_minutes)

        # 查找运行时间过长的任务
        long_running_tasks = [
            m for m in metrics_collector.get_task_metrics()
            if m.status == "running" and m.start_time and m.start_time < timeout_threshold
        ]

        if long_running_tasks:
            # 返回第一个超时任务的告警
            task = long_running_tasks[0]
            duration = (datetime.utcnow() - task.start_time).total_seconds() / 60

            return Alert(
                id=f"task_timeout_{task.task_id}_{datetime.utcnow().timestamp()}",
                name=self.name,
                level=self.level,
                message=f"任务执行超时: 任务ID {task.task_id}, 已运行 {duration:.1f} 分钟 (阈值: {self.timeout_minutes})",
                timestamp=datetime.utcnow(),
                metadata={
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "duration_minutes": duration,
                    "threshold_minutes": self.timeout_minutes,
                    "start_time": task.start_time.isoformat()
                }
            )

        return None


class AlertManager:
    """告警管理器"""

    def __init__(self):
        """初始化告警管理器"""
        self.rules: List[AlertRule] = []
        self.alerts: List[Alert] = []
        self.handlers: Dict[AlertLevel, List[Callable]] = {
            AlertLevel.INFO: [],
            AlertLevel.WARNING: [],
            AlertLevel.ERROR: [],
            AlertLevel.CRITICAL: []
        }
        self.enabled = True

        # 注册默认告警处理器
        self._register_default_handlers()

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)
        logger.info(f"添加告警规则: {rule.name}")

    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        logger.info(f"移除告警规则: {rule_name}")

    def add_handler(self, level: AlertLevel, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.handlers[level].append(handler)
        logger.info(f"添加告警处理器: {level} -> {handler.__name__}")

    def check_alerts(self):
        """检查所有告警规则"""
        if not self.enabled:
            return

        for rule in self.rules:
            try:
                alert = rule.check()
                if alert:
                    self._handle_alert(alert)
            except Exception as e:
                logger.error(f"检查告警规则失败 {rule.name}: {e}")

    def _handle_alert(self, alert: Alert):
        """处理告警"""
        # 记录告警
        self.alerts.append(alert)

        # 限制告警历史数量
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        logger.warning(f"触发告警 [{alert.level}]: {alert.message}")

        # 调用处理器
        for handler in self.handlers[alert.level]:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")

    def _register_default_handlers(self):
        """注册默认告警处理器"""
        # 日志处理器（所有级别）
        for level in AlertLevel:
            self.add_handler(level, self._log_handler)

    def _log_handler(self, alert: Alert):
        """日志告警处理器"""
        if alert.level == AlertLevel.INFO:
            logger.info(f"[告警] {alert.message}")
        elif alert.level == AlertLevel.WARNING:
            logger.warning(f"[告警] {alert.message}")
        elif alert.level == AlertLevel.ERROR:
            logger.error(f"[告警] {alert.message}")
        elif alert.level == AlertLevel.CRITICAL:
            logger.critical(f"[告警] {alert.message}")

    def get_recent_alerts(self, hours: int = 24, level: Optional[AlertLevel] = None) -> List[Dict[str, Any]]:
        """
        获取最近的告警

        Args:
            hours: 获取最近N小时的告警
            level: 过滤特定级别

        Returns:
            告警列表
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        alerts = self.alerts
        if level:
            alerts = [a for a in alerts if a.level == level]

        recent_alerts = [
            a for a in alerts if a.timestamp >= cutoff_time
        ]

        return [
            {
                "id": alert.id,
                "name": alert.name,
                "level": alert.level,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "metadata": alert.metadata
            }
            for alert in recent_alerts
        ]

    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        # 按级别统计最近24小时的告警
        recent_alerts = self.get_recent_alerts(24)

        level_counts = {level.value: 0 for level in AlertLevel}
        for alert in recent_alerts:
            level_counts[alert.level] += 1

        # 获取最新的告警
        latest_alerts = sorted(recent_alerts, key=lambda x: x["timestamp"], reverse=True)[:10]

        return {
            "total": len(recent_alerts),
            "by_level": level_counts,
            "latest": latest_alerts,
            "active_rules": len(self.rules)
        }

    def enable(self):
        """启用告警"""
        self.enabled = True
        logger.info("告警系统已启用")

    def disable(self):
        """禁用告警"""
        self.enabled = False
        logger.info("告警系统已禁用")

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                logger.info(f"告警已解决: {alert_id}")
                return True
        return False


# 创建全局告警管理器
alert_manager = AlertManager()

# 注册默认告警规则
alert_manager.add_rule(QueueDepthAlertRule(threshold=100, level=AlertLevel.WARNING))
alert_manager.add_rule(QueueDepthAlertRule(threshold=200, level=AlertLevel.ERROR))
alert_manager.add_rule(FailureRateAlertRule(threshold=0.2, window_minutes=10, level=AlertLevel.WARNING))
alert_manager.add_rule(FailureRateAlertRule(threshold=0.5, window_minutes=5, level=AlertLevel.ERROR))
alert_manager.add_rule(SystemResourceAlertRule("cpu", threshold=0.8, level=AlertLevel.WARNING))
alert_manager.add_rule(SystemResourceAlertRule("cpu", threshold=0.95, level=AlertLevel.ERROR))
alert_manager.add_rule(SystemResourceAlertRule("memory", threshold=0.8, level=AlertLevel.WARNING))
alert_manager.add_rule(SystemResourceAlertRule("memory", threshold=0.95, level=AlertLevel.ERROR))
alert_manager.add_rule(TaskTimeoutAlertRule(timeout_minutes=60, level=AlertLevel.WARNING))
alert_manager.add_rule(TaskTimeoutAlertRule(timeout_minutes=120, level=AlertLevel.ERROR))