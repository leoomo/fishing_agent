#!/usr/bin/env python3
"""
监控系统测试

测试指标收集、告警和监控服务功能
"""

import logging
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from packages.agent_fishing.tools.crawler.monitoring import (
    metrics_collector, alert_manager, AlertLevel,
    MonitoringService
)
from packages.agent_fishing.tools.crawler.monitoring.alerts import (
    QueueDepthAlertRule, FailureRateAlertRule,
    SystemResourceAlertRule, TaskTimeoutAlertRule
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_metrics_collection():
    """测试指标收集"""
    logger.info("=== 测试指标收集 ===")

    try:
        # 模拟任务执行
        task_id = 1001

        # 记录任务开始
        metrics_collector.record_task_start(task_id, "taobao")
        logger.info("✅ 记录任务开始")

        # 等待一秒
        time.sleep(1)

        # 记录任务完成
        metrics_collector.record_task_complete(
            task_id=task_id,
            status="success",
            items_processed=100,
            items_success=95,
            items_failed=5
        )
        logger.info("✅ 记录任务完成")

        # 获取任务指标
        task_metric = metrics_collector.get_task_metrics(task_id)
        if task_metric:
            logger.info(f"任务指标: 状态={task_metric.status}, 耗时={task_metric.duration:.2f}秒")
        else:
            logger.error("❌ 无法获取任务指标")
            return False

        # 获取当前指标
        current = metrics_collector.get_current_metrics()
        logger.info(f"当前指标: 计数器={current['counters']}, 仪表盘={current['gauges']}")

        return True

    except Exception as e:
        logger.error(f"❌ 指标收集测试失败: {e}")
        return False


def test_alert_rules():
    """测试告警规则"""
    logger.info("\n=== 测试告警规则 ===")

    try:
        # 创建测试告警规则
        test_rule = QueueDepthAlertRule(threshold=1, level=AlertLevel.WARNING)
        logger.info(f"创建告警规则: {test_rule.name}")

        # 记录队列深度（模拟超过阈值）
        metrics_collector.record_queue_metrics(depth=5, running=2)
        logger.info("模拟队列深度为5")

        # 检查告警
        alert = test_rule.check()
        if alert:
            logger.info(f"✅ 触发告警: {alert.message}")
            logger.info(f"  级别: {alert.level}")
            logger.info(f"  元数据: {alert.metadata}")
        else:
            logger.warning("⚠️ 未触发告警")
            return False

        # 测试添加告警规则到管理器
        alert_manager.add_rule(test_rule)
        logger.info("✅ 添加告警规则到管理器")

        # 检查所有告警
        alert_manager.check_alerts()
        logger.info("✅ 执行告警检查")

        # 获取最近的告警
        recent_alerts = alert_manager.get_recent_alerts(hours=1)
        if recent_alerts:
            logger.info(f"最近告警数量: {len(recent_alerts)}")
            logger.info(f"最新告警: {recent_alerts[-1]['message']}")

        return True

    except Exception as e:
        logger.error(f"❌ 告警规则测试失败: {e}")
        return False


def test_monitoring_service():
    """测试监控服务"""
    logger.info("\n=== 测试监控服务 ===")

    try:
        # 创建监控服务
        monitor = MonitoringService()
        logger.info("✅ 创建监控服务")

        # 记录一些任务事件
        monitor.record_task_event("start", 2001, task_type="taobao")
        time.sleep(0.5)
        monitor.record_task_event("complete", 2001, status="success", items_processed=50)
        logger.info("✅ 记录任务事件")

        monitor.record_task_event("start", 2002, task_type="jd")
        time.sleep(0.3)
        monitor.record_task_event("complete", 2002, status="failed", error_message="测试错误")
        logger.info("✅ 记录失败任务事件")

        # 获取仪表盘数据
        dashboard = monitor.get_dashboard_data()
        logger.info("✅ 获取仪表盘数据")
        logger.info(f"  当前指标: {dashboard['current_metrics']['task_stats']}")
        logger.info(f"  告警摘要: {dashboard['alert_summary']}")
        logger.info(f"  任务类型统计: {dashboard['task_type_stats']}")

        # 获取系统健康状态
        health = monitor.get_system_health()
        logger.info("✅ 获取系统健康状态")
        logger.info(f"  状态: {health['status']}")
        logger.info(f"  评分: {health['score']}")
        logger.info(f"  检查项: {health['checks']}")

        # 获取任务报告
        report = monitor.get_task_report(2001)
        if report:
            logger.info("✅ 获取任务报告")
            logger.info(f"  任务2001: 状态={report['status']}, 耗时={report['duration']:.2f}秒")

        return True

    except Exception as e:
        logger.error(f"❌ 监控服务测试失败: {e}")
        return False


def test_alert_levels():
    """测试不同级别的告警"""
    logger.info("\n=== 测试告警级别 ===")

    try:
        # 测试不同级别的告警规则
        rules = [
            ("INFO", AlertLevel.INFO),
            ("WARNING", AlertLevel.WARNING),
            ("ERROR", AlertLevel.ERROR),
            ("CRITICAL", AlertLevel.CRITICAL)
        ]

        for level_name, level in rules:
            rule = SystemResourceAlertRule(
                resource="cpu",
                threshold=0.5,  # 50%触发（便于测试）
                level=level
            )
            logger.info(f"测试 {level_name} 级别告警规则")

            # 模拟高CPU使用率
            metrics_collector.gauges["cpu_usage"] = 80

            alert = rule.check()
            if alert:
                logger.info(f"  ✅ 触发 {level} 告警: {alert.message}")
            else:
                logger.warning(f"  ⚠️ 未触发 {level} 告警")

        # 清理
        metrics_collector.gauges["cpu_usage"] = 0

        return True

    except Exception as e:
        logger.error(f"❌ 告警级别测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    logger.info("开始监控系统测试")

    tests = [
        ("指标收集", test_metrics_collection),
        ("告警规则", test_alert_rules),
        ("监控服务", test_monitoring_service),
        ("告警级别", test_alert_levels)
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 异常: {e}", exc_info=True)
            results.append((test_name, False))

    # 输出测试结果
    logger.info(f"\n{'='*50}")
    logger.info("测试结果汇总:")
    logger.info(f"{'='*50}")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        logger.info("🎉 所有测试通过！监控系统功能正常。")
        return 0
    else:
        logger.error("部分测试失败，需要进一步调试。")
        return 1


if __name__ == "__main__":
    exit(main())