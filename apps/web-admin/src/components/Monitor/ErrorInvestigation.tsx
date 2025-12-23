import React, { useState, useEffect } from 'react'
import {
  Modal,
  Timeline,
  Tag,
  Card,
  Descriptions,
  Alert,
  Button,
  Space,
  Tooltip,
  Typography,
  Row,
  Col,
  Collapse,
  Badge,
  Spin,
} from 'antd'
import {
  ExclamationCircleOutlined,
  BugOutlined,
  InfoCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useFailurePatterns, type ErrorChain } from '../../hooks/useFailurePatterns'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text } = Typography
const { Panel } = Collapse

interface ErrorInvestigationProps {
  correlationId: string
  visible: boolean
  onClose: () => void
}

interface ErrorDetailProps {
  error: any
  index: number
}

const ErrorDetail: React.FC<ErrorDetailProps> = ({ error, index }) => {
  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'red'
      case 'high': return 'orange'
      case 'medium': return 'yellow'
      case 'low': return 'green'
      default: return 'blue'
    }
  }

  const getCategoryColor = (category?: string) => {
    switch (category) {
      case 'llm_api': return 'purple'
      case 'external': return 'cyan'
      case 'database': return 'red'
      case 'timeout': return 'orange'
      case 'validation': return 'blue'
      case 'auth': return 'yellow'
      default: return 'default'
    }
  }

  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Row gutter={16}>
        <Col span={2}>
          <Badge count={index + 1} style={{ backgroundColor: '#1890ff' }} />
        </Col>
        <Col span={14}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Space wrap>
              <Tag color={getSeverityColor(error.severity)}>
                {error.severity?.toUpperCase() || 'UNKNOWN'}
              </Tag>
              {error.error_category && (
                <Tag color={getCategoryColor(error.error_category)}>
                  {error.error_category.toUpperCase()}
                </Tag>
              )}
              <Tag color={error.success === false ? 'red' : 'green'}>
                {error.service?.toUpperCase() || 'UNKNOWN'}
              </Tag>
              {error.failure_stage && (
                <Tag color="orange">
                  {error.failure_stage}
                </Tag>
              )}
            </Space>

            <div>
              <Text strong>服务:</Text> {error.service || 'Unknown'}{' '}
              {error.endpoint && <span>• <Text strong>端点:</Text> {error.endpoint}</span>}{' '}
              {error.agent_type && <span>• <Text strong>Agent:</Text> {error.agent_type}</span>}
            </div>

            {error.error_message && (
              <Alert
                message="错误信息"
                description={
                  <Text code style={{ fontSize: 12 }}>
                    {error.error_message.length > 200
                      ? `${error.error_message.substring(0, 200)}...`
                      : error.error_message
                    }
                  </Text>
                }
                type="error"
                showIcon
              />
            )}

            {error.failed_tool_name && (
              <div>
                <Text type="danger">失败的工具: {error.failed_tool_name}</Text>
              </div>
            )}
          </Space>
        </Col>
        <Col span={8}>
          <Space direction="vertical" size="small" align="end">
            <Tooltip title={dayjs(error.timestamp).format('YYYY-MM-DD HH:mm:ss')}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {dayjs(error.timestamp).fromNow()}
              </Text>
            </Tooltip>
            {error.status_code && (
              <Tag color={error.status_code >= 500 ? 'red' : 'orange'}>
                HTTP {error.status_code}
              </Tag>
            )}
          </Space>
        </Col>
      </Row>
    </Card>
  )
}

