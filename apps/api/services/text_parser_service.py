"""
规格表文本解析服务

支持从粘贴的表格文本中提取装备规格信息
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from apps.api.schemas.equipment_batch import (
    EquipmentCategory,
    TextParseResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class HeaderMapping:
    """表头映射配置"""
    patterns: List[str]  # 正则模式列表
    field: str  # 目标字段名


class TextParserService:
    """规格表文本解析服务"""

    def __init__(self):
        # 鱼竿表头映射
        self.rod_header_mappings = [
            HeaderMapping(['型号', 'model', '规格'], 'model'),
            HeaderMapping(['长度', 'length', '尺寸', '全长'], 'length'),
            HeaderMapping(['调性', 'power', '硬度'], 'power'),
            HeaderMapping(['动作', 'action'], 'action'),
            HeaderMapping(['自重', 'weight', '重量', '净重'], 'weight'),
            HeaderMapping(['饵重', 'lure.*weight', '拟饵重量', '适用饵重'], 'lure_weight'),
            HeaderMapping(['线重', 'line.*weight', '适用线号'], 'line_weight'),
            HeaderMapping(['收缩', 'closed', '收纳长度'], 'closed_length'),
            HeaderMapping(['节数', 'sections', '段数'], 'sections'),
            HeaderMapping(['价格', 'price', '售价'], 'price'),
        ]

        # 渔轮表头映射
        self.reel_header_mappings = [
            HeaderMapping(['型号', 'model', '规格', '型号'], 'model'),
            HeaderMapping(['速比', 'gear.*ratio', '传动比'], 'gear_ratio'),
            HeaderMapping(['轴承', 'bearing', 'bb'], 'bearings'),
            HeaderMapping(['拽力', 'drag', '刹车力'], 'max_drag'),
            HeaderMapping(['线容量', 'line.*capacity', '容线量'], 'line_capacity'),
            HeaderMapping(['自重', 'weight', '重量'], 'weight'),
            HeaderMapping(['价格', 'price', '售价'], 'price'),
        ]

        # 鱼线表头映射
        self.line_header_mappings = [
            HeaderMapping(['型号', 'model', '规格', '号数'], 'model'),
            HeaderMapping(['线径', 'diameter'], 'diameter'),
            HeaderMapping(['拉力', 'strength', '强度', '磅数'], 'breaking_strength'),
            HeaderMapping(['长度', 'length', '米数'], 'length'),
            HeaderMapping(['pe号', 'pe'], 'pe_number'),
            HeaderMapping(['价格', 'price', '售价'], 'price'),
        ]

        # 拟饵表头映射
        self.lure_header_mappings = [
            HeaderMapping(['型号', 'model', '色号', '颜色'], 'model'),
            HeaderMapping(['重量', 'weight', '克重'], 'weight'),
            HeaderMapping(['长度', 'length', '尺寸'], 'length'),
            HeaderMapping(['潜深', 'depth', '泳层'], 'diving_depth'),
            HeaderMapping(['颜色', 'color'], 'color'),
            HeaderMapping(['价格', 'price', '售价'], 'price'),
        ]

        # 分隔符优先级
        self.delimiters = [
            '\t',      # Tab
            '|',       # 竖线
            ',',       # 逗号
            '  ',      # 双空格
        ]

    def parse(
        self,
        text: str,
        category: EquipmentCategory,
        delimiter: Optional[str] = None
    ) -> TextParseResponse:
        """
        解析规格表文本

        Args:
            text: 规格表文本
            category: 装备类别
            delimiter: 分隔符（可选，自动检测）

        Returns:
            TextParseResponse: 解析结果
        """
        warnings = []
        variants = []
        template = {}

        try:
            # 1. 预处理文本
            lines = self._preprocess_text(text)
            if len(lines) < 2:
                return TextParseResponse(
                    success=False,
                    warnings=["文本行数不足，至少需要表头和一行数据"]
                )

            # 2. 检测分隔符
            if delimiter is None:
                delimiter = self._detect_delimiter(lines[0])
                if delimiter is None:
                    return TextParseResponse(
                        success=False,
                        warnings=["无法检测到有效的分隔符"]
                    )

            # 3. 解析表头
            header_row = lines[0]
            raw_headers = self._split_line(header_row, delimiter)

            # 4. 映射表头到字段
            header_mappings = self._get_header_mappings(category)
            field_indices = self._map_headers(raw_headers, header_mappings)

            if not field_indices:
                return TextParseResponse(
                    success=False,
                    warnings=["无法识别任何表头字段"],
                    raw_headers=raw_headers
                )

            # 检查必填字段
            if 'model' not in field_indices:
                warnings.append("警告: 未识别到型号列，将使用第一列作为型号")
                field_indices['model'] = 0

            # 5. 解析数据行
            for i, line in enumerate(lines[1:], start=2):
                if not line.strip():
                    continue

                values = self._split_line(line, delimiter)
                variant = self._parse_row(values, field_indices, category)

                if variant:
                    variants.append(variant)
                else:
                    warnings.append(f"第{i}行解析失败: {line[:50]}...")

            if not variants:
                return TextParseResponse(
                    success=False,
                    warnings=["未解析出任何有效数据行"],
                    raw_headers=raw_headers
                )

            # 6. 提取可能的模板信息
            template = self._extract_template_hints(text, category)
            if not template.get('brand_name'):
                warnings.append("未能识别品牌信息，请手动选择")
            if not template.get('product_line'):
                warnings.append("未能识别产品线信息，请手动填写")

            return TextParseResponse(
                success=True,
                template=template,
                variants=variants,
                warnings=warnings,
                raw_headers=raw_headers,
                row_count=len(variants)
            )

        except Exception as e:
            logger.error(f"解析文本失败: {e}", exc_info=True)
            return TextParseResponse(
                success=False,
                warnings=[f"解析失败: {str(e)}"]
            )

    def _preprocess_text(self, text: str) -> List[str]:
        """预处理文本，移除空行和清理格式"""
        lines = []
        for line in text.strip().split('\n'):
            # 移除 Markdown 表格分隔行
            if re.match(r'^[\s|:-]+$', line):
                continue
            line = line.strip()
            if line:
                lines.append(line)
        return lines

    def _detect_delimiter(self, line: str) -> Optional[str]:
        """检测分隔符"""
        # 优先检测 Tab
        if '\t' in line:
            return '\t'

        # 检测竖线
        if '|' in line:
            return '|'

        # 检测逗号
        if ',' in line and line.count(',') >= 2:
            return ','

        # 检测多个空格
        if '  ' in line:
            return '  '

        # 尝试单空格
        if ' ' in line and line.count(' ') >= 3:
            return ' '

        return None

    def _split_line(self, line: str, delimiter: str) -> List[str]:
        """按分隔符拆分行"""
        parts = line.split(delimiter)
        # 清理每个部分
        return [p.strip().strip('|').strip() for p in parts if p.strip()]

    def _get_header_mappings(
        self,
        category: EquipmentCategory
    ) -> List[HeaderMapping]:
        """获取类别对应的表头映射"""
        if category == EquipmentCategory.ROD:
            return self.rod_header_mappings
        elif category == EquipmentCategory.REEL:
            return self.reel_header_mappings
        elif category == EquipmentCategory.LINE:
            return self.line_header_mappings
        elif category == EquipmentCategory.LURE:
            return self.lure_header_mappings
        return []

    def _map_headers(
        self,
        headers: List[str],
        mappings: List[HeaderMapping]
    ) -> Dict[str, int]:
        """映射表头到字段索引"""
        field_indices = {}

        for i, header in enumerate(headers):
            header_lower = header.lower()

            for mapping in mappings:
                for pattern in mapping.patterns:
                    if re.search(pattern, header_lower, re.IGNORECASE):
                        if mapping.field not in field_indices:
                            field_indices[mapping.field] = i
                        break

        return field_indices

    def _parse_row(
        self,
        values: List[str],
        field_indices: Dict[str, int],
        category: EquipmentCategory
    ) -> Optional[Dict[str, Any]]:
        """解析单行数据"""
        if not values:
            return None

        variant = {}

        for field, index in field_indices.items():
            if index < len(values):
                raw_value = values[index]
                parsed_value = self._parse_value(field, raw_value, category)
                if parsed_value is not None:
                    variant[field] = parsed_value

        # 必须有型号
        if 'model' not in variant or not variant['model']:
            return None

        return variant

    def _parse_value(
        self,
        field: str,
        raw_value: str,
        category: EquipmentCategory
    ) -> Any:
        """解析字段值"""
        if not raw_value or raw_value == '-':
            return None

        # 数值字段
        if field in ['length', 'weight', 'diameter', 'breaking_strength',
                     'max_drag', 'lure_weight_min', 'lure_weight_max']:
            return self._extract_number(raw_value)

        # 整数字段
        if field in ['bearings', 'sections']:
            num = self._extract_number(raw_value)
            return int(num) if num else None

        # 范围字段
        if field == 'lure_weight':
            return self._parse_weight_range(raw_value)

        if field == 'line_weight':
            return self._parse_weight_range(raw_value)

        # 调性字段
        if field == 'power':
            return self._normalize_power(raw_value)

        # 动作字段
        if field == 'action':
            return self._normalize_action(raw_value)

        # 默认返回原值
        return raw_value.strip()

    def _extract_number(self, text: str) -> Optional[float]:
        """从文本中提取数字"""
        # 移除单位
        cleaned = re.sub(r'[a-zA-Z米m克g磅lb千克kg厘米cm毫米mm]', '', text)
        # 提取数字
        match = re.search(r'[\d.]+', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    def _parse_weight_range(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """解析重量范围，如 '7-21g' -> (7.0, 21.0)"""
        # 匹配范围格式
        match = re.search(r'([\d.]+)\s*[-~]\s*([\d.]+)', text)
        if match:
            try:
                return float(match.group(1)), float(match.group(2))
            except ValueError:
                pass
        return None, None

    def _normalize_power(self, value: str) -> Optional[str]:
        """标准化调性值"""
        value = value.upper().strip()
        valid_powers = ['UL', 'L', 'ML', 'M', 'MH', 'H', 'XH']
        if value in valid_powers:
            return value

        # 尝试从型号中提取
        for power in valid_powers:
            if power in value:
                return power

        return None

    def _normalize_action(self, value: str) -> Optional[str]:
        """标准化动作值"""
        value = value.lower().strip()
        if 'fast' in value or '快' in value:
            return 'Fast'
        if 'medium' in value or 'moderate' in value or '中' in value:
            return 'Medium'
        if 'slow' in value or '慢' in value:
            return 'Slow'
        return None

    def _extract_template_hints(
        self,
        text: str,
        category: EquipmentCategory
    ) -> Dict[str, Any]:
        """从文本中提取模板提示信息"""
        template = {}

        # 尝试识别常见品牌
        brands = [
            '达瓦', 'DAIWA', '禧玛诺', 'SHIMANO', '阿布', 'ABU',
            '伽玛卡兹', 'GAMAKATSU', '一味', 'MEGABASS',
            'JACKALL', 'EVERGREEN', 'DEPS', 'O.S.P'
        ]
        for brand in brands:
            if brand.upper() in text.upper():
                template['brand_name'] = brand
                break

        # 尝试识别产品线（通常是大写字母组合）
        product_line_match = re.search(
            r'\b([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)?(?:\s+\d+)?)\b',
            text
        )
        if product_line_match:
            template['product_line'] = product_line_match.group(1)

        return template


# 单例服务实例
text_parser_service = TextParserService()
