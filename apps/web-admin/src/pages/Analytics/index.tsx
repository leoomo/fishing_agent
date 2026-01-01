import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Select,
  Button,
  Spin,
  message,
  Tabs,
  Modal,
  Typography,
  DatePicker,
  Space,
  Descriptions,
} from 'antd'
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  FileTextOutlined,
  DownloadOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { analyticsApi } from '@/api/services/analytics'
import type {
  EquipmentStats,
  EquipmentTrend,
  PriceDistribution,
  BrandStats,
  BusinessReport,
} from '@/types/analytics'
import type { ColumnsType } from 'antd/es/table'
import dayjs, { Dayjs } from 'dayjs'

const { Paragraph, Text } = Typography
const { RangePicker } = DatePicker

// CSV 导出工具函数
const exportToCSV = (data: Record<string, unknown>[], filename: string) => {
  if (!data || data.length === 0) {
    message.warning('没有数据可导出')
    return
  }

  const headers = Object.keys(data[0])
  const csvRows = [
    headers.join(','),
    ...data.map((row) =>
      headers.map((h) => {
        const val = row[h]
        // 处理包含逗号或引号的值
        if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
          return `"${val.replace(/"/g, '""')}"`
        }
        return val
      }).join(',')
    ),
  ]

  const csvContent = '\uFEFF' + csvRows.join('\n') // BOM for Excel UTF-8
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
  link.click()
  URL.revokeObjectURL(url)
  message.success('导出成功')
}

