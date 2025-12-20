"""
监控服务 - 系统统计和健康检查
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, case, text

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import APILog, LLMLog, AgentExecutionLog, ToolCallLog

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

            # 排除监控API本身的调用，避免循环统计
            query = query.filter(~APILog.endpoint.like('%/admin/monitor/%'))

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

            # 按端点统计
            requests_by_endpoint = {}
            for ep in top_endpoints:
                requests_by_endpoint[ep["endpoint"]] = ep["count"]

            # 按状态码统计
            status_stats = session.query(
                APILog.status_code,
                func.count(APILog.id).label('count')
            ).filter(
                APILog.timestamp >= start_date
            ).group_by(
                APILog.status_code
            ).all()

            requests_by_status = {str(status): count for status, count in status_stats}

            # 按日期统计
            daily_stats = session.query(
                func.date(APILog.timestamp).label('date'),
                func.count(APILog.id).label('count')
            ).filter(
                APILog.timestamp >= start_date
            ).group_by(
                func.date(APILog.timestamp)
            ).order_by('date').all()

            requests_by_day = [
                {"date": str(date), "count": count}
                for date, count in daily_stats
            ]

            return {
                "total_requests": total_calls,
                "avg_response_time": round(avg_response_time, 2),
                "error_rate": round(error_rate, 2) / 100,  # 转换为小数
                "requests_by_endpoint": requests_by_endpoint,
                "requests_by_status": requests_by_status,
                "requests_by_day": requests_by_day
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
            by_provider_stats = session.query(
                LLMLog.model_provider,
                func.count(LLMLog.id).label('calls'),
                func.sum(LLMLog.total_tokens).label('tokens'),
                func.sum(LLMLog.cost).label('cost'),
                func.avg(LLMLog.response_time).label('avg_latency')
            ).filter(
                LLMLog.timestamp >= start_date
            ).group_by(
                LLMLog.model_provider
            ).all()

            by_provider = [
                {
                    "provider": provider,
                    "calls": calls,
                    "tokens": int(tokens or 0),
                    "cost": round(float(cost or 0), 4),
                    "avg_latency": round(float(avg_latency or 0), 2)
                }
                for provider, calls, tokens, cost, avg_latency in by_provider_stats
                if provider
            ]

            # 按日期统计
            daily_stats = session.query(
                func.date(LLMLog.timestamp).label('date'),
                func.count(LLMLog.id).label('calls'),
                func.sum(LLMLog.total_tokens).label('tokens')
            ).filter(
                LLMLog.timestamp >= start_date
            ).group_by(
                func.date(LLMLog.timestamp)
            ).order_by('date').all()

            by_day = [
                {
                    "date": str(date),
                    "calls": calls,
                    "tokens": int(tokens or 0)
                }
                for date, calls, tokens in daily_stats
            ]

            return {
                "total_calls": total_calls,
                "total_tokens": int(total_tokens),
                "total_cost": round(float(total_cost), 4),
                "success_rate": round(success_rate, 2) / 100,  # 转换为小数
                "by_provider": by_provider,
                "by_day": by_day
            }

    def get_db_performance(self) -> Dict:
        """
        获取数据库性能指标

        Returns:
            dict: 数据库性能数据
        """
        with get_db_session() as session:
            # 获取表大小统计（使用SQLite的特定查询）
            table_stats_raw = session.execute(text("""
                SELECT
                    name as table_name,
                    sql as create_sql
                FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)).fetchall()

            table_sizes = []
            for table_info in table_stats_raw:
                table_name = table_info[0]

                # 获取行数
                try:
                    count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    row_count = count_result or 0
                except:
                    row_count = 0

                # SQLite 没有直接获取表大小的方法，这里使用估算
                # 假设平均每行约1KB的数据
                estimated_size_mb = max(0.01, round(row_count * 0.001, 2))

                table_sizes.append({
                    "table": table_name,
                    "size_mb": estimated_size_mb,
                    "row_count": row_count
                })

            # SQLite 特定的性能指标
            # 获取数据库页面大小和总页数来估算数据库大小
            db_stats = session.execute(text("PRAGMA page_count")).scalar()
            page_size = session.execute(text("PRAGMA page_size")).scalar()
            db_size_mb = round((db_stats * page_size) / (1024 * 1024), 2)

            # SQLite 没有连接池概念，使用默认值
            connection_pool_size = 10
            active_connections = 1  # SQLite是单连接数据库

            return {
                "avg_query_time": 5.2,  # SQLite通常较快
                "slow_queries": 0,  # 慢查询计数需要额外实现
                "connection_pool_size": connection_pool_size,
                "active_connections": active_connections,
                "table_sizes": table_sizes,
                "database_size_mb": db_size_mb
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
                session.execute(text("SELECT 1"))
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

    # ========== Agent 监控方法 ==========

    def get_agent_stats(
        self,
        agent_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取 Agent 执行统计

        Args:
            agent_type: 过滤特定 Agent 类型
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            dict: Agent 统计数据
        """
        with get_db_session() as session:
            query = session.query(AgentExecutionLog)

            # 默认统计最近7天
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            query = query.filter(AgentExecutionLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AgentExecutionLog.timestamp <= end_date)
            if agent_type:
                query = query.filter(AgentExecutionLog.agent_type == agent_type)

            # 按 Agent 类型聚合
            stats = session.query(
                AgentExecutionLog.agent_type,
                func.count(AgentExecutionLog.id).label('total_executions'),
                func.avg(AgentExecutionLog.latency_ms).label('avg_latency'),
                func.sum(AgentExecutionLog.total_tokens).label('total_tokens'),
                func.sum(AgentExecutionLog.estimated_cost).label('total_cost'),
                func.sum(case((AgentExecutionLog.success == True, 1), else_=0)).label('success_count'),
            ).filter(
                AgentExecutionLog.timestamp >= start_date
            )

            if end_date:
                stats = stats.filter(AgentExecutionLog.timestamp <= end_date)
            if agent_type:
                stats = stats.filter(AgentExecutionLog.agent_type == agent_type)

            stats = stats.group_by(AgentExecutionLog.agent_type).all()

            agents = []
            total_executions = 0
            total_tokens = 0
            total_cost = 0.0

            for row in stats:
                exec_count = row.total_executions or 0
                success_rate = (row.success_count / exec_count * 100) if exec_count > 0 else 0
                tokens = row.total_tokens or 0
                cost = row.total_cost or 0

                agents.append({
                    "agent_type": row.agent_type,
                    "total_executions": exec_count,
                    "success_rate": round(success_rate, 2),
                    "avg_latency_ms": round(row.avg_latency, 2) if row.avg_latency else 0,
                    "total_tokens": int(tokens),
                    "total_cost": round(float(cost), 4),
                })

                total_executions += exec_count
                total_tokens += tokens
                total_cost += cost

            return {
                "agents": agents,
                "total_executions": total_executions,
                "total_tokens": int(total_tokens),
                "total_cost": round(total_cost, 4)
            }

    def get_tool_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取工具使用统计

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: 工具统计数据
        """
        with get_db_session() as session:
            # 默认统计最近7天
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            # 按工具聚合
            by_tool = session.query(
                ToolCallLog.tool_name,
                ToolCallLog.tool_category,
                func.count(ToolCallLog.id).label('call_count'),
                func.avg(ToolCallLog.latency_ms).label('avg_latency'),
                func.sum(case((ToolCallLog.success == True, 1), else_=0)).label('success_count'),
            ).filter(
                ToolCallLog.timestamp >= start_date
            )

            if end_date:
                by_tool = by_tool.filter(ToolCallLog.timestamp <= end_date)

            by_tool = by_tool.group_by(
                ToolCallLog.tool_name, ToolCallLog.tool_category
            ).order_by(
                func.count(ToolCallLog.id).desc()
            ).all()

            tools = []
            for row in by_tool:
                call_count = row.call_count or 0
                success_rate = (row.success_count / call_count * 100) if call_count > 0 else 0

                tools.append({
                    "tool_name": row.tool_name,
                    "category": row.tool_category or "other",
                    "call_count": call_count,
                    "success_rate": round(success_rate, 2),
                    "avg_latency_ms": round(row.avg_latency, 2) if row.avg_latency else 0,
                })

            # 按类别统计
            by_category_query = session.query(
                ToolCallLog.tool_category,
                func.count(ToolCallLog.id).label('count'),
            ).filter(
                ToolCallLog.timestamp >= start_date
            )

            if end_date:
                by_category_query = by_category_query.filter(ToolCallLog.timestamp <= end_date)

            by_category_result = by_category_query.group_by(ToolCallLog.tool_category).all()

            by_category = {
                (row.tool_category or "other"): row.count
                for row in by_category_result
            }

            return {
                "tools": tools,
                "by_category": by_category,
            }

    def get_latency_percentiles(
        self,
        agent_type: Optional[str] = None,
        start_date: Optional[str] = None
    ) -> Dict:
        """
        获取延时百分位数据 (P50/P90/P99)

        Args:
            agent_type: 过滤特定 Agent 类型
            start_date: 开始日期

        Returns:
            dict: 延时百分位数据
        """
        with get_db_session() as session:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            query = session.query(AgentExecutionLog.latency_ms).filter(
                AgentExecutionLog.latency_ms.isnot(None),
                AgentExecutionLog.timestamp >= start_date
            )

            if agent_type:
                query = query.filter(AgentExecutionLog.agent_type == agent_type)

            latencies = sorted([r[0] for r in query.all() if r[0] is not None])

            if not latencies:
                return {"p50": 0, "p90": 0, "p99": 0, "min": 0, "max": 0}

            def percentile(data: List[int], p: int) -> int:
                idx = int(len(data) * p / 100)
                return data[min(idx, len(data) - 1)]

            return {
                "p50": percentile(latencies, 50),
                "p90": percentile(latencies, 90),
                "p99": percentile(latencies, 99),
                "min": latencies[0],
                "max": latencies[-1],
            }

    def get_cost_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "day"
    ) -> Dict:
        """
        获取成本报表

        Args:
            start_date: 开始日期
            end_date: 结束日期
            group_by: 分组方式 (day/week/month)

        Returns:
            dict: 成本报表数据
        """
        with get_db_session() as session:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            query = session.query(AgentExecutionLog).filter(
                AgentExecutionLog.timestamp >= start_date
            )

            if end_date:
                query = query.filter(AgentExecutionLog.timestamp <= end_date)

            # 获取所有记录并在 Python 中处理（避免数据库特定 SQL）
            records = query.all()

            # 按日期和 Agent 类型分组
            daily_stats = {}
            by_agent = {}

            for record in records:
                date_str = record.timestamp.strftime('%Y-%m-%d')
                agent = record.agent_type

                key = (date_str, agent)
                if key not in daily_stats:
                    daily_stats[key] = {
                        "date": date_str,
                        "agent_type": agent,
                        "total_cost": 0,
                        "total_tokens": 0,
                        "executions": 0
                    }

                daily_stats[key]["total_cost"] += record.estimated_cost or 0
                daily_stats[key]["total_tokens"] += record.total_tokens or 0
                daily_stats[key]["executions"] += 1

                by_agent[agent] = by_agent.get(agent, 0) + (record.estimated_cost or 0)

            items = list(daily_stats.values())
            items.sort(key=lambda x: (x["date"], x["agent_type"]))

            total_cost = sum(item["total_cost"] for item in items)

            return {
                "items": items,
                "total_cost": round(total_cost, 4),
                "by_agent": {k: round(v, 4) for k, v in by_agent.items()}
            }

    def get_agent_trends(
        self,
        agent_type: Optional[str] = None,
        days: int = 7
    ) -> Dict:
        """
        获取 Agent 趋势数据

        Args:
            agent_type: 过滤特定 Agent 类型
            days: 统计天数

        Returns:
            dict: 趋势数据
        """
        with get_db_session() as session:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            query = session.query(AgentExecutionLog).filter(
                AgentExecutionLog.timestamp >= start_date
            )

            if agent_type:
                query = query.filter(AgentExecutionLog.agent_type == agent_type)

            records = query.all()

            # 按日期分组
            daily_stats = {}

            for record in records:
                date_str = record.timestamp.strftime('%Y-%m-%d')

                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        "date": date_str,
                        "executions": 0,
                        "tokens": 0,
                        "cost": 0,
                        "success_count": 0
                    }

                daily_stats[date_str]["executions"] += 1
                daily_stats[date_str]["tokens"] += record.total_tokens or 0
                daily_stats[date_str]["cost"] += record.estimated_cost or 0
                if record.success:
                    daily_stats[date_str]["success_count"] += 1

            # 计算成功率并格式化
            trends = []
            for date_str in sorted(daily_stats.keys()):
                stats = daily_stats[date_str]
                success_rate = (stats["success_count"] / stats["executions"] * 100) if stats["executions"] > 0 else 0

                trends.append({
                    "date": date_str,
                    "executions": stats["executions"],
                    "tokens": stats["tokens"],
                    "cost": round(stats["cost"], 4),
                    "success_rate": round(success_rate, 2)
                })

            return {
                "agent_type": agent_type,
                "trends": trends
            }
