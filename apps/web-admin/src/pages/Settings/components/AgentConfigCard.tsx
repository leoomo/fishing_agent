import { Card, Form, Select, InputNumber, Slider, Switch, Typography, Space, Button, Tooltip } from 'antd'
import { SaveOutlined, UndoOutlined, InfoCircleOutlined } from '@ant-design/icons'
import type { AgentConfig, AgentConfigParam } from '../constants'

const { Text, Paragraph } = Typography

interface AgentConfigCardProps {
  agent: AgentConfig
  values: Record<string, string | number | boolean>
  onChange: (key: string, value: string | number | boolean) => void
  onSave: () => void
  onReset: () => void
  saving?: boolean
  modified?: boolean
}

const AgentConfigCard: React.FC<AgentConfigCardProps> = ({
  agent,
  values,
  onChange,
  onSave,
  onReset,
  saving = false,
  modified = false,
}) => {
  const renderParamControl = (param: AgentConfigParam) => {
    const value = values[param.key] ?? param.defaultValue

    switch (param.type) {
      case 'select':
        return (
          <Select
            style={{ width: '100%' }}
            value={value as string}
            onChange={(v) => onChange(param.key, v)}
            options={param.options}
          />
        )

      case 'number':
        return (
          <InputNumber
            style={{ width: '100%' }}
            value={value as number}
            onChange={(v) => onChange(param.key, v ?? param.defaultValue)}
            min={param.min}
            max={param.max}
          />
        )

      case 'slider':
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Slider
              style={{ flex: 1 }}
              value={value as number}
              onChange={(v) => onChange(param.key, v)}
              min={param.min}
              max={param.max}
              step={param.step}
            />
            <Text style={{ minWidth: 40, textAlign: 'right' }}>{value}</Text>
          </div>
        )

      case 'switch':
        return (
          <Switch
            checked={value as boolean}
            onChange={(v) => onChange(param.key, v)}
          />
        )

      default:
        return null
    }
  }

  return (
    <Card
      title={
        <Space>
          <span style={{ fontSize: 20 }}>{agent.icon}</span>
          <span>{agent.name}</span>
        </Space>
      }
      extra={
        <Space>
          {modified && (
            <Tooltip title="重置为默认值">
              <Button
                size="small"
                icon={<UndoOutlined />}
                onClick={onReset}
              />
            </Tooltip>
          )}
          <Button
            type="primary"
            size="small"
            icon={<SaveOutlined />}
            onClick={onSave}
            loading={saving}
            disabled={!modified}
          >
            保存
          </Button>
        </Space>
      }
      style={{
        borderLeft: `4px solid ${agent.color}`,
        height: '100%',
      }}
    >
      <Paragraph type="secondary" style={{ marginBottom: 16 }}>
        {agent.description}
      </Paragraph>

      <Form layout="vertical" size="small">
        {agent.params.map((param) => (
          <Form.Item
            key={param.key}
            label={
              <Space>
                <span>{param.label}</span>
                <Tooltip title={param.description}>
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>
            }
            style={{ marginBottom: 12 }}
          >
            {renderParamControl(param)}
          </Form.Item>
        ))}
      </Form>
    </Card>
  )
}

export default AgentConfigCard
