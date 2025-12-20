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
  DatePicker,
  Space,
} from 'antd'
import {
  ToolOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { monitorApi } from '@/api/services/monitor'
import type { ToolStatsResponse, ToolStats } from '@/types/monitor'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

// 工具类别颜色映射
const categoryColors: Record<string, string> = {
  weather: '#1890ff',
  fishing: '#52c41a',
  lure: '#722ed1',
  equipment: '#13c2c2',
  basic: '#fa8c16',
  other: '#8c8c8c',
}

const ToolAnalytics = () => {
  const [loading, setLoading] = useState(true)
  const [toolStats, setToolStats] = useState<ToolStatsResponse | null>(null)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)

  useEffect(() => {
    fetchData()
  }, [dateRange])

  const fetchData = async () => {
    setLoading(true)
    try {
      const params: {
        start_date?: string
        end_date?: string
      } = {}

      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD')
        params.end_date = dateRange[1].format('YYYY-MM-DD')
      }

      const stats = await monitorApi.getToolStats(params)
      setToolStats(stats)
    } catch {
      message.error('加载工具统计数据失败')
    } finally {
      setLoading(false)
    }
  }

  // 工具统计表格列
  const toolColumns: ColumnsType<ToolStats> = [
    {
      title: '工具名称',
      dataIndex: 'tool_name',
      width: 200,
      render: (name: string) => (
        <Space>
          <ToolOutlined />
          {name}
        </Space>
      ),
    },
    {
      title: '类别',
      dataIndex: 'category',
      width: 100,
      render: (category: string) => (
        <Tag color={categoryColors[category] || categoryColors.other}>
          {category}
        </Tag>
      ),
      filters: Object.keys(categoryColors).map((cat) => ({ text: cat, value: cat })),
      onFilter: (value, record) => record.category === value,
    },
    {
      title: '调用次数',
      dataIndex: 'call_count',
      width: 100,
      sorter: (a, b) => a.call_count - b.call_count,
      defaultSortOrder: 'descend',
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
      render: (ms: number) => (
        <span style={{ color: ms > 1000 ? '#ff4d4f' : ms > 500 ? '#faad14' : '#52c41a' }}>
          {ms.toFixed(0)}ms
        </span>
      ),
      sorter: (a, b) => a.avg_latency_ms - b.avg_latency_ms,
    },
  ]

  // 工具调用排行图
  const toolRankOption = toolStats
    ? {
        title: { text: '工具调用排行 Top 10', left: 'center' },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '20%', right: '10%', top: 50, bottom: 30 },
        xAxis: { type: 'value', name: '调用次数' },
        yAxis: {
          type: 'category',
          data: toolStats.tools
            .slice(0, 10)
            .sort((a, b) => a.call_count - b.call_count)
            .map((t) => t.tool_name),
          axisLabel: {
            width: 150,
            overflow: 'truncate',
          },
        },
        series: [
          {
            type: 'bar',
            data: toolStats.tools
              .slice(0, 10)
              .sort((a, b) => a.call_count - b.call_count)
              .map((t) => ({
                value: t.call_count,
                itemStyle: { color: categoryColors[t.category] || categoryColors.other },
              })),
            label: {
              show: true,
              position: 'right',
              formatter: '{c}',
            },
          },
        ],
      }
    : {}

  // 类别分布饼图
  const categoryPieOption = toolStats
    ? {
        title: { text: '工具类别分布', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { top: 30 },
        series: [
          {
            type: 'pie',
            radius: ['35%', '60%'],
            center: ['50%', '55%'],
            data: Object.entries(toolStats.by_category).map(([category, count]) => ({
              name: category,
              value: count,
              itemStyle: { color: categoryColors[category] || categoryColors.other },
            })),
            label: {
              formatter: '{b}\n{d}%',
            },
          },
        ],
      }
    : {}

  // 工具延时对比图
  const latencyCompareOption = toolStats
    ? {
        title: { text: '工具平均延时对比', left: 'center' },
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          data: toolStats.tools.slice(0, 15).map((t) => t.tool_name),
          axisLabel: {
            rotate: 45,
            interval: 0,
          },
        },
        yAxis: { type: 'value', name: '延时 (ms)' },
        series: [
          {
            type: 'bar',
            data: toolStats.tools.slice(0, 15).map((t) => ({
              value: t.avg_latency_ms,
              itemStyle: {
                color:
                  t.avg_latency_ms > 1000
                    ? '#ff4d4f'
                    : t.avg_latency_ms > 500
                    ? '#faad14'
                    : '#52c41a',
              },
            })),
          },
        ],
      }
    : {}

  // 成功率热力图 (简化为条形图)
  const successRateOption = toolStats
    ? {
        title: { text: '工具成功率分布', left: 'center' },
        tooltip: { trigger: 'axis' },
        grid: { left: '20%', right: '10%', top: 50, bottom: 30 },
        xAxis: { type: 'value', name: '成功率 (%)', min: 0, max: 100 },
        yAxis: {
          type: 'category',
          data: toolStats.tools
            .slice(0, 10)
            .sort((a, b) => a.success_rate - b.success_rate)
            .map((t) => t.tool_name),
        },
        series: [
          {
            type: 'bar',
            data: toolStats.tools
              .slice(0, 10)
              .sort((a, b) => a.success_rate - b.success_rate)
              .map((t) => ({
                value: t.success_rate,
                itemStyle: {
                  color:
                    t.success_rate >= 95
                      ? '#52c41a'
                      : t.success_rate >= 80
                      ? '#faad14'
                      : '#ff4d4f',
                },
              })),
            label: {
              show: true,
              position: 'right',
              formatter: '{c}%',
            },
          },
        ],
      }
    : {}

  // 计算总体统计
  const totalCalls = toolStats?.tools.reduce((sum, t) => sum + t.call_count, 0) || 0
  const avgSuccessRate =
    toolStats && toolStats.tools.length > 0
      ? toolStats.tools.reduce((sum, t) => sum + t.success_rate, 0) / toolStats.tools.length
      : 0
  const avgLatency =
    toolStats && toolStats.tools.length > 0
      ? toolStats.tools.reduce((sum, t) => sum + t.avg_latency_ms, 0) / toolStats.tools.length
      : 0

  if (loading && !toolStats) {
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
        </Space>
      </Card>

      {/* 总体统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="工具总数"
              value={toolStats?.tools.length || 0}
              prefix={<ToolOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总调用次数"
              value={totalCalls}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均成功率"
              value={avgSuccessRate}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: avgSuccessRate >= 95 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均延时"
              value={avgLatency}
              precision={0}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: avgLatency > 500 ? '#faad14' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <ReactECharts option={toolRankOption} style={{ height: 400 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <ReactECharts option={categoryPieOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <ReactECharts option={latencyCompareOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <ReactECharts option={successRateOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      {/* 工具详情表格 */}
      <Card title="工具使用详情">
        <Table
          columns={toolColumns}
          dataSource={toolStats?.tools || []}
          rowKey="tool_name"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>
    </div>
  )
}

export default ToolAnalytics
