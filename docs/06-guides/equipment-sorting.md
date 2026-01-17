# 装备管理排序功能指南

## 概述

装备管理页面提供了强大的多字段排序功能，支持12个不同的排序字段，包括通用字段和鱼竿专属字段。用户可以通过表格列头点击或高级筛选面板进行排序操作。

**版本**: v5.1.0
**最后更新**: 2026-01-17

## 功能特性

### 支持的排序字段

#### 通用字段（7个）
1. **名称** (`name`) - 按装备名称字母顺序排序
2. **类别** (`category`) - 按装备类别排序（鱼竿/渔轮/鱼线/拟饵）
3. **品牌** (`brand_name`) - 按品牌名称排序（需要 JOIN Brand 表）
4. **最低价** (`price_min`) - 按价格范围最低价排序
5. **最高价** (`price_max`) - 按价格范围最高价排序
6. **创建时间** (`created_at`) - 按记录创建时间排序
7. **更新时间** (`updated_at`) - 按记录更新时间排序

#### 鱼竿专属字段（5个）
8. **竿长** (`length`) - 按鱼竿长度排序（米）
9. **自重** (`weight`) - 按鱼竿重量排序（克）
10. **动作** (`action`) - 按鱼竿动作排序（Fast/Moderate/Slow）
11. **调性** (`power`) - 按鱼竿调性排序（UL/L/ML/M/MH/H/XH）
12. **节数** (`sections`) - 按鱼竿节数排序

### 排序方式

- **升序** (`asc`) - 从小到大、A-Z
- **降序** (`desc`) - 从大到小、Z-A（默认）

### 使用方式

#### 1. 表格列头排序
- 点击可排序列的列头进行排序
- 首次点击：升序排序
- 再次点击：降序排序
- 第三次点击：取消排序
- 当前排序列会高亮显示

#### 2. 高级筛选面板排序
- 点击"高级筛选"按钮打开面板
- 在"排序"区域选择排序字段和排序方向
- 支持所有12个排序字段

### UI 反馈

1. **列头图标** - 可排序列显示上下箭头图标
2. **高亮状态** - 当前排序列高亮显示
3. **排序标签** - 页面顶部显示当前排序状态（如"排序: 名称 升序"）
4. **URL 持久化** - 排序参数保存在 URL 中，支持分享和刷新

## 技术实现

### 后端实现

#### 1. 数据库查询层 (`equipment_repo.py`)

```python
def _apply_sorting(self, query, sort_by: Optional[str] = None, sort_order: str = "desc"):
    """应用排序到查询"""
    if not sort_by:
        return query.order_by(Equipment.equipment_id.desc())

    # 有效排序字段
    valid_fields = {
        'name', 'price_min', 'price_max', 'created_at', 'updated_at',
        'category', 'brand_name', 'length', 'weight', 'action', 'power', 'sections'
    }

    if sort_by not in valid_fields:
        return query.order_by(Equipment.equipment_id.desc())

    # 处理需要 JOIN 的字段
    if sort_by == 'brand_name':
        from ...models.brand import Brand
        query = query.outerjoin(Brand, Equipment.brand_id == Brand.brand_id)
        field = Brand.name_cn
    elif sort_by in ['length', 'weight', 'action', 'power', 'sections']:
        # 鱼竿规格字段 - 使用 outerjoin 避免过滤掉非鱼竿装备
        query = query.outerjoin(RodSpec, Equipment.equipment_id == RodSpec.equipment_id)
        field = getattr(RodSpec, sort_by)
    else:
        # 直接 Equipment 字段
        field = getattr(Equipment, sort_by)

    # 应用排序，NULL 值排在最后
    if sort_order == 'asc':
        return query.order_by(field.asc().nullslast())
    else:
        return query.order_by(field.desc().nullslast())
```

