# Refactor Tools Module - OpenSpec Proposal

## 📋 Overview

**Change ID**: `refactor-tools-module`
**Title**: 重构 Tools 模块架构
**Status**: 🟡 In Progress
**Priority**: High
**Impact**: Code organization, developer experience, maintainability

## 🎯 Problem Statement

当前 `src/tools/` 目录存在以下问题：

1. **文件散乱**: 13+ 个工具文件，命名不一致，组织混乱
2. **重复功能**: 多个相似工具文件（weather_tool.py, weather_tool_sync.py 等）
3. **业务重叠**: 钓鱼工具和天气工具存在功能重复，导致重复API调用
4. **扩展困难**: 新增工具缺乏清晰的分类指导
5. **架构不清**: 缺乏明确的业务分层和模块边界

## 🏗️ Solution Overview

### 新架构设计

重构为清晰的分类体系：
- **Basic Tools**: 简单工具，方便编写和添加
- **Fishing Business**: 完整的钓鱼业务模块，按业务分层

### 目录结构

```
src/tools/
├── basic/                      # 基础工具类别
├── fishing/                   # 钓鱼完整业务模块
│   ├── weather/               # 天气工具模块（数据获取层）
│   ├── advice/                # 钓鱼意见模块（业务分析层）
│   └── equipment/             # 钓鱼装备模块（装备推荐层）
└── core/                      # 核心基础设施
```

## 📊 Impact Analysis

### Affected Components
- ✅ `src/tools/` - 完全重构
- ✅ `src/agent.py` - 工具导入方式更新
- ✅ `CLAUDE.md` - 文档更新

### Backward Compatibility
- ✅ 保持所有现有工具功能不变
- ✅ 提供兼容性导入别名
- ✅ 渐进式迁移，支持新旧并存

### Performance Impact
- ✅ 减少重复API调用
- ✅ 提高工具加载效率
- ✅ 优化内存使用

## ✨ Benefits

### Developer Experience
- **简易添加**: 基础工具只需一个 `@tool` 装饰器
- **清晰分类**: 新工具定位明确，易于维护
- **模块化**: 各模块可独立开发和测试

### Code Quality
- **消除重复**: 合并相似工具文件
- **职责分离**: 清晰的业务分层架构
- **命名规范**: 避免与Python标准库冲突

### Maintainability
- **业务清晰**: fishing 模块按业务逻辑分层
- **扩展友好**: 为装备工具预留完整空间
- **架构稳定**: 核心基础设施支持长期发展

## 🔄 Migration Strategy

### Phase 1: Infrastructure
1. 创建 core/ 核心基础设施
2. 建立工具注册系统
3. 创建辅助函数

### Phase 2: Basic Tools
1. 创建 basic/ 目录结构
2. 迁移简单工具
3. 统一命名规范

### Phase 3: Fishing Business
1. 重组天气工具到 fishing/weather/
2. 创建钓鱼意见工具 fishing/advice/
3. 预留装备工具 fishing/equipment/

### Phase 4: Integration
1. 更新 agent.py 使用新架构
2. 完整功能测试
3. 文档更新

## 📈 Success Metrics

- **代码组织**: 90%+ 工具按类别清晰分类
- **开发效率**: 新增基础工具时间减少 50%+
- **重复消除**: 减少 5+ 个重复工具文件
- **功能稳定**: 100% 现有功能保持正常运行
- **扩展能力**: 钓鱼装备工具预留完整扩展空间

## 🚀 Next Steps

1. **创建 tasks.md**: 详细实施检查清单
2. **建立核心基础设施**: tool_registry.py, base_interfaces.py
3. **开始基础工具迁移**: time_utils.py, math_ops.py 等
4. **重组钓鱼业务模块**: weather/, advice/, equipment/
5. **完整测试验证**: 确保功能正常

---

**Approval Status**: ✅ Approved
**Implementation Start**: 2025-11-18
**Estimated Completion**: 3 days