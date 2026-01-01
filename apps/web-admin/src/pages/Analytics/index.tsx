import { useState, useEffect } from 'react'
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
} from 'antd'
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  FileTextOutlined,
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
import dayjs from 'dayjs'

const { Paragraph } = Typography

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

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    setLoading(true)
    try {
      const [statsData, trendsData, priceData, brandData] = await Promise.all([
        analyticsApi.getEquipmentStats(),
        analyticsApi.getEquipmentTrends(12),
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
  }

  const handleCategoryChange = async (category?: string) => {
    setSelectedCategory(category)
    try {
      const data = await analyticsApi.getPriceDistribution(category)
      setPriceDistribution(data)
    } catch {
      message.error('加载价格分布失败')
    }
  }

  const handleGenerateReport = async (reportType: string) => {
    setReportLoading(true)
    try {
      // 计算日期范围
      const endDate = dayjs()
      const startDate = reportType === 'weekly'
        ? endDate.subtract(7, 'day')
        : endDate.subtract(30, 'day')

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
          name: p.range,
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
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              loading={reportLoading}
              onClick={() => handleGenerateReport('weekly')}
            >
              生成周报
            </Button>
            <Button
              style={{ marginLeft: 8 }}
              icon={<FileTextOutlined />}
              loading={reportLoading}
              onClick={() => handleGenerateReport('monthly')}
            >
              生成月报
            </Button>
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
          <Card>
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
          <Card>
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
              <Card>
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
        width={800}
        footer={[
          <Button key="close" onClick={() => setReportVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {currentReport && (
          <div>
            <p style={{ color: '#999' }}>
              生成时间: {new Date(currentReport.generated_at).toLocaleString('zh-CN')}
              &nbsp;&nbsp;|&nbsp;&nbsp;
              生成人: {currentReport.generated_by}
            </p>
            <Paragraph>
              <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16 }}>
                {JSON.stringify(currentReport.report_data, null, 2)}
              </pre>
            </Paragraph>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Analytics