**关键点：**
- 使用 `outerjoin` 而不是 `join`，确保非鱼竿装备不会被过滤掉
- 使用 `.nullslast()` 确保 NULL 值排在最后
- 品牌排序需要 JOIN Brand 表
- 鱼竿规格字段需要 JOIN RodSpec 表

#### 2. API 路由 (`equipment_admin.py`)

```python
@router.get("/equipment")
async def get_equipment_list(
    # ... 其他参数
    sort_by: Optional[str] = Query(
        None,
        description="排序字段: name/price_min/price_max/created_at/updated_at/category/brand_name/length/weight/action/power/sections"
    ),
    sort_order: Optional[str] = Query("desc", description="排序方向: asc/desc"),
):
    """查询装备列表（分页 + 多条件筛选 + 排序）"""
    # ... 实现
```

### 前端实现

#### 1. 类型定义 (`equipment.ts`)

```typescript
export interface EquipmentSearchFilters {
  // ... 其他字段
  sort_by?: 'name' | 'price_min' | 'price_max' | 'created_at' | 'updated_at'
    | 'category' | 'brand_name' | 'length' | 'weight' | 'action' | 'power' | 'sections'
  sort_order?: 'asc' | 'desc'
}
```

#### 2. 表格列定义 (`List.tsx`)

```typescript
const allColumns = [
  {
    key: 'name',
    title: '名称',
    dataIndex: 'name',
    width: 200,
    sorter: true,  // 启用排序
  },
  {
    key: 'power',
    title: '调性',
    width: 80,
    sorter: true,  // 启用排序
    render: (_: unknown, record: Equipment) => {
      if (record.category !== '鱼竿') return '-'
      const specs = record.specs as Record<string, unknown> | undefined
      return specs?.power || '-'
    },
  },
  // ... 其他列
]
```

#### 3. 表格排序处理 (`List.tsx`)

```typescript
<Table
  columns={columns}
  dataSource={data}
  onChange={(pagination, filters, sorter) => {
    // 处理排序
    if (sorter && !Array.isArray(sorter) && sorter.field && sorter.order) {
      const sortField = sorter.field as string
      const sortOrder = sorter.order === 'ascend' ? 'asc' : 'desc'
      // 映射 'price' 到 'price_min'
      const backendSortField = sortField === 'price' ? 'price_min' : sortField
      setFilters({
        ...filters,
        sort_by: backendSortField as any,
        sort_order: sortOrder
      })
    } else if (sorter && !Array.isArray(sorter) && !sorter.order) {
      // 清除排序
      setFilters({
        ...filters,
        sort_by: undefined,
        sort_order: undefined
      })
    }
  }}
  // ... 其他属性
/>
```

#### 4. 高级筛选面板 (`AdvancedSearch.tsx`)

```typescript
<Select
  placeholder="排序字段"
  style={{ width: 120 }}
  allowClear
  value={filters.sort_by}
  onChange={(value) => handleChange('sort_by', value)}
  options={[
    { label: '名称', value: 'name' },
    { label: '类别', value: 'category' },
    { label: '品牌', value: 'brand_name' },
    { label: '最低价', value: 'price_min' },
    { label: '最高价', value: 'price_max' },
    { label: '竿长', value: 'length' },
    { label: '自重', value: 'weight' },
    { label: '动作', value: 'action' },
    { label: '调性', value: 'power' },
    { label: '节数', value: 'sections' },
    { label: '创建时间', value: 'created_at' },
    { label: '更新时间', value: 'updated_at' },
  ]}
/>
```

## 性能优化

### 数据库索引

建议为常用排序字段添加索引：

