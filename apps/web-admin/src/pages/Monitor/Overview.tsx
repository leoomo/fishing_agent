import { useEffect, useState, useMemo } from 'react'
import { Card, Row, Col, Statistic, Progress, Tag, Space, Spin, Alert, Divider } from 'antd'
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ApiOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  RiseOutlined,
  FallOutlined,
  CloudOutlined,
  MessageOutlined,
  ToolOutlined,
  CompassOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { monitorApi } from '@/api/services/monitor'
import { useMonitorContext } from '@/contexts/MonitorContext'
import type { APIStats, LLMStats, DBPerformance, SystemHealth, AgentStatsResponse, ToolStatsResponse } from '@/types/monitor'

interface OverviewData {
  apiStats: APIStats | null
  llmStats: LLMStats | null
  dbPerformance: DBPerformance | null
  health: SystemHealth | null
  agentStats: AgentStatsResponse | null
  toolStats: ToolStatsResponse | null
}

const Overview = () => {
  const { startDate, endDate, refreshKey } = useMonitorContext()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<OverviewData>({
    apiStats: null,
    llmStats: null,
    dbPerformance: null,
    health: null,
    agentStats: null,
    toolStats: null,
  })

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const results = await Promise.allSettled([
          monitorApi.getApiStats({ start_date: startDate, end_date: endDate }),
          monitorApi.getLlmStats({ start_date: startDate, end_date: endDate }),
          monitorApi.getDbPerformance(),
          monitorApi.getHealthCheck(),
          monitorApi.getAgentStats({ start_date: startDate, end_date: endDate }),
          monitorApi.getToolStats({ start_date: startDate, end_date: endDate }),
        ])

        setData({
          apiStats: results[0].status === 'fulfilled' ? results[0].value : null,
          llmStats: results[1].status === 'fulfilled' ? results[1].value : null,
          dbPerformance: results[2].status === 'fulfilled' ? results[2].value : null,
          health: results[3].status === 'fulfilled' ? results[3].value : null,
          agentStats: results[4].status === 'fulfilled' ? results[4].value : null,
          toolStats: results[5].status === 'fulfilled' ? results[5].value : null,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [startDate, endDate, refreshKey])

  const getHealthStatus = () => {
    const status = data.health?.status || 'unknown'
    const config = {
      healthy: { color: '#52c41a', icon: <CheckCircleOutlined />, text: '系统健康' },
      degraded: { color: '#faad14', icon: <WarningOutlined />, text: '系统降级' },
      unhealthy: { color: '#ff4d4f', icon: <CloseCircleOutlined />, text: '系统异常' },
      unknown: { color: '#999', icon: <ClockCircleOutlined />, text: '未知状态' },
    }
    return config[status as keyof typeof config] || config.unknown
  }

  // 迷你趋势图配置
  const miniTrendOption = useMemo(() => {
    const days = data.apiStats?.requests_by_day || []
    if (days.length === 0) return null

    return {
      grid: { top: 5, right: 5, bottom: 5, left: 5 },
      xAxis: { type: 'category', show: false, data: days.map(d => d.date) },
      yAxis: { type: 'value', show: false },
      series: [{
        type: 'line',
        data: days.map(d => d.count),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#1890ff' },
        areaStyle: { color: 'rgba(24,144,255,0.1)' },
      }],
    }
  }, [data.apiStats])

  // Token 趋势图配置
  const tokenTrendOption = useMemo(() => {
    const days = data.llmStats?.by_day || []
    if (days.length === 0) return null

    return {
      grid: { top: 5, right: 5, bottom: 5, left: 5 },
      xAxis: { type: 'category', show: false, data: days.map(d => d.date) },
      yAxis: { type: 'value', show: false },
      series: [{
        type: 'line',
        data: days.map(d => d.tokens),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#722ed1' },
        areaStyle: { color: 'rgba(114,46,209,0.1)' },
      }],
    }
  }, [data.llmStats])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (error) {
    return <Alert type="error" message="加载失败" description={error} showIcon />
  }

  const healthStatus = getHealthStatus()
  const errorRate = (data.apiStats?.error_rate || 0) * 100
  const successRate = (data.llmStats?.success_rate || 0) * 100

  return (
    <div>
      {/* 系统状态概览 */}
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 48, color: healthStatus.color }}>
                {healthStatus.icon}
              </div>
              <Tag color={healthStatus.color} style={{ marginTop: 8 }}>
                {healthStatus.text}
              </Tag>
              <div style={{ marginTop: 16, color: '#666', fontSize: 12 }}>
                API: {data.health?.api_status || '-'} | DB: {data.health?.db_status || '-'}
              </div>
            </div>
          </Card>
        </Col>

        <Col span={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <ApiOutlined />
                  <span>API 请求</span>
                </Space>
              }
              value={data.apiStats?.total_requests || 0}
              suffix={
                <span style={{ fontSize: 12, color: errorRate > 5 ? '#ff4d4f' : '#52c41a' }}>
                  {errorRate > 5 ? <FallOutlined /> : <RiseOutlined />}
                  {errorRate.toFixed(1)}% 错误率
                </span>
              }
            />
            {miniTrendOption && (
              <ReactECharts
                option={miniTrendOption}
                style={{ height: 50, marginTop: 8 }}
                opts={{ renderer: 'svg' }}
              />
            )}
          </Card>
        </Col>

        <Col span={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <RobotOutlined />
                  <span>LLM Token</span>
                </Space>
              }
              value={data.llmStats?.total_tokens || 0}
              suffix={
                <span style={{ fontSize: 12, color: '#52c41a' }}>
                  <RiseOutlined />
                  {successRate.toFixed(0)}% 成功率
                </span>
              }
            />
            {tokenTrendOption && (
              <ReactECharts
                option={tokenTrendOption}
                style={{ height: 50, marginTop: 8 }}
                opts={{ renderer: 'svg' }}
              />
            )}
          </Card>
        </Col>

        <Col span={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <ThunderboltOutlined />
                  <span>LLM 成本</span>
                </Space>
              }
              value={data.llmStats?.total_cost || 0}
              precision={4}
              prefix="¥"
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 16 }}>
              <span style={{ color: '#666', fontSize: 12 }}>
                调用 {data.llmStats?.total_calls || 0} 次
              </span>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 性能指标 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={8}>
          <Card title="API 响应时间">
            <Statistic
              value={data.apiStats?.avg_response_time || 0}
              suffix="ms"
              precision={0}
              valueStyle={{
                color: (data.apiStats?.avg_response_time || 0) > 500 ? '#ff4d4f' : '#52c41a',
              }}
            />
            <Progress
              percent={Math.min(((data.apiStats?.avg_response_time || 0) / 1000) * 100, 100)}
              showInfo={false}
              strokeColor={(data.apiStats?.avg_response_time || 0) > 500 ? '#ff4d4f' : '#52c41a'}
              style={{ marginTop: 8 }}
            />
            <div style={{ color: '#666', fontSize: 12, marginTop: 4 }}>
              目标: &lt; 500ms
            </div>
          </Card>
        </Col>

        <Col span={8}>
          <Card title="数据库连接">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="活跃连接"
                  value={data.dbPerformance?.active_connections || 0}
                  suffix={`/ ${data.dbPerformance?.connection_pool_size || 0}`}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="慢查询"
                  value={data.dbPerformance?.slow_queries || 0}
                  valueStyle={{
                    color: (data.dbPerformance?.slow_queries || 0) > 10 ? '#ff4d4f' : '#52c41a',
                  }}
                />
              </Col>
            </Row>
            <Progress
              percent={
                data.dbPerformance
                  ? Math.round(
                      (data.dbPerformance.active_connections / data.dbPerformance.connection_pool_size) * 100
                    )
                  : 0
              }
              showInfo={false}
              strokeColor={
                data.dbPerformance &&
                data.dbPerformance.active_connections / data.dbPerformance.connection_pool_size > 0.8
                  ? '#ff4d4f'
                  : '#52c41a'
              }
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>

        <Col span={8}>
          <Card title="热门端点 Top 5">
            {Object.entries(data.apiStats?.requests_by_endpoint || {})
              .sort((a, b) => (b[1] as number) - (a[1] as number))
              .slice(0, 5)
              .map(([endpoint, count], index) => (
                <div
                  key={endpoint}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '4px 0',
                    borderBottom: index < 4 ? '1px solid #f0f0f0' : 'none',
                  }}
                >
                  <span style={{ fontSize: 12, color: '#666', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {endpoint.replace('/api/v1/', '')}
                  </span>
                  <Tag color="blue">{count as number}</Tag>
                </div>
              ))}
            {Object.keys(data.apiStats?.requests_by_endpoint || {}).length === 0 && (
              <div style={{ color: '#999', textAlign: 'center', padding: 20 }}>暂无数据</div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 状态码分布 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="状态码分布">
            <Row gutter={16}>
              {Object.entries(data.apiStats?.requests_by_status || {})
                .sort((a, b) => (b[1] as number) - (a[1] as number))
                .map(([status, count]) => {
                  const color = status.startsWith('2')
                    ? '#52c41a'
                    : status.startsWith('4')
                    ? '#faad14'
                    : '#ff4d4f'
                  const total = data.apiStats?.total_requests || 1
                  const percent = ((count as number) / total) * 100

                  return (
                    <Col span={3} key={status}>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 24, fontWeight: 'bold', color }}>{status}</div>
                        <div style={{ fontSize: 12, color: '#666' }}>{count as number} 次</div>
                        <Progress
                          percent={percent}
                          size="small"
                          showInfo={false}
                          strokeColor={color}
                        />
                        <div style={{ fontSize: 12, color: '#999' }}>{percent.toFixed(1)}%</div>
                      </div>
                    </Col>
                  )
                })}
              {Object.keys(data.apiStats?.requests_by_status || {}).length === 0 && (
                <Col span={24}>
                  <div style={{ color: '#999', textAlign: 'center', padding: 20 }}>暂无数据</div>
                </Col>
              )}
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 业务指标 */}
      <Divider orientation="left">业务指标</Divider>
      <Row gutter={[16, 16]}>
        {/* Agent 执行统计 */}
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <CompassOutlined />
                  <span>钓鱼助手调用</span>
                </Space>
              }
              value={
                data.agentStats?.agents?.find(a => a.agent_type === 'fishing')?.total_executions || 0
              }
              suffix="次"
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8 }}>
              <Progress
                percent={
                  (data.agentStats?.agents?.find(a => a.agent_type === 'fishing')?.success_rate || 0) * 100
                }
                size="small"
                format={(p) => `成功率 ${p?.toFixed(0)}%`}
                strokeColor="#52c41a"
              />
            </div>
          </Card>
        </Col>

        {/* 天气查询 */}
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <CloudOutlined />
                  <span>天气查询</span>
                </Space>
              }
              value={
                data.toolStats?.tools?.find(t =>
                  t.tool_name.toLowerCase().includes('weather') ||
                  t.tool_name.includes('天气')
                )?.call_count || 0
              }
              suffix="次"
              valueStyle={{ color: '#13c2c2' }}
            />
            <div style={{ marginTop: 8 }}>
              <Progress
                percent={
                  (data.toolStats?.tools?.find(t =>
                    t.tool_name.toLowerCase().includes('weather') ||
                    t.tool_name.includes('天气')
                  )?.success_rate || 0) * 100
                }
                size="small"
                format={(p) => `成功率 ${p?.toFixed(0)}%`}
                strokeColor="#13c2c2"
              />
            </div>
          </Card>
        </Col>

        {/* 钓鱼推荐 */}
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <MessageOutlined />
                  <span>钓鱼推荐</span>
                </Space>
              }
              value={
                data.toolStats?.tools?.find(t =>
                  t.tool_name.toLowerCase().includes('recommendation') ||
                  t.tool_name.includes('推荐')
                )?.call_count || 0
              }
              suffix="次"
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ marginTop: 8 }}>
              <Progress
                percent={
                  (data.toolStats?.tools?.find(t =>
                    t.tool_name.toLowerCase().includes('recommendation') ||
                    t.tool_name.includes('推荐')
                  )?.success_rate || 0) * 100
                }
                size="small"
                format={(p) => `成功率 ${p?.toFixed(0)}%`}
                strokeColor="#722ed1"
              />
            </div>
          </Card>
        </Col>

        {/* 工具调用总览 */}
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <Space>
                  <ToolOutlined />
                  <span>工具调用</span>
                </Space>
              }
              value={
                data.toolStats?.tools?.reduce((sum, t) => sum + t.call_count, 0) || 0
              }
              suffix="次"
              valueStyle={{ color: '#fa8c16' }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              共 {data.toolStats?.tools?.length || 0} 种工具
            </div>
          </Card>
        </Col>
      </Row>

      {/* 工具分类统计 */}
      {data.toolStats?.by_category && Object.keys(data.toolStats.by_category).length > 0 && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="工具调用分类">
              <Row gutter={16}>
                {Object.entries(data.toolStats.by_category)
                  .sort((a, b) => b[1] - a[1])
                  .map(([category, count]) => {
                    const total = Object.values(data.toolStats!.by_category).reduce((a, b) => a + b, 0)
                    const percent = (count / total) * 100
                    const colors = ['#1890ff', '#52c41a', '#722ed1', '#fa8c16', '#13c2c2', '#eb2f96']
                    const colorIndex = Object.keys(data.toolStats!.by_category).indexOf(category) % colors.length

                    return (
                      <Col span={4} key={category}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 'bold', color: colors[colorIndex] }}>
                            {count}
                          </div>
                          <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>{category}</div>
                          <Progress
                            percent={percent}
                            size="small"
                            showInfo={false}
                            strokeColor={colors[colorIndex]}
                          />
                          <div style={{ fontSize: 12, color: '#999' }}>{percent.toFixed(1)}%</div>
                        </div>
                      </Col>
                    )
                  })}
              </Row>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default Overview
