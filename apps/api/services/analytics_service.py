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

    def get_categories(self) -> List[str]:
        """
        获取所有装备类别列表

        Returns:
            list: 类别名称列表
        """
        with get_db_session() as session:
            categories = session.query(
                Equipment.category
            ).filter(
                Equipment.is_active == True,
                Equipment.category.isnot(None)
            ).distinct().all()

            return [cat[0] for cat in categories if cat[0]]

    def get_user_retention(self, days: int = 30) -> Dict:
        """
        获取用户留存率分析

        基于 API 日志计算用户留存率：
        - 找出在分析期间首次活跃的用户（新用户）
        - 计算这些新用户在 N 天后是否还有活跃行为

        Args:
            days: 分析周期（天）

        Returns:
            dict: 留存率数据
        """
        with get_db_session() as session:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 获取每个用户的首次活跃日期
            first_active_subquery = session.query(
                APILog.user_id,
                func.min(func.date(APILog.timestamp)).label('first_active_date')
            ).filter(
                APILog.user_id.isnot(None),
                APILog.timestamp >= start_date - timedelta(days=30)  # 扩展范围以获取完整的首次活跃日期
            ).group_by(
                APILog.user_id
            ).subquery()

            # 找出在分析期间首次活跃的新用户
            new_users = session.query(
                first_active_subquery.c.user_id,
                first_active_subquery.c.first_active_date
            ).filter(
                first_active_subquery.c.first_active_date >= start_date.date(),
                first_active_subquery.c.first_active_date <= (end_date - timedelta(days=30)).date()  # 确保有30天观察期
            ).all()

            if not new_users:
                return {
                    "retention_1d": 0.0,
                    "retention_7d": 0.0,
                    "retention_30d": 0.0,
                    "new_users_count": 0,
                    "analysis_period_days": days
                }

            # 获取所有用户的活跃日期集合
            user_active_dates = {}
            active_logs = session.query(
                APILog.user_id,
                func.date(APILog.timestamp).label('active_date')
            ).filter(
                APILog.user_id.isnot(None),
                APILog.timestamp >= start_date
            ).distinct().all()

            for user_id, active_date in active_logs:
                if user_id not in user_active_dates:
                    user_active_dates[user_id] = set()
                user_active_dates[user_id].add(active_date)

            # 计算留存率
            retention_1d_count = 0
            retention_7d_count = 0
            retention_30d_count = 0
            total_new_users = len(new_users)

            for user_id, first_active_date in new_users:
                user_dates = user_active_dates.get(user_id, set())

                # 次日留存
                day1 = first_active_date + timedelta(days=1)
                if day1 in user_dates:
                    retention_1d_count += 1

                # 7日留存
                day7 = first_active_date + timedelta(days=7)
                if day7 in user_dates:
                    retention_7d_count += 1

                # 30日留存
                day30 = first_active_date + timedelta(days=30)
                if day30 in user_dates:
                    retention_30d_count += 1

            return {
                "retention_1d": round(retention_1d_count / total_new_users * 100, 2) if total_new_users > 0 else 0.0,
                "retention_7d": round(retention_7d_count / total_new_users * 100, 2) if total_new_users > 0 else 0.0,
                "retention_30d": round(retention_30d_count / total_new_users * 100, 2) if total_new_users > 0 else 0.0,
                "new_users_count": total_new_users,
                "analysis_period_days": days
            }

    def get_query_hotspots(self, top_n: int = 20, days: int = 7) -> List[Dict]:
        """
        获取查询热点分析

        基于 Agent 执行日志提取用户查询的热门关键词

        Args:
            top_n: 返回前 N 个热点
            days: 统计天数

        Returns:
            list: 热点数据
        """
        import re
        from collections import Counter

        with get_db_session() as session:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 从 AgentExecutionLog 获取用户输入
            logs = session.query(
                AgentExecutionLog.input_text
            ).filter(
                AgentExecutionLog.timestamp >= start_date,
                AgentExecutionLog.input_text.isnot(None)
            ).all()

            if not logs:
                return []

            # 提取关键词
            keyword_counter = Counter()

            # 定义钓鱼相关的关键词模式
            fishing_keywords = [
                # 鱼种
                '鲈鱼', '鲤鱼', '鲫鱼', '草鱼', '鳜鱼', '翘嘴', '黑鱼', '鲶鱼', '罗非',
                '鳊鱼', '青鱼', '鲢鱼', '鳙鱼', '鲑鱼', '鳟鱼', '马口', '军鱼',
                # 装备类型
                '鱼竿', '路亚竿', '台钓竿', '矶钓竿', '海竿', '筏竿',
                '渔轮', '纺车轮', '水滴轮', '鼓轮',
                '鱼线', 'PE线', '尼龙线', '碳线', '碳素线',
                '拟饵', '软饵', '硬饵', '铅头钩', 'VIB', '米诺', '波爬', '铅笔',
                # 钓法
                '路亚', '台钓', '矶钓', '海钓', '筏钓', '飞蝇',
                # 品牌
                '达瓦', '禧玛诺', '阿布', '美国纯钓', '狼王',
                # 场景
                '野钓', '黑坑', '水库', '江河', '湖泊', '海边',
                # 其他
                '推荐', '入门', '新手', '高端', '性价比', '预算'
            ]

            for (input_text,) in logs:
                if not input_text:
                    continue

                # input_text 是纯文本，直接作为用户消息
                user_message = str(input_text) if input_text else ''

                # 匹配关键词
                for keyword in fishing_keywords:
                    if keyword in user_message:
                        keyword_counter[keyword] += 1

                # 提取中文词汇（简单分词）
                chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', user_message)
                for word in chinese_words:
                    if word not in fishing_keywords and len(word) >= 2:
                        keyword_counter[word] += 1

            # 过滤低频词并返回 Top N
            result = []
            for keyword, count in keyword_counter.most_common(top_n):
                if count >= 2:  # 至少出现2次
                    result.append({
                        "keyword": keyword,
                        "count": count,
                        "category": self._categorize_keyword(keyword)
                    })

            return result

    def _categorize_keyword(self, keyword: str) -> str:
        """
        对关键词进行分类

        Args:
            keyword: 关键词

        Returns:
            str: 分类名称
        """
        fish_keywords = ['鲈鱼', '鲤鱼', '鲫鱼', '草鱼', '鳜鱼', '翘嘴', '黑鱼', '鲶鱼', '罗非', '鳊鱼', '青鱼', '鲢鱼', '鳙鱼', '马口', '军鱼']
        rod_keywords = ['鱼竿', '路亚竿', '台钓竿', '矶钓竿', '海竿', '筏竿']
        reel_keywords = ['渔轮', '纺车轮', '水滴轮', '鼓轮']
        line_keywords = ['鱼线', 'PE线', '尼龙线', '碳线', '碳素线']
        lure_keywords = ['拟饵', '软饵', '硬饵', '铅头钩', 'VIB', '米诺', '波爬', '铅笔']
        method_keywords = ['路亚', '台钓', '矶钓', '海钓', '筏钓', '飞蝇']
        scene_keywords = ['野钓', '黑坑', '水库', '江河', '湖泊', '海边']

        if keyword in fish_keywords:
            return '鱼种'
        elif keyword in rod_keywords:
            return '鱼竿'
        elif keyword in reel_keywords:
            return '渔轮'
        elif keyword in line_keywords:
            return '鱼线'
        elif keyword in lure_keywords:
            return '拟饵'
        elif keyword in method_keywords:
            return '钓法'
        elif keyword in scene_keywords:
            return '场景'
        else:
            return '其他'

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
            # 使用 LEFT JOIN 关联查询获取生成人用户名
            query = session.query(
                AnalyticsReport,
                AdminUser.username
            ).outerjoin(
                AdminUser,
                AnalyticsReport.generated_by == AdminUser.id
            )

            if report_type:
                query = query.filter(AnalyticsReport.report_type == report_type)

            # 计算总数
            total = session.query(AnalyticsReport).filter(
                AnalyticsReport.report_type == report_type if report_type else True
            ).count()

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
                        "report_data": json.loads(r.report_data),
                        "generated_at": r.created_at.isoformat(),
                        "generated_by": username or "系统"
                    }
                    for r, username in reports
                ]
            }
