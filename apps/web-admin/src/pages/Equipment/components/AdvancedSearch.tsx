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
} from '@/types/equipment'

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
    // 如果类别变了且不是鱼竿，清除鱼竿专属筛选
    if (key === 'category' && value !== '鱼竿') {
      delete newFilters.power
      delete newFilters.action
      delete newFilters.length_min
      delete newFilters.length_max
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

    return tags
  }, [filters, brands])

  // 移除单个筛选
  const handleRemoveTag = (key: string) => {
    const newFilters = { ...filters }
    if (key === 'price') {
      delete newFilters.price_min
      delete newFilters.price_max
    } else if (key === 'length') {
      delete newFilters.length_min
      delete newFilters.length_max
    } else {
      delete newFilters[key as keyof EquipmentSearchFilters]
    }
    onChange(newFilters)
  }

  // 是否显示鱼竿专属筛选
  const showRodFilters = filters.category === '鱼竿'

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
                {/* 通用高级筛选 */}
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
