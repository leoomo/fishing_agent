import { useEffect, useState } from 'react'
import { Table, Button, Input, Select, Space, Modal, message, Tag } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ExportOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import type { Equipment } from '@/types/equipment'

const { Search } = Input

const EquipmentList = () => {
  const navigate = useNavigate()
  const [data, setData] = useState<Equipment[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [category, setCategory] = useState<string>()
  const [keyword, setKeyword] = useState<string>()

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await equipmentApi.list({
        page,
        page_size: pageSize,
        category,
        keyword,
      })
      setData(response.items)
      setTotal(response.total)
    } catch {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [page, pageSize, category])

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个装备吗？',
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
  }

  const handleExport = async () => {
    try {
      const blob = await equipmentApi.exportCSV({ category })
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

  const handleSearch = (value: string) => {
    setKeyword(value)
    setPage(1)
    fetchData()
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'equipment_id',
      width: 80,
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 200,
    },
    {
      title: '类别',
      dataIndex: 'category',
      width: 100,
      render: (cat: string) => (
        <Tag color={
          cat === '鱼竿' ? 'blue' :
          cat === '渔轮' ? 'green' :
          cat === '鱼线' ? 'orange' :
          cat === '拟饵' ? 'purple' : 'default'
        }>
          {cat}
        </Tag>
      ),
    },
    {
      title: '品牌',
      dataIndex: 'brand_name',
      width: 120,
    },
    {
      title: '型号',
      dataIndex: 'model',
      width: 120,
    },
    {
      title: '价格范围',
      width: 150,
      render: (_: unknown, record: Equipment) =>
        record.price_min && record.price_max
          ? `¥${record.price_min} - ¥${record.price_max}`
          : '-',
    },
    {
      title: '适用水平',
      dataIndex: 'user_level',
      width: 100,
      render: (level: string) => (
        <Tag color={
          level === '新手' ? 'green' :
          level === '进阶' ? 'blue' :
          level === '高手' ? 'gold' : 'default'
        }>
          {level}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'error'}>
          {active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
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
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Select
            placeholder="选择类别"
            style={{ width: 120 }}
            allowClear
            onChange={setCategory}
          >
            <Select.Option value="鱼竿">鱼竿</Select.Option>
            <Select.Option value="渔轮">渔轮</Select.Option>
            <Select.Option value="鱼线">鱼线</Select.Option>
            <Select.Option value="拟饵">拟饵</Select.Option>
            <Select.Option value="路亚竿">路亚竿</Select.Option>
          </Select>

          <Search
            placeholder="搜索装备名称"
            style={{ width: 200 }}
            onSearch={handleSearch}
          />
        </Space>

        <Space>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            导出
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
          onChange: (page, pageSize) => {
            setPage(page)
            setPageSize(pageSize)
          },
        }}
        scroll={{ x: 1200 }}
      />
    </div>
  )
}

export default EquipmentList
