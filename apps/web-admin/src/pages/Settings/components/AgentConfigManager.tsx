import { useState, useEffect, useCallback } from 'react'
import { Row, Col, message, Spin, Card, Statistic, Alert } from 'antd'
import { RobotOutlined, SettingOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { configApi } from '@/api/services/config'
import type { Config } from '@/types/config'
import { AGENT_CONFIGS, type AgentConfig } from '../constants'
import AgentConfigCard from './AgentConfigCard'

type ConfigValues = Record<string, Record<string, string | number | boolean>>

const AgentConfigManager: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [configValues, setConfigValues] = useState<ConfigValues>({})
  const [modifiedAgents, setModifiedAgents] = useState<Set<string>>(new Set())

  // 加载配置数据
  const loadConfigs = useCallback(async () => {
    try {
      setLoading(true)
      const response = await configApi.list('agent')
      const configs = Array.isArray(response) ? response : []

      // 构建配置值映射
      const values: ConfigValues = {}

      AGENT_CONFIGS.forEach((agent) => {
        values[agent.key] = {}
        agent.params.forEach((param) => {
          const config = configs.find((c: Config) => c.config_key === param.key)
          if (config) {
            // 解析配置值
            let value: string | number | boolean = config.config_value
            if (param.type === 'number' || param.type === 'slider') {
              value = parseFloat(config.config_value)
            } else if (param.type === 'switch') {
              value = config.config_value === 'true'
            }
            values[agent.key][param.key] = value
          } else {
            values[agent.key][param.key] = param.defaultValue
          }
        })
      })

      setConfigValues(values)
      setModifiedAgents(new Set())
    } catch {
      message.error('加载配置失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadConfigs()
  }, [loadConfigs])

  // 获取默认值
  const getDefaultValues = (agent: AgentConfig): Record<string, string | number | boolean> => {
    const defaults: Record<string, string | number | boolean> = {}
    agent.params.forEach((param) => {
      defaults[param.key] = param.defaultValue
    })
    return defaults
  }

  // 处理值变更
  const handleChange = (agentKey: string, paramKey: string, value: string | number | boolean) => {
    setConfigValues((prev) => ({
      ...prev,
      [agentKey]: {
        ...prev[agentKey],
        [paramKey]: value,
      },
    }))
    setModifiedAgents((prev) => new Set(prev).add(agentKey))
  }

  // 保存配置
  const handleSave = async (agentKey: string) => {
    const agent = AGENT_CONFIGS.find((a) => a.key === agentKey)
    if (!agent) return

    setSaving(agentKey)
    try {
      const values = configValues[agentKey]

      // 保存每个参数
      for (const param of agent.params) {
        const value = values[param.key]
        const stringValue = String(value)

        try {
          // 尝试更新，如果不存在则创建
          await configApi.update(param.key, {
            config_value: stringValue,
          })
        } catch {
          // 配置不存在，创建新配置
          await configApi.create({
            config_key: param.key,
            config_value: stringValue,
            config_type: 'agent',
            description: param.description,
          })
        }
      }

      message.success(`${agent.name} 配置保存成功`)
      setModifiedAgents((prev) => {
        const next = new Set(prev)
        next.delete(agentKey)
        return next
      })
    } catch {
      message.error('保存配置失败')
    } finally {
      setSaving(null)
    }
  }

  // 重置配置
  const handleReset = (agentKey: string) => {
    const agent = AGENT_CONFIGS.find((a) => a.key === agentKey)
    if (!agent) return

    setConfigValues((prev) => ({
      ...prev,
      [agentKey]: getDefaultValues(agent),
    }))
    setModifiedAgents((prev) => new Set(prev).add(agentKey))
  }

  // 计算统计数据
  const getStats = () => {
    let configured = 0
    let total = 0

    AGENT_CONFIGS.forEach((agent) => {
      agent.params.forEach((param) => {
        total++
        const value = configValues[agent.key]?.[param.key]
        if (value !== undefined && value !== param.defaultValue) {
          configured++
        }
      })
    })

    return { configured, total, agents: AGENT_CONFIGS.length }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  const stats = getStats()

  return (
    <div>
      {/* 统计概览 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="Agent 数量"
              value={stats.agents}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="配置项总数"
              value={stats.total}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="已自定义"
              value={stats.configured}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: stats.configured > 0 ? '#52c41a' : undefined }}
            />
          </Card>
        </Col>
      </Row>

      {/* 提示信息 */}
      <Alert
        type="info"
        showIcon
        message="Agent 配置说明"
        description="修改配置后需要点击保存按钮。配置保存到数据库后，后端 Agent 将在下次启动时读取新配置。"
        style={{ marginBottom: 24 }}
      />

      {/* Agent 配置卡片 */}
      <Row gutter={[16, 16]}>
        {AGENT_CONFIGS.map((agent) => (
          <Col xs={24} lg={12} key={agent.key}>
            <AgentConfigCard
              agent={agent}
              values={configValues[agent.key] || getDefaultValues(agent)}
              onChange={(paramKey, value) => handleChange(agent.key, paramKey, value)}
              onSave={() => handleSave(agent.key)}
              onReset={() => handleReset(agent.key)}
              saving={saving === agent.key}
              modified={modifiedAgents.has(agent.key)}
            />
          </Col>
        ))}
      </Row>
    </div>
  )
}

export default AgentConfigManager