```sql
-- 品牌名称索引（已有外键索引）
CREATE INDEX idx_equipment_brand_id ON equipment(brand_id);

-- 类别索引
CREATE INDEX idx_equipment_category ON equipment(category);

-- 价格索引
CREATE INDEX idx_equipment_price_min ON equipment(price_min);
CREATE INDEX idx_equipment_price_max ON equipment(price_max);

-- 时间索引
CREATE INDEX idx_equipment_created_at ON equipment(created_at);
CREATE INDEX idx_equipment_updated_at ON equipment(updated_at);

-- 鱼竿规格索引
CREATE INDEX idx_rod_spec_length ON rod_spec(length);
CREATE INDEX idx_rod_spec_weight ON rod_spec(weight);
CREATE INDEX idx_rod_spec_power ON rod_spec(power);
CREATE INDEX idx_rod_spec_action ON rod_spec(action);
CREATE INDEX idx_rod_spec_sections ON rod_spec(sections);
```

### JOIN 优化

- 使用 `outerjoin` 避免过滤掉没有规格的装备
- 只在需要时才执行 JOIN（根据 `sort_by` 参数）
- 利用外键索引加速 JOIN 操作

## 测试用例

### 功能测试

1. **列头点击排序**
   - ✅ 点击"名称"列头，验证按名称升序/降序排序
   - ✅ 点击"品牌"列头，验证按品牌名称排序
   - ✅ 点击"价格范围"列头，验证按最低价排序
   - ✅ 点击"类别"列头，验证按类别排序

2. **鱼竿专属字段排序**
   - ✅ 筛选"鱼竿"类别，点击"竿长"列头排序
   - ✅ 筛选"鱼竿"类别，点击"自重"列头排序
   - ✅ 筛选"鱼竿"类别，点击"动作"列头排序
   - ✅ 筛选"鱼竿"类别，点击"调性"列头排序
   - ✅ 筛选"鱼竿"类别，点击"节数"列头排序
   - ✅ 验证没有规格数据的装备不会被过滤掉

3. **高级筛选面板排序**
   - ✅ 在下拉菜单中选择各个排序字段
   - ✅ 切换升序/降序
   - ✅ 验证与表格列头排序状态同步

4. **排序状态持久化**
   - ✅ 应用排序后切换页码，验证排序保持
   - ✅ 修改每页条数，验证排序保持
   - ✅ 刷新页面，验证排序状态从 URL 恢复

5. **筛选与排序组合**
   - ✅ 应用类别筛选 + 排序
   - ✅ 应用品牌筛选 + 排序
   - ✅ 应用价格范围筛选 + 排序

### 边界情况

1. **NULL 值处理**
   - ✅ 鱼竿规格字段可能为空，NULL 值排在最后
   - ✅ 非鱼竿装备的规格字段显示"-"

2. **相同值排序**
   - ✅ 相同值的记录按 equipment_id 排序（稳定排序）

3. **多次点击**
   - ✅ 多次点击同一列头正确切换升序/降序/取消排序

## 故障排除

### 常见问题

**Q: 点击列头没有反应？**
A: 检查列定义中是否添加了 `sorter: true` 属性。

**Q: 排序后非鱼竿装备消失了？**
A: 确保使用 `outerjoin` 而不是 `join`，避免过滤掉没有规格的装备。

**Q: NULL 值排序位置不对？**
A: 确保使用 `.nullslast()` 方法，让 NULL 值排在最后。

**Q: 排序状态不同步？**
A: 检查 Table 的 `onChange` 回调是否正确更新了 filters 状态。

**Q: URL 参数没有更新？**
A: 确保使用了 `useEquipmentSearch` hook 来管理 URL 参数。

## 相关文件

### 后端
- `apps/api/orm/repositories/equipment_repo.py` - 排序逻辑实现
- `apps/api/routes/equipment_admin.py` - API 路由定义
- `apps/api/models/equipment.py` - 数据模型

### 前端
- `apps/web-admin/src/pages/Equipment/List.tsx` - 表格列定义和排序处理
- `apps/web-admin/src/pages/Equipment/components/AdvancedSearch.tsx` - 高级筛选面板
- `apps/web-admin/src/types/equipment.ts` - 类型定义

## 更新历史

- **2026-01-17**: 添加鱼竿专属字段排序（动作/调性/节数）
- **2026-01-17**: 初始实现，支持12个排序字段
