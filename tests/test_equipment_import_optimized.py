"""
装备导入功能优化测试

测试内容：
1. 常量定义
2. 工具参数扩展
3. 重复检查功能
4. dry_run 模式
5. brand_hint 功能
6. Agent API 调用
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, Optional


# ========== 常量测试 ==========

class TestConstants:
    """常量定义测试"""

    def test_equipment_types_complete(self):
        """装备类型完整性"""
        from packages.agents.equipment_import.constants import EQUIPMENT_TYPES

        assert "鱼竿" in EQUIPMENT_TYPES
        assert "渔轮" in EQUIPMENT_TYPES
        assert "鱼线" in EQUIPMENT_TYPES
        assert "拟饵" in EQUIPMENT_TYPES
        assert "路亚竿" in EQUIPMENT_TYPES

    def test_source_types_complete(self):
        """来源类型完整性"""
        from packages.agents.equipment_import.constants import SOURCE_TYPES

        assert "ecommerce" in SOURCE_TYPES
        assert "official" in SOURCE_TYPES
        assert "forum" in SOURCE_TYPES
        assert "unknown" in SOURCE_TYPES

    def test_confidence_thresholds(self):
        """置信度阈值配置"""
        from packages.agents.equipment_import.constants import (
            CONFIDENCE_THRESHOLD_LOW,
            CONFIDENCE_THRESHOLD_HIGH
        )

        assert 0 < CONFIDENCE_THRESHOLD_LOW < CONFIDENCE_THRESHOLD_HIGH <= 1
        assert CONFIDENCE_THRESHOLD_LOW == 0.3
        assert CONFIDENCE_THRESHOLD_HIGH == 0.7

    def test_compression_config(self):
        """压缩配置"""
        from packages.agents.equipment_import.constants import (
            COMPRESSION_MIN_LENGTH,
            BATCH_OCR_TEXT_LIMIT
        )

        assert COMPRESSION_MIN_LENGTH > 0
        assert BATCH_OCR_TEXT_LIMIT > 0


# ========== 工具参数测试 ==========

class TestImportToolParameters:
    """工具参数扩展测试"""

    def test_tool_has_new_parameters(self):
        """工具包含新参数"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )

        # 检查工具函数签名
        import inspect
        sig = inspect.signature(extract_equipment_from_text.func)
        params = list(sig.parameters.keys())

        assert "check_duplicates" in params
        assert "brand_hint" in params
        assert "dry_run" in params

    def test_tool_default_values(self):
        """工具默认值"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )

        import inspect
        sig = inspect.signature(extract_equipment_from_text.func)

        # check_duplicates 默认 True
        assert sig.parameters["check_duplicates"].default is True

        # brand_hint 默认空字符串
        assert sig.parameters["brand_hint"].default == ""

        # dry_run 默认 False
        assert sig.parameters["dry_run"].default is False

    def test_tool_docstring_updated(self):
        """工具文档包含新参数说明"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )

        docstring = extract_equipment_from_text.description
        assert "check_duplicates" in docstring
        assert "brand_hint" in docstring
        assert "dry_run" in docstring


# ========== 重复检查测试 ==========

class TestDuplicateCheck:
    """重复检查功能测试"""

    def test_check_duplicate_equipment_no_match(self):
        """无重复装备"""
        from packages.agents.equipment_import.tools.import_tool import (
            _check_duplicate_equipment
        )

        with patch('apps.api.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.execute.return_value = []
            mock_get_db.return_value = mock_db

            result = _check_duplicate_equipment("禧玛诺", "毒牙264ML", "鱼竿")
            assert result is None

    def test_check_duplicate_equipment_found(self):
        """发现重复装备"""
        from packages.agents.equipment_import.tools.import_tool import (
            _check_duplicate_equipment
        )

        with patch('apps.api.database.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.execute.return_value = [{
                "id": 123,
                "name": "禧玛诺毒牙264ML",
                "category": "鱼竿",
                "brand_name": "禧玛诺"
            }]
            mock_get_db.return_value = mock_db

            result = _check_duplicate_equipment("禧玛诺", "毒牙264ML", "鱼竿")

            assert result is not None
            assert result["id"] == 123
            assert result["name"] == "禧玛诺毒牙264ML"

    def test_check_duplicate_equipment_empty_params(self):
        """空参数返回 None"""
        from packages.agents.equipment_import.tools.import_tool import (
            _check_duplicate_equipment
        )

        result = _check_duplicate_equipment(None, None, None)
        assert result is None

    def test_check_duplicate_pending_no_match(self):
        """待审核表无重复"""
        from packages.agents.equipment_import.tools.import_tool import (
            _check_duplicate_pending
        )

        with patch('apps.api.orm.session.get_db_session') as mock_session:
            mock_ctx = MagicMock()
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            mock_ctx.__enter__ = MagicMock(return_value=MagicMock(query=MagicMock(return_value=mock_query)))
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_session.return_value = mock_ctx

            result = _check_duplicate_pending("禧玛诺", "毒牙264ML")
            assert result is None


