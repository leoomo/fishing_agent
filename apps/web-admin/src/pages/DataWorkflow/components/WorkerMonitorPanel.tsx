/**
 * Worker 监控面板组件
 *
 * 增强版功能:
 * - 显示 CPU/内存/磁盘使用率
 * - Worker 详细信息展示
 * - 任务队列进度
 * - 实时统计
 */

import React from 'react'
import { Card, Row, Col, Space, Typography, Progress, Tag, Empty, Tooltip } from 'antd'
import {
  UpOutlined,
  DownOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DesktopOutlined,
  HddOutlined,
} from '@ant-design/icons'
import type { WorkerInfo, WorkflowStats } from '../../../types/dataWorkflow'

const { Text } = Typography

interface WorkerMonitorPanelProps {
  workers: WorkerInfo[]
  stats: WorkflowStats | null
  loading?: boolean
  collapsed?: boolean
  onToggleCollapse?: () => void
}

/**
 * 格式化最后心跳时间
 */
const formatLastHeartbeat = (heartbeat: string | null): string => {
  if (!heartbeat) return '从未'

  const now = new Date()
  const hbTime = new Date(heartbeat)
  const diffMs = now.getTime() - hbTime.getTime()
  const diffSec = Math.floor(diffMs / 1000)

  if (diffSec < 60) return `${diffSec}秒前`
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}分钟前`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}小时前`
  return `${Math.floor(diffSec / 86400)}天前`
}

/**
 * 获取使用率颜色
 */
const getUsageColor = (usage: number | null | undefined): string => {
  if (usage === null || usage === undefined) return '#d9d9d9'
  if (usage >= 90) return '#ff4d4f'
  if (usage >= 70) return '#faad14'
  return '#52c41a'
}

/**
 * 解析当前任务
 */
const parseCurrentTasks = (current_task: number | string | null): number[] => {
  if (!current_task) return []
  if (typeof current_task === 'number') return [current_task]
  try {
    const parsed = JSON.parse(current_task)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

/**
 * 系统指标小卡片组件
 */
const MetricBadge: React.FC<{
  label: string
  value: number | null | undefined
  icon: React.ReactNode
}> = ({ label, value, icon }) => {
  const displayValue = value !== null && value !== undefined ? `${value.toFixed(1)}%` : '-'
  const color = getUsageColor(value)

  return (
    <Tooltip title={`${label}: ${displayValue}`}>
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 2,
          padding: '2px 6px',
          background: '#fafafa',
          borderRadius: 4,
          fontSize: 11,
        }}
      >
        <span style={{ color }}>{icon}</span>
        <Text style={{ fontSize: 11, color }}>{displayValue}</Text>
      </div>
    </Tooltip>
  )
}

