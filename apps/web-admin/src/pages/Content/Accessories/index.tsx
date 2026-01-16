/**
 * 钓鱼配件管理页面 - 乔布斯简洁风格
 *
 * 功能：
 * - 顶部：分类统计卡片（钩子/铅坠/转环/前导线/浮漂/别针/其他）
 * - 下方：完整表格（分类筛选 + 搜索 + CRUD）
 * - 空数据：显示"初始化数据"按钮
 * - 详情弹窗：只读查看配件信息
 * - 批量删除：多选删除
 * - 导入导出：Excel导入导出
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
  Image,
  Dropdown,
} from 'antd'
import type { MenuProps } from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  DownloadOutlined,
  UploadOutlined,
  MoreOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import type { TableRowSelection } from 'antd/es/table/interface'
import { accessoryApi } from '@/api/services/accessory'
import type {
  AccessoryListItem,
  AccessoryCategory,
  AccessoryCategoryStats,
  AccessoryListParams,
  UserLevel,
} from '@/types/accessory'
import {
  ACCESSORY_CATEGORY_CONFIG,
  ACCESSORY_CATEGORY_OPTIONS,
  USER_LEVEL_CONFIG,
  USER_LEVEL_OPTIONS,
} from '@/types/accessory'
import AccessoryCard from './AccessoryCard'
import AccessoryDrawer from './AccessoryDrawer'
import AccessoryDetailModal from './AccessoryDetailModal'
import AccessoryImportModal from './AccessoryImportModal'

const { Title, Text } = Typography

const AccessoryList: React.FC = () => {
  // State
  const [loading, setLoading] = useState(false)
  const [statsLoading, setStatsLoading] = useState(false)
  const [initLoading, setInitLoading] = useState(false)
  const [accessories, setAccessories] = useState<AccessoryListItem[]>([])
  const [categoryStats, setCategoryStats] = useState<AccessoryCategoryStats[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<AccessoryListParams>({
    page: 1,
    page_size: 10,
  })
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingAccessoryId, setEditingAccessoryId] = useState<number | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<AccessoryCategory | null>(null)

  // Detail modal state
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [detailAccessoryId, setDetailAccessoryId] = useState<number | null>(null)

  // Batch delete state
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [batchDeleting, setBatchDeleting] = useState(false)

  // Import modal state
  const [importModalOpen, setImportModalOpen] = useState(false)

  // Load category stats
  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    try {
      const data = await accessoryApi.getStats()
      setCategoryStats(data.categories)
      setTotal(data.total)
    } catch {
      // Ignore error for stats
    } finally {
      setStatsLoading(false)
    }
  }, [])

  // Load accessories list
  const loadAccessories = useCallback(async () => {
    setLoading(true)
    try {
      const response = await accessoryApi.list(filters)
      setAccessories(response.items)
      setTotal(response.total)
    } catch {
      message.error('加载配件列表失败')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  useEffect(() => {
    loadAccessories()
  }, [loadAccessories])

  // Handle filter changes
  const handleSearch = (keyword: string) => {
    setFilters((prev) => ({ ...prev, keyword, page: 1 }))
  }

  const handleCategoryChange = (category: AccessoryCategory | undefined) => {
    setFilters((prev) => ({ ...prev, category, page: 1 }))
    setSelectedCategory(category || null)
  }

  const handleUserLevelChange = (user_level: UserLevel | undefined) => {
    setFilters((prev) => ({ ...prev, user_level, page: 1 }))
  }

  const handleCardClick = (category: AccessoryCategory | null) => {
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
    setEditingAccessoryId(null)
    setDrawerOpen(true)
  }

  const handleEdit = (accessory: AccessoryListItem) => {
    setEditingAccessoryId(accessory.accessory_id)
    setDrawerOpen(true)
  }

  const handleViewDetail = (accessory: AccessoryListItem) => {
    setDetailAccessoryId(accessory.accessory_id)
    setDetailModalOpen(true)
  }

  const handleDetailToEdit = () => {
    setDetailModalOpen(false)
    if (detailAccessoryId) {
      setEditingAccessoryId(detailAccessoryId)
      setDrawerOpen(true)
    }
  }

  const handleDelete = async (accessoryId: number) => {
    try {
      await accessoryApi.delete(accessoryId)
      message.success('删除成功')
      loadAccessories()
      loadStats()
    } catch {
      message.error('删除失败')
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的配件')
      return
    }

    setBatchDeleting(true)
    try {
      const result = await accessoryApi.batchDelete(selectedRowKeys as number[])
      message.success(result.message)
      setSelectedRowKeys([])
      loadAccessories()
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
      const result = await accessoryApi.initData()
      message.success(result.message)
      loadAccessories()
      loadStats()
    } catch (err: unknown) {
      const error = err as { message?: string }
      message.error(error.message || '初始化失败')
    } finally {
      setInitLoading(false)
    }
  }

  const handleDrawerClose = () => {
    setDrawerOpen(false)
    setEditingAccessoryId(null)
  }

  const handleDrawerSuccess = () => {
    loadAccessories()
    loadStats()
  }

  // Export handler
  const handleExport = async () => {
    try {
      await accessoryApi.exportData()
      message.success('导出成功')
    } catch {
      message.error('导出失败')
    }
  }

  // Download template handler
  const handleDownloadTemplate = async () => {
    try {
      await accessoryApi.downloadTemplate()
      message.success('模板下载成功')
    } catch {
      message.error('模板下载失败')
    }
  }

  // Row selection
  const rowSelection: TableRowSelection<AccessoryListItem> = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  }

  // Table columns
  const columns: ColumnsType<AccessoryListItem> = [
    {
      title: '',
      dataIndex: 'image_url',
      key: 'image',
      width: 60,
      render: (image_url: string) => (
        <Image
          src={image_url}
          alt="配件"
          width={40}
          height={40}
          style={{ borderRadius: 6, objectFit: 'cover' }}
          fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjZjVmNWY1Ii8+PHRleHQgeD0iMjAiIHk9IjIwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiNiZmJmYmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiPvCfjqM8L3RleHQ+PC9zdmc+"
          preview={false}
        />
      ),
    },
    {
      title: '配件名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Text
          strong
          style={{ cursor: 'pointer', color: '#1890ff' }}
          onClick={() => handleViewDetail(record)}
        >
          {name}
        </Text>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: AccessoryCategory) => {
        const config = ACCESSORY_CATEGORY_CONFIG[category] || {
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
      width: 120,
      ellipsis: true,
      render: (species) => species || '-',
    },
    {
      title: '规格',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size) => size || '-',
    },
    {
      title: '材质',
      dataIndex: 'material',
      key: 'material',
      width: 80,
      render: (material) => material || '-',
    },
    {
      title: '品牌',
      dataIndex: 'brand',
      key: 'brand',
      width: 80,
      ellipsis: true,
      render: (brand) => brand || '-',
    },
    {
      title: '价格区间',
      key: 'price_range',
      width: 100,
      render: (_, record) => {
        const min = record.price_min
        const max = record.price_max
        if (min && max) {
          return `${min}-${max}`
        } else if (min) {
          return `${min}`
        } else if (max) {
          return `${max}`
        }
        return '-'
      },
    },
    {
      title: '级别',
      dataIndex: 'user_level',
      key: 'user_level',
      width: 70,
      render: (level: UserLevel) => {
        const config = USER_LEVEL_CONFIG[level] || { label: level, color: '#8c8c8c' }
        return (
          <Tag
            style={{
              borderRadius: 8,
              border: 'none',
              background: `${config.color}15`,
              color: config.color,
            }}
          >
            {config.label}
          </Tag>
        )
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
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          />
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定删除此配件？"
            description="删除后无法恢复"
            onConfirm={() => handleDelete(record.accessory_id)}
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
    ...ACCESSORY_CATEGORY_OPTIONS.map((opt) => ({
      value: opt.value,
      label: `${opt.icon} ${opt.label}`,
    })),
  ]

  // User level options for filter
  const userLevelOptions = [
    { value: '', label: '全部级别' },
    ...USER_LEVEL_OPTIONS.map((opt) => ({
      value: opt.value,
      label: opt.label,
    })),
  ]

  // Check if data is empty
  const isEmpty = total === 0 && !loading && !statsLoading

  // More actions dropdown
  const moreMenuItems: MenuProps['items'] = [
    {
      key: 'import',
      icon: <UploadOutlined />,
      label: '导入配件',
      onClick: () => setImportModalOpen(true),
    },
    {
      key: 'export',
      icon: <DownloadOutlined />,
      label: '导出数据',
      onClick: handleExport,
    },
    {
      key: 'template',
      icon: <DownloadOutlined />,
      label: '下载模板',
      onClick: handleDownloadTemplate,
    },
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
            钓鱼配件
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            管理钩子、铅坠、转环、前导线等钓鱼配件
          </Text>
        </div>
        <Space>
          {isEmpty && (
            <Button icon={<DatabaseOutlined />} onClick={handleInitData} loading={initLoading}>
              初始化数据
            </Button>
          )}
          <Dropdown menu={{ items: moreMenuItems }} placement="bottomRight">
            <Button icon={<MoreOutlined />}>更多</Button>
          </Dropdown>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建配件
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
            <Row gutter={[16, 16]}>
              {categoryStats.map((stats) => (
                <Col xs={12} sm={8} md={6} lg={3} key={stats.category}>
                  <AccessoryCard
                    stats={stats}
                    selected={selectedCategory === stats.category}
                    onClick={() => handleCardClick(stats.category as AccessoryCategory)}
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
              <Empty description="暂无配件数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
                <Button
                  type="primary"
                  icon={<DatabaseOutlined />}
                  onClick={handleInitData}
                  loading={initLoading}
                >
                  初始化常用配件
                </Button>
              </Empty>
            </div>
          ) : null}
        </Spin>
      </div>

      {/* Filters and Batch Actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 12,
          marginBottom: 20,
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Input.Search
            placeholder="搜索配件名称..."
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
            onChange={(v) => handleCategoryChange((v || undefined) as AccessoryCategory | undefined)}
            allowClear
          />
          <Select
            placeholder="全部级别"
            style={{ width: 120 }}
            options={userLevelOptions}
            value={filters.user_level || ''}
            onChange={(v) => handleUserLevelChange((v || undefined) as UserLevel | undefined)}
            allowClear
          />
        </div>

        {selectedRowKeys.length > 0 && (
          <Space>
            <Text type="secondary">已选择 {selectedRowKeys.length} 项</Text>
            <Popconfirm
              title="确定批量删除？"
              description={`将删除 ${selectedRowKeys.length} 个配件，此操作无法恢复`}
              onConfirm={handleBatchDelete}
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <Button danger icon={<DeleteOutlined />} loading={batchDeleting}>
                批量删除
              </Button>
            </Popconfirm>
            <Button onClick={() => setSelectedRowKeys([])}>取消选择</Button>
          </Space>
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
          dataSource={accessories}
          rowKey="accessory_id"
          loading={loading}
          rowSelection={rowSelection}
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
      <AccessoryDrawer
        open={drawerOpen}
        accessoryId={editingAccessoryId}
        onClose={handleDrawerClose}
        onSuccess={handleDrawerSuccess}
      />

      {/* Detail Modal */}
      <AccessoryDetailModal
        open={detailModalOpen}
        accessoryId={detailAccessoryId}
        onClose={() => setDetailModalOpen(false)}
        onEdit={handleDetailToEdit}
      />

      {/* Import Modal */}
      <AccessoryImportModal
        open={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onSuccess={() => {
          loadAccessories()
          loadStats()
        }}
      />
    </div>
  )
}

export default AccessoryList