# ========== dry_run 模式测试 ==========

class TestDryRunMode:
    """dry_run 模式测试"""

    def test_dry_run_returns_no_pending_id(self):
        """dry_run 模式不返回 pending_id"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        mock_extracted = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.85
        )

        with patch('packages.agents.equipment_import.core.extractor.EquipmentExtractor') as MockExtractor:
            mock_instance = MagicMock()
            mock_instance.extract.return_value = mock_extracted
            MockExtractor.return_value = mock_instance

            result = extract_equipment_from_text.func(
                text="禧玛诺毒牙264ML路亚竿",
                dry_run=True
            )

            result_dict = json.loads(result)
            assert result_dict["success"] is True
            assert result_dict["dry_run"] is True
            assert result_dict["pending_id"] is None

    def test_dry_run_does_not_save(self):
        """dry_run 模式不保存到数据库"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        mock_extracted = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.85
        )

        with patch('packages.agents.equipment_import.core.extractor.EquipmentExtractor') as MockExtractor, \
             patch('packages.agents.equipment_import.models.pending.save_pending_equipment') as mock_save:
            mock_instance = MagicMock()
            mock_instance.extract.return_value = mock_extracted
            MockExtractor.return_value = mock_instance

            extract_equipment_from_text.func(
                text="禧玛诺毒牙264ML路亚竿",
                dry_run=True
            )

            # save_pending_equipment 不应该被调用
            mock_save.assert_not_called()


# ========== brand_hint 测试 ==========

class TestBrandHint:
    """brand_hint 功能测试"""

    def test_brand_hint_prepended_to_text(self):
        """brand_hint 添加到文本开头"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        mock_extracted = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.85
        )

        with patch('packages.agents.equipment_import.core.extractor.EquipmentExtractor') as MockExtractor:
            mock_instance = MagicMock()
            mock_instance.extract.return_value = mock_extracted
            MockExtractor.return_value = mock_instance

            extract_equipment_from_text.func(
                text="毒牙264ML路亚竿",
                brand_hint="禧玛诺",
                dry_run=True
            )

            # 检查传递给 extract 的文本是否包含品牌提示
            call_args = mock_instance.extract.call_args[0]
            processed_text = call_args[0]
            assert "[品牌提示: 禧玛诺]" in processed_text

    def test_brand_hint_empty_no_change(self):
        """空 brand_hint 不修改文本"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        mock_extracted = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.85
        )

        with patch('packages.agents.equipment_import.core.extractor.EquipmentExtractor') as MockExtractor:
            mock_instance = MagicMock()
            mock_instance.extract.return_value = mock_extracted
            MockExtractor.return_value = mock_instance

            original_text = "毒牙264ML路亚竿"
            extract_equipment_from_text.func(
                text=original_text,
                brand_hint="",
                dry_run=True
            )

            # 检查传递给 extract 的文本未被修改
            call_args = mock_instance.extract.call_args[0]
            processed_text = call_args[0]
            assert processed_text == original_text


# ========== 提取结果验证测试 ==========

class TestExtractionValidation:
    """提取结果验证测试"""

    def test_empty_text_returns_error(self):
        """空文本返回错误"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )

        result = extract_equipment_from_text.func(text="")
        result_dict = json.loads(result)

        assert result_dict["success"] is False
        assert "空" in result_dict["message"]

    def test_whitespace_text_returns_error(self):
        """空白文本返回错误"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )

        result = extract_equipment_from_text.func(text="   \n\t  ")
        result_dict = json.loads(result)

        assert result_dict["success"] is False

    def test_low_confidence_returns_error(self):
        """低置信度返回错误"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        mock_extracted = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.1  # 低于阈值 0.3
        )

        with patch('packages.agents.equipment_import.core.extractor.EquipmentExtractor') as MockExtractor:
            mock_instance = MagicMock()
            mock_instance.extract.return_value = mock_extracted
            MockExtractor.return_value = mock_instance

            result = extract_equipment_from_text.func(
                text="禧玛诺毒牙264ML路亚竿"
            )

            result_dict = json.loads(result)
            assert result_dict["success"] is False
            assert "置信度" in result_dict["message"]

    def test_invalid_equipment_type_returns_error(self):
        """无效装备类型返回错误"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        mock_extracted = ExtractedEquipment(
            equipment_type="帐篷",  # 不在有效类型列表中
            brand_name="测试",
            model="测试型号",
            confidence=0.85
        )

        with patch('packages.agents.equipment_import.core.extractor.EquipmentExtractor') as MockExtractor:
            mock_instance = MagicMock()
            mock_instance.extract.return_value = mock_extracted
            MockExtractor.return_value = mock_instance

            result = extract_equipment_from_text.func(
                text="测试文本"
            )

            result_dict = json.loads(result)
            assert result_dict["success"] is False
            assert "不支持" in result_dict["message"]

    def test_invalid_source_type_defaults_to_unknown(self):
        """无效来源类型默认为 unknown"""
        from packages.agents.equipment_import.tools.import_tool import (
            extract_equipment_from_text
        )
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        mock_extracted = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.85
        )

        with patch('packages.agents.equipment_import.core.extractor.EquipmentExtractor') as MockExtractor, \
             patch('packages.agents.equipment_import.models.pending.save_pending_equipment') as mock_save:
            mock_instance = MagicMock()
            mock_instance.extract.return_value = mock_extracted
            MockExtractor.return_value = mock_instance
            mock_save.return_value = 1

            extract_equipment_from_text.func(
                text="禧玛诺毒牙264ML路亚竿",
                source_type="invalid_type"
            )

            # 检查保存时使用的 source_type 应该是 unknown
            call_kwargs = mock_save.call_args[1]
            assert call_kwargs["source_type"] == "unknown"


