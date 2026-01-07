import { useState, useEffect, useCallback, useRef } from 'react'
import { Table, Card, Tag, Button, Space, App } from 'antd'
import {
  EyeOutlined,
  EditOutlined,
  ExportOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '@/api/services/users'
import type { User } from '@/types/user'
import type { ColumnsType, TableRowSelection } from 'antd/es/table/interface'
import { useUserSearch } from './hooks/useUserSearch'
import AdvancedSearch from './components/AdvancedSearch'
import UserEditDrawer from './components/UserEditDrawer'
import BatchOperationBar from './components/BatchOperationBar'

const UserList = () => {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [editDrawerOpen, setEditDrawerOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)

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
  } = useUserSearch({ defaultPageSize: 20 })

  // 使用 ref 跟踪上一次的参数，避免不必要的重新请求
  const prevParamsRef = useRef<string>('')

  // 加载用户数据
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const response = await usersApi.list(searchParams)
      setData(response.users)
      setTotal(response.total)
    } catch {
      message.error('加载用户列表失败')
    } finally {
      setLoading(false)
    }
  }, [searchParams, message])

  // 筛选条件变化时重新加载
  useEffect(() => {
    const paramsStr = JSON.stringify(searchParams)
    if (paramsStr !== prevParamsRef.current) {
      prevParamsRef.current = paramsStr
      fetchData()
    }
  }, [searchParams, fetchData])

  // 处理编辑
  const handleEdit = (user: User) => {
    setEditingUser(user)
    setEditDrawerOpen(true)
  }

  // 处理导出全部
  const handleExportAll = async () => {
    try {
      const blob = await usersApi.exportCSV({
        user_level: filters.user_level,
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'users_export.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch {
      message.error('导出失败')
    }
  }

  // 行选择配置
  const rowSelection: TableRowSelection<User> = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys as number[]),
    preserveSelectedRowKeys: true,
  }

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      新手: 'green',
      进阶: 'blue',
      高手: 'gold',
    }
    return colors[level] || 'default'
  }

  const columns: ColumnsType<User> = [
    {
      title: 'ID',
      dataIndex: 'user_id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      width: 120,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      width: 180,
      render: (email) => email || '-',
    },
    {
      title: '手机',
      dataIndex: 'phone',
      width: 130,
      render: (phone) => phone || '-',
    },
    {
      title: '用户水平',
      dataIndex: 'user_level',
      width: 100,
      render: (level) => <Tag color={getLevelColor(level)}>{level}</Tag>,
    },
    {
      title: '钓龄(年)',
      dataIndex: 'fishing_experience_years',
      width: 90,
      render: (years) =>
        years !== null && years !== undefined ? years : '-',
    },
    {
      title: '偏好钓法',
      dataIndex: 'preferred_fishing_method',
      width: 100,
      render: (method) => method || '-',
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/users/${record.user_id}`)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card title="用户管理">
      {/* 高级搜索组件 */}
      <AdvancedSearch
        filters={filters}
        loading={loading}
        onChange={setFilters}
        onSearch={fetchData}
        onReset={resetFilters}
      />

      {/* 批量操作工具栏 */}
      <BatchOperationBar
        selectedIds={selectedRowKeys}
        onClear={() => setSelectedRowKeys([])}
        onSuccess={fetchData}
      />

      {/* 操作按钮 */}
      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        <Button icon={<ExportOutlined />} onClick={handleExportAll}>
          导出全部
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="user_id"
        rowSelection={rowSelection}
        scroll={{ x: 1200 }}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => {
            if (ps !== pageSize) {
              setPageSize(ps)
            } else {
              setPage(p)
            }
          },
        }}
      />

      {/* 用户编辑抽屉 */}
      <UserEditDrawer
        open={editDrawerOpen}
        user={editingUser}
        onClose={() => {
          setEditDrawerOpen(false)
          setEditingUser(null)
        }}
        onSuccess={fetchData}
      />
    </Card>
  )
}

export default UserList
