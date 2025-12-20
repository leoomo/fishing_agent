import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.equipment import Equipment
from packages.agent_fishing.tools.lure.models.brand import Brand
from packages.agent_fishing.tools.lure.models.user import User, UserEquipment
from packages.agent_fishing.tools.lure.models.system import AnalyticsReport, APILog
from packages.agent_fishing.tools.lure.models.admin_user import AdminUser

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
        获取价格分布统计

        Args:
            category: 装备类别（可选）

        Returns:
            list: 价格分布数据
        """
        with get_db_session() as session:
            query = session.query(Equipment).filter(
                Equipment.is_active == True,
                Equipment.price_min.isnot(None),
                Equipment.price_max.isnot(None)
            )

            if category:
                query = query.filter(Equipment.category == category)

            equipment_list = query.all()

            # 定义价格区间
            price_ranges = [
                (0, 100),
                (100, 300),
                (300, 500),
                (500, 1000),
                (1000, 2000),
                (2000, 5000),
                (5000, float('inf'))
            ]

            distribution = []
            total_count = len(equipment_list)

            for min_price, max_price in price_ranges:
                count = sum(
                    1 for eq in equipment_list
                    if min_price <= ((eq.price_min + eq.price_max) / 2) < max_price
                )

                if count > 0:
                    range_label = f"{min_price}-{max_price}" if max_price != float('inf') else f"{min_price}+"

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
        获取用户活跃度统计

        Args:
            days: 统计天数

        Returns:
            list: 活跃度数据
        """
        with get_db_session() as session:
            # TODO: 实现基于 API 日志的活跃度统计
            # 需要从 api_logs 表中提取用户活跃数据

            # 占位符实现
            result = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=days-i-1)).date()
                result.append({
                    "date": date.isoformat(),
                    "dau": 0,  # 日活跃用户数
                    "new_users": 0,  # 新增用户数
                    "active_rate": 0.0  # 活跃率
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
        生成业务报表

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

            # 收集报表数据
            report_data = {
                "equipment": {
                    "new_count": 0,  # 新增装备数
                    "total_count": 0,  # 总装备数
                    "avg_price": 0.0  # 平均价格
                },
                "users": {
                    "new_count": 0,  # 新增用户数
                    "active_count": 0,  # 活跃用户数
                    "retention_rate": 0.0  # 留存率
                },
                "api": {
                    "total_calls": 0,  # 总调用量
                    "avg_response_time": 0.0,  # 平均响应时间
                    "error_rate": 0.0  # 错误率
                },
                "llm": {
                    "total_calls": 0,  # 总调用量
                    "total_tokens": 0,  # 总 Token 数
                    "total_cost": 0.0  # 总成本
                }
            }

            # 创建报表记录
            report = AnalyticsReport(
                report_type=report_type,
                start_date=datetime.fromisoformat(start_date).date(),
                end_date=datetime.fromisoformat(end_date).date(),
                report_data=json.dumps(report_data, ensure_ascii=False),  # JSON 字符串
                generated_by=admin_user_id,  # 关联 admin_user_id
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
