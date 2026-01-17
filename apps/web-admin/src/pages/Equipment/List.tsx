import { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { Table, Button, Space, App, Tag, Card, Row, Col, Statistic, Dropdown } from 'antd'
import type { MenuProps } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExportOutlined,
  AppstoreAddOutlined,
  SettingOutlined,
  DownOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import type { EquipmentStatsResponse } from '@/api/services/equipment'
import type { Equipment, Brand } from '@/types/equipment'
import { useEquipmentSearch } from './hooks/useEquipmentSearch'
import { useColumnSettings } from './hooks/useColumnSettings'
import AdvancedSearch from './components/AdvancedSearch'
import ColumnSettingsModal from './components/ColumnSettingsModal'
import BatchEditModal from './components/BatchEditModal'

const EquipmentList = () => {
  const navigate = useNavigate()
  const { modal, message } = App.useApp()
  const [data, setData] = useState<Equipment[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [brands, setBrands] = useState<Brand[]>([])
  const [columnModalOpen, setColumnModalOpen] = useState(false)

  // 批量操作状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [batchEditModalOpen, setBatchEditModalOpen] = useState(false)
  const [batchLoading, setBatchLoading] = useState(false)

  // 统计数据
  const [stats, setStats] = useState<EquipmentStatsResponse | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)

  // 列配置 Hook
  const { visibleColumns, saving: columnSaving, saveColumns } = useColumnSettings()

  // 使用搜索 Hook
  const {
    filters,
    page,
    pageSize,
    setFilters,
    setPage,
    setPageSize,
    resetFilters,
    searchParams,
  } = useEquipmentSearch({ defaultPageSize: 20 })

  // 加载品牌列表
  const loadBrands = useCallback(async () => {
    try {
      const response = await equipmentApi.listBrands()
      setBrands(response)
    } catch {
      // 品牌加载失败不影响主功能
    }
  }, [])

  // 加载统计数据
  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    try {
      const response = await equipmentApi.getStats()
      setStats(response)
    } catch {
      // 统计加载失败不影响主功能
    } finally {
      setStatsLoading(false)
    }
  }, [])

  // 加载装备数据
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const response = await equipmentApi.list(searchParams)
      setData(response.items)
      setTotal(response.total)
    } catch {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }, [searchParams, message])

  // 初始化加载
  useEffect(() => {
    loadBrands()
    loadStats()
  }, [loadBrands, loadStats])

  // 使用 ref 跟踪上一次的参数，避免不必要的重新请求
  const prevParamsRef = useRef<string>('')

  // 筛选条件变化时重新加载
  useEffect(() => {
    const paramsStr = JSON.stringify(searchParams)
    if (paramsStr !== prevParamsRef.current) {
      prevParamsRef.current = paramsStr
      fetchData()
    }
  }, [searchParams, fetchData])

  const handleDelete = useCallback(
    (id: number) => {
      modal.confirm({
        title: '确认删除',
        content: '确定要删除这个装备吗？',
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
          try {
            await equipmentApi.delete(id)
            message.success('删除成功')
            fetchData()
          } catch {
            message.error('删除失败')
          }
        },
      })
    },
    [modal, message, fetchData]
  )

  const handleExport = async () => {
    try {
      const blob = await equipmentApi.exportCSV({ category: filters.category })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'equipment_export.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch {
      message.error('导出失败')
    }
  }

  // 批量删除
  const handleBatchDelete = useCallback(() => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的装备')
      return
    }

    modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个装备吗？`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setBatchLoading(true)
        try {
          const response = await equipmentApi.batchDelete(selectedRowKeys as number[])
          message.success(response.message)
          setSelectedRowKeys([])
          fetchData()
          loadStats()
        } catch {
          message.error('批量删除失败')
        } finally {
          setBatchLoading(false)
        }
      },
    })
  }, [selectedRowKeys, modal, message, fetchData, loadStats])

  // 批量编辑
  const handleBatchEdit = useCallback(
    async (updates: { brand_id?: number; user_level?: string; is_active?: boolean }) => {
      setBatchLoading(true)
      try {
        const response = await equipmentApi.batchUpdate({
          ids: selectedRowKeys as number[],
          updates,
        })
        message.success(response.message)
        setBatchEditModalOpen(false)
        setSelectedRowKeys([])
        fetchData()
        loadStats()
      } catch {
        message.error('批量更新失败')
      } finally {
        setBatchLoading(false)
      }
    },
    [selectedRowKeys, message, fetchData, loadStats]
  )

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys)
    },
  }

  // 批量操作下拉菜单
  const batchMenuItems: MenuProps['items'] = [
    {
      key: 'edit',
      label: '批量编辑',
      icon: <EditOutlined />,
      onClick: () => setBatchEditModalOpen(true),
    },
    {
      key: 'delete',
      label: '批量删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: handleBatchDelete,
    },
  ]

  // 点击统计卡片快速筛选
  const handleCategoryClick = (category: string) => {
    setFilters({ ...filters, category })
  }

  // 所有列定义（带 key）
  const allColumns = useMemo(
    () => [
      {
        key: 'name',
        title: '名称',
        dataIndex: 'name',
        width: 200,
      },
      {
        key: 'category',
        title: '类别',
        dataIndex: 'category',
        width: 100,
        render: (cat: string) => (
          <Tag
            color={
              cat === '鱼竿'
                ? 'blue'
                : cat === '渔轮'
                  ? 'green'
                  : cat === '鱼线'
                    ? 'orange'
                    : cat === '拟饵'
                      ? 'purple'
                      : 'default'
            }
          >
            {cat}
          </Tag>
        ),
      },
      {
        key: 'brand_name',
        title: '品牌',
        dataIndex: 'brand_name',
        width: 120,
      },
      {
        key: 'model',
        title: '型号',
        dataIndex: 'model',
        width: 120,
      },
      {
        key: 'price',
        title: '价格范围',
        width: 150,
        render: (_: unknown, record: Equipment) =>
          record.price_min && record.price_max
            ? `¥${record.price_min} - ¥${record.price_max}`
            : '-',
      },
      {
        key: 'length',
        title: '竿长',
        width: 80,
        render: (_: unknown, record: Equipment) => {
          if (record.category !== '鱼竿') return '-'
          const specs = record.specs as Record<string, unknown> | undefined
          return specs?.length ? `${specs.length}m` : '-'
        },
      },
      {
        key: 'action',
        title: '动作',
        width: 80,
        render: (_: unknown, record: Equipment) => {
          if (record.category !== '鱼竿') return '-'
          const specs = record.specs as Record<string, unknown> | undefined
          return specs?.action || '-'
        },
      },
      {
        key: 'power',
        title: '调性',
        width: 80,
        render: (_: unknown, record: Equipment) => {
          if (record.category !== '鱼竿') return '-'
          const specs = record.specs as Record<string, unknown> | undefined
          return specs?.power || '-'
        },
      },
      {
        key: 'sections',
        title: '节数',
        width: 80,
        render: (_: unknown, record: Equipment) => {
          if (record.category !== '鱼竿') return '-'
          const specs = record.specs as Record<string, unknown> | undefined
          return specs?.sections ? `${specs.sections}节` : '-'
        },
      },
      {
        key: 'weight',
        title: '自重',
        width: 80,
        render: (_: unknown, record: Equipment) => {
          if (record.category !== '鱼竿') return '-'
          const specs = record.specs as Record<string, unknown> | undefined
          return specs?.weight ? `${specs.weight}g` : '-'
        },
      },
      {
        key: 'lure_weight',
        title: '饵重范围',
        width: 120,
        render: (_: unknown, record: Equipment) => {
          if (record.category !== '鱼竿') return '-'
          const specs = record.specs as Record<string, unknown> | undefined
          if (specs?.lure_weight_min && specs?.lure_weight_max) {
            return `${specs.lure_weight_min}-${specs.lure_weight_max}g`
          }
          return '-'
        },
      },
      {
        key: 'user_level',
        title: '适用水平',
        dataIndex: 'user_level',
        width: 100,
        render: (level: string) => (
          <Tag
            color={
              level === '入门'
                ? 'lime'
                : level === '新手'
                  ? 'green'
                  : level === '进阶'
                    ? 'blue'
                    : level === '高手'
                      ? 'gold'
                      : 'default'
            }
          >
            {level}
          </Tag>
        ),
      },
      {
        key: 'is_active',
        title: '状态',
        dataIndex: 'is_active',
        width: 80,
        render: (active: boolean) => (
          <Tag color={active ? 'success' : 'error'}>{active ? '启用' : '禁用'}</Tag>
        ),
      },
      {
        key: 'actions',
        title: '操作',
        width: 150,
        fixed: 'right' as const,
        render: (_: unknown, record: Equipment) => (
          <Space>
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => navigate(`/equipment/edit/${record.equipment_id}`)}
            >
              编辑
            </Button>
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.equipment_id)}
            >
              删除
            </Button>
          </Space>
        ),
      },
    ],
    [navigate, handleDelete]
  )

  // 根据配置过滤可见列
  const columns = useMemo(() => {
    return allColumns.filter((col) => visibleColumns.includes(col.key))
  }, [allColumns, visibleColumns])

  // 列设置保存
  const handleColumnSave = async (cols: string[]) => {
    const success = await saveColumns(cols)
    if (success) {
      setColumnModalOpen(false)
    }
  }

  return (
    <div>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}>
            <Card size="small" loading={statsLoading}>
              <Statistic title="装备总数" value={stats.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card
              size="small"
              loading={statsLoading}
              hoverable
              onClick={() => handleCategoryClick('鱼竿')}
              style={{ cursor: 'pointer' }}
            >
              <Statistic
                title="鱼竿"
                value={stats.by_category['鱼竿'] || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card
              size="small"
              loading={statsLoading}
              hoverable
              onClick={() => handleCategoryClick('渔轮')}
              style={{ cursor: 'pointer' }}
            >
              <Statistic
                title="渔轮"
                value={stats.by_category['渔轮'] || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card
              size="small"
              loading={statsLoading}
              hoverable
              onClick={() => handleCategoryClick('鱼线')}
              style={{ cursor: 'pointer' }}
            >
              <Statistic
                title="鱼线"
                value={stats.by_category['鱼线'] || 0}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card
              size="small"
              loading={statsLoading}
              hoverable
              onClick={() => handleCategoryClick('拟饵')}
              style={{ cursor: 'pointer' }}
            >
              <Statistic
                title="拟饵"
                value={stats.by_category['拟饵'] || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small" loading={statsLoading}>
              <Statistic
                title="已禁用"
                value={stats.inactive_count}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 高级搜索组件 + 列设置按钮 */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <AdvancedSearch
            filters={filters}
            brands={brands}
            loading={loading}
            onChange={setFilters}
            onSearch={fetchData}
            onReset={resetFilters}
          />
        </div>
        <Button
          icon={<SettingOutlined />}
          onClick={() => setColumnModalOpen(true)}
          title="列设置"
        />
      </div>

      {/* 操作按钮栏 */}
      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {/* 批量操作区域 */}
        <Space>
          {selectedRowKeys.length > 0 && (
            <>
              <span style={{ marginRight: 8 }}>已选择 {selectedRowKeys.length} 项</span>
              <Dropdown menu={{ items: batchMenuItems }} disabled={batchLoading}>
                <Button loading={batchLoading}>
                  批量操作 <DownOutlined />
                </Button>
              </Dropdown>
              <Button onClick={() => setSelectedRowKeys([])}>取消选择</Button>
            </>
          )}
        </Space>

        {/* 右侧操作按钮 */}
        <Space>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            导出
          </Button>
          <Button
            icon={<AppstoreAddOutlined />}
            onClick={() => navigate('/equipment/batch-create')}
          >
            批量添加
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/equipment/create')}
          >
            新增装备
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="equipment_id"
        rowSelection={rowSelection}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (newPage, newPageSize) => {
            if (newPageSize !== pageSize) {
              setPageSize(newPageSize)
            } else {
              setPage(newPage)
            }
          },
        }}
        scroll={{ x: 1200 }}
      />

      {/* 列设置弹窗 */}
      <ColumnSettingsModal
        open={columnModalOpen}
        visibleColumns={visibleColumns}
        saving={columnSaving}
        onOk={handleColumnSave}
        onCancel={() => setColumnModalOpen(false)}
      />

      {/* 批量编辑弹窗 */}
      <BatchEditModal
        open={batchEditModalOpen}
        selectedCount={selectedRowKeys.length}
        brands={brands}
        loading={batchLoading}
        onOk={handleBatchEdit}
        onCancel={() => setBatchEditModalOpen(false)}
      />
    </div>
  )
}

export default EquipmentList
