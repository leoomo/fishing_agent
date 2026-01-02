/**
 * Worker 监控面板组件
 */

import React from 'react'
import { Card, Row, Col, Space, Typography, Progress, Tag, Empty, Tooltip } from 'antd'
import {
  UpOutlined,
  DownOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
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
        {/* 活跃 Worker 列表 */}
        <Col span={8}>
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
            <div style={{ maxHeight: 120, overflowY: 'auto' }}>
              {workers.map((worker) => (
                <div
                  key={worker.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 0',
                    borderBottom: '1px solid #f0f0f0',
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
                    <Tooltip title={worker.id}>
                      <Text ellipsis style={{ maxWidth: 100 }}>
                        {worker.id}
                      </Text>
                    </Tooltip>
                  </Space>
                  <Space size={4}>
                    {worker.current_task && (
                      <Tag color="processing" style={{ margin: 0 }}>
                        #{worker.current_task}
                      </Tag>
                    )}
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {worker.tasks_completed} 完成
                    </Text>
                  </Space>
                </div>
              ))}
            </div>
          )}
        </Col>

        {/* 任务队列进度 */}
        <Col span={8}>
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
                <span>
                  <Tag color="processing" style={{ margin: 0, marginRight: 4 }}>
                    处理中
                  </Tag>
                  <Text strong>{stats?.ocr_processing || 0}</Text>
                </span>
              </Space>
            </div>
          </div>
        </Col>

        {/* 实时统计 */}
        <Col span={8}>
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
