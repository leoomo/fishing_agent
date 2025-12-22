import { useState, useEffect, useRef, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
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
} from '@ant-design/icons'
import { monitorApi } from '@/api/services/monitor'
import type { APIStats, LLMStats, DBPerformance, SystemHealth, RealtimeStats } from '@/types/monitor'
import type { ColumnsType } from 'antd/es/table'
import AgentAnalytics from './AgentAnalytics'
import ToolAnalytics from './ToolAnalytics'
import CostReport from './CostReport'
import FailurePatterns from '../../components/Monitor/FailurePatterns'
import RootCauseAnalysis from '../../components/Monitor/RootCauseAnalysis'

// Safe ECharts wrapper to prevent undefined errors
const SafeReactECharts = ({ option, style, ...props }: any) => {
  if (!option || typeof option !== 'object') {
    return (
      <div style={{
        ...style,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#999',
        fontSize: 16
      }}>
        暂无数据
      </div>
    )
  }

  return (
    <ReactECharts
      option={option}
      style={style}
      {...props}
    />
  )
}

const Monitor = () => {
  const [loading, setLoading] = useState(true)
  const [apiStats, setApiStats] = useState<APIStats | null>(null)
  const [llmStats, setLlmStats] = useState<LLMStats | null>(null)
  const [dbPerformance, setDbPerformance] = useState<DBPerformance | null>(null)
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [realtimeStats, setRealtimeStats] = useState<RealtimeStats | null>(null)
  const [currentUptime, setCurrentUptime] = useState<number>(0)

  const wsRef = useRef<WebSocket | null>(null)
  const uptimeTimerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    fetchAllData()
    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (uptimeTimerRef.current) {
        clearInterval(uptimeTimerRef.current)
      }
    }
  }, [])

  // 更新运行时间
  useEffect(() => {
    if (health?.uptime_seconds) {
      setCurrentUptime(health.uptime_seconds)

      // 启动定时器，每秒更新一次
      uptimeTimerRef.current = setInterval(() => {
        setCurrentUptime(prev => prev + 1)
      }, 1000)
    }

    return () => {
      if (uptimeTimerRef.current) {
        clearInterval(uptimeTimerRef.current)
      }
    }
  }, [health?.uptime_seconds])

  const fetchAllData = async () => {
    setLoading(true)
    try {
      const [api, llm, db, healthData] = await Promise.all([
        monitorApi.getApiStats(),
        monitorApi.getLlmStats(),
        monitorApi.getDbPerformance(),
        monitorApi.getHealthCheck(),
      ])
      setApiStats(api)
      setLlmStats(llm)
      setDbPerformance(db)
      setHealth(healthData)
    } catch {
      message.error('加载监控数据失败')
    } finally {
      setLoading(false)
    }
  }

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/admin/monitor/ws/realtime-stats`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (!data.error) {
        setRealtimeStats(data)
      }
    }

    ws.onerror = () => {
      // WebSocket 连接失败时静默处理
    }

    wsRef.current = ws
  }

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

  // 格式化运行时间
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)  // 86400 = 24 * 60 * 60
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)

    const parts = []

    if (days > 0) {
      parts.push(`${days}天`)
    }

    if (hours > 0) {
      parts.push(`${hours}小时`)
    }

    if (minutes > 0) {
      parts.push(`${minutes}分钟`)
    }

    // 只有当所有单位都是0或者至少有其他单位时才显示秒数
    if ((secs > 0 && parts.length > 0) || parts.length === 0) {
      parts.push(`${secs}秒`)
    }

    return parts.length > 0 ? parts.join('') : '0秒'
  }

  // API 请求趋势图
  const apiTrendOption = useMemo(() => {
    if (!apiStats || !Array.isArray(apiStats.requests_by_day)) {
      return {
        title: { text: 'API 请求趋势', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: [] },
        yAxis: { type: 'value' },
        series: [],
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: { text: '暂无数据', fontSize: 16, fill: '#999' }
        }
      }
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
    if (!llmStats || !Array.isArray(llmStats.by_day)) {
      return {
        title: { text: 'LLM Token 消耗趋势', left: 'center' },
        tooltip: { trigger: 'axis' },
        legend: { top: 30 },
        xAxis: { type: 'category', data: [] },
        yAxis: [
          { type: 'value', name: '调用次数' },
          { type: 'value', name: 'Token 数' },
        ],
        series: [],
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: { text: '暂无数据', fontSize: 16, fill: '#999' }
        }
      }
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
    if (!apiStats || !apiStats.requests_by_status) {
      return {
        title: { text: '状态码分布', left: 'center' },
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          radius: '60%',
          data: [],
        }],
        graphic: {
          type: 'text',
          left: 'center',
          top: 'middle',
          style: { text: '暂无数据', fontSize: 16, fill: '#999' }
        }
      }
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
                color: status.startsWith('2') ? '#52c41a' : status.startsWith('4') ? '#faad14' : '#ff4d4f',
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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      {/* 系统健康状态 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={24} align="middle">
          <Col span={6}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 48 }}>{getHealthStatusIcon(health?.status || 'unknown')}</div>
              <Tag color={getHealthStatusColor(health?.status || 'unknown')} style={{ marginTop: 8 }}>
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
              value={currentUptime > 0 ? formatUptime(currentUptime) : '0小时'}
              valueStyle={{ fontSize: 16 }}
            />
          </Col>
        </Row>
      </Card>

      {/* 实时统计 */}
      {realtimeStats && (
        <Alert
          message="实时统计"
          description={
            <Row gutter={24}>
              <Col span={6}>
                <span>API 请求/分钟: <strong>{realtimeStats.api_requests_per_minute}</strong></span>
              </Col>
              <Col span={6}>
                <span>LLM Token/分钟: <strong>{realtimeStats.llm_tokens_per_minute}</strong></span>
              </Col>
              <Col span={6}>
                <span>错误率: <strong>{(realtimeStats.error_rate * 100).toFixed(2)}%</strong></span>
              </Col>
              <Col span={6}>
                <span>在线用户: <strong>{realtimeStats.active_users}</strong></span>
              </Col>
            </Row>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Tabs defaultActiveKey="api">
        {/* API 统计 */}
        <Tabs.TabPane
          tab={
            <span>
              <ApiOutlined />
              API 统计
            </span>
          }
          key="api"
        >
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
                  valueStyle={{ color: (apiStats?.error_rate || 0) > 0.05 ? '#ff4d4f' : '#52c41a' }}
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
                <SafeReactECharts
                  option={apiTrendOption}
                  style={{ height: 350, width: '100%' }}
                  lazyUpdate={true}
                  notMerge={true}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <SafeReactECharts
                  option={statusCodeOption}
                  style={{ height: 350, width: '100%' }}
                  lazyUpdate={true}
                  notMerge={true}
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
        </Tabs.TabPane>

        {/* LLM 统计 */}
        <Tabs.TabPane
          tab={
            <span>
              <RobotOutlined />
              LLM 统计
            </span>
          }
          key="llm"
        >
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
            <SafeReactECharts
              option={llmTrendOption}
              style={{ height: 350, width: '100%' }}
              lazyUpdate={true}
              notMerge={true}
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
        </Tabs.TabPane>

        {/* 数据库性能 */}
        <Tabs.TabPane
          tab={
            <span>
              <DatabaseOutlined />
              数据库
            </span>
          }
          key="db"
        >
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
                  valueStyle={{ color: (dbPerformance?.slow_queries || 0) > 10 ? '#ff4d4f' : '#52c41a' }}
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
                          (dbPerformance.active_connections / dbPerformance.connection_pool_size) * 100
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
                  {dbPerformance?.active_connections || 0} / {dbPerformance?.connection_pool_size || 0}
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
        </Tabs.TabPane>

        {/* Agent 分析 */}
        <Tabs.TabPane
          tab={
            <span>
              <ThunderboltOutlined />
              Agent 分析
            </span>
          }
          key="agent"
        >
          <AgentAnalytics />
        </Tabs.TabPane>

        {/* 工具分析 */}
        <Tabs.TabPane
          tab={
            <span>
              <ToolOutlined />
              工具分析
            </span>
          }
          key="tool"
        >
          <ToolAnalytics />
        </Tabs.TabPane>

        {/* 成本报表 */}
        <Tabs.TabPane
          tab={
            <span>
              <DollarOutlined />
              成本报表
            </span>
          }
          key="cost"
        >
          <CostReport />
        </Tabs.TabPane>

        {/* 失败模式检测 */}
        <Tabs.TabPane
          tab={
            <span>
              <BugOutlined />
              失败模式
            </span>
          }
          key="failure-patterns"
        >
          <FailurePatterns />
        </Tabs.TabPane>

        {/* 根因分析 */}
        <Tabs.TabPane
          tab={
            <span>
              <SearchOutlined />
              根因分析
            </span>
          }
          key="root-cause"
        >
          <RootCauseAnalysis />
        </Tabs.TabPane>
      </Tabs>
    </div>
  )
}

export default Monitor
