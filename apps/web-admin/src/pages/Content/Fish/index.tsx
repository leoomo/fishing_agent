/**
 * 鱼百科管理页面 - 乔布斯简洁风格
 *
 * 功能：
 * - 顶部：分类统计卡片（淡水鱼/海水鱼/广盐鱼）
 * - 下方：完整表格（分类筛选 + 搜索 + CRUD）
 * - 空数据：显示"初始化数据"按钮
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
  DatabaseOutlined,
  CloudDownloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import { fishApi } from '@/api/services/fish'
import type {
  FishSpeciesListItem,
  FishCategory,
  FishCategoryStats,
  FishSpeciesListParams,
} from '@/types/fish'
import { FISH_CATEGORY_CONFIG, FISH_CATEGORY_OPTIONS } from '@/types/fish'
import FishCard from './FishCard'
import FishDrawer from './FishDrawer'
import FetchModal from './FetchModal'
import FishDetailModal from './FishDetailModal'

const { Title, Text } = Typography

const FishList: React.FC = () => {
  // State
  const [loading, setLoading] = useState(false)
  const [statsLoading, setStatsLoading] = useState(false)
  const [initLoading, setInitLoading] = useState(false)
  const [fishes, setFishes] = useState<FishSpeciesListItem[]>([])
  const [categoryStats, setCategoryStats] = useState<FishCategoryStats[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<FishSpeciesListParams>({
    page: 1,
    page_size: 10,
  })
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingSpeciesId, setEditingSpeciesId] = useState<number | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<FishCategory | null>(null)
  const [fetchModalOpen, setFetchModalOpen] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [batchDeleting, setBatchDeleting] = useState(false)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [viewingSpeciesId, setViewingSpeciesId] = useState<number | null>(null)

  // Load category stats
  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    try {
      const data = await fishApi.getStats()
      setCategoryStats(data.categories)
      setTotal(data.total)
    } catch {
      // Ignore error for stats
    } finally {
      setStatsLoading(false)
    }
  }, [])

  // Load fish list
  const loadFishes = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fishApi.list(filters)
      setFishes(response.items)
      setTotal(response.total)
    } catch {
      message.error('加载鱼种列表失败')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  useEffect(() => {
    loadFishes()
  }, [loadFishes])

  // Handle filter changes
  const handleSearch = (keyword: string) => {
    setFilters((prev) => ({ ...prev, keyword, page: 1 }))
  }

  const handleCategoryChange = (category: FishCategory | undefined) => {
    setFilters((prev) => ({ ...prev, category, page: 1 }))
    setSelectedCategory(category || null)
  }

  const handleHabitatChange = (habitat: string | undefined) => {
    setFilters((prev) => ({ ...prev, habitat, page: 1 }))
  }

  const handleCardClick = (category: FishCategory | null) => {
    if (selectedCategory === category) {
      // 取消选择
      setSelectedCategory(null)
      setFilters((prev) => ({ ...prev, category: undefined, page: 1 }))
    } else {
      setSelectedCategory(category)
      setFilters((prev) => ({ ...prev, category: category || undefined, page: 1 }))
    }
  }

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setFilters((prev) => ({
      ...prev,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 10,
    }))
  }

  // Handle actions
  const handleCreate = () => {
    setEditingSpeciesId(null)
    setDrawerOpen(true)
  }

  const handleView = (fish: FishSpeciesListItem) => {
    setViewingSpeciesId(fish.species_id)
    setDetailModalOpen(true)
  }

  const handleEdit = (fish: FishSpeciesListItem) => {
    setEditingSpeciesId(fish.species_id)
    setDrawerOpen(true)
  }

  const handleEditFromDetail = () => {
    setDetailModalOpen(false)
    setEditingSpeciesId(viewingSpeciesId)
    setDrawerOpen(true)
  }

  const handleDelete = async (speciesId: number) => {
    try {
      await fishApi.delete(speciesId)
      message.success('删除成功')
      loadFishes()
      loadStats()
    } catch {
      message.error('删除失败')
    }
  }

  const handleBatchDelete = async () => {
    setBatchDeleting(true)
    try {
      await fishApi.batchDelete(selectedRowKeys)
      message.success(`成功删除 ${selectedRowKeys.length} 条记录`)
      setSelectedRowKeys([])
      loadFishes()
      loadStats()
    } catch {
      message.error('批量删除失败')
    } finally {
      setBatchDeleting(false)
    }
  }

  const handleInitData = async () => {
    setInitLoading(true)
    try {
      const result = await fishApi.initData()
      message.success(result.message)
      loadFishes()
      loadStats()
    } catch (err: any) {
      message.error(err.message || '初始化失败')
    } finally {
      setInitLoading(false)
    }
  }

  const handleDrawerClose = () => {
    setDrawerOpen(false)
    setEditingSpeciesId(null)
  }

  const handleDrawerSuccess = () => {
    loadFishes()
    loadStats()
  }

  // Table columns
  const columns: ColumnsType<FishSpeciesListItem> = [
    {
      title: '鱼种名称',
      dataIndex: 'name_cn',
      key: 'name_cn',
      render: (name, record) => (
        <div>
          <Text
            strong
            style={{ cursor: 'pointer', color: '#1890ff' }}
            onClick={() => handleView(record)}
          >
            {name}
          </Text>
          {record.name_en && (
            <div style={{ fontSize: 12, color: '#999' }}>{record.name_en}</div>
          )}
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 110,
      render: (category: FishCategory) => {
        const config = FISH_CATEGORY_CONFIG[category] || {
          label: category,
          color: '#8c8c8c',
          icon: '🐟',
        }
        return (
          <Tag
            style={{
              borderRadius: 8,
              border: 'none',
              background: `${config.color}15`,
              color: config.color,
            }}
          >
            {config.icon} {config.label}
          </Tag>
        )
      },
    },
    {
      title: '栖息环境',
      dataIndex: 'habitat',
      key: 'habitat',
      width: 150,
      ellipsis: true,
      render: (habitat) => habitat || '-',
    },
    {
      title: '知识条目',
      dataIndex: 'knowledge_count',
      key: 'knowledge_count',
      width: 90,
      align: 'center',
      render: (count) => (
        <Tag
          style={{
            borderRadius: 8,
            border: 'none',
            background: count > 0 ? '#e6f7ff' : '#f0f0f0',
            color: count > 0 ? '#1890ff' : '#999',
          }}
        >
          {count}
        </Tag>
      ),
    },
    {
      title: '季节活动',
      dataIndex: 'season_count',
      key: 'season_count',
      width: 90,
      align: 'center',
      render: (count) => (
        <Tag
          style={{
            borderRadius: 8,
            border: 'none',
            background: count > 0 ? '#f6ffed' : '#f0f0f0',
            color: count > 0 ? '#52c41a' : '#999',
          }}
        >
          {count}/4
        </Tag>
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
            title="确定删除此鱼种？"
            description="删除后将同时删除关联的知识和季节活动"
            onConfirm={() => handleDelete(record.species_id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Category options for filter
  const categoryOptions = [
    { value: '', label: '全部分类' },
    ...FISH_CATEGORY_OPTIONS.map((opt) => ({
      value: opt.value,
      label: `${opt.icon} ${opt.label}`,
    })),
  ]

  // Common habitats for filter
  const habitatOptions = [
    { value: '', label: '全部环境' },
    { value: '湖泊', label: '湖泊' },
    { value: '水库', label: '水库' },
    { value: '河流', label: '河流' },
    { value: '池塘', label: '池塘' },
    { value: '近海', label: '近海' },
    { value: '深海', label: '深海' },
  ]

  // Check if data is empty
  const isEmpty = total === 0 && !loading && !statsLoading

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
            鱼类百科
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            管理淡水鱼、海水鱼等鱼种信息和钓鱼技巧
          </Text>
        </div>
        <Space>
          <Button
            icon={<CloudDownloadOutlined />}
            onClick={() => setFetchModalOpen(true)}
          >
            网络采集
          </Button>
          {isEmpty && (
            <Button icon={<DatabaseOutlined />} onClick={handleInitData} loading={initLoading}>
              初始化数据
            </Button>
          )}
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建鱼种
          </Button>
        </Space>
      </div>

      {/* Category Stats Cards */}
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
            分类统计
          </Text>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={loadStats}
            loading={statsLoading}
          >
            刷新
          </Button>
        </div>

        <Spin spinning={statsLoading}>
          {categoryStats.length > 0 ? (
            <Row gutter={[24, 16]}>
              {categoryStats.map((stats) => (
                <Col xs={24} sm={8} md={8} lg={8} key={stats.category}>
                  <FishCard
                    stats={stats}
                    selected={selectedCategory === stats.category}
                    onClick={() => handleCardClick(stats.category as FishCategory)}
                  />
                </Col>
              ))}
            </Row>
          ) : isEmpty ? (
            <div
              style={{
                background: '#fafafa',
                borderRadius: 12,
                padding: '40px 0',
              }}
            >
              <Empty description="暂无鱼种数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
                <Button
                  type="primary"
                  icon={<DatabaseOutlined />}
                  onClick={handleInitData}
                  loading={initLoading}
                >
                  初始化常用鱼种
                </Button>
              </Empty>
            </div>
          ) : null}
        </Spin>
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginBottom: 20,
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Input.Search
            placeholder="搜索鱼种名称..."
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
            onChange={(v) => handleCategoryChange((v || undefined) as FishCategory | undefined)}
            allowClear
          />
          <Select
            placeholder="全部环境"
            style={{ width: 120 }}
            options={habitatOptions}
            value={filters.habitat || ''}
            onChange={(v) => handleHabitatChange(v || undefined)}
            allowClear
          />
        </div>
        {selectedRowKeys.length > 0 && (
          <Popconfirm
            title={`确定删除选中的 ${selectedRowKeys.length} 条记录？`}
            description="删除后将同时删除关联的知识和季节活动"
            onConfirm={handleBatchDelete}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button danger loading={batchDeleting} icon={<DeleteOutlined />}>
              批量删除 ({selectedRowKeys.length})
            </Button>
          </Popconfirm>
        )}
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
          dataSource={fishes}
          rowKey="species_id"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
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
      <FishDrawer
        open={drawerOpen}
        speciesId={editingSpeciesId}
        onClose={handleDrawerClose}
        onSuccess={handleDrawerSuccess}
      />

      {/* Fetch Modal */}
      <FetchModal
        open={fetchModalOpen}
        onClose={() => setFetchModalOpen(false)}
        onComplete={() => {
          loadFishes()
          loadStats()
        }}
      />

      {/* Detail Modal */}
      <FishDetailModal
        open={detailModalOpen}
        speciesId={viewingSpeciesId}
        onClose={() => setDetailModalOpen(false)}
        onEdit={handleEditFromDetail}
      />
    </div>
  )
}

export default FishList
