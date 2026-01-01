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
  KeyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import { configApi } from '@/api/services/config'
import type { Config, ConfigCreate } from '@/types/config'
import type { ColumnsType } from 'antd/es/table'

const { TextArea } = Input
const { Text } = Typography

const Settings = () => {
  const [loading, setLoading] = useState(false)
  const [configs, setConfigs] = useState<Config[]>([])
  const [selectedType, setSelectedType] = useState<string>()
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<Config | null>(null)
  const [form] = Form.useForm()

  // API 密钥测试状态
  const [testingKey, setTestingKey] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { valid: boolean; message: string }>>({})

  useEffect(() => {
    fetchConfigs()
  }, [selectedType])

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

  const handleTestApiKey = async (configKey: string, provider: string) => {
    setTestingKey(configKey)
    try {
      // 获取实际的 key 值
      const config = configs.find(c => c.config_key === configKey)
      if (!config) return

      const result = await configApi.testApiKey(provider, config.config_value)
      setTestResults(prev => ({
        ...prev,
        [configKey]: result,
      }))

      if (result.valid) {
        message.success('API 密钥有效')
      } else {
        message.warning(result.message || 'API 密钥无效')
      }
    } catch {
      setTestResults(prev => ({
        ...prev,
        [configKey]: { valid: false, message: '测试失败' },
      }))
      message.error('测试失败')
    } finally {
      setTestingKey(null)
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
      width: 200,
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

          {record.config_type === 'api' && (
            <Button
              type="link"
              size="small"
              icon={testingKey === record.config_key ? <LoadingOutlined /> : <KeyOutlined />}
              onClick={() => {
                // 从 config_key 中提取 provider
                const provider = record.config_key.replace('_API_KEY', '').toLowerCase()
                handleTestApiKey(record.config_key, provider)
              }}
              disabled={testingKey !== null}
            >
              测试
            </Button>
          )}

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

  // API 密钥专用列
  const apiKeyColumns: ColumnsType<Config> = [
    {
      title: 'API 服务',
      dataIndex: 'config_key',
      width: 180,
      render: (key) => {
        const name = key.replace('_API_KEY', '')
        return <Text strong>{name}</Text>
      },
    },
    {
      title: '密钥',
      dataIndex: 'config_value',
      width: 300,
      render: (value, record) => {
        if (record.is_encrypted) {
          return <Text type="secondary">••••••••••••••••</Text>
        }
        // 部分显示
        if (value.length > 8) {
          return <Text code>{value.substring(0, 4)}...{value.substring(value.length - 4)}</Text>
        }
        return <Text code>{value}</Text>
      },
    },
    {
      title: '状态',
      width: 120,
      render: (_, record) => {
        const result = testResults[record.config_key]
        if (!result) return <Tag>未测试</Tag>
        return result.valid ? (
          <Tag icon={<CheckCircleOutlined />} color="success">有效</Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">无效</Tag>
        )
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: 200,
      render: (desc) => desc || '-',
    },
    {
      title: '操作',
      width: 180,
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
          <Button
            type="link"
            size="small"
            icon={testingKey === record.config_key ? <LoadingOutlined /> : <KeyOutlined />}
            onClick={() => {
              const provider = record.config_key.replace('_API_KEY', '').toLowerCase()
              handleTestApiKey(record.config_key, provider)
            }}
            disabled={testingKey !== null}
          >
            测试
          </Button>
        </Space>
      ),
    },
  ]

  const apiConfigs = configs.filter(c => c.config_type === 'api')

  return (
    <div>
      <Card title="配置管理">
        <Tabs
          defaultActiveKey="api"
          items={[
            {
              key: 'api',
              label: 'API 密钥',
              children: (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                      新增配置
                    </Button>
                  </div>
                  <Table
                    columns={apiKeyColumns}
                    dataSource={apiConfigs}
                    loading={loading}
                    rowKey="config_key"
                    pagination={false}
                  />
                </div>
              ),
            },
            {
              key: 'agent',
              label: 'Agent 配置',
              children: (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                      新增配置
                    </Button>
                  </div>
                  <Table
                    columns={columns}
                    dataSource={configs.filter(c => c.config_type === 'agent')}
                    loading={loading}
                    rowKey="config_key"
                    pagination={false}
                  />
                </div>
              ),
            },
            {
              key: 'algorithm',
              label: '算法参数',
              children: (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                      新增配置
                    </Button>
                  </div>
                  <Table
                    columns={columns}
                    dataSource={configs.filter(c => c.config_type === 'algorithm')}
                    loading={loading}
                    rowKey="config_key"
                    pagination={false}
                  />
                </div>
              ),
            },
            {
              key: 'all',
              label: '全部配置',
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
          ]}
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
            <Input
              placeholder="如: DASHSCOPE_API_KEY"
              disabled={!!editingConfig}
            />
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
