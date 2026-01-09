import { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { Table, Button, Space, App, Tag } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ExportOutlined, AppstoreAddOutlined, SettingOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import type { Equipment, Brand } from '@/types/equipment'
import { useEquipmentSearch } from './hooks/useEquipmentSearch'
import { useColumnSettings } from './hooks/useColumnSettings'
import AdvancedSearch from './components/AdvancedSearch'
import ColumnSettingsModal from './components/ColumnSettingsModal'

const EquipmentList = () => {
  const navigate = useNavigate()
  const { modal, message } = App.useApp()
  const [data, setData] = useState<Equipment[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [brands, setBrands] = useState<Brand[]>([])
  const [columnModalOpen, setColumnModalOpen] = useState(false)

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
  }, [loadBrands])

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

      {/* 操作按钮 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
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
    </div>
  )
}

export default EquipmentList
