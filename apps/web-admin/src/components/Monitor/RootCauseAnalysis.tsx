import React, { useState, useCallback } from 'react'
import {
  Card,
  Timeline,
  Tag,
  Button,
  Space,
  Alert,
  Tooltip,
  Typography,
  Row,
  Col,
  Statistic,
  Progress,
  Select,
  Badge,
  Collapse,
  Empty,
  Spin,
  List,
  Divider,
} from 'antd'
import {
  SearchOutlined,
  ReloadOutlined,
  BugOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useFailurePatterns } from '../../hooks/useFailurePatterns'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { Panel } = Collapse

interface RootCauseAnalysisProps {
  height?: number
}

const RootCauseAnalysis: React.FC<RootCauseAnalysisProps> = ({ height = 600 }) => {
  const {
    rootCauses,
    fetchRootCauses,
    loading,
    error,
    clearError,
  } = useFailurePatterns()

  const [selectedTimeRange, setSelectedTimeRange] = useState('24h')

  const handleRefresh = useCallback(() => {
    clearError()
    fetchRootCauses(selectedTimeRange)
  }, [fetchRootCauses, selectedTimeRange, clearError])

  const handleTimeRangeChange = useCallback((value: string) => {
    setSelectedTimeRange(value)
    fetchRootCauses(value)
  }, [fetchRootCauses])

  const getCauseIcon = (causeType: string) => {
    switch (causeType) {
      case 'rate_limiting':
        return <WarningOutlined style={{ color: '#fa8c16' }} />
      case 'timeout':
        return <ThunderboltOutlined style={{ color: '#f5222d' }} />
      case 'external_service':
        return <ExclamationCircleOutlined style={{ color: '#722ed1' }} />
      case 'tool_failure':
        return <BugOutlined style={{ color: '#eb2f96' }} />
      case 'database_connection':
      case 'database_timeout':
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />
      default:
        return <SearchOutlined style={{ color: '#52c41a' }} />
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#52c41a'
    if (confidence >= 0.6) return '#faad14'
    return '#f5222d'
  }

  const getConfidenceStatus = (confidence: number) => {
    if (confidence >= 0.8) return 'success'
    if (confidence >= 0.6) return 'normal'
    return 'exception'
  }

  const getCauseTypeColor = (causeType: string) => {
    const colors = {
      rate_limiting: 'orange',
      timeout: 'red',
      external_service: 'purple',
      tool_failure: 'pink',
      database_connection: 'blue',
      database_timeout: 'cyan',
    }
    return colors[causeType as keyof typeof colors] || 'default'
  }

  const groupByCauseType = () => {
    const groups: Record<string, any[]> = {}
    rootCauses.forEach(cause => {
      if (!groups[cause.cause_type]) {
        groups[cause.cause_type] = []
      }
      groups[cause.cause_type].push(cause)
    })
    return groups
  }

  const getCauseStats = () => {
    if (rootCauses.length === 0) return { high: 0, medium: 0, low: 0 }

    return rootCauses.reduce((acc, cause) => {
      if (cause.confidence >= 0.8) acc.high++
      else if (cause.confidence >= 0.6) acc.medium++
      else acc.low++
      return acc
    }, { high: 0, medium: 0, low: 0 })
  }

  const stats = getCauseStats()
  const groupedCauses = groupByCauseType()

  return (
    <div style={{ height }}>
      <Card
        title={
          <Space>
            <SearchOutlined />
            <span>根因分析</span>
            <Select
              value={selectedTimeRange}
              onChange={handleTimeRangeChange}
              style={{ width: 120 }}
              size="small"
            >
              <Option value="1h">最近1小时</Option>
              <Option value="6h">最近6小时</Option>
              <Option value="24h">最近24小时</Option>
              <Option value="7d">最近7天</Option>
            </Select>
          </Space>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading.rootCauses}
          >
            刷新
          </Button>
        }
        size="small"
      >
        {error && (
          <Alert
            message="根因分析时出错"
            description={error}
            type="error"
            closable
            onClose={clearError}
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Statistics Row */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic
              title="检测到的根因"
              value={rootCauses.length}
              prefix={<SearchOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="高置信度"
              value={stats.high}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="中置信度"
              value={stats.medium}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="低置信度"
              value={stats.low}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Col>
        </Row>

        <div style={{ height: 'calc(100% - 120px)', overflow: 'auto' }}>
          {loading.rootCauses ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>分析根因中...</div>
            </div>
          ) : rootCauses.length === 0 ? (
            <Empty
              description={
                <div>
                  <Text type="secondary">暂未检测到明确的根因</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    系统运行正常，或选择的时间范围内无需要分析的失败
                  </Text>
                </div>
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <Collapse defaultActiveKey={Object.keys(groupedCauses)} ghost>
              {Object.entries(groupedCauses).map(([causeType, causes]) => (
                <Panel
                  key={causeType}
                  header={
                    <Space>
                      {getCauseIcon(causeType)}
                      <Tag color={getCauseTypeColor(causeType)}>
                        {causeType.replace('_', ' ').toUpperCase()}
                      </Tag>
                      <Badge count={causes.length} style={{ backgroundColor: '#1890ff' }} />
                    </Space>
                  }
                >
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    {causes.map((cause, index) => (
                      <Card key={cause.cause_id} size="small">
                        <Row gutter={16}>
                          <Col span={16}>
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <div>
                                <Text strong>{cause.description}</Text>
                              </div>

                              <div>
                                <Text type="secondary">建议操作: </Text>
                                <Text code style={{ fontSize: 12 }}>
                                  {cause.suggested_action}
                                </Text>
                              </div>

                              {cause.evidence.length > 0 && (
                                <div>
                                  <Text type="secondary">证据:</Text>
                                  <List
                                    size="small"
                                    dataSource={cause.evidence.slice(0, 3)}
                                    renderItem={(evidence: string, idx: number) => (
                                      <List.Item key={idx}>
                                        <Text code style={{ fontSize: 11 }}>
                                          {evidence.length > 100
                                            ? `${evidence.substring(0, 100)}...`
                                            : evidence
                                          }
                                        </Text>
                                      </List.Item>
                                    )}
                                  />
                                  {cause.evidence.length > 3 && (
                                    <Text type="secondary" style={{ fontSize: 11 }}>
                                      还有 {cause.evidence.length - 3} 条证据...
                                    </Text>
                                  )}
                                </div>
                              )}
                            </Space>
                          </Col>

                          <Col span={8}>
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <div style={{ textAlign: 'center' }}>
                                <Progress
                                  type="circle"
                                  percent={Math.round(cause.confidence * 100)}
                                  size={80}
                                  strokeColor={getConfidenceColor(cause.confidence)}
                                  format={percent => (
                                    <div style={{ fontSize: 14 }}>
                                      <div>{percent}%</div>
                                      <div style={{ fontSize: 10, color: '#666' }}>置信度</div>
                                    </div>
                                  )}
                                />
                              </div>

                              <div style={{ textAlign: 'center' }}>
                                <Text type="secondary" style={{ fontSize: 11 }}>
                                  {dayjs(cause.generated_at).fromNow()}
                                </Text>
                              </div>
                            </Space>
                          </Col>
                        </Row>
                      </Card>
                    ))}
                  </Space>
                </Panel>
              ))}
            </Collapse>
          )}
        </div>
      </Card>
    </div>
  )
}

export default RootCauseAnalysis