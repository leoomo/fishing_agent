import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, case, and_

from apps.api.orm.session import get_db_session
from apps.api.models.equipment import Equipment
from apps.api.models.brand import Brand
from apps.api.models.user import User, UserEquipment
from apps.api.models.system import AnalyticsReport, APILog, AgentExecutionLog
from apps.api.models.admin_user import AdminUser

logger = logging.getLogger(__name__)


class AnalyticsService:
    """数据分析服务"""

    def get_equipment_stats(self) -> Dict:
        """
        获取装备统计总览

        Returns:
            dict: 装备统计数据
        """
        with get_db_session() as session:
            # 总装备数
            total_equipment = session.query(Equipment).filter(
                Equipment.is_active == True
            ).count()

            # 总品牌数
            total_brands = session.query(Brand).count()

            # 平均价格
            avg_price = session.query(
                func.avg((Equipment.price_min + Equipment.price_max) / 2)
            ).filter(
                Equipment.is_active == True,
                Equipment.price_min.isnot(None),
                Equipment.price_max.isnot(None)
            ).scalar() or 0

            # 价格分布
            price_distribution = self.get_price_distribution()

            # Top 品牌
            top_brands = self.get_brand_stats(top_n=10)

            # 按类别统计
            by_category = {}
            categories = session.query(
                Equipment.category,
                func.count(Equipment.equipment_id)
            ).filter(
                Equipment.is_active == True
            ).group_by(
                Equipment.category
            ).all()

            for category, count in categories:
                by_category[category] = count

            return {
                "total_equipment": total_equipment,
                "total_brands": total_brands,
                "avg_price": round(avg_price, 2),
                "price_distribution": price_distribution,
                "top_brands": top_brands,
                "by_category": by_category
            }

    def get_equipment_trends(self, months: int = 12) -> List[Dict]:
        """
        获取装备数量趋势（按月）

        Args:
            months: 统计月数

        Returns:
            list: 趋势数据
        """
        with get_db_session() as session:
            # 计算起始月份
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

            # 按月统计
            trends = session.query(
                func.strftime('%Y-%m', Equipment.created_at).label('month'),
                func.count(Equipment.equipment_id).label('count'),
                Equipment.category
            ).filter(
                Equipment.created_at >= start_date,
                Equipment.is_active == True
            ).group_by(
                'month',
                Equipment.category
            ).order_by(
                'month'
            ).all()

            # 组织数据
            result = {}
            for month, count, category in trends:
                if month not in result:
                    result[month] = {
                        'date': month,
                        'total_count': 0,
                        'by_category': {}
                    }

                result[month]['total_count'] += count
                result[month]['by_category'][category] = count

            return list(result.values())

    def get_price_distribution(self, category: Optional[str] = None) -> List[Dict]:
        """
        获取价格分布统计（使用 SQL CASE WHEN 优化性能）

        Args:
            category: 装备类别（可选）

        Returns:
            list: 价格分布数据
        """
        with get_db_session() as session:
            # 计算平均价格表达式
            avg_price_expr = (Equipment.price_min + Equipment.price_max) / 2

            # 使用 SQL CASE WHEN 进行分组统计
            price_range_expr = case(
                (avg_price_expr < 100, '0-100'),
                (and_(avg_price_expr >= 100, avg_price_expr < 300), '100-300'),
                (and_(avg_price_expr >= 300, avg_price_expr < 500), '300-500'),
                (and_(avg_price_expr >= 500, avg_price_expr < 1000), '500-1000'),
                (and_(avg_price_expr >= 1000, avg_price_expr < 2000), '1000-2000'),
                (and_(avg_price_expr >= 2000, avg_price_expr < 5000), '2000-5000'),
                else_='5000+'
            ).label('price_range')

            # 构建查询
            query = session.query(
                price_range_expr,
                func.count(Equipment.equipment_id).label('count')
            ).filter(
                Equipment.is_active == True,
                Equipment.price_min.isnot(None),
                Equipment.price_max.isnot(None)
            )

            if category:
                query = query.filter(Equipment.category == category)

            # 执行分组统计
            results = query.group_by('price_range').all()

            # 计算总数
            total_count = sum(r.count for r in results)

            # 定义价格区间顺序
            range_order = ['0-100', '100-300', '300-500', '500-1000', '1000-2000', '2000-5000', '5000+']
            result_dict = {r.price_range: r.count for r in results}

            # 按顺序返回结果
            distribution = []
            for range_label in range_order:
                count = result_dict.get(range_label, 0)
                if count > 0:
                    distribution.append({
                        "price_range": range_label,
                        "count": count,
                        "percentage": round(count / total_count * 100, 2) if total_count > 0 else 0
                    })

            return distribution

    def get_brand_stats(self, top_n: int = 10) -> List[Dict]:
        """
        获取品牌统计排行

        Args:
            top_n: 返回前 N 个品牌

        Returns:
            list: 品牌统计数据
        """
        with get_db_session() as session:
            # 统计每个品牌的装备数量和平均价格
            brand_stats = session.query(
                Brand.brand_id,
                Brand.name_cn,
                func.count(Equipment.equipment_id).label('equipment_count'),
                func.avg((Equipment.price_min + Equipment.price_max) / 2).label('avg_price'),
                func.sum((Equipment.price_min + Equipment.price_max) / 2).label('total_value')
            ).join(
                Equipment,
                Equipment.brand_id == Brand.brand_id
            ).filter(
                Equipment.is_active == True
            ).group_by(
                Brand.brand_id,
                Brand.name_cn
            ).order_by(
                func.count(Equipment.equipment_id).desc()
            ).limit(top_n).all()

            # 计算总装备数（用于计算百分比）
            total_equipment = session.query(Equipment).filter(
                Equipment.is_active == True
            ).count()

            result = []
            for brand_id, name_cn, count, avg_price, total_value in brand_stats:
                result.append({
                    "brand_id": brand_id,
                    "brand_name": name_cn,
                    "equipment_count": count,
                    "avg_price": round(avg_price or 0, 2),
                    "total_value": round(total_value or 0, 2),
                    "percentage": round(count / total_equipment * 100, 2) if total_equipment > 0 else 0
                })

            return result

    def get_user_activity(self, days: int = 30) -> List[Dict]:
        """
        获取用户活跃度统计（基于 API 日志）

        Args:
            days: 统计天数

        Returns:
            list: 活跃度数据
        """
        with get_db_session() as session:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 获取总用户数（用于计算活跃率）
            total_users = session.query(func.count(User.user_id)).scalar() or 1

            # 按日期统计活跃用户数（基于 API 日志）
            dau_query = session.query(
                func.date(APILog.timestamp).label('date'),
                func.count(func.distinct(APILog.user_id)).label('dau')
            ).filter(
                APILog.timestamp >= start_date,
                APILog.user_id.isnot(None)
            ).group_by(
                func.date(APILog.timestamp)
            ).all()

            dau_dict = {str(r.date): r.dau for r in dau_query}

            # 按日期统计新增用户数
            new_users_query = session.query(
                func.date(User.created_at).label('date'),
                func.count(User.user_id).label('new_count')
            ).filter(
                User.created_at >= start_date
            ).group_by(
                func.date(User.created_at)
            ).all()

            new_users_dict = {str(r.date): r.new_count for r in new_users_query}

            # 构建结果
            result = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=days-i-1)).date()
                date_str = date.isoformat()
                dau = dau_dict.get(date_str, 0)
                new_users = new_users_dict.get(date_str, 0)
                active_rate = round(dau / total_users * 100, 2) if total_users > 0 else 0.0

                result.append({
                    "date": date_str,
                    "dau": dau,
                    "new_users": new_users,
                    "active_rate": active_rate
                })

            return result

    def get_user_retention(self) -> Dict:
        """
        获取用户留存率分析

        Returns:
            dict: 留存率数据
        """
        # TODO: 实现用户留存率计算
        # 次日留存、7日留存、30日留存

        return {
            "retention_1d": 0.0,
            "retention_7d": 0.0,
            "retention_30d": 0.0
        }

    def get_query_hotspots(self, top_n: int = 20) -> List[Dict]:
        """
        获取查询热点分析

        Args:
            top_n: 返回前 N 个热点

        Returns:
            list: 热点数据
        """
        # TODO: 实现基于 LLM 日志或 API 日志的查询热点分析
        # 需要提取用户查询关键词

        return []

    def generate_report(
        self,
        report_type: str,
        start_date: str,
        end_date: str,
        generated_by: str
    ) -> Dict:
        """
        生成业务报表（收集真实数据）

        Args:
            report_type: 报表类型（weekly/monthly/custom）
            start_date: 开始日期
            end_date: 结束日期
            generated_by: 生成人

        Returns:
            dict: 报表数据
        """
        with get_db_session() as session:
            # 查找管理员用户ID
            admin_user = session.query(AdminUser).filter(
                AdminUser.username == generated_by
            ).first()

            admin_user_id = admin_user.id if admin_user else None

            # 解析日期范围
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)  # 包含结束日期

            # ========== 装备统计 ==========
            # 新增装备数
            new_equipment_count = session.query(func.count(Equipment.equipment_id)).filter(
                Equipment.created_at >= start_dt,
                Equipment.created_at < end_dt,
                Equipment.is_active == True
            ).scalar() or 0

            # 总装备数
            total_equipment_count = session.query(func.count(Equipment.equipment_id)).filter(
                Equipment.is_active == True
            ).scalar() or 0

            # 平均价格
            avg_price = session.query(
                func.avg((Equipment.price_min + Equipment.price_max) / 2)
            ).filter(
                Equipment.is_active == True,
                Equipment.price_min.isnot(None),
                Equipment.price_max.isnot(None)
            ).scalar() or 0.0

            # ========== 用户统计 ==========
            # 新增用户数
            new_users_count = session.query(func.count(User.user_id)).filter(
                User.created_at >= start_dt,
                User.created_at < end_dt
            ).scalar() or 0

            # 活跃用户数（基于 API 日志）
            active_users_count = session.query(
                func.count(func.distinct(APILog.user_id))
            ).filter(
                APILog.timestamp >= start_dt,
                APILog.timestamp < end_dt,
                APILog.user_id.isnot(None)
            ).scalar() or 0

            # 总用户数（用于计算留存率）
            total_users = session.query(func.count(User.user_id)).scalar() or 1
            retention_rate = round(active_users_count / total_users * 100, 2) if total_users > 0 else 0.0

            # ========== API 统计 ==========
            # 总调用量
            api_total_calls = session.query(func.count(APILog.id)).filter(
                APILog.timestamp >= start_dt,
                APILog.timestamp < end_dt
            ).scalar() or 0

            # 平均响应时间
            api_avg_response_time = session.query(
                func.avg(APILog.response_time)
            ).filter(
                APILog.timestamp >= start_dt,
                APILog.timestamp < end_dt,
                APILog.response_time.isnot(None)
            ).scalar() or 0.0

            # 错误率
            api_error_count = session.query(func.count(APILog.id)).filter(
                APILog.timestamp >= start_dt,
                APILog.timestamp < end_dt,
                APILog.status_code >= 400
            ).scalar() or 0
            api_error_rate = round(api_error_count / api_total_calls * 100, 2) if api_total_calls > 0 else 0.0

            # ========== LLM/Agent 统计 ==========
            # 总调用量
            llm_total_calls = session.query(func.count(AgentExecutionLog.id)).filter(
                AgentExecutionLog.timestamp >= start_dt,
                AgentExecutionLog.timestamp < end_dt
            ).scalar() or 0

            # 总 Token 数
            llm_total_tokens = session.query(
                func.sum(AgentExecutionLog.total_tokens)
            ).filter(
                AgentExecutionLog.timestamp >= start_dt,
                AgentExecutionLog.timestamp < end_dt
            ).scalar() or 0

            # 收集报表数据
            report_data = {
                "equipment": {
                    "new_count": new_equipment_count,
                    "total_count": total_equipment_count,
                    "avg_price": round(avg_price, 2)
                },
                "users": {
                    "new_count": new_users_count,
                    "active_count": active_users_count,
                    "retention_rate": retention_rate
                },
                "api": {
                    "total_calls": api_total_calls,
                    "avg_response_time": round(api_avg_response_time, 2),
                    "error_rate": api_error_rate
                },
                "llm": {
                    "total_calls": llm_total_calls,
                    "total_tokens": llm_total_tokens,
                    "total_cost": 0.0  # 成本需要根据具体定价计算
                }
            }

            # 创建报表记录
            report = AnalyticsReport(
                report_type=report_type,
                start_date=datetime.fromisoformat(start_date).date(),
                end_date=datetime.fromisoformat(end_date).date(),
                report_data=json.dumps(report_data, ensure_ascii=False),
                generated_by=admin_user_id,
                is_published=True
            )

            session.add(report)
            session.commit()
            session.refresh(report)

            return {
                "report_id": report.id,
                "report_type": report.report_type,
                "start_date": report.start_date.isoformat(),
                "end_date": report.end_date.isoformat(),
                "report_data": report_data,
                "generated_at": report.created_at.isoformat(),
                "generated_by": generated_by
            }

    def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        report_type: Optional[str] = None
    ) -> Dict:
        """
        查询报表列表

        Args:
            page: 页码
            page_size: 每页数量
            report_type: 报表类型过滤

        Returns:
            dict: 报表列表
        """
        with get_db_session() as session:
            query = session.query(AnalyticsReport)

            if report_type:
                query = query.filter(AnalyticsReport.report_type == report_type)

            total = query.count()

            reports = query.order_by(
                AnalyticsReport.created_at.desc()
            ).limit(page_size).offset((page - 1) * page_size).all()

            return {
                "total": total,
                "reports": [
                    {
                        "report_id": r.id,
                        "report_type": r.report_type,
                        "start_date": r.start_date.isoformat(),
                        "end_date": r.end_date.isoformat(),
                        "report_data": json.loads(r.report_data),  # 转换回 dict
                        "generated_at": r.created_at.isoformat(),
                        "generated_by": "admin"  # TODO: 从关联表获取
                    }
                    for r in reports
                ]
            }
