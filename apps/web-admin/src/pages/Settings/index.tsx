import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Tabs,
  Popconfirm,
  Typography,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  ControlOutlined,
  DatabaseOutlined,
} from '@ant-design/icons'
import { configApi } from '@/api/services/config'
import type { Config, ConfigCreate } from '@/types/config'
import type { ColumnsType } from 'antd/es/table'
import APIKeyManager from './components/APIKeyManager'
import AgentConfigManager from './components/AgentConfigManager'
import { RobotOutlined } from '@ant-design/icons'

const { TextArea } = Input
const { Text } = Typography

const Settings = () => {
  const [loading, setLoading] = useState(false)
  const [configs, setConfigs] = useState<Config[]>([])
  const [selectedType, setSelectedType] = useState<string>()
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<Config | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('api')

  useEffect(() => {
    // 只在非 api 标签页时加载配置
    if (activeTab !== 'api') {
      fetchConfigs()
    }
  }, [selectedType, activeTab])

  const fetchConfigs = async () => {
    setLoading(true)
    try {
      const data = await configApi.list(selectedType)
      setConfigs(data)
    } catch {
      message.error('加载配置失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingConfig(null)
    form.resetFields()
    // 根据当前标签页设置默认类型
    if (activeTab !== 'all') {
      form.setFieldsValue({ config_type: activeTab })
    }
    setModalVisible(true)
  }

  const handleEdit = (config: Config) => {
    setEditingConfig(config)
    form.setFieldsValue({
      config_key: config.config_key,
      config_value: config.config_value,
      config_type: config.config_type,
      description: config.description,
      is_encrypted: config.is_encrypted,
    })
    setModalVisible(true)
  }

  const handleDelete = async (configKey: string) => {
    try {
      await configApi.delete(configKey)
      message.success('删除成功')
      fetchConfigs()
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (editingConfig) {
        await configApi.update(editingConfig.config_key, {
          config_value: values.config_value,
          description: values.description,
        })
        message.success('更新成功')
      } else {
        await configApi.create(values as ConfigCreate)
        message.success('创建成功')
      }

      setModalVisible(false)
      fetchConfigs()
    } catch {
      message.error('操作失败')
    }
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      agent: 'blue',
      algorithm: 'green',
      api: 'orange',
      system: 'purple',
    }
    return colors[type] || 'default'
  }

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      agent: 'Agent 配置',
      algorithm: '算法参数',
      api: 'API 密钥',
      system: '系统配置',
    }
    return labels[type] || type
  }

  const columns: ColumnsType<Config> = [
    {
      title: '配置键',
      dataIndex: 'config_key',
      width: 200,
      render: (key) => <Text code>{key}</Text>,
    },
    {
      title: '配置值',
      dataIndex: 'config_value',
      width: 250,
      render: (value, record) => {
        if (record.is_encrypted) {
          return <Text type="secondary">******** (已加密)</Text>
        }
        return value.length > 50 ? `${value.substring(0, 50)}...` : value
      },
    },
    {
      title: '类型',
      dataIndex: 'config_type',
      width: 120,
      render: (type) => <Tag color={getTypeColor(type)}>{getTypeLabel(type)}</Tag>,
    },
    {
      title: '加密',
      dataIndex: 'is_encrypted',
      width: 80,
      render: (encrypted) => (encrypted ? <Tag color="red">是</Tag> : <Tag>否</Tag>),
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: 200,
      ellipsis: true,
      render: (desc) => desc || '-',
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
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
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>

          <Popconfirm
            title="确定删除此配置？"
            onConfirm={() => handleDelete(record.config_key)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const tabItems = [
    {
      key: 'api',
      label: (
        <span>
          <ApiOutlined />
          API 密钥
        </span>
      ),
      children: <APIKeyManager />,
    },
    {
      key: 'agent',
      label: (
        <span>
          <RobotOutlined />
          Agent 配置
        </span>
      ),
      children: <AgentConfigManager />,
    },
    {
      key: 'algorithm',
      label: (
        <span>
          <ControlOutlined />
          算法参数
        </span>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              新增配置
            </Button>
          </div>
          <Table
            columns={columns}
            dataSource={configs.filter((c) => c.config_type === 'algorithm')}
            loading={loading}
            rowKey="config_key"
            pagination={false}
          />
        </div>
      ),
    },
    {
      key: 'all',
      label: (
        <span>
          <DatabaseOutlined />
          全部配置
        </span>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16 }}>
            <Space>
              <Select
                placeholder="筛选类型"
                style={{ width: 150 }}
                allowClear
                value={selectedType}
                onChange={setSelectedType}
              >
                <Select.Option value="agent">Agent 配置</Select.Option>
                <Select.Option value="algorithm">算法参数</Select.Option>
                <Select.Option value="api">API 密钥</Select.Option>
                <Select.Option value="system">系统配置</Select.Option>
              </Select>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                新增配置
              </Button>
            </Space>
          </div>
          <Table
            columns={columns}
            dataSource={configs}
            loading={loading}
            rowKey="config_key"
            scroll={{ x: 1200 }}
            pagination={{ pageSize: 20 }}
          />
        </div>
      ),
    },
  ]

  return (
    <div>
      <Card title="配置管理">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>

      <Modal
        title={editingConfig ? '编辑配置' : '新增配置'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="config_key"
            label="配置键"
            rules={[{ required: true, message: '请输入配置键' }]}
          >
            <Input placeholder="如: AGENT_MODEL" disabled={!!editingConfig} />
          </Form.Item>

          <Form.Item
            name="config_value"
            label="配置值"
            rules={[{ required: true, message: '请输入配置值' }]}
          >
            <TextArea rows={3} placeholder="请输入配置值" />
          </Form.Item>

          <Form.Item
            name="config_type"
            label="配置类型"
            rules={[{ required: true, message: '请选择配置类型' }]}
          >
            <Select placeholder="选择类型" disabled={!!editingConfig}>
              <Select.Option value="agent">Agent 配置</Select.Option>
              <Select.Option value="algorithm">算法参数</Select.Option>
              <Select.Option value="api">API 密钥</Select.Option>
              <Select.Option value="system">系统配置</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="可选描述" />
          </Form.Item>

          {!editingConfig && (
            <Form.Item name="is_encrypted" label="是否加密存储" valuePropName="checked">
              <Switch />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default Settings
