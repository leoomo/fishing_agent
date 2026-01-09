import { useState, useMemo } from 'react'
import {
  Space,
  Select,
  Input,
  Button,
  InputNumber,
  Tag,
  Collapse,
  Row,
  Col,
  Segmented,
  DatePicker,
} from 'antd'
import {
  FilterOutlined,
  ReloadOutlined,
  DownOutlined,
  UpOutlined,
} from '@ant-design/icons'
import type { Brand, EquipmentSearchFilters } from '@/types/equipment'
import {
  EQUIPMENT_CATEGORIES,
  USER_LEVELS,
  ROD_POWERS,
  ROD_ACTIONS,
  REEL_TYPES,
  REEL_TYPE_LABELS,
  LINE_TYPES,
  LURE_CATEGORIES,
  DATA_SOURCES,
  DATA_SOURCE_LABELS,
  ROD_SECTIONS,
} from '@/types/equipment'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const { Search } = Input

interface AdvancedSearchProps {
  filters: EquipmentSearchFilters
  brands: Brand[]
  loading?: boolean
  onChange: (filters: EquipmentSearchFilters) => void
  onSearch: () => void
  onReset: () => void
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  filters,
  brands,
  loading: _loading,
  onChange,
  onSearch,
  onReset,
}) => {
  const [expanded, setExpanded] = useState(false)

  // 处理筛选变更
  const handleChange = (key: keyof EquipmentSearchFilters, value: unknown) => {
    const newFilters = { ...filters, [key]: value || undefined }
    // 如果类别变了，清除所有类别专属筛选
    if (key === 'category') {
      // 清除鱼竿专属
      delete newFilters.power
      delete newFilters.action
      delete newFilters.length_min
      delete newFilters.length_max
      delete newFilters.rod_lure_weight_min
      delete newFilters.rod_lure_weight_max
      delete newFilters.sections
      delete newFilters.rod_weight_min
      delete newFilters.rod_weight_max
      delete newFilters.guide_type
      delete newFilters.handle_type
      // 清除渔轮专属
      delete newFilters.reel_type
      delete newFilters.max_drag_min
      delete newFilters.max_drag_max
      delete newFilters.reel_weight_min
      delete newFilters.reel_weight_max
      delete newFilters.gear_ratio
      delete newFilters.bearings_min
      delete newFilters.bearings_max
      // 清除鱼线专属
      delete newFilters.line_type
      delete newFilters.diameter_min
      delete newFilters.diameter_max
      delete newFilters.strength_min
      delete newFilters.strength_max
      // 清除拟饵专属
      delete newFilters.lure_category
      delete newFilters.lure_weight_min
      delete newFilters.lure_weight_max
      delete newFilters.diving_depth_min
      delete newFilters.diving_depth_max
      delete newFilters.lure_type
      delete newFilters.lure_length_min
      delete newFilters.lure_length_max
    }
    onChange(newFilters)
  }

  // 计算已选筛选标签
  const selectedTags = useMemo(() => {
    const tags: { key: string; label: string; value: string }[] = []

    if (filters.category) {
      tags.push({ key: 'category', label: '类别', value: filters.category })
    }
    if (filters.brand_id) {
      const brand = brands.find((b) => b.brand_id === filters.brand_id)
      if (brand) {
        tags.push({ key: 'brand_id', label: '品牌', value: brand.name_cn })
      }
    }
    if (filters.user_level) {
      tags.push({ key: 'user_level', label: '水平', value: filters.user_level })
    }
    if (filters.price_min !== undefined || filters.price_max !== undefined) {
      const priceLabel =
        filters.price_min !== undefined && filters.price_max !== undefined
          ? `¥${filters.price_min}-${filters.price_max}`
          : filters.price_min !== undefined
            ? `¥${filters.price_min}+`
            : `¥0-${filters.price_max}`
      tags.push({ key: 'price', label: '价格', value: priceLabel })
    }
    if (filters.is_active !== undefined) {
      tags.push({
        key: 'is_active',
        label: '状态',
        value: filters.is_active ? '启用' : '禁用',
      })
    }
    // 通用扩展筛选
    if (filters.source) {
      tags.push({
        key: 'source',
        label: '来源',
        value: DATA_SOURCE_LABELS[filters.source as keyof typeof DATA_SOURCE_LABELS] || filters.source,
      })
    }
    if (filters.model) {
      tags.push({ key: 'model', label: '型号', value: filters.model })
    }
    if (filters.created_after || filters.created_before) {
      const dateLabel =
        filters.created_after && filters.created_before
          ? `${filters.created_after.slice(0, 10)} ~ ${filters.created_before.slice(0, 10)}`
          : filters.created_after
            ? `${filters.created_after.slice(0, 10)}起`
            : `至${filters.created_before?.slice(0, 10)}`
      tags.push({ key: 'created_at', label: '创建时间', value: dateLabel })
    }
    // 鱼竿专属
    if (filters.power) {
      tags.push({ key: 'power', label: '调性', value: filters.power })
    }
    if (filters.action) {
      tags.push({ key: 'action', label: '动作', value: filters.action })
    }
    if (filters.length_min !== undefined || filters.length_max !== undefined) {
      const lengthLabel =
        filters.length_min !== undefined && filters.length_max !== undefined
          ? `${filters.length_min}-${filters.length_max}m`
          : filters.length_min !== undefined
            ? `${filters.length_min}m+`
            : `0-${filters.length_max}m`
      tags.push({ key: 'length', label: '竿长', value: lengthLabel })
    }
    if (filters.rod_lure_weight_min !== undefined || filters.rod_lure_weight_max !== undefined) {
      const lureWeightLabel =
        filters.rod_lure_weight_min !== undefined && filters.rod_lure_weight_max !== undefined
          ? `${filters.rod_lure_weight_min}-${filters.rod_lure_weight_max}g`
          : filters.rod_lure_weight_min !== undefined
            ? `${filters.rod_lure_weight_min}g+`
            : `0-${filters.rod_lure_weight_max}g`
      tags.push({ key: 'rod_lure_weight', label: '适用饵重', value: lureWeightLabel })
    }
    if (filters.sections !== undefined) {
      tags.push({ key: 'sections', label: '节数', value: `${filters.sections}节` })
    }
    // 渔轮专属
    if (filters.reel_type) {
      tags.push({
        key: 'reel_type',
        label: '轮类型',
        value: REEL_TYPE_LABELS[filters.reel_type] || filters.reel_type,
      })
    }
    if (filters.max_drag_min !== undefined || filters.max_drag_max !== undefined) {
      const dragLabel =
        filters.max_drag_min !== undefined && filters.max_drag_max !== undefined
          ? `${filters.max_drag_min}-${filters.max_drag_max}kg`
          : filters.max_drag_min !== undefined
            ? `${filters.max_drag_min}kg+`
            : `0-${filters.max_drag_max}kg`
      tags.push({ key: 'max_drag', label: '最大拽力', value: dragLabel })
    }
    if (filters.reel_weight_min !== undefined || filters.reel_weight_max !== undefined) {
      const weightLabel =
        filters.reel_weight_min !== undefined && filters.reel_weight_max !== undefined
          ? `${filters.reel_weight_min}-${filters.reel_weight_max}g`
          : filters.reel_weight_min !== undefined
            ? `${filters.reel_weight_min}g+`
            : `0-${filters.reel_weight_max}g`
      tags.push({ key: 'reel_weight', label: '轮自重', value: weightLabel })
    }
    // 鱼线专属
    if (filters.line_type) {
      tags.push({ key: 'line_type', label: '线型', value: filters.line_type })
    }
    if (filters.diameter_min !== undefined || filters.diameter_max !== undefined) {
      const diameterLabel =
        filters.diameter_min !== undefined && filters.diameter_max !== undefined
          ? `${filters.diameter_min}-${filters.diameter_max}mm`
          : filters.diameter_min !== undefined
            ? `${filters.diameter_min}mm+`
            : `0-${filters.diameter_max}mm`
      tags.push({ key: 'diameter', label: '线径', value: diameterLabel })
    }
    if (filters.strength_min !== undefined || filters.strength_max !== undefined) {
      const strengthLabel =
        filters.strength_min !== undefined && filters.strength_max !== undefined
          ? `${filters.strength_min}-${filters.strength_max}lb`
          : filters.strength_min !== undefined
            ? `${filters.strength_min}lb+`
            : `0-${filters.strength_max}lb`
      tags.push({ key: 'strength', label: '拉力', value: strengthLabel })
    }
    // 拟饵专属
    if (filters.lure_category) {
      tags.push({ key: 'lure_category', label: '拟饵分类', value: filters.lure_category })
    }
    if (filters.lure_weight_min !== undefined || filters.lure_weight_max !== undefined) {
      const lureWeightLabel =
        filters.lure_weight_min !== undefined && filters.lure_weight_max !== undefined
          ? `${filters.lure_weight_min}-${filters.lure_weight_max}g`
          : filters.lure_weight_min !== undefined
            ? `${filters.lure_weight_min}g+`
            : `0-${filters.lure_weight_max}g`
      tags.push({ key: 'lure_weight', label: '拟饵重量', value: lureWeightLabel })
    }
    if (filters.diving_depth_min !== undefined || filters.diving_depth_max !== undefined) {
      const depthLabel =
        filters.diving_depth_min !== undefined && filters.diving_depth_max !== undefined
          ? `${filters.diving_depth_min}-${filters.diving_depth_max}m`
          : filters.diving_depth_min !== undefined
            ? `${filters.diving_depth_min}m+`
            : `0-${filters.diving_depth_max}m`
      tags.push({ key: 'diving_depth', label: '潜深', value: depthLabel })
    }
    // 鱼竿扩展
    if (filters.rod_weight_min !== undefined || filters.rod_weight_max !== undefined) {
      const weightLabel =
        filters.rod_weight_min !== undefined && filters.rod_weight_max !== undefined
          ? `${filters.rod_weight_min}-${filters.rod_weight_max}g`
          : filters.rod_weight_min !== undefined
            ? `${filters.rod_weight_min}g+`
            : `0-${filters.rod_weight_max}g`
      tags.push({ key: 'rod_weight', label: '竿自重', value: weightLabel })
    }
    if (filters.guide_type) {
      tags.push({ key: 'guide_type', label: '导环类型', value: filters.guide_type })
    }
    if (filters.handle_type) {
      tags.push({ key: 'handle_type', label: '握把类型', value: filters.handle_type })
    }
    // 渔轮扩展
    if (filters.gear_ratio) {
      tags.push({ key: 'gear_ratio', label: '齿比', value: filters.gear_ratio })
    }
    if (filters.bearings_min !== undefined || filters.bearings_max !== undefined) {
      const bearingsLabel =
        filters.bearings_min !== undefined && filters.bearings_max !== undefined
          ? `${filters.bearings_min}-${filters.bearings_max}个`
          : filters.bearings_min !== undefined
            ? `${filters.bearings_min}个+`
            : `0-${filters.bearings_max}个`
      tags.push({ key: 'bearings', label: '轴承数', value: bearingsLabel })
    }
    // 拟饵扩展
    if (filters.lure_type) {
      tags.push({ key: 'lure_type', label: '拟饵类型', value: filters.lure_type })
    }
    if (filters.lure_length_min !== undefined || filters.lure_length_max !== undefined) {
      const lengthLabel =
        filters.lure_length_min !== undefined && filters.lure_length_max !== undefined
          ? `${filters.lure_length_min}-${filters.lure_length_max}cm`
          : filters.lure_length_min !== undefined
            ? `${filters.lure_length_min}cm+`
            : `0-${filters.lure_length_max}cm`
      tags.push({ key: 'lure_length', label: '拟饵长度', value: lengthLabel })
    }
    // 排序
    if (filters.sort_by) {
      const sortLabels: Record<string, string> = {
        name: '名称',
        price_min: '最低价',
        price_max: '最高价',
        created_at: '创建时间',
        updated_at: '更新时间',
      }
      const orderLabel = filters.sort_order === 'asc' ? '升序' : '降序'
      tags.push({ key: 'sort', label: '排序', value: `${sortLabels[filters.sort_by] || filters.sort_by} ${orderLabel}` })
    }

    return tags
  }, [filters, brands])

  // 移除单个筛选
  const handleRemoveTag = (key: string) => {
    const newFilters = { ...filters }
    // 范围类型筛选需要同时清除 min 和 max
    const rangeKeys: Record<string, (keyof EquipmentSearchFilters)[]> = {
      price: ['price_min', 'price_max'],
      length: ['length_min', 'length_max'],
      rod_lure_weight: ['rod_lure_weight_min', 'rod_lure_weight_max'],
      max_drag: ['max_drag_min', 'max_drag_max'],
      reel_weight: ['reel_weight_min', 'reel_weight_max'],
      diameter: ['diameter_min', 'diameter_max'],
      strength: ['strength_min', 'strength_max'],
      lure_weight: ['lure_weight_min', 'lure_weight_max'],
      diving_depth: ['diving_depth_min', 'diving_depth_max'],
      created_at: ['created_after', 'created_before'],
      // 新增扩展
      rod_weight: ['rod_weight_min', 'rod_weight_max'],
      bearings: ['bearings_min', 'bearings_max'],
      lure_length: ['lure_length_min', 'lure_length_max'],
      sort: ['sort_by', 'sort_order'],
    }

    if (rangeKeys[key]) {
      rangeKeys[key].forEach((k) => delete newFilters[k])
    } else {
      delete newFilters[key as keyof EquipmentSearchFilters]
    }
    onChange(newFilters)
  }

  // 类别专属筛选显示控制
  const showRodFilters = filters.category === '鱼竿'
  const showReelFilters = filters.category === '渔轮'
  const showLineFilters = filters.category === '鱼线'
  const showLureFilters = filters.category === '拟饵'

  return (
    <div style={{ marginBottom: 16 }}>
      {/* 基础搜索栏 */}
      <Row gutter={[12, 12]} align="middle">
        <Col>
          <Select
            placeholder="选择类别"
            style={{ width: 120 }}
            allowClear
            value={filters.category}
            onChange={(value) => handleChange('category', value)}
            options={EQUIPMENT_CATEGORIES.map((cat) => ({
              label: cat,
              value: cat,
            }))}
          />
        </Col>
        <Col>
          <Select
            placeholder="选择品牌"
            style={{ width: 140 }}
            allowClear
            showSearch
            optionFilterProp="label"
            value={filters.brand_id}
            onChange={(value) => handleChange('brand_id', value)}
            options={brands.map((brand) => ({
              label: brand.name_cn,
              value: brand.brand_id,
            }))}
          />
        </Col>
        <Col flex="auto">
          <Search
            placeholder="搜索装备名称、描述..."
            allowClear
            value={filters.keyword}
            onChange={(e) => handleChange('keyword', e.target.value)}
            onSearch={onSearch}
            style={{ maxWidth: 300 }}
          />
        </Col>
        <Col>
          <Space>
            <Button
              icon={expanded ? <UpOutlined /> : <DownOutlined />}
              onClick={() => setExpanded(!expanded)}
            >
              <FilterOutlined /> 高级筛选
            </Button>
            <Button icon={<ReloadOutlined />} onClick={onReset}>
              重置
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 高级筛选面板 */}
      <Collapse
        activeKey={expanded ? ['advanced'] : []}
        ghost
        items={[
          {
            key: 'advanced',
            showArrow: false,
            label: null,
            children: (
              <div
                style={{
                  background: '#fafafa',
                  padding: 16,
                  borderRadius: 8,
                  marginTop: 12,
                }}
              >
                {/* 通用高级筛选 - 第一行 */}
                <Row gutter={[16, 16]} align="middle">
                  <Col>
                    <span style={{ marginRight: 8 }}>价格:</span>
                    <InputNumber
                      placeholder="最低"
                      style={{ width: 100 }}
                      min={0}
                      prefix="¥"
                      value={filters.price_min}
                      onChange={(value) => handleChange('price_min', value)}
                    />
                    <span style={{ margin: '0 8px' }}>~</span>
                    <InputNumber
                      placeholder="最高"
                      style={{ width: 100 }}
                      min={0}
                      prefix="¥"
                      value={filters.price_max}
                      onChange={(value) => handleChange('price_max', value)}
                    />
                  </Col>
                  <Col>
                    <span style={{ marginRight: 8 }}>适用水平:</span>
                    <Select
                      placeholder="选择"
                      style={{ width: 100 }}
                      allowClear
                      value={filters.user_level}
                      onChange={(value) => handleChange('user_level', value)}
                      options={USER_LEVELS.map((level) => ({
                        label: level,
                        value: level,
                      }))}
                    />
                  </Col>
                  <Col>
                    <span style={{ marginRight: 8 }}>状态:</span>
                    <Segmented
                      value={
                        filters.is_active === undefined
                          ? 'all'
                          : filters.is_active
                            ? 'active'
                            : 'inactive'
                      }
                      onChange={(value) => {
                        if (value === 'all') {
                          handleChange('is_active', undefined)
                        } else {
                          handleChange('is_active', value === 'active')
                        }
                      }}
                      options={[
                        { label: '全部', value: 'all' },
                        { label: '启用', value: 'active' },
                        { label: '禁用', value: 'inactive' },
                      ]}
                    />
                  </Col>
                </Row>

                {/* 通用高级筛选 - 第二行（扩展） */}
                <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                  <Col>
                    <span style={{ marginRight: 8 }}>型号:</span>
                    <Input
                      placeholder="输入型号"
                      style={{ width: 140 }}
                      allowClear
                      value={filters.model}
                      onChange={(e) => handleChange('model', e.target.value)}
                    />
                  </Col>
                  <Col>
                    <span style={{ marginRight: 8 }}>来源:</span>
                    <Select
                      placeholder="选择"
                      style={{ width: 120 }}
                      allowClear
                      value={filters.source}
                      onChange={(value) => handleChange('source', value)}
                      options={DATA_SOURCES.map((s) => ({
                        label: DATA_SOURCE_LABELS[s],
                        value: s,
                      }))}
                    />
                  </Col>
                  <Col>
                    <span style={{ marginRight: 8 }}>创建时间:</span>
                    <RangePicker
                      value={
                        filters.created_after || filters.created_before
                          ? [
                              filters.created_after ? dayjs(filters.created_after) : null,
                              filters.created_before ? dayjs(filters.created_before) : null,
                            ]
                          : null
                      }
                      onChange={(dates) => {
                        if (dates && dates[0] && dates[1]) {
                          handleChange('created_after', dates[0].format('YYYY-MM-DD'))
                          // 设置 created_before 时需要单独调用
                          const newFilters = {
                            ...filters,
                            created_after: dates[0].format('YYYY-MM-DD'),
                            created_before: dates[1].format('YYYY-MM-DD'),
                          }
                          onChange(newFilters)
                        } else {
                          const newFilters = { ...filters }
                          delete newFilters.created_after
                          delete newFilters.created_before
                          onChange(newFilters)
                        }
                      }}
                      style={{ width: 240 }}
                    />
                  </Col>
                  <Col>
                    <span style={{ marginRight: 8 }}>排序:</span>
                    <Select
                      placeholder="排序字段"
                      style={{ width: 120 }}
                      allowClear
                      value={filters.sort_by}
                      onChange={(value) => handleChange('sort_by', value)}
                      options={[
                        { label: '名称', value: 'name' },
                        { label: '最低价', value: 'price_min' },
                        { label: '最高价', value: 'price_max' },
                        { label: '创建时间', value: 'created_at' },
                        { label: '更新时间', value: 'updated_at' },
                      ]}
                    />
                    <Select
                      style={{ width: 80, marginLeft: 4 }}
                      value={filters.sort_order || 'desc'}
                      onChange={(value) => handleChange('sort_order', value)}
                      options={[
                        { label: '降序', value: 'desc' },
                        { label: '升序', value: 'asc' },
                      ]}
                    />
                  </Col>
                </Row>

                {/* 鱼竿专属筛选 */}
                {showRodFilters && (
                  <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px dashed #d9d9d9' }}>
                    <div style={{ color: '#666', marginBottom: 12 }}>
                      -- 鱼竿专属筛选 --
                    </div>
                    <Row gutter={[16, 16]} align="middle">
                      <Col>
                        <span style={{ marginRight: 8 }}>调性:</span>
                        <Segmented
                          value={filters.power || ''}
                          onChange={(value) =>
                            handleChange('power', value || undefined)
                          }
                          options={[
                            { label: '全部', value: '' },
                            ...ROD_POWERS.map((p) => ({ label: p, value: p })),
                          ]}
                        />
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>动作:</span>
                        <Segmented
                          value={filters.action || ''}
                          onChange={(value) =>
                            handleChange('action', value || undefined)
                          }
                          options={[
                            { label: '全部', value: '' },
                            ...ROD_ACTIONS.map((a) => ({ label: a, value: a })),
                          ]}
                        />
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                      <Col>
                        <span style={{ marginRight: 8 }}>竿长:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          max={10}
                          step={0.1}
                          value={filters.length_min}
                          onChange={(value) => handleChange('length_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          max={10}
                          step={0.1}
                          value={filters.length_max}
                          onChange={(value) => handleChange('length_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>米</span>
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>节数:</span>
                        <Select
                          placeholder="选择"
                          style={{ width: 100 }}
                          allowClear
                          value={filters.sections}
                          onChange={(value) => handleChange('sections', value)}
                          options={ROD_SECTIONS.map((s) => ({
                            label: `${s}节`,
                            value: s,
                          }))}
                        />
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>适用饵重:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={1}
                          value={filters.rod_lure_weight_min}
                          onChange={(value) => handleChange('rod_lure_weight_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={1}
                          value={filters.rod_lure_weight_max}
                          onChange={(value) => handleChange('rod_lure_weight_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>g</span>
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>竿自重:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={10}
                          value={filters.rod_weight_min}
                          onChange={(value) => handleChange('rod_weight_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={10}
                          value={filters.rod_weight_max}
                          onChange={(value) => handleChange('rod_weight_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>g</span>
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                      <Col>
                        <span style={{ marginRight: 8 }}>导环类型:</span>
                        <Select
                          placeholder="选择"
                          style={{ width: 120 }}
                          allowClear
                          value={filters.guide_type}
                          onChange={(value) => handleChange('guide_type', value)}
                          options={[
                            { label: 'Fuji', value: 'Fuji' },
                            { label: 'SiC', value: 'SiC' },
                            { label: '钛合金', value: '钛合金' },
                            { label: '不锈钢', value: '不锈钢' },
                          ]}
                        />
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>握把类型:</span>
                        <Select
                          placeholder="选择"
                          style={{ width: 120 }}
                          allowClear
                          value={filters.handle_type}
                          onChange={(value) => handleChange('handle_type', value)}
                          options={[
                            { label: 'EVA', value: 'EVA' },
                            { label: '软木', value: '软木' },
                            { label: '碳布', value: '碳布' },
                            { label: '直柄', value: '直柄' },
                            { label: '枪柄', value: '枪柄' },
                          ]}
                        />
                      </Col>
                    </Row>
                  </div>
                )}

                {/* 渔轮专属筛选 */}
                {showReelFilters && (
                  <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px dashed #d9d9d9' }}>
                    <div style={{ color: '#666', marginBottom: 12 }}>
                      -- 渔轮专属筛选 --
                    </div>
                    <Row gutter={[16, 16]} align="middle">
                      <Col>
                        <span style={{ marginRight: 8 }}>轮类型:</span>
                        <Segmented
                          value={filters.reel_type || ''}
                          onChange={(value) =>
                            handleChange('reel_type', value || undefined)
                          }
                          options={[
                            { label: '全部', value: '' },
                            ...REEL_TYPES.map((t) => ({
                              label: REEL_TYPE_LABELS[t] || t,
                              value: t,
                            })),
                          ]}
                        />
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                      <Col>
                        <span style={{ marginRight: 8 }}>最大拽力:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={0.5}
                          value={filters.max_drag_min}
                          onChange={(value) => handleChange('max_drag_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={0.5}
                          value={filters.max_drag_max}
                          onChange={(value) => handleChange('max_drag_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>kg</span>
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>轮自重:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={10}
                          value={filters.reel_weight_min}
                          onChange={(value) => handleChange('reel_weight_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={10}
                          value={filters.reel_weight_max}
                          onChange={(value) => handleChange('reel_weight_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>g</span>
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                      <Col>
                        <span style={{ marginRight: 8 }}>齿比:</span>
                        <Select
                          placeholder="选择"
                          style={{ width: 120 }}
                          allowClear
                          value={filters.gear_ratio}
                          onChange={(value) => handleChange('gear_ratio', value)}
                          options={[
                            { label: '4.7:1', value: '4.7:1' },
                            { label: '5.2:1', value: '5.2:1' },
                            { label: '5.5:1', value: '5.5:1' },
                            { label: '6.2:1', value: '6.2:1' },
                            { label: '6.4:1', value: '6.4:1' },
                            { label: '7.1:1', value: '7.1:1' },
                            { label: '7.3:1', value: '7.3:1' },
                            { label: '8.1:1', value: '8.1:1' },
                          ]}
                        />
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>轴承数:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 70 }}
                          min={0}
                          max={20}
                          value={filters.bearings_min}
                          onChange={(value) => handleChange('bearings_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 70 }}
                          min={0}
                          max={20}
                          value={filters.bearings_max}
                          onChange={(value) => handleChange('bearings_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>个</span>
                      </Col>
                    </Row>
                  </div>
                )}

                {/* 鱼线专属筛选 */}
                {showLineFilters && (
                  <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px dashed #d9d9d9' }}>
                    <div style={{ color: '#666', marginBottom: 12 }}>
                      -- 鱼线专属筛选 --
                    </div>
                    <Row gutter={[16, 16]} align="middle">
                      <Col>
                        <span style={{ marginRight: 8 }}>线型:</span>
                        <Segmented
                          value={filters.line_type || ''}
                          onChange={(value) =>
                            handleChange('line_type', value || undefined)
                          }
                          options={[
                            { label: '全部', value: '' },
                            ...LINE_TYPES.map((t) => ({ label: t, value: t })),
                          ]}
                        />
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                      <Col>
                        <span style={{ marginRight: 8 }}>线径:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={0.01}
                          value={filters.diameter_min}
                          onChange={(value) => handleChange('diameter_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={0.01}
                          value={filters.diameter_max}
                          onChange={(value) => handleChange('diameter_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>mm</span>
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>拉力:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={1}
                          value={filters.strength_min}
                          onChange={(value) => handleChange('strength_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={1}
                          value={filters.strength_max}
                          onChange={(value) => handleChange('strength_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>lb</span>
                      </Col>
                    </Row>
                  </div>
                )}

                {/* 拟饵专属筛选 */}
                {showLureFilters && (
                  <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px dashed #d9d9d9' }}>
                    <div style={{ color: '#666', marginBottom: 12 }}>
                      -- 拟饵专属筛选 --
                    </div>
                    <Row gutter={[16, 16]} align="middle">
                      <Col>
                        <span style={{ marginRight: 8 }}>分类:</span>
                        <Segmented
                          value={filters.lure_category || ''}
                          onChange={(value) =>
                            handleChange('lure_category', value || undefined)
                          }
                          options={[
                            { label: '全部', value: '' },
                            ...LURE_CATEGORIES.map((c) => ({ label: c, value: c })),
                          ]}
                        />
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                      <Col>
                        <span style={{ marginRight: 8 }}>重量:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={1}
                          value={filters.lure_weight_min}
                          onChange={(value) => handleChange('lure_weight_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={1}
                          value={filters.lure_weight_max}
                          onChange={(value) => handleChange('lure_weight_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>g</span>
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>潜深:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={0.5}
                          value={filters.diving_depth_min}
                          onChange={(value) => handleChange('diving_depth_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={0.5}
                          value={filters.diving_depth_max}
                          onChange={(value) => handleChange('diving_depth_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>m</span>
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} align="middle" style={{ marginTop: 12 }}>
                      <Col>
                        <span style={{ marginRight: 8 }}>拟饵类型:</span>
                        <Select
                          placeholder="选择"
                          style={{ width: 140 }}
                          allowClear
                          value={filters.lure_type}
                          onChange={(value) => handleChange('lure_type', value)}
                          options={[
                            { label: 'Crankbait', value: 'crankbait' },
                            { label: 'Jerkbait', value: 'jerkbait' },
                            { label: 'Topwater', value: 'topwater' },
                            { label: 'Spinnerbait', value: 'spinnerbait' },
                            { label: 'Jig', value: 'jig' },
                            { label: 'Swimbait', value: 'swimbait' },
                            { label: 'Worm', value: 'worm' },
                            { label: 'Creature', value: 'creature' },
                            { label: 'Spoon', value: 'spoon' },
                            { label: 'Blade', value: 'blade' },
                          ]}
                        />
                      </Col>
                      <Col>
                        <span style={{ marginRight: 8 }}>长度:</span>
                        <InputNumber
                          placeholder="最小"
                          style={{ width: 80 }}
                          min={0}
                          step={0.5}
                          value={filters.lure_length_min}
                          onChange={(value) => handleChange('lure_length_min', value)}
                        />
                        <span style={{ margin: '0 8px' }}>~</span>
                        <InputNumber
                          placeholder="最大"
                          style={{ width: 80 }}
                          min={0}
                          step={0.5}
                          value={filters.lure_length_max}
                          onChange={(value) => handleChange('lure_length_max', value)}
                        />
                        <span style={{ marginLeft: 4 }}>cm</span>
                      </Col>
                    </Row>
                  </div>
                )}
              </div>
            ),
          },
        ]}
      />

      {/* 已选筛选标签 */}
      {selectedTags.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <span style={{ marginRight: 8, color: '#666' }}>已选:</span>
          {selectedTags.map((tag) => (
            <Tag
              key={tag.key}
              closable
              onClose={() => handleRemoveTag(tag.key)}
              style={{ marginBottom: 4 }}
            >
              {tag.label}: {tag.value}
            </Tag>
          ))}
          {selectedTags.length > 1 && (
            <Button type="link" size="small" onClick={onReset}>
              清空全部
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

export default AdvancedSearch
