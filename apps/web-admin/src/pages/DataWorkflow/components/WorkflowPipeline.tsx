/**
 * 工作流管道可视化组件
 */

import React from 'react'
import { Card, Space, Typography, Tooltip } from 'antd'
import {
  RobotOutlined,
  ScanOutlined,
  FileSearchOutlined,
  AuditOutlined,
  CheckCircleOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import type { WorkflowStats, WorkflowTab } from '../../../types/dataWorkflow'

const { Text } = Typography

interface WorkflowPipelineProps {
  stats: WorkflowStats | null
  loading?: boolean
  onStageClick?: (tab: WorkflowTab) => void
}

interface StageConfig {
  key: string
  tab?: WorkflowTab
  title: string
  icon: React.ReactNode
  color: string
  getValue: (stats: WorkflowStats) => number
  getSubValue?: (stats: WorkflowStats) => { value: number; label: string } | null
}

const STAGES: StageConfig[] = [
  {
    key: 'crawl',
    title: '采集队列',
    icon: <RobotOutlined />,
    color: '#1890ff',
    getValue: (stats) => stats.crawl_pending,
  },
  {
    key: 'ocr',
    tab: 'ocr',
    title: 'OCR识别',
    icon: <ScanOutlined />,
    color: '#722ed1',
    getValue: (stats) => stats.ocr_pending,
    getSubValue: (stats) => ({
      value: stats.ocr_processing,
      label: '处理中',
    }),
  },
  {
    key: 'extract',
    title: '数据提取',
    icon: <FileSearchOutlined />,
    color: '#13c2c2',
    getValue: (stats) => stats.ocr_completed,
  },
  {
    key: 'review',
    tab: 'review',
    title: '人工审核',
    icon: <AuditOutlined />,
    color: '#faad14',
    getValue: (stats) => stats.review_pending,
  },
  {
    key: 'done',
    tab: 'completed',
    title: '已入库',
    icon: <CheckCircleOutlined />,
    color: '#52c41a',
    getValue: (stats) => stats.review_approved,
  },
]

const WorkflowPipeline: React.FC<WorkflowPipelineProps> = ({
  stats,
  loading,
  onStageClick,
}) => {
  const handleStageClick = (stage: StageConfig) => {
    if (stage.tab && onStageClick) {
      onStageClick(stage.tab)
    }
  }

  return (
    <Card
      size="small"
      loading={loading}
      styles={{ body: { padding: '16px 24px' } }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
        }}
      >
        {STAGES.map((stage, index) => (
          <React.Fragment key={stage.key}>
            {/* 阶段卡片 */}
            <Tooltip title={stage.tab ? '点击查看详情' : undefined}>
              <div
                onClick={() => handleStageClick(stage)}
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  borderRadius: 8,
                  backgroundColor: `${stage.color}10`,
                  border: `1px solid ${stage.color}30`,
                  cursor: stage.tab ? 'pointer' : 'default',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (stage.tab) {
                    e.currentTarget.style.backgroundColor = `${stage.color}20`
                    e.currentTarget.style.borderColor = stage.color
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = `${stage.color}10`
                  e.currentTarget.style.borderColor = `${stage.color}30`
                }}
              >
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  <Space>
                    <span style={{ color: stage.color, fontSize: 18 }}>
                      {stage.icon}
                    </span>
                    <Text strong style={{ fontSize: 13 }}>
                      {stage.title}
                    </Text>
                  </Space>
                  <div>
                    <Text
                      style={{
                        fontSize: 24,
                        fontWeight: 600,
                        color: stage.color,
                      }}
                    >
                      {stats ? stage.getValue(stats) : '-'}
                    </Text>
                    {stats && stage.getSubValue && stage.getSubValue(stats) && (
                      <Text
                        type="secondary"
                        style={{ fontSize: 12, marginLeft: 8 }}
                      >
                        {stage.getSubValue(stats)?.value} {stage.getSubValue(stats)?.label}
                      </Text>
                    )}
                  </div>
                </Space>
              </div>
            </Tooltip>

            {/* 箭头连接器 */}
            {index < STAGES.length - 1 && (
              <ArrowRightOutlined
                style={{ color: '#d9d9d9', fontSize: 16, flexShrink: 0 }}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* 底部统计指标 */}
      {stats && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 24,
            marginTop: 12,
            paddingTop: 12,
            borderTop: '1px solid #f0f0f0',
          }}
        >
          <Text type="secondary" style={{ fontSize: 12 }}>
            今日处理: <Text strong>{stats.today_processed}</Text>
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            平均耗时:{' '}
            <Text strong>
              {stats.avg_processing_time_ms > 0
                ? `${(stats.avg_processing_time_ms / 1000).toFixed(1)}s`
                : '-'}
            </Text>
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            成功率:{' '}
            <Text strong style={{ color: stats.success_rate >= 0.9 ? '#52c41a' : '#faad14' }}>
              {(stats.success_rate * 100).toFixed(1)}%
            </Text>
          </Text>
        </div>
      )}
    </Card>
  )
}

export default WorkflowPipeline
