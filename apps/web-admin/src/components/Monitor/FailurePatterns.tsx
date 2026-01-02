import React, { useState, useCallback } from 'react'
import {
  Card,
  Table,
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
  Empty,
  Spin,
} from 'antd'
import {
  ExclamationCircleOutlined,
  ReloadOutlined,
  BugOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { useFailurePatterns } from '../../hooks/useFailurePatterns'
import ErrorInvestigation from './ErrorInvestigation'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

const { Text } = Typography
const { Option } = Select

interface FailurePatternsProps {
  height?: number
}

const FailurePatterns: React.FC<FailurePatternsProps> = ({ height = 600 }) => {
  const {
    patterns,
    fetchPatterns,
    loading,
    error,
    clearError,
  } = useFailurePatterns()

  const [selectedTimeRange, setSelectedTimeRange] = useState('1h')
  const [investigationModal, setInvestigationModal] = useState<{
    visible: boolean
    correlationId: string | null
  }>({ visible: false, correlationId: null })

  const handleRefresh = useCallback(() => {
    clearError()
    fetchPatterns(selectedTimeRange)
  }, [fetchPatterns, selectedTimeRange, clearError])

  const handleTimeRangeChange = useCallback((value: string) => {
    setSelectedTimeRange(value)
    fetchPatterns(value)
  }, [fetchPatterns])

  const getSeverityTag = (severity: string) => {
    const colors = {
      critical: 'red',
      high: 'orange',
      medium: 'yellow',
      low: 'green',
    }
    return colors[severity as keyof typeof colors] || 'blue'
  }

  const getPatternIcon = (patternType: string) => {
    switch (patternType) {
      case 'error_burst':
        return <ThunderboltOutlined style={{ color: '#f5222d' }} />
      case 'cascading_failure':
        return <WarningOutlined style={{ color: '#fa8c16' }} />
      case 'recurring_error':
        return <ClockCircleOutlined style={{ color: '#fadb14' }} />
      case 'dependency_failure':
        return <ExclamationCircleOutlined style={{ color: '#722ed1' }} />
      default:
        return <BugOutlined style={{ color: '#1890ff' }} />
    }
  }

  const handleInvestigate = (correlationId: string) => {
    setInvestigationModal({
      visible: true,
      correlationId,
    })
  }

  const columns = [
    {
      title: '类型',
      dataIndex: 'pattern_type',
      key: 'pattern_type',
      width: 120,
      render: (type: string) => (
        <Space>
          {getPatternIcon(type)}
          <Text>{type.replace('_', ' ')}</Text>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => (
        <Tag color={getSeverityTag(severity)}>
          {severity.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '频率',
      dataIndex: 'frequency',
      key: 'frequency',
      width: 80,
      sorter: (a: any, b: any) => a.frequency - b.frequency,
      render: (frequency: number) => (
        <Badge count={frequency} style={{ backgroundColor: '#1890ff' }} />
      ),
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 100,
      render: (confidence: number) => (
        <Progress
          percent={Math.round(confidence * 100)}
          size="small"
          status={confidence >= 0.8 ? 'success' : confidence >= 0.6 ? 'normal' : 'exception'}
        />
      ),
    },
    {
      title: '影响服务',
      dataIndex: 'affected_services',
      key: 'affected_services',
      width: 150,
      render: (services: string[]) => (
        <Space wrap>
          {services.slice(0, 2).map(service => (
            <Tag key={service}>
              {service}
            </Tag>
          ))}
          {services.length > 2 && (
            <Tag>+{services.length - 2}</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '检测时间',
      dataIndex: 'detected_at',
      key: 'detected_at',
      width: 120,
      render: (time: string) => (
        <Tooltip title={dayjs(time).format('YYYY-MM-DD HH:mm:ss')}>
          <Text>{dayjs(time).fromNow()}</Text>
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: any, record: any) => (
        <Space>
          <Tooltip title="调查错误详情">
            <Button
              type="link"
              size="small"
              icon={<BugOutlined />}
              onClick={() => {
                const correlationId = record.metadata?.correlation_id
                if (correlationId) {
                  handleInvestigate(correlationId)
                }
              }}
              disabled={!record.metadata?.correlation_id}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  const getPatternStats = () => {
    if (patterns.length === 0) return { critical: 0, high: 0, medium: 0, low: 0 }

    return patterns.reduce((acc, pattern) => {
      acc[pattern.severity as keyof typeof acc]++
      return acc
    }, { critical: 0, high: 0, medium: 0, low: 0 })
  }

  const stats = getPatternStats()

  return (
    <div style={{ height }}>
      <Card
        title={
          <Space>
            <BugOutlined />
            <span>失败模式检测</span>
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
            loading={loading.patterns}
          >
            刷新
          </Button>
        }
        size="small"
      >
        {error && (
          <Alert
            message="获取失败模式时出错"
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
              title="总模式数"
              value={patterns.length}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="严重模式"
              value={stats.critical}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="高危模式"
              value={stats.high}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="平均置信度"
              value={patterns.length > 0 ? Math.round(patterns.reduce((acc, p) => acc + p.confidence, 0) / patterns.length * 100) : 0}
              suffix="%"
              prefix={<InfoCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
        </Row>

        {/* Pattern Distribution */}
        {patterns.length > 0 && (
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={24}>
              <Card size="small" title="模式严重程度分布">
                <Row gutter={16}>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#f5222d' }}>{stats.critical}</div>
                      <div>严重</div>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#fa8c16' }}>{stats.high}</div>
                      <div>高危</div>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#fadb14' }}>{stats.medium}</div>
                      <div>中等</div>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#52c41a' }}>{stats.low}</div>
                      <div>低危</div>
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        )}

        {/* Patterns Table */}
        <div style={{ height: 'calc(100% - 200px)', overflow: 'auto' }}>
          {loading.patterns ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>分析失败模式中...</div>
            </div>
          ) : patterns.length === 0 ? (
            <Empty
              description={
                <div>
                  <Text type="secondary">暂未检测到失败模式</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    系统运行正常，或选择的时间范围内无异常模式
                  </Text>
                </div>
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <Table
              columns={columns}
              dataSource={patterns}
              rowKey="pattern_id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `${range[0]}-${range[1]} / ${total} 个模式`,
              }}
              size="small"
              scroll={{ y: 'calc(100vh - 400px)' }}
            />
          )}
        </div>
      </Card>

      {/* Error Investigation Modal */}
      <ErrorInvestigation
        correlationId={investigationModal.correlationId!}
        visible={investigationModal.visible}
        onClose={() => setInvestigationModal({ visible: false, correlationId: null })}
      />
    </div>
  )
}

export default FailurePatterns