const ErrorInvestigation: React.FC<ErrorInvestigationProps> = ({
  correlationId,
  visible,
  onClose,
}) => {
  const { fetchErrorCorrelation, loading } = useFailurePatterns()
  const [errorChain, setErrorChain] = useState<ErrorChain | null>(null)
  const [localLoading, setLocalLoading] = useState(false)

  useEffect(() => {
    if (visible && correlationId) {
      loadErrorChain()
    }
  }, [visible, correlationId])

  const loadErrorChain = async () => {
    setLocalLoading(true)
    try {
      const chain = await fetchErrorCorrelation(correlationId)
      setErrorChain(chain)
    } catch (error) {
      console.error('Failed to load error chain:', error)
    } finally {
      setLocalLoading(false)
    }
  }

  const getImpactSeverity = (score: number) => {
    if (score >= 50) return { color: 'red', text: '严重' }
    if (score >= 30) return { color: 'orange', text: '中等' }
    if (score >= 10) return { color: 'yellow', text: '轻微' }
    return { color: 'green', text: '低' }
  }

  const impactSeverity = errorChain ? getImpactSeverity(errorChain.impact_score) : null

  return (
    <Modal
      title={
        <Space>
          <BugOutlined />
          <span>错误链调查 - {correlationId}</span>
          {impactSeverity && (
            <Tag color={impactSeverity.color}>
              影响程度: {impactSeverity.text}
            </Tag>
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={1000}
      footer={[
        <Button key="refresh" onClick={loadErrorChain} loading={loading.correlation}>
          刷新
        </Button>,
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      {localLoading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>加载错误链数据...</div>
        </div>
      ) : !errorChain ? (
        <Alert
          message="未找到错误链"
          description="无法找到与该关联ID相关的错误链。请检查关联ID是否正确。"
          type="warning"
          showIcon
        />
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Summary Card */}
          <Card size="small" title="错误链概览">
            <Row gutter={16}>
              <Col span={6}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="错误总数">
                    <Badge count={errorChain.total_errors} style={{ backgroundColor: '#f5222d' }} />
                  </Descriptions.Item>
                </Descriptions>
              </Col>
              <Col span={6}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="影响评分">
                    <Badge
                      count={errorChain.impact_score}
                      style={{ backgroundColor: impactSeverity?.color }}
                    />
                  </Descriptions.Item>
                </Descriptions>
              </Col>
              <Col span={12}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="推断根因">
                    <Text code style={{ fontSize: 12 }}>
                      {errorChain.root_cause.length > 100
                        ? `${errorChain.root_cause.substring(0, 100)}...`
                        : errorChain.root_cause
                      }
                    </Text>
                  </Descriptions.Item>
                </Descriptions>
              </Col>
            </Row>
          </Card>

          {/* Error Timeline */}
          <Card size="small" title={`错误时间线 (${errorChain.total_errors} 个错误)`}>
            <Timeline mode="left">
              {errorChain.errors.map((error: any, index: number) => (
                <Timeline.Item
                  key={index}
                  dot={
                    error.severity === 'critical' ? (
                      <CloseCircleOutlined style={{ color: 'red' }} />
                    ) : error.severity === 'high' ? (
                      <ExclamationCircleOutlined style={{ color: 'orange' }} />
                    ) : (
                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                    )
                  }
                  color={
                    error.severity === 'critical' ? 'red' :
                    error.severity === 'high' ? 'orange' :
                    error.severity === 'medium' ? 'yellow' : 'blue'
                  }
                >
                  <ErrorDetail
                    error={error}
                    index={index}
                  />
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>

          {/* Error Details Collapsible */}
          <Collapse>
            <Panel header="详细错误信息" key="details">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {errorChain.errors.map((error: any, index: number) => (
                  <Card key={index} size="small" title={`错误 ${index + 1} - ${error.service || 'Unknown'}`}>
                    <Descriptions column={2} size="small" bordered>
                      <Descriptions.Item label="时间戳" span={2}>
                        {dayjs(error.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                      </Descriptions.Item>
                      <Descriptions.Item label="服务">
                        {error.service || 'Unknown'}
                      </Descriptions.Item>
                      <Descriptions.Item label="端点">
                        {error.endpoint || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Agent类型">
                        {error.agent_type || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="状态码">
                        {error.status_code || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="错误类别">
                        {error.error_category || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="严重程度">
                        {error.severity || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="失败阶段">
                        {error.failure_stage || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="失败工具">
                        {error.failed_tool_name || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="成功状态" span={2}>
                        <Tag color={error.success ? 'green' : 'red'}>
                          {error.success ? '成功' : '失败'}
                        </Tag>
                      </Descriptions.Item>
                      {error.error_message && (
                        <Descriptions.Item label="错误信息" span={2}>
                          <Text code style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
                            {error.error_message}
                          </Text>
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </Card>
                ))}
              </Space>
            </Panel>
          </Collapse>
        </Space>
      )}
    </Modal>
  )
}

export default ErrorInvestigation