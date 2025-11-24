"""
LangChain工具集成测试

测试lure_tools.py中的4个核心工具:
1. recommend_equipment - 装备推荐
2. compare_equipment - 装备对比
3. lookup_fishing_knowledge - 知识查询
4. identify_from_image - 图片识别
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from ..init_data import init_all_data


class TestRecommendEquipmentTool:
    """装备推荐工具测试"""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """初始化测试数据"""
        init_all_data()

    def test_recommend_rod_basic(self):
        """测试基础鱼竿推荐"""
        from ...lure_tools import recommend_equipment

        result = recommend_equipment.invoke({
            "equipment_type": "鱼竿",
            "budget": 500,
            "user_level": "新手"
        })

        assert "推荐报告" in result
        assert "鱼竿" in result

    def test_recommend_with_specs(self):
        """测试带规格的推荐"""
        from ...lure_tools import recommend_equipment

        result = recommend_equipment.invoke({
            "equipment_type": "鱼竿",
            "budget": 800,
            "specifications": json.dumps({"硬度": "ML"}),
            "user_level": "进阶"
        })

        assert "推荐报告" in result

    def test_recommend_package(self):
        """测试套装推荐"""
        from ...lure_tools import recommend_equipment

        result = recommend_equipment.invoke({
            "equipment_type": "套装",
            "budget": 1000,
            "user_level": "新手"
        })

        assert "套装" in result

    def test_recommend_invalid_type(self):
        """测试无效装备类型"""
        from ...lure_tools import recommend_equipment

        result = recommend_equipment.invoke({
            "equipment_type": "无效类型"
        })

        assert "无法识别" in result

    def test_recommend_type_aliases(self):
        """测试装备类型别名"""
        from ...lure_tools import recommend_equipment

        # 测试各种别名
        aliases = ["竿子", "路亚竿", "轮子", "纺车轮", "线", "PE线", "饵", "假饵"]

        for alias in aliases:
            result = recommend_equipment.invoke({
                "equipment_type": alias
            })
            # 不应返回无法识别
            assert "无法识别" not in result or "未找到" in result


class TestCompareEquipmentTool:
    """装备对比工具测试"""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """初始化测试数据"""
        init_all_data()

    def test_compare_two_items(self):
        """测试对比两款装备"""
        from ...lure_tools import compare_equipment

        result = compare_equipment.invoke({
            "equipment_names": "狼王青锋ML, 狼王青锋M"
        })

        # 应返回对比结果或未找到提示
        assert isinstance(result, str)

    def test_compare_single_item_error(self):
        """测试单个装备报错"""
        from ...lure_tools import compare_equipment

        result = compare_equipment.invoke({
            "equipment_names": "狼王青锋ML"
        })

        assert "至少2个" in result

    def test_compare_too_many_items(self):
        """测试超过5个装备"""
        from ...lure_tools import compare_equipment

        result = compare_equipment.invoke({
            "equipment_names": "A, B, C, D, E, F"
        })

        assert "不能超过5个" in result

    def test_compare_with_aspects(self):
        """测试指定对比维度"""
        from ...lure_tools import compare_equipment

        result = compare_equipment.invoke({
            "equipment_names": "狼王青锋ML, 狼王青锋M",
            "compare_aspects": "价格, 性能"
        })

        assert isinstance(result, str)


class TestLookupKnowledgeTool:
    """知识查询工具测试"""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """初始化测试数据"""
        init_all_data()

    def test_lookup_fish_knowledge(self):
        """测试查询鱼类知识"""
        from ...lure_tools import lookup_fishing_knowledge

        result = lookup_fishing_knowledge.invoke({
            "topic": "鲈鱼"
        })

        assert isinstance(result, str)

    def test_lookup_rig_knowledge(self):
        """测试查询钓组知识"""
        from ...lure_tools import lookup_fishing_knowledge

        result = lookup_fishing_knowledge.invoke({
            "topic": "德州钓组怎么绑"
        })

        assert isinstance(result, str)

    def test_lookup_with_images(self):
        """测试包含图片的查询"""
        from ...lure_tools import lookup_fishing_knowledge

        result = lookup_fishing_knowledge.invoke({
            "topic": "翘嘴",
            "include_images": True
        })

        assert isinstance(result, str)

    def test_lookup_unknown_topic(self):
        """测试未知主题"""
        from ...lure_tools import lookup_fishing_knowledge

        result = lookup_fishing_knowledge.invoke({
            "topic": "完全不存在的内容xyz123"
        })

        # 应返回未找到提示或搜索结果
        assert isinstance(result, str)


class TestIdentifyFromImageTool:
    """图片识别工具测试"""

    def test_identify_nonexistent_file(self):
        """测试不存在的文件"""
        from ...lure_tools import identify_from_image

        result = identify_from_image.invoke({
            "image_path": "/nonexistent/path/image.jpg"
        })

        assert "不存在" in result

    def test_identify_url_not_supported(self):
        """测试URL图片不支持"""
        from ...lure_tools import identify_from_image

        result = identify_from_image.invoke({
            "image_path": "https://example.com/image.jpg"
        })

        assert "暂不支持" in result


class TestToolMetadata:
    """工具元数据测试"""

    def test_tool_names(self):
        """测试工具名称"""
        from ...lure_tools import LURE_TOOLS

        names = [tool.name for tool in LURE_TOOLS]

        assert "recommend_equipment" in names
        assert "compare_equipment" in names
        assert "lookup_fishing_knowledge" in names
        assert "identify_from_image" in names

    def test_tool_descriptions(self):
        """测试工具描述"""
        from ...lure_tools import LURE_TOOLS

        for tool in LURE_TOOLS:
            assert tool.description, f"工具 {tool.name} 缺少描述"
            assert len(tool.description) > 10, f"工具 {tool.name} 描述太短"

    def test_get_lure_tools(self):
        """测试获取工具列表"""
        from ...lure_tools import get_lure_tools

        tools = get_lure_tools()

        assert len(tools) == 4
        assert all(hasattr(t, 'invoke') for t in tools)


class TestNormalizeEquipmentType:
    """装备类型标准化测试"""

    def test_rod_aliases(self):
        """测试鱼竿别名"""
        from ...lure_tools import _normalize_equipment_type

        rod_aliases = ["鱼竿", "竿子", "路亚竿", "竿"]
        for alias in rod_aliases:
            assert _normalize_equipment_type(alias) == "鱼竿"

    def test_reel_aliases(self):
        """测试渔轮别名"""
        from ...lure_tools import _normalize_equipment_type

        reel_aliases = ["渔轮", "轮子", "纺车轮", "水滴轮", "轮"]
        for alias in reel_aliases:
            assert _normalize_equipment_type(alias) == "渔轮"

    def test_line_aliases(self):
        """测试鱼线别名"""
        from ...lure_tools import _normalize_equipment_type

        line_aliases = ["鱼线", "线", "PE线", "碳线", "尼龙线"]
        for alias in line_aliases:
            assert _normalize_equipment_type(alias) == "鱼线"

    def test_lure_aliases(self):
        """测试拟饵别名"""
        from ...lure_tools import _normalize_equipment_type

        lure_aliases = ["拟饵", "饵", "假饵", "软饵", "硬饵"]
        for alias in lure_aliases:
            assert _normalize_equipment_type(alias) == "拟饵"

    def test_unknown_type(self):
        """测试未知类型"""
        from ...lure_tools import _normalize_equipment_type

        assert _normalize_equipment_type("未知类型") is None


class TestClassifyTopic:
    """主题分类测试"""

    def test_fish_topics(self):
        """测试鱼类主题"""
        from ...lure_tools import _classify_topic

        fish_topics = ["鲈鱼习性", "翘嘴什么时候活跃", "黑鱼吃什么"]
        for topic in fish_topics:
            assert _classify_topic(topic) == "fish"

    def test_rig_topics(self):
        """测试钓组主题"""
        from ...lure_tools import _classify_topic

        rig_topics = ["德州钓组怎么绑", "无铅钓组怎么用", "卡罗钓组组装"]
        for topic in rig_topics:
            assert _classify_topic(topic) == "rig"

    def test_technique_topics(self):
        """测试技巧主题"""
        from ...lure_tools import _classify_topic

        tech_topics = ["怎么钓鲈鱼", "作钓技巧", "收线方法"]
        for topic in tech_topics:
            assert _classify_topic(topic) == "technique"

    def test_unknown_topics(self):
        """测试未知主题"""
        from ...lure_tools import _classify_topic

        assert _classify_topic("随机内容") == "unknown"


class TestServiceLazyLoading:
    """服务懒加载测试"""

    def test_services_initialized_on_first_call(self):
        """测试首次调用时初始化服务"""
        from ...lure_tools import _get_services, _services

        # 清空缓存
        _services.clear()

        services = _get_services()

        assert 'db' in services
        assert 'recommender' in services
        assert 'comparator' in services
        assert 'search_service' in services

    def test_services_cached(self):
        """测试服务缓存"""
        from ...lure_tools import _get_services

        services1 = _get_services()
        services2 = _get_services()

        assert services1 is services2
