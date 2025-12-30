"""
Excel 导入服务

将 Excel/CSV 文件导入到待审核队列（pending_equipment 表）
"""

import json
import logging
from io import BytesIO
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, BinaryIO

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from apps.api.orm.session import get_db_session
from packages.agents.equipment_import.models.pending import PendingEquipment

logger = logging.getLogger(__name__)


# 装备类型映射
EQUIPMENT_TYPE_MAP = {
    "rod": "鱼竿",
    "reel": "渔轮",
    "line": "鱼线",
    "lure": "拟饵",
    "鱼竿": "鱼竿",
    "渔轮": "渔轮",
    "鱼线": "鱼线",
    "拟饵": "拟饵",
}

# 通用字段定义（所有装备类型共有）
COMMON_FIELDS = [
    {"name": "brand_name", "label": "品牌名称", "required": True, "description": "例如: 达亿瓦, 禧玛诺"},
    {"name": "name", "label": "产品名称", "required": True, "description": "例如: 黑纹鲤 C3000"},
    {"name": "model", "label": "型号", "required": False, "description": "例如: C3000MHG"},
    {"name": "price_min", "label": "最低价格", "required": False, "description": "数字，单位：元"},
    {"name": "price_max", "label": "最高价格", "required": False, "description": "数字，单位：元"},
    {"name": "description", "label": "产品描述", "required": False, "description": "详细描述文本"},
    {"name": "features", "label": "特点", "required": False, "description": "多个特点用逗号分隔"},
    {"name": "target_fish", "label": "目标鱼种", "required": False, "description": "多个鱼种用逗号分隔"},
    {"name": "user_level", "label": "适合人群", "required": False, "description": "新手/进阶/高手"},
]

# 各装备类型的规格字段定义
SPEC_FIELDS = {
    "鱼竿": [
        {"name": "length", "label": "长度", "description": "例如: 2.1m, 7ft"},
        {"name": "power", "label": "调性", "description": "例如: UL, L, ML, M, MH, H, XH"},
        {"name": "action", "label": "动作", "description": "例如: F(快), MF(中快), M(中), S(慢)"},
        {"name": "sections", "label": "节数", "description": "例如: 2"},
        {"name": "weight", "label": "自重", "description": "例如: 125g"},
        {"name": "lure_weight_min", "label": "饵重下限", "description": "例如: 5g"},
        {"name": "lure_weight_max", "label": "饵重上限", "description": "例如: 21g"},
        {"name": "line_weight_min", "label": "线负荷下限", "description": "例如: 6lb"},
        {"name": "line_weight_max", "label": "线负荷上限", "description": "例如: 12lb"},
    ],
    "渔轮": [
        {"name": "reel_type", "label": "轮型", "description": "纺车轮/水滴轮/鼓轮"},
        {"name": "gear_ratio", "label": "齿比", "description": "例如: 6.2:1"},
        {"name": "bearings", "label": "轴承数", "description": "例如: 7+1"},
        {"name": "weight", "label": "自重", "description": "例如: 200g"},
        {"name": "max_drag", "label": "最大刹车力", "description": "例如: 5kg"},
        {"name": "line_capacity", "label": "线容量", "description": "例如: PE2-200m"},
        {"name": "retrieve_per_turn", "label": "摇把一圈收线", "description": "例如: 87cm"},
    ],
    "鱼线": [
        {"name": "line_type", "label": "线型", "description": "PE线/碳线/尼龙线"},
        {"name": "diameter", "label": "线径", "description": "例如: 0.12mm"},
        {"name": "strength_lb", "label": "强度(lb)", "description": "例如: 12"},
        {"name": "length_m", "label": "长度(m)", "description": "例如: 150"},
        {"name": "color", "label": "颜色", "description": "例如: 绿色"},
        {"name": "strands", "label": "编数", "description": "例如: 8编"},
    ],
    "拟饵": [
        {"name": "lure_type", "label": "饵型", "description": "米诺/VIB/铅笔/波趴/软饵等"},
        {"name": "length", "label": "长度", "description": "例如: 85mm"},
        {"name": "weight", "label": "重量", "description": "例如: 12g"},
        {"name": "diving_depth_min", "label": "潜深下限", "description": "例如: 0.5m"},
        {"name": "diving_depth_max", "label": "潜深上限", "description": "例如: 1.5m"},
        {"name": "color", "label": "颜色", "description": "例如: 银白"},
        {"name": "action_type", "label": "泳姿", "description": "例如: S形, 摆动"},
    ],
}


@dataclass
class ValidationError:
    """验证错误"""
    row: int
    field: str
    message: str


@dataclass
class ImportPreviewRow:
    """导入预览行"""
    row_number: int
    data: Dict[str, Any]
    is_valid: bool
    errors: List[str]


