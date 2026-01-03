import { Card, Button, Tag, Space, Tooltip, Typography, Spin } from 'antd'
import {
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  PlusCircleOutlined,
  SettingOutlined,
  ExperimentOutlined,
  LinkOutlined,
} from '@ant-design/icons'
import type { APIProvider, APIKeyStatus } from '../constants'
import { API_KEY_STATUS_CONFIG } from '../constants'

const { Text, Paragraph } = Typography

interface APIKeyCardProps {
  provider: APIProvider
  status: APIKeyStatus
  maskedKey?: string
  latency?: number
  lastTested?: string
  onEdit: () => void
  onTest: () => void
  onDelete: () => void
  testing?: boolean
}

const getStatusIcon = (status: APIKeyStatus) => {
  switch (status) {
    case 'verified':
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />
    case 'pending':
      return <ClockCircleOutlined style={{ color: '#faad14' }} />
    case 'invalid':
      return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
    case 'configured':
      return <SettingOutlined style={{ color: '#1677ff' }} />
    case 'unconfigured':
    default:
      return <PlusCircleOutlined style={{ color: '#999' }} />
  }
}

const APIKeyCard: React.FC<APIKeyCardProps> = ({
  provider,
  status,
  maskedKey,
  latency,
  lastTested,
  onEdit,
  onTest,
  onDelete,
  testing = false,
}) => {
  const statusConfig = API_KEY_STATUS_CONFIG[status]
  const isConfigured = status !== 'unconfigured'

  return (
    <Card
      size="small"
      style={{
        borderLeft: `4px solid ${provider.color}`,
        height: '100%',
      }}
      styles={{
        body: {
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
        },
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 24, marginRight: 8 }}>{provider.icon}</span>
        <div style={{ flex: 1 }}>
          <Text strong style={{ fontSize: 14 }}>
            {provider.name}
          </Text>
          <div>
            <Tag
              color={statusConfig.color}
              icon={getStatusIcon(status)}
              style={{ marginTop: 4 }}
            >
              {statusConfig.label}
            </Tag>
          </div>
        </div>
      </div>

      {/* Description */}
      <Paragraph
        type="secondary"
        style={{ fontSize: 12, marginBottom: 12, flex: 1 }}
        ellipsis={{ rows: 2 }}
      >
        {provider.description}
      </Paragraph>

      {/* API Key Display */}
      {isConfigured && maskedKey && (
        <div
          style={{
            background: '#f5f5f5',
            padding: '8px 12px',
            borderRadius: 4,
            marginBottom: 12,
            fontFamily: 'monospace',
            fontSize: 12,
          }}
        >
          {maskedKey}
        </div>
      )}

      {/* Latency Info */}
      {latency !== undefined && (
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            响应延时:{' '}
            <Text
              style={{
                color: latency < 500 ? '#52c41a' : latency < 1000 ? '#faad14' : '#ff4d4f',
              }}
            >
              {latency}ms
            </Text>
          </Text>
          {lastTested && (
            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
              · {lastTested}
            </Text>
          )}
        </div>
      )}

      {/* Actions */}
      <Space size="small" style={{ marginTop: 'auto' }}>
        {isConfigured ? (
          <>
            <Tooltip title="编辑密钥">
              <Button size="small" icon={<EditOutlined />} onClick={onEdit}>
                编辑
              </Button>
            </Tooltip>
            <Tooltip title="测试连接">
              <Button
                size="small"
                icon={testing ? <Spin size="small" /> : <ExperimentOutlined />}
                onClick={onTest}
                disabled={testing}
              >
                {testing ? '测试中' : '测试'}
              </Button>
            </Tooltip>
            <Tooltip title="删除配置">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={onDelete}
              />
            </Tooltip>
          </>
        ) : (
          <Button type="primary" size="small" icon={<PlusCircleOutlined />} onClick={onEdit}>
            配置密钥
          </Button>
        )}
        <Tooltip title="查看文档">
          <Button
            size="small"
            type="link"
            icon={<LinkOutlined />}
            href={provider.docUrl}
            target="_blank"
          />
        </Tooltip>
      </Space>
    </Card>
  )
}

export default APIKeyCard
