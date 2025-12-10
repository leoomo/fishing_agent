"""
监控服务 - 系统统计和健康检查
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import APILog, LLMLog

logger = logging.getLogger(__name__)


class MonitorService:
    """监控服务"""

    def __init__(self):
        """初始化监控服务"""
        self.start_time = time.time()

    def get_api_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取 API 调用统计

        Args:
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            dict: API 统计数据
        """
        with get_db_session() as session:
            query = session.query(APILog)

            # 默认统计最近7天
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            # 日期过滤
            if start_date:
                query = query.filter(APILog.timestamp >= start_date)
            if end_date:
                query = query.filter(APILog.timestamp <= end_date)

            # 总调用数
            total_calls = query.count()

            # 平均响应时间
            avg_response_time = session.query(
                func.avg(APILog.response_time)
            ).filter(
                APILog.timestamp >= start_date
            ).scalar() or 0

            # 错误率
            error_count = query.filter(APILog.status_code >= 400).count()
            error_rate = (error_count / total_calls * 100) if total_calls > 0 else 0

            # Top 端点
            top_endpoints_raw = session.query(
                APILog.endpoint,
                func.count(APILog.id).label('count'),
                func.avg(APILog.response_time).label('avg_time')
            ).filter(
                APILog.timestamp >= start_date
            ).group_by(
                APILog.endpoint
            ).order_by(
                func.count(APILog.id).desc()
            ).limit(10).all()

            top_endpoints = [
                {
                    "endpoint": ep.endpoint,
                    "count": ep.count,
                    "avg_time": round(ep.avg_time, 2) if ep.avg_time else 0
                }
                for ep in top_endpoints_raw
            ]

            return {
                "total_calls": total_calls,
                "avg_response_time": round(avg_response_time, 2),
                "error_rate": round(error_rate, 2),
                "top_endpoints": top_endpoints
            }

    def get_llm_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取 LLM 使用统计

        Args:
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            dict: LLM 统计数据
        """
        with get_db_session() as session:
            query = session.query(LLMLog)

            # 默认统计最近7天
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            # 日期过滤
            if start_date:
                query = query.filter(LLMLog.timestamp >= start_date)
            if end_date:
                query = query.filter(LLMLog.timestamp <= end_date)

            # 总调用数
            total_calls = query.count()

            # 总 Token 数
            total_tokens = session.query(
                func.sum(LLMLog.total_tokens)
            ).filter(
                LLMLog.timestamp >= start_date
            ).scalar() or 0

            # 总成本
            total_cost = session.query(
                func.sum(LLMLog.cost)
            ).filter(
                LLMLog.timestamp >= start_date
            ).scalar() or 0

            # 平均响应时间
            avg_response_time = session.query(
                func.avg(LLMLog.response_time)
            ).filter(
                LLMLog.timestamp >= start_date
            ).scalar() or 0

            # 成功率
            success_count = query.filter(LLMLog.success == True).count()
            success_rate = (success_count / total_calls * 100) if total_calls > 0 else 0

            # 按提供商统计
            by_provider = {}
            providers_raw = session.query(LLMLog.model_provider).distinct().all()

            for (provider,) in providers_raw:
                if not provider:
                    continue

                provider_logs = query.filter(LLMLog.model_provider == provider)

                by_provider[provider] = {
                    "calls": provider_logs.count(),
                    "tokens": session.query(
                        func.sum(LLMLog.total_tokens)
                    ).filter(
                        LLMLog.model_provider == provider,
                        LLMLog.timestamp >= start_date
                    ).scalar() or 0,
                    "cost": session.query(
                        func.sum(LLMLog.cost)
                    ).filter(
                        LLMLog.model_provider == provider,
                        LLMLog.timestamp >= start_date
                    ).scalar() or 0
                }

            return {
                "total_calls": total_calls,
                "total_tokens": int(total_tokens),
                "total_cost": round(float(total_cost), 2),
                "avg_response_time": round(avg_response_time, 2),
                "success_rate": round(success_rate, 2),
                "by_provider": by_provider
            }

    def get_db_performance(self) -> Dict:
        """
        获取数据库性能指标

        Returns:
            dict: 数据库性能数据

        Note:
            当前为简化实现，返回模拟数据
            实际生产环境需要实现真实的数据库监控
        """
        # TODO: 实现真实的数据库性能监控
        # - 查询执行时间统计
        # - 慢查询检测
        # - 连接池状态
        # - 表大小统计

        return {
            "avg_query_time": 25.5,  # 模拟：平均查询时间 25.5ms
            "slow_queries_count": 3,  # 模拟：3个慢查询
            "connection_pool_size": 10,
            "active_connections": 2,
            "table_sizes": {
                "equipment": 150,  # MB
                "users": 80,
                "fishing_logs": 120,
                "crawler_tasks": 45,
                "api_logs": 200
            }
        }

    def check_system_health(self) -> Dict:
        """
        系统健康检查

        Returns:
            dict: 健康状态
        """
        api_status = "healthy"
        db_status = "healthy"
        llm_status = "healthy"

        # TODO: 实现真实的健康检查
        # - API 响应正常
        # - 数据库连接正常
        # - LLM 调用正常

        try:
            # 简单的数据库连通性检查
            with get_db_session() as session:
                session.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            db_status = "unhealthy"

        # 综合判断系统状态
        if db_status == "unhealthy":
            overall_status = "unhealthy"
        elif api_status == "degraded" or llm_status == "degraded":
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "api_status": api_status,
            "db_status": db_status,
            "llm_status": llm_status,
            "uptime_seconds": time.time() - self.start_time
        }

    def get_realtime_stats(self) -> Dict:
        """
        获取实时统计数据（最近1分钟）

        Returns:
            dict: 实时统计
        """
        one_minute_ago = datetime.now() - timedelta(minutes=1)

        with get_db_session() as session:
            # 最近1分钟 API 调用量
            api_calls = session.query(APILog).filter(
                APILog.timestamp >= one_minute_ago
            ).count()

            # 最近1分钟错误数
            api_errors = session.query(APILog).filter(
                APILog.timestamp >= one_minute_ago,
                APILog.status_code >= 400
            ).count()

            # 最近1分钟 LLM 调用
            llm_calls = session.query(LLMLog).filter(
                LLMLog.timestamp >= one_minute_ago
            ).count()

            # 最近1分钟 Token 消耗
            llm_tokens = session.query(
                func.sum(LLMLog.total_tokens)
            ).filter(
                LLMLog.timestamp >= one_minute_ago
            ).scalar() or 0

            return {
                "api_calls_per_minute": api_calls,
                "api_errors_per_minute": api_errors,
                "llm_calls_per_minute": llm_calls,
                "llm_tokens_per_minute": int(llm_tokens)
            }