const Analytics = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<EquipmentStats | null>(null)
  const [trends, setTrends] = useState<EquipmentTrend[]>([])
  const [priceDistribution, setPriceDistribution] = useState<PriceDistribution[]>([])
  const [brandStats, setBrandStats] = useState<BrandStats[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>()
  const [reportLoading, setReportLoading] = useState(false)
  const [reportVisible, setReportVisible] = useState(false)
  const [currentReport, setCurrentReport] = useState<BusinessReport | null>(null)

  // 日期范围状态
  const [trendDateRange, setTrendDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(12, 'month'),
    dayjs(),
  ])
  const [reportDateRange, setReportDateRange] = useState<[Dayjs, Dayjs] | null>(null)

  const fetchAllData = useCallback(async () => {
    setLoading(true)
    try {
      // 计算月数
      const months = Math.ceil(trendDateRange[1].diff(trendDateRange[0], 'month', true)) || 12

      const [statsData, trendsData, priceData, brandData] = await Promise.all([
        analyticsApi.getEquipmentStats(),
        analyticsApi.getEquipmentTrends(months),
        analyticsApi.getPriceDistribution(),
        analyticsApi.getBrandStats(10),
      ])
      setStats(statsData)
      setTrends(trendsData)
      setPriceDistribution(priceData)
      setBrandStats(brandData)
    } catch {
      message.error('加载分析数据失败')
    } finally {
      setLoading(false)
    }
  }, [trendDateRange])

  useEffect(() => {
    fetchAllData()
  }, [fetchAllData])

  const handleCategoryChange = async (category?: string) => {
    setSelectedCategory(category)
    try {
      const data = await analyticsApi.getPriceDistribution(category)
      setPriceDistribution(data)
    } catch {
      message.error('加载价格分布失败')
    }
  }

  const handleTrendDateChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    if (dates && dates[0] && dates[1]) {
      setTrendDateRange([dates[0], dates[1]])
    }
  }

  const handleGenerateReport = async (reportType: string) => {
    setReportLoading(true)
    try {
      let startDate: Dayjs
      let endDate: Dayjs

      if (reportDateRange) {
        startDate = reportDateRange[0]
        endDate = reportDateRange[1]
      } else {
        endDate = dayjs()
        startDate = reportType === 'weekly'
          ? endDate.subtract(7, 'day')
          : endDate.subtract(30, 'day')
      }

      const report = await analyticsApi.generateReport({
        report_type: reportType,
        start_date: startDate.format('YYYY-MM-DD'),
        end_date: endDate.format('YYYY-MM-DD'),
      })
      setCurrentReport(report)
      setReportVisible(true)
      message.success('报表生成成功')
    } catch {
      message.error('生成报表失败')
    } finally {
      setReportLoading(false)
    }
  }

  // 导出趋势数据
  const handleExportTrends = () => {
    const data = trends.map((t) => ({
      日期: t.date,
      总数量: t.total_count,
      ...t.by_category,
    }))
    exportToCSV(data, '装备趋势')
  }

  // 导出品牌数据
  const handleExportBrands = () => {
    const data = brandStats.map((b, index) => ({
      排名: index + 1,
      品牌: b.brand_name,
      装备数量: b.equipment_count,
      平均价格: b.avg_price,
      占比: `${b.percentage}%`,
    }))
    exportToCSV(data, '品牌排行')
  }

  // 导出价格分布
  const handleExportPriceDistribution = () => {
    const data = priceDistribution.map((p) => ({
      价格区间: p.price_range,
      数量: p.count,
      占比: `${p.percentage}%`,
    }))
    exportToCSV(data, '价格分布')
  }

  // 趋势图配置
  const trendChartOption = {
    title: { text: '装备数量趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: trends.map((t) => t.date),
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '装备数量',
        type: 'line',
        data: trends.map((t) => t.total_count),
        smooth: true,
        areaStyle: { opacity: 0.3 },
      },
    ],
  }

  // 价格分布图配置
  const priceChartOption = {
    title: { text: '价格分布', left: 'center' },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: priceDistribution.map((p) => ({
          name: p.price_range,
          value: p.count,
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }

  // 品牌排行图配置
  const brandChartOption = {
    title: { text: 'Top 10 品牌', left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: brandStats.map((b) => b.brand_name).reverse(),
    },
    series: [
      {
        name: '装备数量',
        type: 'bar',
        data: brandStats.map((b) => b.equipment_count).reverse(),
        itemStyle: {
          color: '#1890ff',
        },
      },
    ],
  }

  // 类别分布图配置
  const categoryChartOption = stats
    ? {
        title: { text: '装备类别分布', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        series: [
          {
            type: 'pie',
            radius: '60%',
            data: Object.entries(stats.by_category).map(([name, value]) => ({
              name,
              value,
            })),
          },
        ],
      }
    : {}

  const brandColumns: ColumnsType<BrandStats> = [
    { title: '排名', width: 60, render: (_, __, index) => index + 1 },
    { title: '品牌', dataIndex: 'brand_name', width: 150 },
    { title: '装备数量', dataIndex: 'equipment_count', width: 100 },
    {
      title: '平均价格',
      dataIndex: 'avg_price',
      width: 120,
      render: (price) => `¥${price?.toFixed(0) || 0}`,
    },
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
      <Card title="数据分析" style={{ marginBottom: 16 }}>
        <Row gutter={24}>
          <Col span={6}>
            <Statistic
              title="装备总数"
              value={stats?.total_equipment || 0}
              prefix={<BarChartOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic title="品牌总数" value={stats?.total_brands || 0} />
          </Col>
          <Col span={6}>
            <Statistic
              title="平均价格"
              value={stats?.avg_price || 0}
              prefix="¥"
              precision={0}
            />
          </Col>
          <Col span={6}>
            <Space direction="vertical" size="small">
              <Space>
                <Button
                  type="primary"
                  icon={<FileTextOutlined />}
                  loading={reportLoading}
                  onClick={() => handleGenerateReport('weekly')}
                >
                  周报
                </Button>
                <Button
                  icon={<FileTextOutlined />}
                  loading={reportLoading}
                  onClick={() => handleGenerateReport('monthly')}
                >
                  月报
                </Button>
              </Space>
              <RangePicker
                size="small"
                value={reportDateRange}
                onChange={(dates) => setReportDateRange(dates as [Dayjs, Dayjs] | null)}
                placeholder={['自定义开始', '自定义结束']}
                style={{ width: '100%' }}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      <Tabs defaultActiveKey="trends">
        <Tabs.TabPane
          tab={
            <span>
              <LineChartOutlined />
              趋势分析
            </span>
          }
          key="trends"
        >
          <Card
            extra={
              <Space>
                <RangePicker
                  picker="month"
                  value={trendDateRange}
                  onChange={handleTrendDateChange}
                />
                <Button icon={<ReloadOutlined />} onClick={fetchAllData}>
                  刷新
                </Button>
                <Button icon={<DownloadOutlined />} onClick={handleExportTrends}>
                  导出 CSV
                </Button>
              </Space>
            }
          >
            <ReactECharts option={trendChartOption} style={{ height: 400 }} />
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane
          tab={
            <span>
              <PieChartOutlined />
              价格分布
            </span>
          }
          key="price"
        >
          <Card
            extra={
              <Button icon={<DownloadOutlined />} onClick={handleExportPriceDistribution}>
                导出 CSV
              </Button>
            }
          >
            <div style={{ marginBottom: 16 }}>
              <Select
                placeholder="选择类别"
                style={{ width: 150 }}
                allowClear
                value={selectedCategory}
                onChange={handleCategoryChange}
              >
                <Select.Option value="鱼竿">鱼竿</Select.Option>
                <Select.Option value="渔轮">渔轮</Select.Option>
                <Select.Option value="鱼线">鱼线</Select.Option>
                <Select.Option value="拟饵">拟饵</Select.Option>
              </Select>
            </div>
            <ReactECharts option={priceChartOption} style={{ height: 400 }} />
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane
          tab={
            <span>
              <BarChartOutlined />
              品牌排行
            </span>
          }
          key="brands"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Card
                extra={
                  <Button icon={<DownloadOutlined />} onClick={handleExportBrands}>
                    导出 CSV
                  </Button>
                }
              >
                <ReactECharts option={brandChartOption} style={{ height: 400 }} />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="品牌详情">
                <Table
                  columns={brandColumns}
                  dataSource={brandStats}
                  rowKey="brand_id"
                  pagination={false}
                  size="small"
                />
              </Card>
            </Col>
          </Row>
        </Tabs.TabPane>

        <Tabs.TabPane
          tab={
            <span>
              <PieChartOutlined />
              类别分布
            </span>
          }
          key="category"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Card>
                <ReactECharts option={categoryChartOption} style={{ height: 400 }} />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="装备类别详情">
                {stats && (
                  <Table
                    dataSource={Object.entries(stats.by_category).map(
                      ([category, count]) => ({ category, count })
                    )}
                    columns={[
                      { title: '装备类别', dataIndex: 'category' },
                      { title: '装备数量', dataIndex: 'count' },
                    ]}
                    rowKey="category"
                    pagination={false}
                    size="small"
                  />
                )}
              </Card>
            </Col>
          </Row>
        </Tabs.TabPane>
      </Tabs>

      <Modal
        title={`${currentReport?.report_type === 'weekly' ? '周报' : '月报'} - ${currentReport?.start_date} 至 ${currentReport?.end_date}`}
        open={reportVisible}
        onCancel={() => setReportVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setReportVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {currentReport && (
          <div>
            <p style={{ color: '#999', marginBottom: 16 }}>
              生成时间: {new Date(currentReport.generated_at).toLocaleString('zh-CN')}
              &nbsp;&nbsp;|&nbsp;&nbsp;
              生成人: {currentReport.generated_by}
            </p>

            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="装备统计" style={{ marginBottom: 16 }}>
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="新增装备">
                      <Text strong>{currentReport.report_data?.equipment?.new_count || 0}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="总装备数">
                      {currentReport.report_data?.equipment?.total_count || 0}
                    </Descriptions.Item>
                    <Descriptions.Item label="平均价格">
                      ¥{(currentReport.report_data?.equipment?.avg_price || 0).toFixed(0)}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="用户统计" style={{ marginBottom: 16 }}>
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="新增用户">
                      <Text strong>{currentReport.report_data?.users?.new_count || 0}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="活跃用户">
                      {currentReport.report_data?.users?.active_count || 0}
                    </Descriptions.Item>
                    <Descriptions.Item label="总用户数">
                      {currentReport.report_data?.users?.total_count || 0}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="API 统计">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="总调用量">
                      <Text strong>{currentReport.report_data?.api?.total_requests || 0}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="平均响应时间">
                      {(currentReport.report_data?.api?.avg_response_time || 0).toFixed(1)} ms
                    </Descriptions.Item>
                    <Descriptions.Item label="成功率">
                      {((currentReport.report_data?.api?.success_rate || 0) * 100).toFixed(1)}%
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="LLM 统计">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="总调用量">
                      <Text strong>{currentReport.report_data?.llm?.total_calls || 0}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="总 Token 数">
                      {(currentReport.report_data?.llm?.total_tokens || 0).toLocaleString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="平均延迟">
                      {(currentReport.report_data?.llm?.avg_latency || 0).toFixed(0)} ms
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>

            <div style={{ marginTop: 16 }}>
              <Paragraph>
                <Text type="secondary">原始数据：</Text>
                <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 12, fontSize: 12 }}>
                  {JSON.stringify(currentReport.report_data, null, 2)}
                </pre>
              </Paragraph>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Analytics
