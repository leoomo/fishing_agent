/**
 * 拟饵类型管理页面 - 乔布斯简洁风格
 *
 * 功能：
 * - 顶部：分类统计卡片（硬饵/软饵/金属/飞蝇）
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
  Progress,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  PauseCircleOutlined,
  SyncOutlined,
  GlobalOutlined,
} from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import { lureTypeApi } from '@/api/services/lureType'
import type {
  LureTypeListItem,
  LureCategory,
  CategoryStats,
  LureTypeListParams,
  CrawlProgressResponse,
} from '@/types/lureType'
import { LURE_CATEGORY_CONFIG, LURE_CATEGORY_OPTIONS } from '@/types/lureType'
import LureTypeCard from './LureTypeCard'
import LureTypeDrawer from './LureTypeDrawer'
import LureTypeDetailModal from './LureTypeDetailModal'

const { Title, Text } = Typography

const LureTypeList: React.FC = () => {
  // State
  const [loading, setLoading] = useState(false)
  const [statsLoading, setStatsLoading] = useState(false)
  const [initLoading, setInitLoading] = useState(false)
  const [lureTypes, setLureTypes] = useState<LureTypeListItem[]>([])
  const [categoryStats, setCategoryStats] = useState<CategoryStats[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<LureTypeListParams>({
    page: 1,
    page_size: 10,
  })
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingLureTypeId, setEditingLureTypeId] = useState<number | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<LureCategory | null>(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [viewingLureTypeId, setViewingLureTypeId] = useState<number | null>(null)
  // Crawl state
  const [crawlProgress, setCrawlProgress] = useState<CrawlProgressResponse | null>(null)
  const [crawlLoading, setCrawlLoading] = useState(false)
  // Batch delete state
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [batchDeleteLoading, setBatchDeleteLoading] = useState(false)

  // Load category stats
  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    try {
      const data = await lureTypeApi.getStats()
      setCategoryStats(data.categories)
      setTotal(data.total)
    } catch {
      // Ignore error for stats
    } finally {
      setStatsLoading(false)
    }
  }, [])

  // Load lure types list
  const loadLureTypes = useCallback(async () => {
    setLoading(true)
    try {
      const response = await lureTypeApi.list(filters)
      setLureTypes(response.items)
      setTotal(response.total)
    } catch {
      message.error('加载拟饵类型列表失败')
    } finally {
      setLoading(false)
    }
  }, [filters])

  // Load crawl progress
  const loadCrawlProgress = useCallback(async () => {
    try {
      const data = await lureTypeApi.getCrawlProgress()
      setCrawlProgress(data)
      return data
    } catch {
      // Ignore error
      return null
    }
  }, [])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  useEffect(() => {
    loadLureTypes()
  }, [loadLureTypes])

  // Load crawl progress on mount and poll when running
  useEffect(() => {
    loadCrawlProgress()
  }, [loadCrawlProgress])

  useEffect(() => {
    if (crawlProgress?.is_running) {
      const timer = setInterval(async () => {
        const data = await loadCrawlProgress()
        if (data && !data.is_running) {
          // Crawl finished, reload data
          loadLureTypes()
          loadStats()
        }
      }, 2000)
      return () => clearInterval(timer)
    }
  }, [crawlProgress?.is_running, loadCrawlProgress, loadLureTypes, loadStats])

  // Handle filter changes
  const handleSearch = (keyword: string) => {
    setFilters(prev => ({ ...prev, keyword, page: 1 }))
  }

  const handleCategoryChange = (category: LureCategory | undefined) => {
    setFilters(prev => ({ ...prev, category, page: 1 }))
    setSelectedCategory(category || null)
  }

  const handleCardClick = (category: LureCategory | null) => {
    if (selectedCategory === category) {
      // 取消选择
      setSelectedCategory(null)
      setFilters(prev => ({ ...prev, category: undefined, page: 1 }))
    } else {
      setSelectedCategory(category)
      setFilters(prev => ({ ...prev, category: category || undefined, page: 1 }))
    }
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
    setEditingLureTypeId(null)
    setDrawerOpen(true)
  }

  const handleView = (lureType: LureTypeListItem) => {
    setViewingLureTypeId(lureType.lure_type_id)
    setDetailModalOpen(true)
  }

  const handleEdit = (lureType: LureTypeListItem) => {
    setEditingLureTypeId(lureType.lure_type_id)
    setDrawerOpen(true)
  }

  const handleDetailEdit = () => {
    setDetailModalOpen(false)
    if (viewingLureTypeId) {
      setEditingLureTypeId(viewingLureTypeId)
      setDrawerOpen(true)
    }
  }

  const handleDelete = async (lureTypeId: number) => {
    try {
      await lureTypeApi.delete(lureTypeId)
      message.success('删除成功')
      loadLureTypes()
      loadStats()
    } catch {
      message.error('删除失败')
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的拟饵类型')
      return
    }

    setBatchDeleteLoading(true)
    try {
      const result = await lureTypeApi.batchDelete(selectedRowKeys as number[])
      message.success(result.message)
      setSelectedRowKeys([])
      loadLureTypes()
      loadStats()
    } catch (err: any) {
      message.error(err.message || '批量删除失败')
    } finally {
      setBatchDeleteLoading(false)
    }
  }

  const handleInitData = async () => {
    setInitLoading(true)
    try {
      const result = await lureTypeApi.initData()
      message.success(result.message)
      loadLureTypes()
      loadStats()
    } catch (err: any) {
      message.error(err.message || '初始化失败')
    } finally {
      setInitLoading(false)
    }
  }

  const handleDrawerClose = () => {
    setDrawerOpen(false)
    setEditingLureTypeId(null)
  }

  const handleDrawerSuccess = () => {
    loadLureTypes()
    loadStats()
  }

  // Crawl handlers
  const handleStartCrawl = async () => {
    setCrawlLoading(true)
    try {
      const result = await lureTypeApi.startCrawl()
      message.success(result.message)
      loadCrawlProgress()
    } catch (err: any) {
      message.error(err.message || '启动采集失败')
    } finally {
      setCrawlLoading(false)
    }
  }

  const handleStopCrawl = async () => {
    setCrawlLoading(true)
    try {
      const result = await lureTypeApi.stopCrawl()
      message.success(result.message)
      loadCrawlProgress()
    } catch (err: any) {
      message.error(err.message || '停止采集失败')
    } finally {
      setCrawlLoading(false)
    }
  }

  // Table columns
  const columns: ColumnsType<LureTypeListItem> = [
    {
      title: '拟饵名称',
      dataIndex: 'name',
      key: 'name',
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
            <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
              {record.name_en}
            </Text>
          )}
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category: LureCategory) => {
        const config = LURE_CATEGORY_CONFIG[category] || {
          label: category,
          color: '#8c8c8c',
          icon: '🎣',
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
      title: '目标鱼种',
      dataIndex: 'target_species',
      key: 'target_species',
      width: 180,
      ellipsis: true,
      render: (species) => species || '-',
    },
    {
      title: '重量范围',
      key: 'weight_range',
      width: 140,
      render: (_, record) => {
        const min = record.typical_weight_min
        const max = record.typical_weight_max
        if (min && max) {
          return `${min} - ${max}g`
        } else if (min) {
          return `≥${min}g`
        } else if (max) {
          return `≤${max}g`
        }
        return '-'
      },
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
            title="确定删除此拟饵类型？"
            description="删除后无法恢复"
            onConfirm={() => handleDelete(record.lure_type_id)}
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
    ...LURE_CATEGORY_OPTIONS.map(opt => ({
      value: opt.value,
      label: `${opt.icon} ${opt.label}`,
    })),
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
            拟饵类型
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            管理路亚钓法使用的各类拟饵
          </Text>
        </div>
        <Space>
          {/* Crawl Button - 网页采集 */}
          {!isEmpty && crawlProgress?.is_running && (
            <Button
              icon={<PauseCircleOutlined />}
              onClick={handleStopCrawl}
              loading={crawlLoading}
            >
              停止采集
              {crawlProgress.total_count > 0 && (
                <span style={{ marginLeft: 8, color: '#52c41a' }}>
                  ({crawlProgress.translated_count}/{crawlProgress.total_count})
                </span>
              )}
            </Button>
          )}
          {!isEmpty && !crawlProgress?.is_running && (
            <Button
              icon={<GlobalOutlined />}
              onClick={handleStartCrawl}
              loading={crawlLoading}
            >
              网络采集
            </Button>
          )}
          {isEmpty && (
            <Button
              icon={<DatabaseOutlined />}
              onClick={handleInitData}
              loading={initLoading}
            >
              初始化数据
            </Button>
          )}
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建拟饵
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
            <Row gutter={[20, 20]}>
              {categoryStats.map(stats => (
                <Col xs={12} sm={8} md={6} lg={4} key={stats.category}>
                  <LureTypeCard
                    stats={stats}
                    selected={selectedCategory === stats.category}
                    onClick={() => handleCardClick(stats.category as LureCategory)}
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
              <Empty
                description="暂无拟饵类型数据"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button
                  type="primary"
                  icon={<DatabaseOutlined />}
                  onClick={handleInitData}
                  loading={initLoading}
                >
                  初始化常用拟饵
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
          alignItems: 'center',
        }}
      >
        <Input.Search
          placeholder="搜索拟饵名称..."
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
          onChange={v => handleCategoryChange((v || undefined) as LureCategory | undefined)}
          allowClear
        />
        {selectedRowKeys.length > 0 && (
          <Popconfirm
            title={`确定删除选中的 ${selectedRowKeys.length} 条拟饵类型？`}
            description="删除后无法恢复"
            onConfirm={handleBatchDelete}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              loading={batchDeleteLoading}
            >
              批量删除 ({selectedRowKeys.length})
            </Button>
          </Popconfirm>
        )}
      </div>

      {/* Crawl Progress */}
      {crawlProgress?.is_running && (
        <div
          style={{
            background: '#e6f7ff',
            border: '1px solid #91d5ff',
            borderRadius: 8,
            padding: '12px 16px',
            marginBottom: 20,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <Space>
              <SyncOutlined spin style={{ color: '#1890ff' }} />
              <Text strong>{crawlProgress.message || '正在从维基百科采集数据...'}</Text>
            </Space>
            {crawlProgress.total_count > 0 && (
              <Text type="secondary">
                {crawlProgress.translated_count} / {crawlProgress.total_count}
              </Text>
            )}
          </div>
          {crawlProgress.total_count > 0 && (
            <Progress
              percent={Math.round((crawlProgress.translated_count / crawlProgress.total_count) * 100)}
              status="active"
              strokeColor="#1890ff"
            />
          )}
        </div>
      )}

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
          dataSource={lureTypes}
          rowKey="lure_type_id"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
          }}
          pagination={{
            current: filters.page,
            pageSize: filters.page_size,
            total,
            showSizeChanger: true,
            showTotal: t => `共 ${t} 条`,
          }}
          onChange={handleTableChange}
        />
      </div>

      {/* Drawer */}
      <LureTypeDrawer
        open={drawerOpen}
        lureTypeId={editingLureTypeId}
        onClose={handleDrawerClose}
        onSuccess={handleDrawerSuccess}
      />

      {/* Detail Modal */}
      <LureTypeDetailModal
        open={detailModalOpen}
        lureTypeId={viewingLureTypeId}
        onClose={() => setDetailModalOpen(false)}
        onEdit={handleDetailEdit}
      />
    </div>
  )
}

export default LureTypeList