const WorkerMonitorPanel: React.FC<WorkerMonitorPanelProps> = ({
  workers,
  stats,
  loading,
  collapsed = false,
  onToggleCollapse,
}) => {
  const activeWorkers = workers.filter((w) => w.status === 'active')
  const totalPending = stats ? stats.ocr_pending + stats.ocr_processing : 0
  const totalCompleted = stats?.ocr_completed || 0
  const queueProgress =
    totalPending + totalCompleted > 0
      ? Math.round((totalCompleted / (totalPending + totalCompleted)) * 100)
      : 0

  return (
    <Card
      size="small"
      loading={loading}
      title={
        <Space>
          <Text strong>Worker 监控</Text>
          <Tag color={activeWorkers.length > 0 ? 'green' : 'default'}>
            {activeWorkers.length} 活跃
          </Tag>
          {workers.length > activeWorkers.length && (
            <Tag color="default">
              {workers.length - activeWorkers.length} 离线
            </Tag>
          )}
        </Space>
      }
      extra={
        <span
          onClick={onToggleCollapse}
          style={{ cursor: 'pointer', color: '#1890ff' }}
        >
          {collapsed ? <DownOutlined /> : <UpOutlined />}
          {collapsed ? ' 展开' : ' 收起'}
        </span>
      }
      styles={{ body: collapsed ? { display: 'none' } : { padding: '16px 24px' } }}
    >
      <Row gutter={24}>
        {/* 活跃 Worker 列表 - 增强版 */}
        <Col span={10}>
          <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
            Worker 列表
          </Text>
          {workers.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无 Worker"
              style={{ margin: '8px 0' }}
            />
          ) : (
            <div style={{ maxHeight: 150, overflowY: 'auto' }}>
              {workers.map((worker) => {
                const currentTasks = parseCurrentTasks(worker.current_task)
                return (
                  <div
                    key={worker.id}
                    style={{
                      padding: '8px 0',
                      borderBottom: '1px solid #f0f0f0',
                    }}
                  >
                    {/* Worker 基本信息行 */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: 4,
                      }}
                    >
                      <Space size={8}>
                        <span
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor:
                              worker.status === 'active' ? '#52c41a' : '#d9d9d9',
                            display: 'inline-block',
                          }}
                        />
                        <Tooltip title={`ID: ${worker.id}${worker.name ? ` | 名称: ${worker.name}` : ''}`}>
                          <Text ellipsis style={{ maxWidth: 120 }}>
                            {worker.name || worker.id}
                          </Text>
                        </Tooltip>
                        {worker.worker_version && (
                          <Tag style={{ margin: 0, fontSize: 10, padding: '0 4px' }}>
                            v{worker.worker_version}
                          </Tag>
                        )}
                      </Space>
                      <Space size={4}>
                        {currentTasks.length > 0 ? (
                          <Tag color="processing" style={{ margin: 0 }}>
                            {currentTasks.length} 任务
                          </Tag>
                        ) : (
                          <Tag color="default" style={{ margin: 0 }}>
                            空闲
                          </Tag>
                        )}
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {worker.tasks_completed} 完成
                        </Text>
                      </Space>
                    </div>

                    {/* 系统指标行 */}
                    {worker.status === 'active' && (
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <Space size={4}>
                          <MetricBadge
                            label="CPU"
                            value={worker.cpu_usage}
                            icon={<DesktopOutlined style={{ fontSize: 10 }} />}
                          />
                          <MetricBadge
                            label="内存"
                            value={worker.memory_usage}
                            icon={<HddOutlined style={{ fontSize: 10 }} />}
                          />
                          {worker.disk_usage !== null && worker.disk_usage !== undefined && (
                            <MetricBadge
                              label="磁盘"
                              value={worker.disk_usage}
                              icon={<HddOutlined style={{ fontSize: 10 }} />}
                            />
                          )}
                        </Space>
                        <Tooltip title={`最后心跳: ${worker.last_heartbeat || '从未'}`}>
                          <Text type="secondary" style={{ fontSize: 10 }}>
                            {formatLastHeartbeat(worker.last_heartbeat)}
                          </Text>
                        </Tooltip>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Col>

        {/* 任务队列进度 */}
        <Col span={7}>
          <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
            任务队列
          </Text>
          <div style={{ padding: '8px 0' }}>
            <Progress
              percent={queueProgress}
              status="active"
              strokeColor={{
                '0%': '#722ed1',
                '100%': '#52c41a',
              }}
            />
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginTop: 8,
              }}
            >
              <Space size={16}>
                <span>
                  <ClockCircleOutlined style={{ color: '#722ed1', marginRight: 4 }} />
                  <Text type="secondary">待处理: </Text>
                  <Text strong>{stats?.ocr_pending || 0}</Text>
                </span>
              </Space>
            </div>
            <div style={{ marginTop: 4 }}>
              <span>
                <Tag color="processing" style={{ margin: 0, marginRight: 4 }}>
                  处理中
                </Tag>
                <Text strong>{stats?.ocr_processing || 0}</Text>
              </span>
            </div>
          </div>
        </Col>

        {/* 实时统计 */}
        <Col span={7}>
          <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
            实时统计
          </Text>
          <div style={{ padding: '8px 0' }}>
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ textAlign: 'center' }}>
                  <Text
                    style={{
                      fontSize: 28,
                      fontWeight: 600,
                      color: '#52c41a',
                    }}
                  >
                    {stats?.today_processed || 0}
                  </Text>
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      今日处理
                    </Text>
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ textAlign: 'center' }}>
                  <Text
                    style={{
                      fontSize: 28,
                      fontWeight: 600,
                      color:
                        stats && stats.success_rate >= 0.9 ? '#52c41a' : '#faad14',
                    }}
                  >
                    {stats ? `${(stats.success_rate * 100).toFixed(1)}%` : '-'}
                  </Text>
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      成功率
                    </Text>
                  </div>
                </div>
              </Col>
            </Row>
            <div style={{ marginTop: 12, textAlign: 'center' }}>
              <Space split={<span style={{ color: '#d9d9d9' }}>|</span>}>
                <span>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                  <Text type="secondary">完成: </Text>
                  <Text strong>{stats?.ocr_completed || 0}</Text>
                </span>
                <span>
                  <Text type="secondary" style={{ color: '#ff4d4f' }}>失败: </Text>
                  <Text strong style={{ color: '#ff4d4f' }}>
                    {stats?.ocr_failed || 0}
                  </Text>
                </span>
              </Space>
            </div>
          </div>
        </Col>
      </Row>
    </Card>
  )
}

export default WorkerMonitorPanel
