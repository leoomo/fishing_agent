"""
LangChain Learning - Math Tool

数学工具模块提供基本和高级数学计算功能。
"""

import math
import random
import statistics
from typing import Optional, Any, Dict, Union, List
import logging
from core.base_tool import BaseTool, ConfigurableTool
from core.interfaces import ToolMetadata, ToolResult


class MathTool(ConfigurableTool):
    """数学工具类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._precision = self.get_config_value("precision", 10)

    @property
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        return ToolMetadata(
            name="math_tool",
            description="提供数学计算和统计功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["math", "calculation", "statistics"],
            dependencies=[]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        operation = kwargs.get("operation")
        return operation in [
            "add", "subtract", "multiply", "divide", "power", "sqrt",
            "sin", "cos", "tan", "log", "factorial", "average",
            "median", "mode", "std_dev", "random", "round"
        ]

    async def _execute(self, **kwargs) -> ToolResult:
        """执行数学操作"""
        operation = kwargs.get("operation")

        try:
            if operation == "add":
                return await self._add(**kwargs)
            elif operation == "subtract":
                return await self._subtract(**kwargs)
            elif operation == "multiply":
                return await self._multiply(**kwargs)
            elif operation == "divide":
                return await self._divide(**kwargs)
            elif operation == "power":
                return await self._power(**kwargs)
            elif operation == "sqrt":
                return await self._sqrt(**kwargs)
            elif operation == "sin":
                return await self._sin(**kwargs)
            elif operation == "cos":
                return await self._cos(**kwargs)
            elif operation == "tan":
                return await self._tan(**kwargs)
            elif operation == "log":
                return await self._log(**kwargs)
            elif operation == "factorial":
                return await self._factorial(**kwargs)
            elif operation == "average":
                return await self._average(**kwargs)
            elif operation == "median":
                return await self._median(**kwargs)
            elif operation == "mode":
                return await self._mode(**kwargs)
            elif operation == "std_dev":
                return await self._std_dev(**kwargs)
            elif operation == "random":
                return await self._random(**kwargs)
            elif operation == "round":
                return await self._round(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {operation}"
                )

        except Exception as e:
            self._logger.error(f"数学工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"数学工具执行失败: {str(e)}"
            )

    async def _add(self, a: Union[int, float], b: Union[int, float], **kwargs) -> ToolResult:
        """加法"""
        try:
            result = a + b
            return ToolResult(
                success=True,
                data={
                    "operation": "add",
                    "operands": [a, b],
                    "result": result,
                    "formatted": f"{a} + {b} = {result}"
                },
                metadata={"operation": "add"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"加法计算失败: {str(e)}"
            )

    async def _subtract(self, a: Union[int, float], b: Union[int, float], **kwargs) -> ToolResult:
        """减法"""
        try:
            result = a - b
            return ToolResult(
                success=True,
                data={
                    "operation": "subtract",
                    "operands": [a, b],
                    "result": result,
                    "formatted": f"{a} - {b} = {result}"
                },
                metadata={"operation": "subtract"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"减法计算失败: {str(e)}"
            )

    async def _multiply(self, a: Union[int, float], b: Union[int, float], **kwargs) -> ToolResult:
        """乘法"""
        try:
            result = a * b
            return ToolResult(
                success=True,
                data={
                    "operation": "multiply",
                    "operands": [a, b],
                    "result": result,
                    "formatted": f"{a} × {b} = {result}"
                },
                metadata={"operation": "multiply"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"乘法计算失败: {str(e)}"
            )

    async def _divide(self, a: Union[int, float], b: Union[int, float], **kwargs) -> ToolResult:
        """除法"""
        try:
            if b == 0:
                return ToolResult(
                    success=False,
                    error="除数不能为零"
                )

            result = a / b
            return ToolResult(
                success=True,
                data={
                    "operation": "divide",
                    "operands": [a, b],
                    "result": result,
                    "formatted": f"{a} ÷ {b} = {result}"
                },
                metadata={"operation": "divide"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"除法计算失败: {str(e)}"
            )

    async def _power(self, base: Union[int, float], exponent: Union[int, float], **kwargs) -> ToolResult:
        """幂运算"""
        try:
            result = base ** exponent
            return ToolResult(
                success=True,
                data={
                    "operation": "power",
                    "base": base,
                    "exponent": exponent,
                    "result": result,
                    "formatted": f"{base}^{exponent} = {result}"
                },
                metadata={"operation": "power"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"幂运算失败: {str(e)}"
            )

    async def _sqrt(self, number: Union[int, float], **kwargs) -> ToolResult:
        """平方根"""
        try:
            if number < 0:
                return ToolResult(
                    success=False,
                    error="不能计算负数的平方根"
                )

            result = math.sqrt(number)
            return ToolResult(
                success=True,
                data={
                    "operation": "sqrt",
                    "number": number,
                    "result": result,
                    "formatted": f"√{number} = {result}"
                },
                metadata={"operation": "sqrt"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"平方根计算失败: {str(e)}"
            )

    async def _sin(self, angle: Union[int, float], degrees: bool = True, **kwargs) -> ToolResult:
        """正弦函数"""
        try:
            if degrees:
                angle_rad = math.radians(angle)
            else:
                angle_rad = angle

            result = math.sin(angle_rad)
            return ToolResult(
                success=True,
                data={
                    "operation": "sin",
                    "angle": angle,
                    "degrees": degrees,
                    "result": result,
                    "formatted": f"sin({angle}°) = {result}" if degrees else f"sin({angle}) = {result}"
                },
                metadata={"operation": "sin"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"正弦计算失败: {str(e)}"
            )

    async def _cos(self, angle: Union[int, float], degrees: bool = True, **kwargs) -> ToolResult:
        """余弦函数"""
        try:
            if degrees:
                angle_rad = math.radians(angle)
            else:
                angle_rad = angle

            result = math.cos(angle_rad)
            return ToolResult(
                success=True,
                data={
                    "operation": "cos",
                    "angle": angle,
                    "degrees": degrees,
                    "result": result,
                    "formatted": f"cos({angle}°) = {result}" if degrees else f"cos({angle}) = {result}"
                },
                metadata={"operation": "cos"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"余弦计算失败: {str(e)}"
            )

    async def _tan(self, angle: Union[int, float], degrees: bool = True, **kwargs) -> ToolResult:
        """正切函数"""
        try:
            if degrees:
                angle_rad = math.radians(angle)
            else:
                angle_rad = angle

            result = math.tan(angle_rad)
            return ToolResult(
                success=True,
                data={
                    "operation": "tan",
                    "angle": angle,
                    "degrees": degrees,
                    "result": result,
                    "formatted": f"tan({angle}°) = {result}" if degrees else f"tan({angle}) = {result}"
                },
                metadata={"operation": "tan"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"正切计算失败: {str(e)}"
            )

    async def _log(self, number: Union[int, float], base: Union[int, float] = 10, **kwargs) -> ToolResult:
        """对数函数"""
        try:
            if number <= 0:
                return ToolResult(
                    success=False,
                    error="对数的真数必须大于零"
                )
            if base <= 0 or base == 1:
                return ToolResult(
                    success=False,
                    error="对数的底数必须大于零且不等于1"
                )

            result = math.log(number, base)
            return ToolResult(
                success=True,
                data={
                    "operation": "log",
                    "number": number,
                    "base": base,
                    "result": result,
                    "formatted": f"log_{base}({number}) = {result}"
                },
                metadata={"operation": "log"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"对数计算失败: {str(e)}"
            )

    async def _factorial(self, n: int, **kwargs) -> ToolResult:
        """阶乘"""
        try:
            if n < 0:
                return ToolResult(
                    success=False,
                    error="不能计算负数的阶乘"
                )

            result = math.factorial(n)
            return ToolResult(
                success=True,
                data={
                    "operation": "factorial",
                    "n": n,
                    "result": result,
                    "formatted": f"{n}! = {result}"
                },
                metadata={"operation": "factorial"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"阶乘计算失败: {str(e)}"
            )

    async def _average(self, numbers: List[Union[int, float]], **kwargs) -> ToolResult:
        """平均值"""
        try:
            if not numbers:
                return ToolResult(
                    success=False,
                    error="数字列表不能为空"
                )

            result = statistics.mean(numbers)
            return ToolResult(
                success=True,
                data={
                    "operation": "average",
                    "numbers": numbers,
                    "count": len(numbers),
                    "result": result,
                    "formatted": f"平均值 {numbers} = {result}"
                },
                metadata={"operation": "average"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"平均值计算失败: {str(e)}"
            )

    async def _median(self, numbers: List[Union[int, float]], **kwargs) -> ToolResult:
        """中位数"""
        try:
            if not numbers:
                return ToolResult(
                    success=False,
                    error="数字列表不能为空"
                )

            result = statistics.median(numbers)
            return ToolResult(
                success=True,
                data={
                    "operation": "median",
                    "numbers": numbers,
                    "count": len(numbers),
                    "result": result,
                    "formatted": f"中位数 {numbers} = {result}"
                },
                metadata={"operation": "median"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"中位数计算失败: {str(e)}"
            )

    async def _mode(self, numbers: List[Union[int, float]], **kwargs) -> ToolResult:
        """众数"""
        try:
            if not numbers:
                return ToolResult(
                    success=False,
                    error="数字列表不能为空"
                )

            result = statistics.mode(numbers)
            return ToolResult(
                success=True,
                data={
                    "operation": "mode",
                    "numbers": numbers,
                    "count": len(numbers),
                    "result": result,
                    "formatted": f"众数 {numbers} = {result}"
                },
                metadata={"operation": "mode"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"众数计算失败: {str(e)}"
            )

    async def _std_dev(self, numbers: List[Union[int, float]], **kwargs) -> ToolResult:
        """标准差"""
        try:
            if not numbers:
                return ToolResult(
                    success=False,
                    error="数字列表不能为空"
                )

            if len(numbers) < 2:
                return ToolResult(
                    success=False,
                    error="计算标准差至少需要2个数字"
                )

            result = statistics.stdev(numbers)
            return ToolResult(
                success=True,
                data={
                    "operation": "std_dev",
                    "numbers": numbers,
                    "count": len(numbers),
                    "result": result,
                    "formatted": f"标准差 {numbers} = {result}"
                },
                metadata={"operation": "std_dev"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"标准差计算失败: {str(e)}"
            )

    async def _random(self, min_val: Union[int, float] = 0, max_val: Union[int, float] = 100,
                     integer: bool = True, **kwargs) -> ToolResult:
        """随机数生成"""
        try:
            if integer:
                result = random.randint(int(min_val), int(max_val))
            else:
                result = random.uniform(min_val, max_val)

            return ToolResult(
                success=True,
                data={
                    "operation": "random",
                    "min_val": min_val,
                    "max_val": max_val,
                    "integer": integer,
                    "result": result,
                    "formatted": f"随机数 [{min_val}, {max_val}] = {result}"
                },
                metadata={"operation": "random"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"随机数生成失败: {str(e)}"
            )

    async def _round(self, number: Union[int, float], decimals: int = 0, **kwargs) -> ToolResult:
        """四舍五入"""
        try:
            result = round(number, decimals)
            return ToolResult(
                success=True,
                data={
                    "operation": "round",
                    "number": number,
                    "decimals": decimals,
                    "result": result,
                    "formatted": f"round({number}, {decimals}) = {result}"
                },
                metadata={"operation": "round"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"四舍五入失败: {str(e)}"
            )

    def _validate_required_params(self, required_params: list, **kwargs) -> bool:
        """验证必需参数"""
        for param in required_params:
            if param not in kwargs or kwargs[param] is None:
                self._logger.error(f"缺少必需参数: {param}")
                return False
        return True