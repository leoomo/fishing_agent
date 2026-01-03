import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Spin,
  message,
  Tabs,
  Alert,
  Progress,
  DatePicker,
  Button,
  Space,
  Badge,
} from 'antd'
import {
  ApiOutlined,
  RobotOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  ToolOutlined,
  DollarOutlined,
  BugOutlined,
  SearchOutlined,
  ReloadOutlined,
  WifiOutlined,
  DisconnectOutlined,
  DashboardOutlined,
} from '@ant-design/icons'
import type { Dayjs } from 'dayjs'
import { monitorApi } from '@/api/services/monitor'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { APIStats, LLMStats, DBPerformance, SystemHealth, RealtimeStats } from '@/types/monitor'
import type { ColumnsType } from 'antd/es/table'
import { MonitorProvider, useMonitorContext, DATE_RANGE_PRESETS } from '@/contexts/MonitorContext'
import ChartWrapper from '@/components/Monitor/ChartWrapper'
import Overview from './Overview'
import AgentAnalytics from './AgentAnalytics'
import ToolAnalytics from './ToolAnalytics'
import CostReport from './CostReport'
import FailurePatterns from '../../components/Monitor/FailurePatterns'
import RootCauseAnalysis from '../../components/Monitor/RootCauseAnalysis'

const { RangePicker } = DatePicker

// 错误状态类型
interface ErrorStates {
  api: string | null
  llm: string | null
  db: string | null
  health: string | null
}

