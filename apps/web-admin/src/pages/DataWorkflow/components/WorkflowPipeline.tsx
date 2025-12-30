/**
 * 工作流管道可视化组件
 *
 * 显示两条数据来源路径汇聚到审核阶段：
 * 采集 → OCR ─┐
 *             ├→ 审核 → 入库
 * 导入 ───────┘
 */

import React from 'react'
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
  padding: '10px 14px',
  borderRadius: 8,
  backgroundColor: `${color}10`,
  border: `1px solid ${color}30`,
  cursor: clickable ? 'pointer' : 'default',
  transition: 'all 0.2s',
  minWidth: 110,
})

// 阶段卡片组件
const StageCard: React.FC<{
  stage: StageConfig
  stats: WorkflowStats | null
  onClick: () => void
  compact?: boolean
}> = ({ stage, stats, onClick, compact }) => (
  <Tooltip title={stage.tab ? '点击查看详情' : undefined}>
    <div
      onClick={onClick}
      style={getStageStyle(stage.color, !!stage.tab)}
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
      <Space direction="vertical" size={2} style={{ width: '100%' }}>
        <Space size={6}>
          <span style={{ color: stage.color, fontSize: compact ? 14 : 16 }}>
            {stage.icon}
          </span>
          <Text strong style={{ fontSize: compact ? 12 : 13 }}>
            {stage.title}
          </Text>
        </Space>
        <div>
          <Text
            style={{
              fontSize: compact ? 18 : 22,
              fontWeight: 600,
              color: stage.color,
            }}
          >
            {stats ? stage.getValue(stats) : '-'}
          </Text>
          {stats && stage.getSubValue && stage.getSubValue(stats) && (
            <Text
              type="secondary"
              style={{ fontSize: 11, marginLeft: 6 }}
            >
              {stage.getSubValue(stats)?.value} {stage.getSubValue(stats)?.label}
            </Text>
          )}
        </div>
      </Space>
    </div>
  </Tooltip>
)

// 采集路径阶段（上半部分）
const CRAWL_PATH_STAGES: StageConfig[] = [
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
]

// 导入路径阶段（下半部分）
const IMPORT_PATH_STAGE: StageConfig = {
  key: 'import',
  tab: 'import',
  title: '数据导入',
  icon: <ImportOutlined />,
  color: '#13c2c2',
  getValue: () => 0, // 导入没有队列统计，显示0
}

// 汇合后阶段
const MERGED_STAGES: StageConfig[] = [
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
      {/* 双路径汇聚布局 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* 左侧：两条数据来源路径 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {/* 上方：采集 → OCR 路径 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {CRAWL_PATH_STAGES.map((stage, index) => (
              <React.Fragment key={stage.key}>
                <StageCard
                  stage={stage}
                  stats={stats}
                  onClick={() => handleStageClick(stage)}
                  compact
                />
                {index < CRAWL_PATH_STAGES.length - 1 && (
                  <ArrowRightOutlined style={{ color: '#d9d9d9', fontSize: 14 }} />
                )}
              </React.Fragment>
            ))}
          </div>

          {/* 下方：导入路径 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <StageCard
              stage={IMPORT_PATH_STAGE}
              stats={stats}
              onClick={() => handleStageClick(IMPORT_PATH_STAGE)}
              compact
            />
          </div>
        </div>

        {/* 汇聚符号 */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            color: '#d9d9d9',
            fontSize: 12,
            gap: 2,
          }}
        >
          <div style={{ borderBottom: '1px solid #d9d9d9', width: 20, marginBottom: 2 }} />
          <ArrowRightOutlined style={{ fontSize: 16 }} />
          <div style={{ borderTop: '1px solid #d9d9d9', width: 20, marginTop: 2 }} />
        </div>

        {/* 右侧：审核 → 入库 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
          {MERGED_STAGES.map((stage, index) => (
            <React.Fragment key={stage.key}>
              <StageCard
                stage={stage}
                stats={stats}
                onClick={() => handleStageClick(stage)}
              />
              {index < MERGED_STAGES.length - 1 && (
                <ArrowRightOutlined style={{ color: '#d9d9d9', fontSize: 16 }} />
              )}
            </React.Fragment>
          ))}
        </div>
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
