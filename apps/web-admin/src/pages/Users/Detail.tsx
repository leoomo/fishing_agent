import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Descriptions,
  Table,
  Tabs,
  Tag,
  Button,
  Spin,
  message,
  Empty,
  Space,
  Statistic,
  Row,
  Col,
} from 'antd'
import {
  ArrowLeftOutlined,
  StarOutlined,
  StarFilled,
  EnvironmentOutlined,
} from '@ant-design/icons'
import { usersApi } from '@/api/services/users'
import type { User, UserEquipment, FishingLog } from '@/types/user'
import type { ColumnsType } from 'antd/es/table'

const UserDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<User | null>(null)
  const [equipment, setEquipment] = useState<UserEquipment[]>([])
  const [fishingLogs, setFishingLogs] = useState<FishingLog[]>([])
  const [equipmentLoading, setEquipmentLoading] = useState(false)
  const [logsLoading, setLogsLoading] = useState(false)

  const userId = parseInt(id || '0', 10)

  useEffect(() => {
    if (userId) {
      fetchUserDetail()
    }
  }, [userId])

  const fetchUserDetail = async () => {
    setLoading(true)
    try {
      const userData = await usersApi.get(userId)
      setUser(userData)
    } catch {
      message.error('加载用户信息失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchEquipment = async () => {
    setEquipmentLoading(true)
    try {
      const data = await usersApi.getEquipment(userId)
      setEquipment(data)
    } catch {
      message.error('加载装备库失败')
    } finally {
      setEquipmentLoading(false)
    }
  }

  const fetchFishingLogs = async () => {
    setLogsLoading(true)
    try {
      const data = await usersApi.getFishingLogs(userId, { limit: 50 })
      setFishingLogs(data)
    } catch {
      message.error('加载钓鱼记录失败')
    } finally {
      setLogsLoading(false)
    }
  }

  const handleTabChange = (key: string) => {
    if (key === 'equipment' && equipment.length === 0) {
      fetchEquipment()
    } else if (key === 'logs' && fishingLogs.length === 0) {
      fetchFishingLogs()
    }
  }

  const equipmentColumns: ColumnsType<UserEquipment> = [
    {
      title: '装备名称',
      dataIndex: 'equipment_name',
      width: 200,
    },
    {
      title: '类别',
      dataIndex: 'category',
      width: 100,
    },
    {
      title: '品牌',
      dataIndex: 'brand_name',
      width: 120,
    },
    {
      title: '购买价格',
      dataIndex: 'purchase_price',
      width: 120,
      render: (price) => (price ? `¥${price}` : '-'),
    },
    {
      title: '状况',
      dataIndex: 'condition',
      width: 100,
      render: (condition) => condition || '-',
    },
    {
      title: '收藏',
      dataIndex: 'is_favorite',
      width: 80,
      render: (isFav) =>
        isFav ? (
          <StarFilled style={{ color: '#faad14' }} />
        ) : (
          <StarOutlined style={{ color: '#d9d9d9' }} />
        ),
    },
    {
      title: '购买日期',
      dataIndex: 'purchase_date',
      width: 120,
      render: (date) => (date ? new Date(date).toLocaleDateString('zh-CN') : '-'),
    },
  ]

  const logsColumns: ColumnsType<FishingLog> = [
    {
      title: '日期',
      dataIndex: 'fishing_date',
      width: 120,
      render: (date) => new Date(date).toLocaleDateString('zh-CN'),
    },
    {
      title: '地点',
      dataIndex: 'location',
      width: 150,
      render: (loc) =>
        loc ? (
          <Space>
            <EnvironmentOutlined />
            {loc}
          </Space>
        ) : (
          '-'
        ),
    },
    {
      title: '天气',
      dataIndex: 'weather_condition',
      width: 100,
      render: (weather) => weather || '-',
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      width: 80,
      render: (temp) => (temp !== null ? `${temp}°C` : '-'),
    },
    {
      title: '鱼种',
      dataIndex: 'fish_species',
      width: 100,
    },
    {
      title: '数量',
      dataIndex: 'fish_count',
      width: 80,
    },
    {
      title: '总重量',
      dataIndex: 'fish_total_weight',
      width: 100,
      render: (weight) => (weight ? `${weight}kg` : '-'),
    },
    {
      title: '使用装备',
      dataIndex: 'equipment_used',
      width: 150,
      ellipsis: true,
    },
    {
      title: '备注',
      dataIndex: 'notes',
      width: 200,
      ellipsis: true,
    },
  ]

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!user) {
    return (
      <Card>
        <Empty description="用户不存在" />
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button onClick={() => navigate('/users')}>返回列表</Button>
        </div>
      </Card>
    )
  }

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      '新手': 'green',
      '进阶': 'blue',
      '高手': 'gold',
    }
    return colors[level] || 'default'
  }

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/users')}
        style={{ marginBottom: 16 }}
      >
        返回列表
      </Button>

      <Card title={`用户详情 - ${user.username}`}>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="用户ID">{user.user_id}</Descriptions.Item>
          <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user.email || '-'}</Descriptions.Item>
          <Descriptions.Item label="手机">{user.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="用户水平">
            <Tag color={getLevelColor(user.user_level)}>{user.user_level}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="钓龄">
            {user.fishing_experience_years !== null && user.fishing_experience_years !== undefined
              ? `${user.fishing_experience_years} 年`
              : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="喜欢鱼种">
            {user.favorite_fish_species || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="偏好钓法">
            {user.preferred_fishing_method || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="地区" span={2}>
            {user.location || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="注册时间">
            {new Date(user.created_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
          <Descriptions.Item label="最后更新">
            {new Date(user.updated_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Tabs defaultActiveKey="stats" onChange={handleTabChange}>
          <Tabs.TabPane tab="统计概览" key="stats">
            <Row gutter={24}>
              <Col span={6}>
                <Statistic title="装备总数" value={equipment.length || '-'} />
              </Col>
              <Col span={6}>
                <Statistic title="钓鱼记录" value={fishingLogs.length || '-'} />
              </Col>
              <Col span={6}>
                <Statistic
                  title="收藏装备"
                  value={equipment.filter((e) => e.is_favorite).length || '-'}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="装备总花费"
                  prefix="¥"
                  value={
                    equipment.reduce((sum, e) => sum + (e.purchase_price || 0), 0) || '-'
                  }
                />
              </Col>
            </Row>
          </Tabs.TabPane>

          <Tabs.TabPane tab="装备库" key="equipment">
            <Table
              columns={equipmentColumns}
              dataSource={equipment}
              loading={equipmentLoading}
              rowKey="user_equipment_id"
              scroll={{ x: 1000 }}
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>

          <Tabs.TabPane tab="钓鱼记录" key="logs">
            <Table
              columns={logsColumns}
              dataSource={fishingLogs}
              loading={logsLoading}
              rowKey="log_id"
              scroll={{ x: 1200 }}
              pagination={{ pageSize: 10 }}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default UserDetail