const MonitorContent = () => {
  const { dateRange, setDateRange, startDate, endDate, refreshKey, refresh, setLastUpdated, activeTab, setActiveTab } =
    useMonitorContext()

  const [loading, setLoading] = useState(true)
  const [apiStats, setApiStats] = useState<APIStats | null>(null)
  const [llmStats, setLlmStats] = useState<LLMStats | null>(null)
  const [dbPerformance, setDbPerformance] = useState<DBPerformance | null>(null)
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [realtimeStats, setRealtimeStats] = useState<RealtimeStats | null>(null)
  const [currentUptime, setCurrentUptime] = useState<number>(0)
  const [errors, setErrors] = useState<ErrorStates>({
    api: null,
    llm: null,
    db: null,
    health: null,
  })

  // 使用 useWebSocket hook 替代手动 WebSocket 管理
  const wsUrl = import.meta.env.DEV
    ? '/api/v1/admin/monitor/ws/realtime-stats'
    : '/api/v1/admin/monitor/ws/realtime-stats'

  const { isConnected, error: wsError, reconnectAttempts } = useWebSocket(wsUrl, {
    onMessage: (data) => {
      try {
        const stats = JSON.parse(data)
        if (!stats.error) {
          setRealtimeStats(stats)
        }
      } catch (e) {
        console.error('Failed to parse realtime stats:', e)
      }
    },
    reconnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    heartbeat: true,
    heartbeatInterval: 30000,
  })

  // 轮询降级：当 WebSocket 断开时使用轮询
  useEffect(() => {
    if (!isConnected && !wsError) {
      // WebSocket 未连接时，每10秒轮询一次
      const pollInterval = setInterval(async () => {
        try {
          // 使用现有的 API 获取最近的统计数据
          const [api] = await Promise.all([monitorApi.getApiStats()])
          if (api) {
            // 模拟实时统计
            setRealtimeStats({
              api_requests_per_minute: Math.round(api.total_requests / 1440), // 估算每分钟
              llm_tokens_per_minute: 0,
              error_rate: api.error_rate,
              active_users: 0,
            })
          }
        } catch {
          // 静默处理轮询错误
        }
      }, 10000)

      return () => clearInterval(pollInterval)
    }
  }, [isConnected, wsError])

  // 更新运行时间
  useEffect(() => {
    if (health?.uptime_seconds) {
      setCurrentUptime(health.uptime_seconds)

      const timer = setInterval(() => {
        setCurrentUptime((prev) => prev + 1)
      }, 1000)

      return () => clearInterval(timer)
    }
  }, [health?.uptime_seconds])

  const fetchAllData = useCallback(async () => {
    setLoading(true)
    const newErrors: ErrorStates = { api: null, llm: null, db: null, health: null }

    const results = await Promise.allSettled([
      monitorApi.getApiStats({ start_date: startDate, end_date: endDate }),
      monitorApi.getLlmStats({ start_date: startDate, end_date: endDate }),
      monitorApi.getDbPerformance(),
      monitorApi.getHealthCheck(),
    ])

    if (results[0].status === 'fulfilled') {
      setApiStats(results[0].value)
    } else {
      newErrors.api = results[0].reason?.message || 'API统计加载失败'
    }

    if (results[1].status === 'fulfilled') {
      setLlmStats(results[1].value)
    } else {
      newErrors.llm = results[1].reason?.message || 'LLM统计加载失败'
    }

    if (results[2].status === 'fulfilled') {
      setDbPerformance(results[2].value)
    } else {
      newErrors.db = results[2].reason?.message || '数据库性能加载失败'
    }

    if (results[3].status === 'fulfilled') {
      setHealth(results[3].value)
    } else {
      newErrors.health = results[3].reason?.message || '健康检查失败'
    }

    setErrors(newErrors)
    setLastUpdated(new Date())
    setLoading(false)

    // 如果有任何错误，显示提示
    const errorCount = Object.values(newErrors).filter(Boolean).length
    if (errorCount > 0) {
      message.warning(`部分数据加载失败 (${errorCount}个)`)
    }
  }, [startDate, endDate, setLastUpdated])

  useEffect(() => {
    fetchAllData()
  }, [fetchAllData, refreshKey])

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'degraded':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'unhealthy':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#999' }} />
    }
  }

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success'
      case 'degraded':
        return 'warning'
      case 'unhealthy':
        return 'error'
      default:
        return 'default'
    }
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)

    const parts = []
    if (days > 0) parts.push(`${days}天`)
    if (hours > 0) parts.push(`${hours}小时`)
    if (minutes > 0) parts.push(`${minutes}分钟`)
    if ((secs > 0 && parts.length > 0) || parts.length === 0) {
      parts.push(`${secs}秒`)
    }

    return parts.length > 0 ? parts.join('') : '0秒'
  }

  // API 请求趋势图
  const apiTrendOption = useMemo(() => {
    if (!apiStats || !Array.isArray(apiStats.requests_by_day) || apiStats.requests_by_day.length === 0) {
      return null
    }

    return {
      title: { text: 'API 请求趋势', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: apiStats.requests_by_day.map((d) => d.date),
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '请求数',
          type: 'line',
          data: apiStats.requests_by_day.map((d) => d.count),
          smooth: true,
          areaStyle: { opacity: 0.3 },
        },
      ],
    }
  }, [apiStats])

  // LLM Token 趋势图
  const llmTrendOption = useMemo(() => {
    if (!llmStats || !Array.isArray(llmStats.by_day) || llmStats.by_day.length === 0) {
      return null
    }

    return {
      title: { text: 'LLM Token 消耗趋势', left: 'center' },
      tooltip: { trigger: 'axis' },
      legend: { top: 30 },
      xAxis: {
        type: 'category',
        data: llmStats.by_day.map((d) => d.date),
      },
      yAxis: [
        { type: 'value', name: '调用次数' },
        { type: 'value', name: 'Token 数' },
      ],
      series: [
        {
          name: '调用次数',
          type: 'bar',
          data: llmStats.by_day.map((d) => d.calls),
        },
        {
          name: 'Token 数',
          type: 'line',
          yAxisIndex: 1,
          data: llmStats.by_day.map((d) => d.tokens),
          smooth: true,
        },
      ],
    }
  }, [llmStats])

  // 状态码分布图
  const statusCodeOption = useMemo(() => {
    if (!apiStats || !apiStats.requests_by_status || Object.keys(apiStats.requests_by_status).length === 0) {
      return null
    }

    return {
      title: { text: '状态码分布', left: 'center' },
      tooltip: { trigger: 'item' },
      series: [
        {
          type: 'pie',
          radius: '60%',
          data: Object.entries(apiStats.requests_by_status).map(([status, count]) => ({
            name: status,
            value: count,
            itemStyle: {
              color: status.startsWith('2')
                ? '#52c41a'
                : status.startsWith('4')
                ? '#faad14'
                : '#ff4d4f',
            },
          })),
        },
      ],
    }
  }, [apiStats])

  // LLM 提供商统计表格列
  const llmProviderColumns: ColumnsType<{
    provider: string
    calls: number
    tokens: number
    cost: number
    avg_latency: number
  }> = [
    { title: '提供商', dataIndex: 'provider', width: 120 },
    { title: '调用次数', dataIndex: 'calls', width: 100 },
    { title: 'Token 数', dataIndex: 'tokens', width: 120 },
    {
      title: '成本',
      dataIndex: 'cost',
      width: 100,
      render: (cost) => `¥${cost?.toFixed(4) || 0}`,
    },
    {
      title: '平均延迟',
      dataIndex: 'avg_latency',
      width: 120,
      render: (latency) => `${latency?.toFixed(0) || 0}ms`,
    },
  ]

  // 数据库表大小列
  const tableColumns: ColumnsType<{
    table: string
    size_mb: number
    row_count: number
  }> = [
    { title: '表名', dataIndex: 'table', width: 200 },
    {
      title: '大小',
      dataIndex: 'size_mb',
      width: 100,
      render: (size) => `${size?.toFixed(2) || 0} MB`,
    },
    { title: '行数', dataIndex: 'row_count', width: 100 },
  ]

  // 使用 items API 替代 Tabs.TabPane
  // 重组为分层结构：概览 -> 系统监控 -> Agent监控 -> 故障分析 -> 成本
  const tabItems = useMemo(
    () => [
      {
        key: 'overview',
        label: (
          <span>
            <DashboardOutlined /> 概览
          </span>
        ),
        children: <Overview />,
      },
      {
        key: 'api',
        label: (
          <span>
            <ApiOutlined /> API 统计
          </span>
        ),
        children: (
          <>
            <Row gutter={16}>
              <Col span={6}>
                <Card>
                  <Statistic title="总请求数" value={apiStats?.total_requests || 0} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="平均响应时间"
                    value={apiStats?.avg_response_time || 0}
                    suffix="ms"
                    precision={0}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="错误率"
                    value={(apiStats?.error_rate || 0) * 100}
                    suffix="%"
                    precision={2}
                    valueStyle={{
                      color: (apiStats?.error_rate || 0) > 0.05 ? '#ff4d4f' : '#52c41a',
                    }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="端点数"
                    value={Object.keys(apiStats?.requests_by_endpoint || {}).length}
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={16}>
                <Card>
                  <ChartWrapper
                    option={apiTrendOption}
                    style={{ height: 350, width: '100%' }}
                    error={errors.api}
                    onRetry={fetchAllData}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <ChartWrapper
                    option={statusCodeOption}
                    style={{ height: 350, width: '100%' }}
                    error={errors.api}
                    onRetry={fetchAllData}
                  />
                </Card>
              </Col>
            </Row>

            <Card title="热门端点" style={{ marginTop: 16 }}>
              <Table
                dataSource={Object.entries(apiStats?.requests_by_endpoint || {})
                  .map(([endpoint, count]) => ({ endpoint, count }))
                  .sort((a, b) => (b.count as number) - (a.count as number))
                  .slice(0, 10)}
                columns={[
                  { title: '端点', dataIndex: 'endpoint' },
                  { title: '请求数', dataIndex: 'count', width: 120 },
                ]}
                rowKey="endpoint"
                pagination={false}
                size="small"
              />
            </Card>
          </>
        ),
      },
      {
        key: 'llm',
        label: (
          <span>
            <RobotOutlined /> LLM 统计
          </span>
        ),
        children: (
          <>
            <Row gutter={16}>
              <Col span={6}>
                <Card>
                  <Statistic title="总调用次数" value={llmStats?.total_calls || 0} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="总 Token 数" value={llmStats?.total_tokens || 0} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总成本"
                    value={llmStats?.total_cost || 0}
                    prefix="¥"
                    precision={4}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="成功率"
                    value={(llmStats?.success_rate || 0) * 100}
                    suffix="%"
                    precision={2}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
            </Row>

            <Card style={{ marginTop: 16 }}>
              <ChartWrapper
                option={llmTrendOption}
                style={{ height: 350, width: '100%' }}
                error={errors.llm}
                onRetry={fetchAllData}
              />
            </Card>

            <Card title="提供商统计" style={{ marginTop: 16 }}>
              <Table
                columns={llmProviderColumns}
                dataSource={llmStats?.by_provider || []}
                rowKey="provider"
                pagination={false}
              />
            </Card>
          </>
        ),
      },
      {
        key: 'db',
        label: (
          <span>
            <DatabaseOutlined /> 数据库
          </span>
        ),
        children: (
          <>
            <Row gutter={16}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="平均查询时间"
                    value={dbPerformance?.avg_query_time || 0}
                    suffix="ms"
                    precision={2}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="慢查询数"
                    value={dbPerformance?.slow_queries || 0}
                    valueStyle={{
                      color: (dbPerformance?.slow_queries || 0) > 10 ? '#ff4d4f' : '#52c41a',
                    }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="连接池大小" value={dbPerformance?.connection_pool_size || 0} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <div style={{ marginBottom: 8 }}>活动连接</div>
                  <Progress
                    percent={
                      dbPerformance
                        ? Math.round(
                            (dbPerformance.active_connections / dbPerformance.connection_pool_size) *
                              100
                          )
                        : 0
                    }
                    status={
                      dbPerformance &&
                      dbPerformance.active_connections / dbPerformance.connection_pool_size > 0.8
                        ? 'exception'
                        : 'normal'
                    }
                  />
                  <div style={{ textAlign: 'center', color: '#999' }}>
                    {dbPerformance?.active_connections || 0} /{' '}
                    {dbPerformance?.connection_pool_size || 0}
                  </div>
                </Card>
              </Col>
            </Row>

            <Card title="表大小统计" style={{ marginTop: 16 }}>
              <Table
                columns={tableColumns}
                dataSource={dbPerformance?.table_sizes || []}
                rowKey="table"
                pagination={false}
              />
            </Card>
          </>
        ),
      },
      {
        key: 'agent',
        label: (
          <span>
            <ThunderboltOutlined /> Agent 分析
          </span>
        ),
        children: <AgentAnalytics />,
      },
      {
        key: 'tool',
        label: (
          <span>
            <ToolOutlined /> 工具分析
          </span>
        ),
        children: <ToolAnalytics />,
      },
      {
        key: 'cost',
        label: (
          <span>
            <DollarOutlined /> 成本报表
          </span>
        ),
        children: <CostReport />,
      },
      {
        key: 'failure-patterns',
        label: (
          <span>
            <BugOutlined /> 失败模式
          </span>
        ),
        children: <FailurePatterns />,
      },
      {
        key: 'root-cause',
        label: (
          <span>
            <SearchOutlined /> 根因分析
          </span>
        ),
        children: <RootCauseAnalysis />,
      },
    ],
    [
      apiStats,
      llmStats,
      dbPerformance,
      apiTrendOption,
      llmTrendOption,
      statusCodeOption,
      errors,
      fetchAllData,
      llmProviderColumns,
      tableColumns,
    ]
  )

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      {/* 时间范围选择器和刷新按钮 */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <span>时间范围：</span>
              <RangePicker
                value={dateRange}
                onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
                presets={DATE_RANGE_PRESETS.map((p) => ({
                  label: p.label,
                  value: p.value(),
                }))}
              />
            </Space>
          </Col>
          <Col>
            <Space>
              {/* WebSocket 连接状态 */}
              <Badge
                status={isConnected ? 'success' : 'error'}
                text={
                  <Space size={4}>
                    {isConnected ? (
                      <WifiOutlined style={{ color: '#52c41a' }} />
                    ) : (
                      <DisconnectOutlined style={{ color: '#ff4d4f' }} />
                    )}
                    <span style={{ fontSize: 12, color: isConnected ? '#52c41a' : '#ff4d4f' }}>
                      {isConnected
                        ? '实时连接'
                        : reconnectAttempts > 0
                        ? `重连中(${reconnectAttempts})`
                        : '已断开'}
                    </span>
                  </Space>
                }
              />
              <Button icon={<ReloadOutlined />} onClick={refresh}>
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* WebSocket 断开警告 */}
      {!isConnected && wsError && (
        <Alert
          message="实时数据连接已断开"
          description={wsError || '正在尝试重连...'}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 系统健康状态 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={24} align="middle">
          <Col span={6}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 48 }}>{getHealthStatusIcon(health?.status || 'unknown')}</div>
              <Tag
                color={getHealthStatusColor(health?.status || 'unknown')}
                style={{ marginTop: 8 }}
              >
                {health?.status?.toUpperCase() || 'UNKNOWN'}
              </Tag>
            </div>
          </Col>
          <Col span={6}>
            <Statistic
              title="API 状态"
              value={health?.api_status || '-'}
              valueStyle={{ color: health?.api_status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="数据库状态"
              value={health?.db_status || '-'}
              valueStyle={{ color: health?.db_status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="运行时间"
              value={currentUptime > 0 ? formatUptime(currentUptime) : '0秒'}
              valueStyle={{ fontSize: 16 }}
            />
          </Col>
        </Row>
      </Card>

      {/* 实时统计 */}
      {realtimeStats && (
        <Alert
          message={
            <Space>
              <span>实时统计</span>
              {isConnected ? (
                <Tag color="green" icon={<WifiOutlined />}>
                  实时
                </Tag>
              ) : (
                <Tag color="orange">轮询</Tag>
              )}
            </Space>
          }
          description={
            <Row gutter={24}>
              <Col span={6}>
                <span>
                  API 请求/分钟: <strong>{realtimeStats.api_requests_per_minute ?? 0}</strong>
                </span>
              </Col>
              <Col span={6}>
                <span>
                  LLM Token/分钟: <strong>{realtimeStats.llm_tokens_per_minute ?? 0}</strong>
                </span>
              </Col>
              <Col span={6}>
                <span>
                  错误率:{' '}
                  <strong
                    style={{
                      color: (realtimeStats.error_rate ?? 0) > 0.05 ? '#ff4d4f' : '#52c41a',
                    }}
                  >
                    {((realtimeStats.error_rate ?? 0) * 100).toFixed(2)}%
                  </strong>
                </span>
              </Col>
              <Col span={6}>
                <span>
                  活跃会话: <strong>{realtimeStats.active_users ?? 0}</strong>
                </span>
              </Col>
            </Row>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 使用 items API 替代 Tabs.TabPane，支持钻取导航 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </div>
  )
}

// 包装组件，提供 MonitorContext
const Monitor = () => {
  return (
    <MonitorProvider>
      <MonitorContent />
    </MonitorProvider>
  )
}

export default Monitor
