import { useState, useEffect } from 'react'
import { Table, Card, Input, Select, Space, Tag, Button, message } from 'antd'
import { EyeOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '@/api/services/users'
import type { User } from '@/types/user'
import type { ColumnsType } from 'antd/es/table'

const { Search } = Input

const UserList = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [userLevel, setUserLevel] = useState<string>()
  const [location, setLocation] = useState<string>()

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await usersApi.list({
        page,
        page_size: pageSize,
        user_level: userLevel,
        location,
      })
      setData(response.users)
      setTotal(response.total)
    } catch {
      message.error('加载用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [page, pageSize, userLevel])

  const handleSearch = (value: string) => {
    setLocation(value || undefined)
    setPage(1)
    fetchData()
  }

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      '新手': 'green',
      '进阶': 'blue',
      '高手': 'gold',
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
      render: (years) => (years !== null && years !== undefined ? years : '-'),
    },
    {
      title: '偏好钓法',
      dataIndex: 'preferred_fishing_method',
      width: 100,
      render: (method) => method || '-',
    },
    {
      title: '地区',
      dataIndex: 'location',
      width: 120,
      render: (loc) => loc || '-',
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/users/${record.user_id}`)}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <Card title="用户管理">
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="用户水平"
          style={{ width: 120 }}
          allowClear
          value={userLevel}
          onChange={(value) => {
            setUserLevel(value)
            setPage(1)
          }}
        >
          <Select.Option value="新手">新手</Select.Option>
          <Select.Option value="进阶">进阶</Select.Option>
          <Select.Option value="高手">高手</Select.Option>
        </Select>

        <Search
          placeholder="搜索地区"
          style={{ width: 200 }}
          allowClear
          enterButton={<SearchOutlined />}
          onSearch={handleSearch}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="user_id"
        scroll={{ x: 1200 }}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => {
            setPage(p)
            setPageSize(ps)
          },
        }}
      />
    </Card>
  )
}

export default UserList