# ========== Agent API 测试 ==========

class TestAgentAPI:
    """Agent API 调用测试"""

    def test_extract_and_save_has_new_parameters(self):
        """extract_and_save 方法包含新参数"""
        from packages.agents.equipment_import.core.agent import EquipmentImportAgent

        import inspect
        sig = inspect.signature(EquipmentImportAgent.extract_and_save)
        params = list(sig.parameters.keys())

        assert "check_duplicates" in params
        assert "brand_hint" in params
        assert "dry_run" in params

    def test_agent_uses_constants(self):
        """Agent 使用常量"""
        from packages.agents.equipment_import.core.agent import EquipmentImportAgent
        from packages.agents.equipment_import.constants import (
            DEFAULT_MODEL_PROVIDER,
            COMPRESSION_MIN_LENGTH
        )

        import inspect
        sig = inspect.signature(EquipmentImportAgent.__init__)

        # model_provider 默认值应该是常量
        assert sig.parameters["model_provider"].default == DEFAULT_MODEL_PROVIDER

        # compression_min_length 默认值应该是常量
        assert sig.parameters["compression_min_length"].default == COMPRESSION_MIN_LENGTH


# ========== 数据模型测试 ==========

class TestDataModels:
    """数据模型测试"""

    def test_extracted_equipment_to_dict(self):
        """ExtractedEquipment 转字典"""
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        eq = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.85,
            specs={"length": 2.1, "power": "ML"}
        )

        d = eq.to_dict()

        assert d["equipment_type"] == "鱼竿"
        assert d["brand_name"] == "禧玛诺"
        assert d["model"] == "毒牙264ML"
        assert d["confidence"] == 0.85
        assert d["specs"]["length"] == 2.1

    def test_extracted_equipment_from_dict(self):
        """从字典创建 ExtractedEquipment"""
        from packages.agents.equipment_import.schemas.extracted import ExtractedEquipment

        data = {
            "equipment_type": "渔轮",
            "brand_name": "达亿瓦",
            "model": "月下美人",
            "confidence": 0.9
        }

        eq = ExtractedEquipment.from_dict(data)

        assert eq.equipment_type == "渔轮"
        assert eq.brand_name == "达亿瓦"
        assert eq.model == "月下美人"
        assert eq.confidence == 0.9

    def test_import_result_to_dict(self):
        """ImportResult 转字典"""
        from packages.agents.equipment_import.schemas.extracted import (
            ExtractedEquipment,
            ImportResult
        )

        extracted = ExtractedEquipment(
            equipment_type="鱼竿",
            brand_name="禧玛诺",
            model="毒牙264ML",
            confidence=0.85
        )

        result = ImportResult(
            success=True,
            pending_id=123,
            message="成功",
            extracted=extracted
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["pending_id"] == 123
        assert d["message"] == "成功"
        assert d["extracted"]["brand_name"] == "禧玛诺"


# ========== 工具列表测试 ==========

class TestToolList:
    """工具列表测试"""

    def test_get_import_tools_returns_list(self):
        """get_import_tools 返回列表"""
        from packages.agents.equipment_import.tools.import_tool import get_import_tools

        tools = get_import_tools()
        assert isinstance(tools, list)
        assert len(tools) == 1  # 只有一个工具

    def test_single_tool_design(self):
        """保持单一工具设计"""
        from packages.agents.equipment_import.tools.import_tool import get_import_tools

        tools = get_import_tools()
        assert len(tools) == 1

        tool = tools[0]
        assert tool.name == "extract_equipment_from_text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