@dataclass
class ImportResult:
    """导入结果"""
    success: bool
    message: str
    total_rows: int
    imported_count: int
    failed_count: int
    pending_ids: List[int]
    errors: List[Dict[str, Any]]


class ExcelImportService:
    """Excel 导入服务"""

    def __init__(self):
        pass

    def generate_template(self, equipment_type: str) -> bytes:
        """
        生成指定装备类型的导入模板

        Args:
            equipment_type: 装备类型 (rod/reel/line/lure)

        Returns:
            Excel 文件的字节数据
        """
        type_cn = EQUIPMENT_TYPE_MAP.get(equipment_type)
        if not type_cn:
            raise ValueError(f"不支持的装备类型: {equipment_type}")

        wb = Workbook()
        ws = wb.active
        ws.title = f"{type_cn}导入模板"

        # 样式定义
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        required_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        desc_font = Font(italic=True, color="808080")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 构建字段列表
        all_fields = COMMON_FIELDS.copy()
        spec_fields = SPEC_FIELDS.get(type_cn, [])
        for field in spec_fields:
            all_fields.append({
                "name": f"spec_{field['name']}",
                "label": field["label"],
                "required": False,
                "description": field.get("description", "")
            })

        # 第1行: 字段标签（表头）
        for col, field in enumerate(all_fields, 1):
            cell = ws.cell(row=1, column=col, value=field["label"])
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = border
            # 设置列宽
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max(15, len(field["label"]) * 2 + 5)

        # 第2行: 字段说明
        for col, field in enumerate(all_fields, 1):
            desc = field.get("description", "")
            if field.get("required"):
                desc = f"[必填] {desc}"
            cell = ws.cell(row=2, column=col, value=desc)
            cell.font = desc_font
            if field.get("required"):
                cell.fill = required_fill
            cell.border = border

        # 第3行: 字段名（用于解析）
        for col, field in enumerate(all_fields, 1):
            cell = ws.cell(row=3, column=col, value=field["name"])
            cell.font = Font(color="808080", size=9)
            cell.border = border

        # 冻结前3行
        ws.freeze_panes = "A4"

        # 输出到字节流
        output = BytesIO()
        wb.save(output)
        return output.getvalue()

    def parse_excel(self, file_content: bytes, equipment_type: str) -> List[ImportPreviewRow]:
        """
        解析 Excel 文件并返回预览数据

        Args:
            file_content: Excel 文件字节内容
            equipment_type: 装备类型

        Returns:
            预览数据列表
        """
        type_cn = EQUIPMENT_TYPE_MAP.get(equipment_type)
        if not type_cn:
            raise ValueError(f"不支持的装备类型: {equipment_type}")

        wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        ws = wb.active

        # 读取字段名行（第3行）获取字段映射
        field_map = {}
        for col in range(1, ws.max_column + 1):
            field_name = ws.cell(row=3, column=col).value
            if field_name:
                field_map[col] = field_name

        # 如果没有找到字段名行，尝试使用标签行（第1行）
        if not field_map:
            label_to_name = {}
            for field in COMMON_FIELDS:
                label_to_name[field["label"]] = field["name"]
            spec_fields = SPEC_FIELDS.get(type_cn, [])
            for field in spec_fields:
                label_to_name[field["label"]] = f"spec_{field['name']}"

            for col in range(1, ws.max_column + 1):
                label = ws.cell(row=1, column=col).value
                if label and label in label_to_name:
                    field_map[col] = label_to_name[label]

        preview_rows = []
        # 从第4行开始读取数据
        for row_idx in range(4, ws.max_row + 1):
            row_data = {}
            is_empty = True

            for col, field_name in field_map.items():
                value = ws.cell(row=row_idx, column=col).value
                if value is not None and str(value).strip():
                    is_empty = False
                    row_data[field_name] = str(value).strip()

            # 跳过空行
            if is_empty:
                continue

            # 验证行数据
            errors = self._validate_row(row_data, type_cn)

            preview_rows.append(ImportPreviewRow(
                row_number=row_idx,
                data=row_data,
                is_valid=len(errors) == 0,
                errors=errors
            ))

        return preview_rows

    def _validate_row(self, row_data: Dict[str, Any], equipment_type: str) -> List[str]:
        """验证单行数据"""
        errors = []

        # 验证必填字段
        for field in COMMON_FIELDS:
            if field.get("required") and not row_data.get(field["name"]):
                errors.append(f"缺少必填字段: {field['label']}")

        # 验证价格字段
        for price_field in ["price_min", "price_max"]:
            if row_data.get(price_field):
                try:
                    float(row_data[price_field])
                except ValueError:
                    errors.append(f"{price_field} 必须是数字")

        return errors

    def import_to_pending(
        self,
        file_content: bytes,
        equipment_type: str,
        admin_user_id: int
    ) -> ImportResult:
        """
        导入 Excel 到待审核队列

        Args:
            file_content: Excel 文件字节内容
            equipment_type: 装备类型
            admin_user_id: 执行导入的管理员 ID

        Returns:
            导入结果
        """
        type_cn = EQUIPMENT_TYPE_MAP.get(equipment_type)
        if not type_cn:
            return ImportResult(
                success=False,
                message=f"不支持的装备类型: {equipment_type}",
                total_rows=0,
                imported_count=0,
                failed_count=0,
                pending_ids=[],
                errors=[]
            )

        # 解析文件
        try:
            preview_rows = self.parse_excel(file_content, equipment_type)
        except Exception as e:
            logger.error(f"解析 Excel 失败: {e}")
            return ImportResult(
                success=False,
                message=f"解析 Excel 失败: {str(e)}",
                total_rows=0,
                imported_count=0,
                failed_count=0,
                pending_ids=[],
                errors=[]
            )

        if not preview_rows:
            return ImportResult(
                success=False,
                message="Excel 文件中没有找到有效数据",
                total_rows=0,
                imported_count=0,
                failed_count=0,
                pending_ids=[],
                errors=[]
            )

        # 导入到数据库
        pending_ids = []
        errors = []

        with get_db_session() as session:
            for row in preview_rows:
                if not row.is_valid:
                    errors.append({
                        "row": row.row_number,
                        "errors": row.errors,
                        "data": row.data
                    })
                    continue

                try:
                    # 构建 extracted_data 结构
                    extracted_data = self._build_extracted_data(row.data, type_cn)

                    # 创建 PendingEquipment 记录
                    pending = PendingEquipment(
                        status="pending",
                        ocr_status="completed",  # Excel 导入跳过 OCR
                        source_type="excel_import",
                        extracted_data=json.dumps(extracted_data, ensure_ascii=False),
                        confidence=1.0,  # 手工导入默认满置信度
                        equipment_type=type_cn,
                        brand_name=row.data.get("brand_name"),
                        model_name=row.data.get("model"),
                        product_name=row.data.get("name"),
                    )

                    session.add(pending)
                    session.flush()
                    pending_ids.append(pending.id)

                except Exception as e:
                    logger.error(f"导入第 {row.row_number} 行失败: {e}")
                    errors.append({
                        "row": row.row_number,
                        "errors": [str(e)],
                        "data": row.data
                    })

            session.commit()

        imported_count = len(pending_ids)
        failed_count = len(errors)

        logger.info(
            f"管理员 {admin_user_id} 导入 Excel: "
            f"总计 {len(preview_rows)} 行, 成功 {imported_count} 行, 失败 {failed_count} 行"
        )

        return ImportResult(
            success=imported_count > 0,
            message=f"成功导入 {imported_count} 条记录到审核队列",
            total_rows=len(preview_rows),
            imported_count=imported_count,
            failed_count=failed_count,
            pending_ids=pending_ids,
            errors=errors
        )

    def _build_extracted_data(self, row_data: Dict[str, Any], equipment_type: str) -> Dict[str, Any]:
        """构建 ExtractedEquipment 结构的数据"""
        # 解析列表字段
        features = []
        if row_data.get("features"):
            features = [f.strip() for f in row_data["features"].split(",") if f.strip()]

        target_fish = []
        if row_data.get("target_fish"):
            target_fish = [f.strip() for f in row_data["target_fish"].split(",") if f.strip()]

        # 解析规格字段
        specs = {}
        spec_fields = SPEC_FIELDS.get(equipment_type, [])
        for field in spec_fields:
            key = f"spec_{field['name']}"
            if row_data.get(key):
                specs[field["name"]] = row_data[key]

        # 解析价格
        price_min = None
        price_max = None
        if row_data.get("price_min"):
            try:
                price_min = float(row_data["price_min"])
            except ValueError:
                pass
        if row_data.get("price_max"):
            try:
                price_max = float(row_data["price_max"])
            except ValueError:
                pass

        return {
            "equipment_type": equipment_type,
            "brand_name": row_data.get("brand_name"),
            "model": row_data.get("model"),
            "name": row_data.get("name"),
            "price_min": price_min,
            "price_max": price_max,
            "description": row_data.get("description"),
            "features": features,
            "target_fish": target_fish,
            "user_level": row_data.get("user_level"),
            "specs": specs,
            "confidence": 1.0,
            "extraction_notes": "Excel 导入"
        }


# 单例服务实例
_excel_import_service: Optional[ExcelImportService] = None


def get_excel_import_service() -> ExcelImportService:
    """获取 Excel 导入服务单例"""
    global _excel_import_service
    if _excel_import_service is None:
        _excel_import_service = ExcelImportService()
    return _excel_import_service
