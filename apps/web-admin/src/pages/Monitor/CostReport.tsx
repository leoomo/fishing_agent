import { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Spin,
  message,
  DatePicker,
  Space,
  Select,
  Tag,
} from 'antd'
import {
  DollarOutlined,
  RiseOutlined,
  PieChartOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { monitorApi } from '@/api/services/monitor'
import type { CostReportResponse, CostReportItem } from '@/types/monitor'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

// Agent 颜色映射
const agentColors: Record<string, string> = {
  fishing: '#1890ff',
  equipment_import: '#52c41a',
  other: '#8c8c8c',
}

const CostReport = () => {
  const [loading, setLoading] = useState(true)
  const [costReport, setCostReport] = useState<CostReportResponse | null>(null)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ])
  const [groupBy, setGroupBy] = useState<'day' | 'week' | 'month'>('day')

  useEffect(() => {
    fetchData()
  }, [dateRange, groupBy])

  const fetchData = async () => {
    setLoading(true)
    try {
      const params: {
        start_date?: string
        end_date?: string
        group_by?: 'day' | 'week' | 'month'
      } = { group_by: groupBy }

      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }

      const report = await monitorApi.getCostReport(params)
      setCostReport(report)
    } catch {
      message.error('加载成本报表失败')
    } finally {
      setLoading(false)
    }
  }

  // 成本报表表格列
  const costColumns: ColumnsType<CostReportItem> = [
    {
      title: '日期',
      dataIndex: 'date',
      width: 120,
    },
    {
      title: 'Agent 类型',
      dataIndex: 'agent_type',
      width: 150,
      render: (type: string) => (
        <Tag color={agentColors[type] || agentColors.other}>{type}</Tag>
      ),
    },
    {
      title: '执行次数',
      dataIndex: 'executions',
      width: 100,
      sorter: (a, b) => a.executions - b.executions,
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
      render: (cost: number) => (
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
          ¥{cost.toFixed(4)}
        </span>
      ),
      sorter: (a, b) => a.total_cost - b.total_cost,
      defaultSortOrder: 'descend',
    },
    {
      title: '单次成本',
      key: 'avg_cost',
      width: 100,
      render: (_: unknown, record: CostReportItem) =>
        record.executions > 0
          ? `¥${(record.total_cost / record.executions).toFixed(4)}`
          : '-',
    },
  ]

  // 成本趋势图
  const costTrendOption = costReport
    ? {
        title: { text: '成本趋势', left: 'center' },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          formatter: (params: Array<{ name: string; seriesName: string; value: number; marker: string }>) => {
            let result = params[0].name + '<br/>'
            params.forEach((param) => {
              result += `${param.marker} ${param.seriesName}: ¥${param.value.toFixed(4)}<br/>`
            })
            return result
          },
        },
        legend: { top: 30 },
        xAxis: {
          type: 'category',
          data: [...new Set(costReport.items.map((item) => item.date))],
        },
        yAxis: { type: 'value', name: '成本 (CNY)' },
        series: Object.keys(costReport.by_agent).map((agent) => ({
          name: agent,
          type: 'line',
          stack: 'Total',
          areaStyle: { opacity: 0.5 },
          emphasis: { focus: 'series' },
          data: [...new Set(costReport.items.map((item) => item.date))].map((date) => {
            const item = costReport.items.find(
              (i) => i.date === date && i.agent_type === agent
            )
            return item?.total_cost || 0
          }),
          itemStyle: { color: agentColors[agent] || agentColors.other },
        })),
      }
    : {}

  // Agent 成本占比饼图
  const costPieOption = costReport
    ? {
        title: { text: 'Agent 成本占比', left: 'center' },
        tooltip: {
          trigger: 'item',
          formatter: (params: { name: string; value: number; percent: number }) =>
            `${params.name}: ¥${params.value.toFixed(4)} (${params.percent}%)`,
        },
        legend: { top: 30 },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '55%'],
            avoidLabelOverlap: true,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2,
            },
            label: {
              show: true,
              formatter: '{b}\n¥{c}',
            },
            data: Object.entries(costReport.by_agent).map(([agent, cost]) => ({
              name: agent,
              value: cost,
              itemStyle: { color: agentColors[agent] || agentColors.other },
            })),
          },
        ],
      }
    : {}

  // Token vs 成本相关性图
  const tokenCostOption = costReport
    ? {
        title: { text: 'Token 与成本关系', left: 'center' },
        tooltip: {
          trigger: 'item',
          formatter: (params: { data: [number, number, string] }) => {
            const [tokens, cost, agent] = params.data
            return `${agent}<br/>Token: ${tokens.toLocaleString()}<br/>成本: ¥${cost.toFixed(4)}`
          },
        },
        xAxis: { type: 'value', name: 'Token 数', scale: true },
        yAxis: { type: 'value', name: '成本 (CNY)', scale: true },
        series: [
          {
            type: 'scatter',
            symbolSize: (data: [number, number]) => Math.min(Math.sqrt(data[0]) / 5, 50),
            data: costReport.items.map((item) => [
              item.total_tokens,
              item.total_cost,
              item.agent_type,
            ]),
            itemStyle: {
              color: (params: { data: [number, number, string] }) =>
                agentColors[params.data[2]] || agentColors.other,
            },
          },
        ],
      }
    : {}

  // 日均成本统计
  const uniqueDays = costReport ? new Set(costReport.items.map((i) => i.date)).size : 1
  const dailyAvgCost = costReport ? costReport.total_cost / uniqueDays : 0
  const totalTokens = costReport?.items.reduce((sum, i) => sum + i.total_tokens, 0) || 0
  const avgCostPerToken = totalTokens > 0 && costReport ? costReport.total_cost / totalTokens : 0

  if (loading && !costReport) {
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
            日期范围：
            <RangePicker
              style={{ marginLeft: 8 }}
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
            />
          </span>
          <span>
            分组方式：
            <Select
              style={{ width: 120, marginLeft: 8 }}
              value={groupBy}
              onChange={(v) => setGroupBy(v)}
              options={[
                { label: '按日', value: 'day' },
                { label: '按周', value: 'week' },
                { label: '按月', value: 'month' },
              ]}
            />
          </span>
        </Space>
      </Card>

      {/* 总体统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总成本"
              value={costReport?.total_cost || 0}
              precision={4}
              prefix={<DollarOutlined />}
              suffix="CNY"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="日均成本"
              value={dailyAvgCost}
              precision={4}
              prefix={<RiseOutlined />}
              suffix="CNY"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总 Token 数"
              value={totalTokens}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="每千 Token 成本"
              value={avgCostPerToken * 1000}
              precision={4}
              prefix={<PieChartOutlined />}
              suffix="CNY"
            />
          </Card>
        </Col>
      </Row>

      {/* 成本趋势图 */}
      <Card style={{ marginBottom: 16 }}>
        <ReactECharts option={costTrendOption} style={{ height: 350 }} />
      </Card>

      {/* 占比和相关性 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <ReactECharts option={costPieOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <ReactECharts option={tokenCostOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      {/* 成本详情表格 */}
      <Card title="成本明细">
        <Table
          columns={costColumns}
          dataSource={costReport?.items || []}
          rowKey={(record) => `${record.date}-${record.agent_type}`}
          pagination={{ pageSize: 10 }}
          size="small"
          summary={(pageData) => {
            const totalCost = pageData.reduce((sum, item) => sum + item.total_cost, 0)
            const totalTokensPage = pageData.reduce((sum, item) => sum + item.total_tokens, 0)
            const totalExecs = pageData.reduce((sum, item) => sum + item.executions, 0)
            return (
              <Table.Summary fixed>
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0} colSpan={2}>
                    <strong>页面小计</strong>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={2}>
                    <strong>{totalExecs}</strong>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={3}>
                    <strong>{totalTokensPage.toLocaleString()}</strong>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={4}>
                    <strong style={{ color: '#52c41a' }}>¥{totalCost.toFixed(4)}</strong>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={5}>-</Table.Summary.Cell>
                </Table.Summary.Row>
              </Table.Summary>
            )
          }}
        />
      </Card>
    </div>
  )
}

export default CostReport
