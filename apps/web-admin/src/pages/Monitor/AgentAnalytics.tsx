import { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Spin,
  message,
  Select,
  DatePicker,
  Space,
  Tooltip,
} from 'antd'
import {
  RocketOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  DownloadOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { monitorApi } from '@/api/services/monitor'
import type {
  AgentStatsResponse,
  AgentStats,
  LatencyPercentiles,
  AgentTrendsResponse,
} from '@/types/monitor'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { Button } from 'antd'
import { exportToCSV, getExportFilename } from '@/utils/export'
import { useMonitorContext } from '@/contexts/MonitorContext'

const { RangePicker } = DatePicker

const AgentAnalytics = () => {
  const { setAgentTypeFilter, setActiveTab } = useMonitorContext()
  const [loading, setLoading] = useState(true)
  const [agentStats, setAgentStats] = useState<AgentStatsResponse | null>(null)
  const [latencyPercentiles, setLatencyPercentiles] = useState<LatencyPercentiles | null>(null)
  const [agentTrends, setAgentTrends] = useState<AgentTrendsResponse | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>(undefined)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)

  // 钻取到工具分析页面
  const handleDrillToTools = (agentType: string) => {
    setAgentTypeFilter(agentType)
    setActiveTab('tool')
  }

  useEffect(() => {
    fetchData()
  }, [selectedAgent, dateRange])

  const fetchData = async () => {
    setLoading(true)
    try {
      const params: {
        agent_type?: string
        start_date?: string
        end_date?: string
      } = {}

      if (selectedAgent) {
        params.agent_type = selectedAgent
      }
      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }

      const [stats, latency, trends] = await Promise.all([
        monitorApi.getAgentStats(params),
        monitorApi.getLatencyPercentiles({
          agent_type: selectedAgent,
          start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        }),
        monitorApi.getAgentTrends({
          agent_type: selectedAgent,
          days: 30,
        }),
      ])

      setAgentStats(stats)
      setLatencyPercentiles(latency)
      setAgentTrends(trends)
    } catch {
      message.error('加载 Agent 统计数据失败')
    } finally {
      setLoading(false)
    }
  }

  // Agent 类型选项
  const agentOptions = [
    { label: '全部 Agent', value: '' },
    { label: 'Fishing Agent', value: 'fishing' },
    { label: 'Equipment Import Agent', value: 'equipment_import' },
  ]

  // Agent 统计表格列
  const agentColumns: ColumnsType<AgentStats> = [
    {
      title: 'Agent 类型',
      dataIndex: 'agent_type',
      width: 180,
      render: (type: string) => (
        <Tag color={type === 'fishing' ? 'blue' : 'green'}>{type}</Tag>
      ),
    },
    {
      title: '执行次数',
      dataIndex: 'total_executions',
      width: 100,
      sorter: (a, b) => a.total_executions - b.total_executions,
    },
    {
      title: '成功率',
      dataIndex: 'success_rate',
      width: 120,
      render: (rate: number) => (
        <span style={{ color: rate >= 95 ? '#52c41a' : rate >= 80 ? '#faad14' : '#ff4d4f' }}>
          {rate.toFixed(1)}%
        </span>
      ),
      sorter: (a, b) => a.success_rate - b.success_rate,
    },
    {
      title: '平均延时',
      dataIndex: 'avg_latency_ms',
      width: 120,
      render: (ms: number) => `${ms.toFixed(0)}ms`,
      sorter: (a, b) => a.avg_latency_ms - b.avg_latency_ms,
    },
    {
      title: 'Token 数',
      dataIndex: 'total_tokens',
      width: 120,
      render: (tokens: number) => tokens.toLocaleString(),
      sorter: (a, b) => a.total_tokens - b.total_tokens,
    },
    {
      title: '成本',
      dataIndex: 'total_cost',
      width: 100,
      render: (cost: number) => `¥${cost.toFixed(2)}`,
      sorter: (a, b) => a.total_cost - b.total_cost,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: AgentStats) => (
        <Tooltip title="查看该 Agent 使用的工具">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleDrillToTools(record.agent_type)}
            size="small"
          >
            工具
          </Button>
        </Tooltip>
      ),
    },
  ]

  // 执行趋势图
  const trendOption = agentTrends
    ? {
        title: { text: 'Agent 执行趋势', left: 'center' },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
        },
        legend: { top: 30, data: ['执行次数', 'Token 数', '成功率'] },
        xAxis: {
          type: 'category',
          data: agentTrends.trends.map((t) => t.date),
        },
        yAxis: [
          { type: 'value', name: '执行次数', position: 'left' },
          { type: 'value', name: '成功率 (%)', position: 'right', min: 0, max: 100 },
        ],
        series: [
          {
            name: '执行次数',
            type: 'bar',
            data: agentTrends.trends.map((t) => t.executions),
            itemStyle: { color: '#1890ff' },
          },
          {
            name: 'Token 数',
            type: 'line',
            data: agentTrends.trends.map((t) => t.tokens),
            smooth: true,
            itemStyle: { color: '#722ed1' },
          },
          {
            name: '成功率',
            type: 'line',
            yAxisIndex: 1,
            data: agentTrends.trends.map((t) => t.success_rate),
            smooth: true,
            itemStyle: { color: '#52c41a' },
          },
        ],
      }
    : {}

  // 延时百分位图
  const latencyOption = latencyPercentiles
    ? {
        title: { text: '响应延时百分位', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: ['最小', 'P50', 'P90', 'P99', '最大'],
        },
        yAxis: {
          type: 'value',
          name: '延时 (ms)',
        },
        series: [
          {
            type: 'bar',
            data: [
              { value: latencyPercentiles.min, itemStyle: { color: '#52c41a' } },
              { value: latencyPercentiles.p50, itemStyle: { color: '#1890ff' } },
              { value: latencyPercentiles.p90, itemStyle: { color: '#faad14' } },
              { value: latencyPercentiles.p99, itemStyle: { color: '#ff7a45' } },
              { value: latencyPercentiles.max, itemStyle: { color: '#ff4d4f' } },
            ],
            label: {
              show: true,
              position: 'top',
              formatter: '{c}ms',
            },
          },
        ],
      }
    : {}

  // Token 使用对比图
  const tokenCompareOption = agentStats
    ? {
        title: { text: 'Agent Token 使用对比', left: 'center' },
        tooltip: { trigger: 'item' },
        legend: { top: 30 },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2,
            },
            label: {
              show: true,
              formatter: '{b}: {d}%',
            },
            data: agentStats.agents.map((agent) => ({
              name: agent.agent_type,
              value: agent.total_tokens,
            })),
          },
        ],
      }
    : {}

  // 成功率迷你趋势图（替代仪表盘）
  const getSuccessRateTrendOption = (_agentType: string) => {
    if (!agentTrends?.trends) return null
    const trendData = agentTrends.trends.slice(-7) // 最近7天
    if (trendData.length === 0) return null

    return {
      grid: { top: 5, right: 5, bottom: 5, left: 5 },
      xAxis: { type: 'category', show: false, data: trendData.map(t => t.date) },
      yAxis: { type: 'value', show: false, min: 0, max: 100 },
      series: [{
        type: 'line',
        data: trendData.map(t => t.success_rate),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#52c41a' },
        areaStyle: { color: 'rgba(82,196,26,0.1)' },
      }],
    }
  }

  // 导出 CSV
  const handleExport = () => {
    if (!agentStats?.agents || agentStats.agents.length === 0) {
      message.warning('没有数据可以导出')
      return
    }

    const exportColumns = [
      { title: 'Agent 类型', dataIndex: 'agent_type' },
      { title: '执行次数', dataIndex: 'total_executions' },
      { title: '成功率 (%)', dataIndex: 'success_rate', render: (v: unknown) => Number(v).toFixed(1) },
      { title: '平均延时 (ms)', dataIndex: 'avg_latency_ms', render: (v: unknown) => Number(v).toFixed(0) },
      { title: 'Token 数', dataIndex: 'total_tokens' },
      { title: '成本 (CNY)', dataIndex: 'total_cost', render: (v: unknown) => Number(v).toFixed(4) },
    ]

    exportToCSV(agentStats.agents as unknown as Record<string, unknown>[], exportColumns, getExportFilename('agent_stats'))
    message.success('导出成功')
  }

  if (loading && !agentStats) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      {/* 筛选器 */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="large">
          <span>
            Agent 类型：
            <Select
              style={{ width: 200, marginLeft: 8 }}
              options={agentOptions}
              value={selectedAgent || ''}
              onChange={(v) => setSelectedAgent(v || undefined)}
              placeholder="选择 Agent"
            />
          </span>
          <span>
            日期范围：
            <RangePicker
              style={{ marginLeft: 8 }}
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
            />
          </span>
        </Space>
      </Card>

      {/* 总体统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总执行次数"
              value={agentStats?.total_executions || 0}
              prefix={<RocketOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总 Token 数"
              value={agentStats?.total_tokens || 0}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总成本"
              value={agentStats?.total_cost || 0}
              prefix={<DollarOutlined />}
              precision={2}
              suffix="CNY"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Agent 数量"
              value={agentStats?.agents?.length || 0}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Agent 成功率卡片 */}
      {agentStats && agentStats.agents.length > 0 && (
        <Card title="Agent 成功率" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            {agentStats.agents.map((agent) => {
              const successRateTrendOption = getSuccessRateTrendOption(agent.agent_type)
              const rateColor = agent.success_rate >= 95 ? '#52c41a' : agent.success_rate >= 80 ? '#faad14' : '#ff4d4f'

              return (
                <Col span={12} key={agent.agent_type}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <Tag color={agent.agent_type === 'fishing' ? 'blue' : 'green'} style={{ marginBottom: 8 }}>
                      {agent.agent_type}
                    </Tag>
                    <div style={{ fontSize: 36, fontWeight: 'bold', color: rateColor }}>
                      {agent.success_rate.toFixed(1)}%
                    </div>
                    <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>
                      成功率 ({agent.total_executions} 次执行)
                    </div>
                    {successRateTrendOption && (
                      <ReactECharts
                        option={successRateTrendOption}
                        style={{ height: 40 }}
                        opts={{ renderer: 'svg' }}
                      />
                    )}
                    <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                      最近7天趋势
                    </div>
                  </Card>
                </Col>
              )
            })}
          </Row>
        </Card>
      )}

      {/* 趋势和延时图表 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={16}>
          <Card>
            <ReactECharts option={trendOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <ReactECharts option={latencyOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      {/* Token 使用对比 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <ReactECharts option={tokenCompareOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title="Agent 执行统计详情"
            extra={
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={handleExport}
                size="small"
                disabled={!agentStats?.agents || agentStats.agents.length === 0}
              >
                导出 CSV
              </Button>
            }
          >
            <Table
              columns={agentColumns}
              dataSource={agentStats?.agents || []}
              rowKey="agent_type"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default AgentAnalytics
