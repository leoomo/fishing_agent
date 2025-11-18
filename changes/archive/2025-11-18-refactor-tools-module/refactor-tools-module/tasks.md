# Refactor Tools Module - Implementation Tasks

## 📋 Implementation Checklist

### Phase 1: 创建 OpenSpec 提案
- [x] 创建 `changes/refactor-tools-module/` 目录
- [x] 编写 `proposal.md` - 变更目标和影响分析
- [ ] 编写 `design.md` - 技术决策和架构设计
- [ ] 创建完整任务检查清单

### Phase 2: 核心基础设施建设
- [ ] 创建 `core/` 目录结构
  - [ ] 创建 `core/__init__.py`
  - [ ] 创建 `core/tool_registry.py` - 工具注册系统
  - [ ] 创建 `core/base_interfaces.py` - 工具接口定义
  - [ ] 创建 `core/tool_factory.py` - 工具工厂
- [ ] 创建 `helper_functions.py` - 工具辅助函数
- [ ] 测试核心基础设施功能

### Phase 3: Basic 工具模块
- [ ] 创建 `basic/` 目录结构
  - [ ] 创建 `basic/__init__.py` - 基础工具注册
  - [ ] 创建 `basic/time_utils.py` - 时间相关工具
  - [ ] 创建 `basic/math_ops.py` - 数学计算工具
  - [ ] 创建 `basic/info_search.py` - 信息搜索工具
  - [ ] 创建 `basic/sys_utils.py` - 系统工具
- [ ] 迁移现有基础工具：
  - [ ] 迁移 `time_tool.py` → `basic/time_utils.py`
  - [ ] 迁移 `math_tool.py` → `basic/math_ops.py`
  - [ ] 迁移 `search_tool.py` → `basic/info_search.py`
  - [ ] 迁移 `basic_tools.py` 内容到对应 basic 文件
- [ ] 创建 `get_basic_tools()` 统一导出函数
- [ ] 测试基础工具功能

### Phase 4: Fishing 业务模块重组
- [ ] 创建 `fishing/` 目录结构
  - [ ] 创建 `fishing/__init__.py` - 钓鱼工具总注册
  - [ ] 创建 `get_fishing_tools()` 统一导出函数

#### Phase 4.1: 天气工具模块 (数据获取层)
- [ ] 创建 `fishing/weather/` 目录结构
  - [ ] 创建 `fishing/weather/__init__.py` - 天气工具注册
  - [ ] 创建 `fishing/weather/current_weather.py` - 当前天气查询
  - [ ] 创建 `fishing/weather/weather_forecast.py` - 天气预报业务
  - [ ] 创建 `fishing/weather/datetime_weather.py` - 日期时间天气查询
- [ ] 重组现有天气工具：
  - [ ] 分解 `langchain_weather_tools_sync.py` 到对应文件
  - [ ] 迁移 `query_current_weather` → `current_weather.py`
  - [ ] 迁移 `query_weather_by_date` → `weather_forecast.py`
  - [ ] 迁移 `query_weather_by_datetime` → `datetime_weather.py`
  - [ ] 迁移 `query_hourly_forecast` → `weather_forecast.py`
  - [ ] 迁移 `query_time_period_weather` → `datetime_weather.py`
- [ ] 创建 `get_weather_tools()` 统一导出函数
- [ ] 测试天气工具功能

#### Phase 4.2: 钓鱼意见模块 (业务分析层)
- [ ] 创建 `fishing/advice/` 目录结构
  - [ ] 创建 `fishing/advice/__init__.py` - 钓鱼意见工具注册
  - [ ] 创建 `fishing/advice/fishing_analyzer.py` - 钓鱼分析引擎
  - [ ] 创建 `fishing/advice/time_recommender.py` - 钓鱼时间推荐
- [ ] 迁移钓鱼分析工具：
  - [ ] 迁移 `fishing_analyzer_sync.py` → `fishing_analyzer.py`
  - [ ] 迁移 `query_fishing_recommendation` → `time_recommender.py`
- [ ] 实现天气数据复用逻辑（避免重复API调用）
- [ ] 创建 `get_advice_tools()` 统一导出函数
- [ ] 测试钓鱼意见工具功能

#### Phase 4.3: 钓鱼装备模块 (装备推荐层)
- [ ] 创建 `fishing/equipment/` 目录结构
  - [ ] 创建 `fishing/equipment/__init__.py` - 钓鱼装备工具注册
  - [ ] 创建 `fishing/equipment/equipment_recommender.py` - 钓鱼装备推荐（预留）
  - [ ] 创建 `fishing/equipment/equipment_comparator.py` - 钓鱼装备对比（预留）
- [ ] 创建 `get_equipment_tools()` 统一导出函数（返回空列表，预留）
- [ ] 添加预留接口文档

### Phase 5: 系统集成
- [ ] 更新主 `src/tools/__init__.py`：
  - [ ] 添加基础工具导入
  - [ ] 添加钓鱼工具导入
  - [ ] 创建 `get_all_tools()` 统一接口
  - [ ] 提供向后兼容的导入别名
- [ ] 更新 `src/agent.py`：
  - [ ] 修改 `_setup_tools()` 方法使用新架构
  - [ ] 更新导入语句
  - [ ] 保持现有功能接口不变
- [ ] 测试完整功能：
  - [ ] 测试基础工具功能
  - [ ] 测试天气工具功能
  - [ ] 测试钓鱼工具功能
  - [ ] 测试工具间协作
  - [ ] 验证向后兼容性

### Phase 6: 清理和文档
- [ ] 清理旧工具文件：
  - [ ] 备份现有工具文件
  - [ ] 删除重复和已迁移的工具文件
  - [ ] 清理 `basic_tools.py`（已迁移）
- [ ] 更新项目文档：
  - [ ] 更新 `CLAUDE.md` 中的工具架构说明
  - [ ] 更新导入示例和使用指南
- [ ] 验证最终架构：
  - [ ] 运行完整测试套件
  - [ ] 检查所有工具功能正常
  - [ ] 确认目录结构清晰
  - [ ] 验证性能优化效果

## ✅ 验收标准

### 功能验收
- [ ] 所有现有工具功能保持不变
- [ ] 新架构工具调用正常
- [ ] 向后兼容性完全支持
- [ ] 工具注册系统正常工作

### 代码质量验收
- [ ] 目录结构清晰，分类明确
- [ ] 命名规范，避免冲突
- [ ] 代码注释完整
- [ ] 模块职责分离清晰

### 性能验收
- [ ] 工具加载时间不增加
- [ ] 内存使用合理
- [ ] 减少重复API调用

### 文档验收
- [ ] 架构文档完整
- [ ] 使用示例清晰
- [ ] 迁移指南详细

## 🚨 注意事项

1. **向后兼容**: 确保现有代码可以无缝迁移
2. **渐进式迁移**: 支持新旧工具系统并存期间
3. **功能验证**: 每个工具迁移后都要进行功能测试
4. **性能监控**: 关注API调用次数，确保优化效果
5. **文档同步**: 代码变更后立即更新相关文档

## 📊 进度跟踪

- **当前阶段**: Phase 1 - OpenSpec 提案创建
- **完成度**: 15%
- **预计完成时间**: 3天
- **下一步**: 创建核心基础设施