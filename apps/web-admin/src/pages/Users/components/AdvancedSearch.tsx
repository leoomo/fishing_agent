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
  DatePicker,
} from 'antd'
import {
  FilterOutlined,
  ReloadOutlined,
  DownOutlined,
  UpOutlined,
} from '@ant-design/icons'
import type { UserSearchFilters } from '@/types/user'
import { USER_LEVELS, FISHING_METHODS } from '@/types/user'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Search } = Input

interface AdvancedSearchProps {
  filters: UserSearchFilters
  loading?: boolean
  onChange: (filters: UserSearchFilters) => void
  onSearch: () => void
  onReset: () => void
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  filters,
  loading: _loading,
  onChange,
  onSearch,
  onReset,
}) => {
  const [expanded, setExpanded] = useState(false)

  // 处理筛选变更
  const handleChange = (key: keyof UserSearchFilters, value: unknown) => {
    const newFilters = { ...filters, [key]: value || undefined }
    onChange(newFilters)
  }

  // 计算已选筛选标签
  const selectedTags = useMemo(() => {
    const tags: { key: string; label: string; value: string }[] = []

    if (filters.keyword) {
      tags.push({ key: 'keyword', label: '关键词', value: filters.keyword })
    }
    if (filters.user_level) {
      tags.push({ key: 'user_level', label: '用户水平', value: filters.user_level })
    }
    if (filters.preferred_fishing_method) {
      tags.push({
        key: 'preferred_fishing_method',
        label: '偏好钓法',
        value: filters.preferred_fishing_method,
      })
    }
    if (
      filters.fishing_experience_min !== undefined ||
      filters.fishing_experience_max !== undefined
    ) {
      const expLabel =
        filters.fishing_experience_min !== undefined &&
        filters.fishing_experience_max !== undefined
          ? `${filters.fishing_experience_min}-${filters.fishing_experience_max}年`
          : filters.fishing_experience_min !== undefined
            ? `${filters.fishing_experience_min}年+`
            : `0-${filters.fishing_experience_max}年`
      tags.push({ key: 'fishing_experience', label: '钓龄', value: expLabel })
    }
    if (filters.created_after || filters.created_before) {
      const dateLabel =
        filters.created_after && filters.created_before
          ? `${filters.created_after.slice(0, 10)} ~ ${filters.created_before.slice(0, 10)}`
          : filters.created_after
            ? `${filters.created_after.slice(0, 10)}起`
            : `至${filters.created_before?.slice(0, 10)}`
      tags.push({ key: 'created_at', label: '注册时间', value: dateLabel })
    }

    return tags
  }, [filters])

  // 移除单个筛选
  const handleRemoveTag = (key: string) => {
    const newFilters = { ...filters }
    const rangeKeys: Record<string, (keyof UserSearchFilters)[]> = {
      fishing_experience: ['fishing_experience_min', 'fishing_experience_max'],
      created_at: ['created_after', 'created_before'],
    }

    if (rangeKeys[key]) {
      rangeKeys[key].forEach((k) => delete newFilters[k])
    } else {
      delete newFilters[key as keyof UserSearchFilters]
    }
    onChange(newFilters)
  }

  return (
    <div style={{ marginBottom: 16 }}>
      {/* 基础搜索栏 */}
      <Row gutter={[12, 12]} align="middle">
        <Col>
          <Select
            placeholder="用户水平"
            style={{ width: 120 }}
            allowClear
            value={filters.user_level}
            onChange={(value) => handleChange('user_level', value)}
            options={USER_LEVELS.map((level) => ({
              label: level,
              value: level,
            }))}
          />
        </Col>
        <Col flex="auto">
          <Search
            placeholder="搜索用户名、邮箱、手机..."
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
                <Row gutter={[16, 16]} align="middle">
                  <Col>
                    <span style={{ marginRight: 8 }}>钓龄:</span>
                    <InputNumber
                      placeholder="最小"
                      style={{ width: 80 }}
                      min={0}
                      max={100}
                      value={filters.fishing_experience_min}
                      onChange={(value) =>
                        handleChange('fishing_experience_min', value)
                      }
                    />
                    <span style={{ margin: '0 8px' }}>~</span>
                    <InputNumber
                      placeholder="最大"
                      style={{ width: 80 }}
                      min={0}
                      max={100}
                      value={filters.fishing_experience_max}
                      onChange={(value) =>
                        handleChange('fishing_experience_max', value)
                      }
                    />
                    <span style={{ marginLeft: 4 }}>年</span>
                  </Col>
                  <Col>
                    <span style={{ marginRight: 8 }}>偏好钓法:</span>
                    <Select
                      placeholder="选择"
                      style={{ width: 120 }}
                      allowClear
                      value={filters.preferred_fishing_method}
                      onChange={(value) =>
                        handleChange('preferred_fishing_method', value)
                      }
                      options={FISHING_METHODS.map((method) => ({
                        label: method,
                        value: method,
                      }))}
                    />
                  </Col>
                  <Col>
                    <span style={{ marginRight: 8 }}>注册时间:</span>
                    <RangePicker
                      value={
                        filters.created_after || filters.created_before
                          ? [
                              filters.created_after
                                ? dayjs(filters.created_after)
                                : null,
                              filters.created_before
                                ? dayjs(filters.created_before)
                                : null,
                            ]
                          : null
                      }
                      onChange={(dates) => {
                        if (dates && dates[0] && dates[1]) {
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
                </Row>
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
