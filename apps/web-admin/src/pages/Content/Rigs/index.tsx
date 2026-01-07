/**
 * Rig Configuration Page - Jobs-style minimalist design
 * Hybrid mode: Featured cards at top + Full table below
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Row,
  Col,
  Table,
  Button,
  Input,
  Select,
  Space,
  Typography,
  Tag,
  Popconfirm,
  message,
  Spin,
  Empty,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import { rigApi, type RigListParams } from '@/api/services/rig'
import type { RigListItem, RigCategory, RigDifficulty } from '@/types/rig'
import { RIG_CATEGORY_CONFIG, RIG_DIFFICULTY_CONFIG } from '@/types/rig'
import RigCard from './RigCard'
import RigDrawer from './RigDrawer'

const { Title, Text } = Typography

const RigList: React.FC = () => {
  // State
  const [loading, setLoading] = useState(false)
  const [featuredLoading, setFeaturedLoading] = useState(false)
  const [rigs, setRigs] = useState<RigListItem[]>([])
  const [featuredRigs, setFeaturedRigs] = useState<RigListItem[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<RigListParams>({
    page: 1,
    page_size: 10,
  })
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingRigId, setEditingRigId] = useState<number | null>(null)

  // Load featured rigs
  const loadFeatured = useCallback(async () => {
    setFeaturedLoading(true)
    try {
      const data = await rigApi.getFeatured(4)
      setFeaturedRigs(data)
    } catch {
      // Ignore error for featured
    } finally {
      setFeaturedLoading(false)
    }
  }, [])

  // Load rigs list
  const loadRigs = useCallback(async () => {
    setLoading(true)
    try {
      const response = await rigApi.list(filters)
      setRigs(response.items)
      setTotal(response.total)
    } catch {
      message.error('加载钓组列表失败')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadFeatured()
  }, [loadFeatured])

  useEffect(() => {
    loadRigs()
  }, [loadRigs])

  // Handle filter changes
  const handleSearch = (keyword: string) => {
    setFilters(prev => ({ ...prev, keyword, page: 1 }))
  }

  const handleCategoryChange = (category: RigCategory | undefined) => {
    setFilters(prev => ({ ...prev, category, page: 1 }))
  }

  const handleDifficultyChange = (difficulty: RigDifficulty | undefined) => {
    setFilters(prev => ({ ...prev, difficulty, page: 1 }))
  }

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setFilters(prev => ({
      ...prev,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 10,
    }))
  }

  // Handle actions
  const handleCreate = () => {
    setEditingRigId(null)
    setDrawerOpen(true)
  }

  const handleEdit = (rig: RigListItem) => {
    setEditingRigId(rig.rig_id)
    setDrawerOpen(true)
  }

  const handleDelete = async (rigId: number) => {
    try {
      await rigApi.delete(rigId)
      message.success('删除成功')
      loadRigs()
      loadFeatured()
    } catch {
      message.error('删除失败')
    }
  }

  const handleDrawerClose = () => {
    setDrawerOpen(false)
    setEditingRigId(null)
  }

  const handleDrawerSuccess = () => {
    loadRigs()
    loadFeatured()
  }

  // Table columns
  const columns: ColumnsType<RigListItem> = [
    {
      title: '钓组名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Space>
          <Text strong style={{ cursor: 'pointer' }} onClick={() => handleEdit(record)}>
            {name}
          </Text>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: RigCategory) => {
        const config = RIG_CATEGORY_CONFIG[category] || { label: category, color: 'default', icon: '' }
        return (
          <Tag color={config.color} style={{ borderRadius: 8, border: 'none' }}>
            {config.icon} {config.label}
          </Tag>
        )
      },
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 80,
      render: (difficulty: RigDifficulty) => {
        const config = RIG_DIFFICULTY_CONFIG[difficulty] || { label: difficulty, color: 'default' }
        return (
          <Tag color={config.color} style={{ borderRadius: 8, border: 'none' }}>
            {config.label}
          </Tag>
        )
      },
    },
    {
      title: '目标鱼种',
      dataIndex: 'target_species',
      key: 'target_species',
      width: 150,
      ellipsis: true,
      render: (species) => species || '-',
    },
    {
      title: '组件',
      dataIndex: 'component_count',
      key: 'component_count',
      width: 70,
      align: 'center',
      render: (count) => (
        <Text type="secondary">{count}</Text>
      ),
    },
    {
      title: '规格',
      dataIndex: 'spec_count',
      key: 'spec_count',
      width: 70,
      align: 'center',
      render: (count) => (
        <Text type="secondary">{count}</Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size={0}>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定删除此钓组？"
            description="关联的组件和规格将一并删除"
            onConfirm={() => handleDelete(record.rig_id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Category options for filter
  const categoryOptions = [
    { value: '', label: '全部分类' },
    ...Object.entries(RIG_CATEGORY_CONFIG).map(([value, config]) => ({
      value,
      label: `${config.icon} ${config.label}`,
    })),
  ]

  // Difficulty options for filter
  const difficultyOptions = [
    { value: '', label: '全部难度' },
    ...Object.entries(RIG_DIFFICULTY_CONFIG).map(([value, config]) => ({
      value,
      label: config.label,
    })),
  ]

  return (
    <div style={{ padding: '24px 0' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 32,
        }}
      >
        <div>
          <Title level={4} style={{ margin: 0 }}>
            钓组配置
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            管理各类钓组的组件配件和规格参数
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建钓组
        </Button>
      </div>

      {/* Featured Cards */}
      <div style={{ marginBottom: 40 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
          }}
        >
          <Text strong style={{ fontSize: 16, color: '#1a1a1a' }}>
            精选钓组
          </Text>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={loadFeatured}
            loading={featuredLoading}
          >
            刷新
          </Button>
        </div>

        <Spin spinning={featuredLoading}>
          {featuredRigs.length > 0 ? (
            <Row gutter={[20, 20]}>
              {featuredRigs.map(rig => (
                <Col xs={24} sm={12} md={8} lg={6} key={rig.rig_id}>
                  <RigCard rig={rig} onClick={handleEdit} />
                </Col>
              ))}
            </Row>
          ) : (
            <div
              style={{
                background: '#fafafa',
                borderRadius: 12,
                padding: '40px 0',
              }}
            >
              <Empty
                description="暂无钓组数据"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" onClick={handleCreate}>
                  创建第一个钓组
                </Button>
              </Empty>
            </div>
          )}
        </Spin>
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 20,
          flexWrap: 'wrap',
        }}
      >
        <Input.Search
          placeholder="搜索钓组名称..."
          allowClear
          onSearch={handleSearch}
          style={{ width: 240 }}
          prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
        />
        <Select
          placeholder="全部分类"
          style={{ width: 140 }}
          options={categoryOptions}
          value={filters.category || ''}
          onChange={(v) => handleCategoryChange((v || undefined) as RigCategory | undefined)}
          allowClear
        />
        <Select
          placeholder="全部难度"
          style={{ width: 120 }}
          options={difficultyOptions}
          value={filters.difficulty || ''}
          onChange={(v) => handleDifficultyChange((v || undefined) as RigDifficulty | undefined)}
          allowClear
        />
      </div>

      {/* Table */}
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          overflow: 'hidden',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        }}
      >
        <Table
          columns={columns}
          dataSource={rigs}
          rowKey="rig_id"
          loading={loading}
          pagination={{
            current: filters.page,
            pageSize: filters.page_size,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
          }}
          onChange={handleTableChange}
        />
      </div>

      {/* Drawer */}
      <RigDrawer
        open={drawerOpen}
        rigId={editingRigId}
        onClose={handleDrawerClose}
        onSuccess={handleDrawerSuccess}
      />
    </div>
  )
}

export default RigList
