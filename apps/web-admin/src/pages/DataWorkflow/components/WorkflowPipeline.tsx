/**
 * 工作流管道可视化组件
 *
 * 双面板布局，清晰展示两条独立的数据流程：
 * - 采集流程：采集 → OCR → 审核 → 入库
 * - 导入流程：导入 → 审核 → 入库
 */

import React, { useState } from 'react'
import { Card, Space, Typography, Tooltip } from 'antd'
import {
  RobotOutlined,
  ScanOutlined,
  ImportOutlined,
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

// 阶段卡片样式
const getStageStyle = (color: string, clickable: boolean) => ({
  padding: '10px 16px',
  borderRadius: 8,
  backgroundColor: `${color}08`,
  border: `1px solid ${color}20`,
  cursor: clickable ? 'pointer' : 'default',
  transition: 'all 0.2s',
  minWidth: 90,
  textAlign: 'center' as const,
  flex: 1,
})

// 阶段卡片组件
const StageCard: React.FC<{
  stage: StageConfig
  stats: WorkflowStats | null
  onClick: () => void
}> = ({ stage, stats, onClick }) => (
  <Tooltip title={stage.tab ? '点击查看详情' : undefined}>
    <div
      onClick={onClick}
      style={getStageStyle(stage.color, !!stage.tab)}
      onMouseEnter={(e) => {
        if (stage.tab) {
          e.currentTarget.style.backgroundColor = `${stage.color}15`
          e.currentTarget.style.borderColor = stage.color
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = `${stage.color}08`
        e.currentTarget.style.borderColor = `${stage.color}20`
      }}
    >
      <Space size={6} align="center">
        <span style={{ color: stage.color, fontSize: 16 }}>
          {stage.icon}
        </span>
        <Text strong style={{ fontSize: 12 }}>
          {stage.title}
        </Text>
      </Space>
      <div style={{ marginTop: 2 }}>
        <Text
          style={{
            fontSize: 20,
            fontWeight: 600,
            color: stage.color,
          }}
        >
          {stats ? stage.getValue(stats) : '-'}
        </Text>
        {stats && stage.getSubValue && stage.getSubValue(stats) && (
          <Text
            type="secondary"
            style={{ fontSize: 10, marginLeft: 4 }}
          >
            {stage.getSubValue(stats)?.value} {stage.getSubValue(stats)?.label}
          </Text>
        )}
      </div>
    </div>
  </Tooltip>
)

// 流程模式类型
type PipelineMode = 'crawl' | 'import'

// 采集流程阶段配置
const CRAWL_PIPELINE: StageConfig[] = [
  {
    key: 'crawl',
    tab: 'collection',
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
    key: 'review-crawl',
    tab: 'review',
    title: '人工审核',
    icon: <AuditOutlined />,
    color: '#faad14',
    getValue: (stats) => stats.review_pending,
  },
  {
    key: 'done-crawl',
    tab: undefined,
    title: '已入库',
    icon: <CheckCircleOutlined />,
    color: '#52c41a',
    getValue: (stats) => stats.review_approved,
  },
]

// 导入流程阶段配置
const IMPORT_PIPELINE: StageConfig[] = [
  {
    key: 'import',
    tab: 'import',
    title: '数据导入',
    icon: <ImportOutlined />,
    color: '#13c2c2',
    getValue: () => 0,
  },
  {
    key: 'review-import',
    tab: 'review',
    title: '人工审核',
    icon: <AuditOutlined />,
    color: '#faad14',
    getValue: (stats) => stats.review_pending,
  },
  {
    key: 'done-import',
    tab: undefined,
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
  const [mode, setMode] = useState<PipelineMode>('crawl')

  const currentConfig = mode === 'crawl'
    ? { title: '采集流程', icon: <RobotOutlined />, stages: CRAWL_PIPELINE }
    : { title: '导入流程', icon: <ImportOutlined />, stages: IMPORT_PIPELINE }

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
      <div style={{ display: 'flex', gap: 24 }}>
        {/* 左侧：流程图 */}
        <div style={{ flex: 1 }}>
          {/* 标签切换 */}
          <div style={{ display: 'flex', gap: 20, marginBottom: 12 }}>
            {([
              { key: 'crawl' as const, label: '采集流程', icon: <RobotOutlined /> },
              { key: 'import' as const, label: '导入流程', icon: <ImportOutlined /> },
            ]).map((item) => (
              <div
                key={item.key}
                onClick={() => setMode(item.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  cursor: 'pointer',
                  color: mode === item.key ? '#1890ff' : '#8c8c8c',
                  fontWeight: mode === item.key ? 600 : 400,
                  borderBottom: mode === item.key ? '2px solid #1890ff' : '2px solid transparent',
                  paddingBottom: 6,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (mode !== item.key) {
                    e.currentTarget.style.color = '#595959'
                  }
                }}
                onMouseLeave={(e) => {
                  if (mode !== item.key) {
                    e.currentTarget.style.color = '#8c8c8c'
                  }
                }}
              >
                <span style={{ fontSize: 14 }}>{item.icon}</span>
                <span style={{ fontSize: 14 }}>{item.label}</span>
              </div>
            ))}
          </div>

          {/* 流程图 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {currentConfig.stages.map((stage, index) => (
              <React.Fragment key={stage.key}>
                <StageCard
                  stage={stage}
                  stats={stats}
                  onClick={() => handleStageClick(stage)}
                />
                {index < currentConfig.stages.length - 1 && (
                  <ArrowRightOutlined style={{ color: '#d9d9d9', fontSize: 12, flexShrink: 0 }} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* 右侧：统计指标 */}
        {stats && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 32,
            paddingLeft: 24,
            borderLeft: '1px solid #f0f0f0',
          }}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: 11 }}>今日处理</Text>
              <div>
                <Text strong style={{ fontSize: 20 }}>{stats.today_processed}</Text>
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: 11 }}>平均耗时</Text>
              <div>
                <Text strong style={{ fontSize: 20 }}>
                  {stats.avg_processing_time_ms > 0
                    ? `${(stats.avg_processing_time_ms / 1000).toFixed(1)}s`
                    : '-'}
                </Text>
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: 11 }}>成功率</Text>
              <div>
                <Text strong style={{ fontSize: 20, color: stats.success_rate >= 0.9 ? '#52c41a' : '#faad14' }}>
                  {(stats.success_rate * 100).toFixed(1)}%
                </Text>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

export default WorkflowPipeline
