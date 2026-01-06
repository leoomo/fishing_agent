import { useState, useEffect, useCallback } from 'react'
import { Row, Col, App, Spin } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'
import { configApi } from '@/api/services/config'
import type { Config } from '@/types/config'
import { API_PROVIDERS, type APIProvider, type APIKeyStatus } from '../constants'
import APIStatusOverview from './APIStatusOverview'
import APIKeyCard from './APIKeyCard'
import QuickAddModal from './QuickAddModal'

interface APIKeyState {
  status: APIKeyStatus
  maskedKey?: string
  latency?: number
  lastTested?: string
  configId?: number
}

const APIKeyManager: React.FC = () => {
  const { modal, message } = App.useApp()
  const [loading, setLoading] = useState(true)
  const [apiKeyStates, setApiKeyStates] = useState<Record<string, APIKeyState>>({})
  const [testingKeys, setTestingKeys] = useState<Set<string>>(new Set())
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<APIProvider | null>(null)
  const [currentKeyValue, setCurrentKeyValue] = useState<string | undefined>()

  // 加载配置数据
  const loadConfigs = useCallback(async () => {
    try {
      setLoading(true)
      const response = await configApi.list('api')
      // 兼容数组和对象两种返回格式
      const configs = Array.isArray(response) ? response : []

      // 构建状态映射
      const states: Record<string, APIKeyState> = {}

      API_PROVIDERS.forEach((provider) => {
        const config = configs.find(
          (c: Config) => c.config_key === provider.configKey
        )

        if (config) {
          states[provider.key] = {
            status: 'configured',
            maskedKey: maskApiKey(config.config_value),
          }
        } else {
          states[provider.key] = {
            status: 'unconfigured',
          }
        }
      })

      setApiKeyStates(states)
    } catch {
      message.error('加载配置失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadConfigs()
  }, [loadConfigs])

  // 遮盖 API Key
  const maskApiKey = (key: string): string => {
    if (!key || key.length < 8) return '****'
    return key.substring(0, 4) + '****' + key.substring(key.length - 4)
  }

  // 计算状态统计
  const getStatusCounts = () => {
    const counts = {
      total: API_PROVIDERS.length,
      configured: 0,
      verified: 0,
      pending: 0,
      invalid: 0,
    }

    Object.values(apiKeyStates).forEach((state) => {
      if (state.status === 'verified') {
        counts.verified++
        counts.configured++
      } else if (state.status === 'configured' || state.status === 'pending') {
        counts.configured++
        if (state.status === 'pending') counts.pending++
      } else if (state.status === 'invalid') {
        counts.invalid++
        counts.configured++
      }
    })

    return counts
  }

  // 打开编辑弹窗
  const handleEdit = (provider: APIProvider) => {
    setSelectedProvider(provider)
    setCurrentKeyValue(undefined) // 编辑时不显示原值，需要重新输入
    setModalVisible(true)
  }

  // 保存配置
  const handleSave = async (key: string, value: string) => {
    const provider = API_PROVIDERS.find((p) => p.configKey === key)
    if (!provider) return

    const state = apiKeyStates[provider.key]

    try {
      if (state?.status !== 'unconfigured') {
        // 更新
        await configApi.update(key, {
          config_value: value,
        })
      } else {
        // 创建
        await configApi.create({
          config_key: key,
          config_value: value,
          config_type: 'api',
          description: provider.description,
          is_encrypted: true,
        })
      }

      message.success('保存成功')
      await loadConfigs()
    } catch {
      message.error('保存失败')
      throw new Error('保存失败')
    }
  }

  // 测试 API Key
  const handleTest = async (provider: APIProvider) => {
    setTestingKeys((prev) => new Set(prev).add(provider.key))

    try {
      const startTime = Date.now()
      const result = await configApi.testApiKey(provider.testEndpoint)
      const latency = Date.now() - startTime

      if (result.valid || result.success) {
        setApiKeyStates((prev) => ({
          ...prev,
          [provider.key]: {
            ...prev[provider.key],
            status: 'verified',
            latency,
            lastTested: '刚刚',
          },
        }))
        message.success(`${provider.name} 连接成功，延时 ${latency}ms`)
      } else {
        setApiKeyStates((prev) => ({
          ...prev,
          [provider.key]: {
            ...prev[provider.key],
            status: 'invalid',
            latency: undefined,
            lastTested: '刚刚',
          },
        }))
        message.error(`${provider.name} 连接失败: ${result.message || '未知错误'}`)
      }
    } catch {
      setApiKeyStates((prev) => ({
        ...prev,
        [provider.key]: {
          ...prev[provider.key],
          status: 'invalid',
          latency: undefined,
          lastTested: '刚刚',
        },
      }))
      message.error(`${provider.name} 测试失败`)
    } finally {
      setTestingKeys((prev) => {
        const next = new Set(prev)
        next.delete(provider.key)
        return next
      })
    }
  }

  // 删除配置
  const handleDelete = (provider: APIProvider) => {
    const state = apiKeyStates[provider.key]
    if (state?.status === 'unconfigured') return

    modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除 ${provider.name} 的 API 密钥配置吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await configApi.delete(provider.configKey)
          message.success('删除成功')
          await loadConfigs()
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      {/* 状态概览 */}
      <div style={{ marginBottom: 24 }}>
        <APIStatusOverview counts={getStatusCounts()} />
      </div>

      {/* API 密钥卡片 */}
      <Row gutter={[16, 16]}>
        {API_PROVIDERS.map((provider) => {
          const state = apiKeyStates[provider.key] || { status: 'unconfigured' as const }

          return (
            <Col xs={24} sm={12} lg={8} xl={6} key={provider.key}>
              <APIKeyCard
                provider={provider}
                status={state.status}
                maskedKey={state.maskedKey}
                latency={state.latency}
                lastTested={state.lastTested}
                testing={testingKeys.has(provider.key)}
                onEdit={() => handleEdit(provider)}
                onTest={() => handleTest(provider)}
                onDelete={() => handleDelete(provider)}
              />
            </Col>
          )
        })}
      </Row>

      {/* 编辑弹窗 */}
      <QuickAddModal
        visible={modalVisible}
        provider={selectedProvider}
        currentValue={currentKeyValue}
        onCancel={() => {
          setModalVisible(false)
          setSelectedProvider(null)
          setCurrentKeyValue(undefined)
        }}
        onSave={handleSave}
      />
    </div>
  )
}

export default APIKeyManager
