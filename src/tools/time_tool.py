"""
LangChain Learning - Time Tool

时间工具模块提供时间查询、计算和格式化功能。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict, Union
import logging
import pytz
from core.base_tool import BaseTool, ConfigurableTool
from core.interfaces import ToolMetadata, ToolResult


class TimeTool(ConfigurableTool):
    """时间工具类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._default_timezone = self.get_config_value("default_timezone", "Asia/Shanghai")

    @property
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        return ToolMetadata(
            name="time_tool",
            description="提供时间查询和计算功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["time", "datetime", "utility"],
            dependencies=[]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        operation = kwargs.get("operation")
        return operation in [
            "current_time", "add_time", "subtract_time", 
            "format_time", "convert_timezone", "get_timezone"
        ]

    async def _execute(self, **kwargs) -> ToolResult:
        """执行时间操作"""
        operation = kwargs.get("operation")

        try:
            if operation == "current_time":
                return await self._get_current_time(**kwargs)
            elif operation == "add_time":
                return await self._add_time(**kwargs)
            elif operation == "subtract_time":
                return await self._subtract_time(**kwargs)
            elif operation == "format_time":
                return await self._format_time(**kwargs)
            elif operation == "convert_timezone":
                return await self._convert_timezone(**kwargs)
            elif operation == "get_timezone":
                return await self._get_timezone(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {operation}"
                )

        except Exception as e:
            self._logger.error(f"时间工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"时间工具执行失败: {str(e)}"
            )

    async def _get_current_time(self, timezone_name: Optional[str] = None, **kwargs) -> ToolResult:
        """获取当前时间"""
        try:
            tz = self._get_timezone_safe(timezone_name or self._default_timezone)
            now = datetime.now(tz)
            
            # 格式化时间信息
            formatted_time = {
                "timestamp": now.isoformat(),
                "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "weekday": now.strftime("%A"),
                "timezone": timezone_name or self._default_timezone,
                "unix_timestamp": now.timestamp(),
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second
            }

            return ToolResult(
                success=True,
                data=formatted_time,
                metadata={"operation": "current_time", "timezone": tz.zone}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取当前时间失败: {str(e)}"
            )

    async def _add_time(self, base_time: str, years: int = 0, months: int = 0, days: int = 0,
                    hours: int = 0, minutes: int = 0, seconds: int = 0, **kwargs) -> ToolResult:
        """时间加法"""
        try:
            # 解析基础时间
            if isinstance(base_time, str):
                base_dt = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
            else:
                return ToolResult(
                    success=False,
                    error="base_time 必须是字符串格式的时间"
                )

            # 处理年和月（需要特殊处理，因为timedelta不支持年和月）
            new_time = base_dt
            if years != 0:
                try:
                    new_time = new_time.replace(year=new_time.year + years)
                except ValueError:
                    # 处理闰年等边界情况
                    return ToolResult(
                        success=False,
                        error=f"无法添加 {years} 年，可能涉及闰年等边界情况"
                    )

            if months != 0:
                # 计算新的月份
                new_month = new_time.month + months
                new_year = new_time.year

                # 处理月份溢出
                while new_month > 12:
                    new_month -= 12
                    new_year += 1
                while new_month < 1:
                    new_month += 12
                    new_year -= 1

                try:
                    new_time = new_time.replace(year=new_year, month=new_month)
                except ValueError:
                    # 处理不同月份天数差异（如2月30日）
                    # 获取目标月份的最后一天
                    import calendar
                    last_day = calendar.monthrange(new_year, new_month)[1]
                    new_time = new_time.replace(year=new_year, month=new_month, day=min(new_time.day, last_day))

            # 创建时间增量（只处理天、小时、分钟、秒）
            delta = timedelta(
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )

            # 计算新时间
            new_time = new_time + delta
            
            result = {
                "original_time": base_time,
                "added_time": {
                    "years": years,
                    "months": months,
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds
                },
                "new_time": new_time.isoformat(),
                "formatted": new_time.strftime("%Y-%m-%d %H:%M:%S")
            }

            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "add_time", "delta_days": delta.days}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"时间加法计算失败: {str(e)}"
            )

    async def _subtract_time(self, base_time: str, years: int = 0, months: int = 0, days: int = 0,
                           hours: int = 0, minutes: int = 0, seconds: int = 0, **kwargs) -> ToolResult:
        """时间减法"""
        try:
            # 解析基础时间
            if isinstance(base_time, str):
                base_dt = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
            else:
                return ToolResult(
                    success=False,
                    error="base_time 必须是字符串格式的时间"
                )

            # 处理年和月（需要特殊处理，因为timedelta不支持年和月）
            new_time = base_dt
            if years != 0:
                try:
                    new_time = new_time.replace(year=new_time.year - years)
                except ValueError:
                    # 处理闰年等边界情况
                    return ToolResult(
                        success=False,
                        error=f"无法减去 {years} 年，可能涉及闰年等边界情况"
                    )

            if months != 0:
                # 计算新的月份
                new_month = new_time.month - months
                new_year = new_time.year

                # 处理月份溢出
                while new_month > 12:
                    new_month -= 12
                    new_year += 1
                while new_month < 1:
                    new_month += 12
                    new_year -= 1

                try:
                    new_time = new_time.replace(year=new_year, month=new_month)
                except ValueError:
                    # 处理不同月份天数差异（如2月30日）
                    # 获取目标月份的最后一天
                    import calendar
                    last_day = calendar.monthrange(new_year, new_month)[1]
                    new_time = new_time.replace(year=new_year, month=new_month, day=min(new_time.day, last_day))

            # 创建时间增量（只处理天、小时、分钟、秒）
            delta = timedelta(
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )

            # 计算新时间
            new_time = new_time - delta
            
            result = {
                "original_time": base_time,
                "subtracted_time": {
                    "years": years,
                    "months": months,
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds
                },
                "new_time": new_time.isoformat(),
                "formatted": new_time.strftime("%Y-%m-%d %H:%M:%S")
            }

            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "subtract_time", "delta_days": delta.days}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"时间减法计算失败: {str(e)}"
            )

    async def _format_time(self, time_input: str, format_type: str = "default", 
                       timezone_name: Optional[str] = None, **kwargs) -> ToolResult:
        """格式化时间"""
        try:
            # 解析时间输入
            if isinstance(time_input, str):
                dt = datetime.fromisoformat(time_input.replace('Z', '+00:00'))
            else:
                return ToolResult(
                    success=False,
                    error="time_input 必须是字符串格式的时间"
                )

            # 应用时区
            if timezone_name:
                tz = self._get_timezone_safe(timezone_name)
                if hasattr(dt, 'astimezone'):
                    dt = dt.astimezone(tz)
                else:
                    dt = dt.replace(tzinfo=tz)

            # 格式化时间
            formats = {
                "default": "%Y-%m-%d %H:%M:%S",
                "date": "%Y-%m-%d",
                "time": "%H:%M:%S",
                "iso": "%Y-%m-%dT%H:%M:%S",
                "us": "%Y-%m-%d %I:%M:%S %p",
                "full": "%Y年%m月%d日 %H时%M分%S秒",
                "compact": "%Y%m%d%H%M%S"
            }

            format_str = formats.get(format_type, formats["default"])
            formatted_time = dt.strftime(format_str)

            result = {
                "original": time_input,
                "formatted": formatted_time,
                "format_type": format_type,
                "timezone": timezone_name or dt.tzname() if dt.tzinfo else None,
                "timestamp": dt.timestamp()
            }

            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "format_time", "format": format_type}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"时间格式化失败: {str(e)}"
            )

    async def _convert_timezone(self, time_input: str, from_tz: str, to_tz: str, **kwargs) -> ToolResult:
        """时区转换"""
        try:
            # 解析时间输入
            if isinstance(time_input, str):
                dt = datetime.fromisoformat(time_input.replace('Z', '+00:00'))
            else:
                return ToolResult(
                    success=False,
                    error="time_input 必须是字符串格式的时间"
                )

            # 获取时区
            from_tz_obj = self._get_timezone_safe(from_tz)
            to_tz_obj = self._get_timezone_safe(to_tz)

            # 设置源时区
            if hasattr(dt, 'astimezone'):
                dt = dt.astimezone(from_tz_obj)
            else:
                dt = dt.replace(tzinfo=from_tz_obj)

            # 转换时区
            converted_dt = dt.astimezone(to_tz_obj)

            result = {
                "original_time": time_input,
                "original_timezone": from_tz,
                "target_timezone": to_tz,
                "converted_time": converted_dt.isoformat(),
                "formatted": converted_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "offset_hours": converted_dt.utcoffset() // 3600
            }

            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": "convert_timezone", "offset": converted_dt.utcoffset()}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"时区转换失败: {str(e)}"
            )

    def _get_timezone(self, timezone_name: str) -> Any:
        """获取时区对象"""
        try:
            return pytz.timezone(timezone_name)
        except pytz.UnknownTimeZoneError:
            self._logger.warning(f"未知时区: {timezone_name}，使用默认时区")
            return pytz.timezone(self._default_timezone)

    def _get_timezone_safe(self, timezone_name: Optional[str]) -> Any:
        """获取时区对象（兼容方法）"""
        if not timezone_name:
            return pytz.timezone(self._default_timezone)
        return self._get_timezone(timezone_name)

    def _validate_required_params(self, required_params: list, **kwargs) -> bool:
        """验证必需参数"""
        for param in required_params:
            if param not in kwargs or kwargs[param] is None:
                self._logger.error(f"缺少必需参数: {param}")
                return False
        return True