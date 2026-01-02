/**
 * OCR 处理进度条组件
 *
 * 显示 OCR 任务的处理进度，包括四个阶段：
 * 1. 下载图片
 * 2. 合并图片
 * 3. OCR 识别
 * 4. 数据提取
 */

import React from 'react'
import { Progress, Steps, Typography, Space } from 'antd'
import {
  DownloadOutlined,
  MergeCellsOutlined,
  ScanOutlined,
  FileSearchOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import type { OCRProgressInfo, OCRStage } from '../../../types/dataWorkflow'
import { OCR_STAGE_CONFIG } from '../../../types/dataWorkflow'

const { Text } = Typography

interface OCRProgressBarProps {
  /** 进度信息 */
  progress: OCRProgressInfo | undefined
  /** 是否显示详细信息 */
  showDetail?: boolean
  /** 是否紧凑模式 */
  compact?: boolean
}

// 阶段顺序
const STAGE_ORDER: OCRStage[] = ['downloading', 'merging', 'ocr_processing', 'extracting']

// 获取阶段图标
const getStageIcon = (stage: OCRStage, isActive: boolean, isCompleted: boolean) => {
  if (isCompleted) {
    return <CheckCircleOutlined style={{ color: '#52c41a' }} />
  }
  if (isActive) {
    return <LoadingOutlined style={{ color: '#1890ff' }} />
  }

  const iconMap: Record<OCRStage, React.ReactNode> = {
    downloading: <DownloadOutlined />,
    merging: <MergeCellsOutlined />,
    ocr_processing: <ScanOutlined />,
    extracting: <FileSearchOutlined />,
  }
  return iconMap[stage]
}

// 获取当前阶段索引
const getStageIndex = (stage: OCRStage): number => {
  return STAGE_ORDER.indexOf(stage)
}

const OCRProgressBar: React.FC<OCRProgressBarProps> = ({
  progress,
  showDetail = true,
  compact = false,
}) => {
  // 无进度信息时显示占位
  if (!progress) {
    return (
      <div style={{ padding: compact ? '4px 0' : '8px 0' }}>
        <Text type="secondary">等待处理...</Text>
      </div>
    )
  }

  const currentStageIndex = getStageIndex(progress.stage)

  // 紧凑模式 - 只显示进度条
  if (compact) {
    return (
      <div style={{ width: '100%' }}>
        <Space size={4} style={{ marginBottom: 4 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {OCR_STAGE_CONFIG[progress.stage].text}
          </Text>
          {progress.current_image && progress.total_images && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              ({progress.current_image}/{progress.total_images})
            </Text>
          )}
        </Space>
        <Progress
          percent={progress.progress}
          size="small"
          status="active"
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          style={{ marginBottom: 0 }}
        />
      </div>
    )
  }

  // 完整模式 - 显示步骤和进度
  const stepsItems = STAGE_ORDER.map((stage, index) => {
    const isActive = index === currentStageIndex
    const isCompleted = index < currentStageIndex
    const config = OCR_STAGE_CONFIG[stage]

    return {
      key: stage,
      title: config.text,
      icon: getStageIcon(stage, isActive, isCompleted),
      status: isCompleted ? 'finish' : isActive ? 'process' : 'wait',
    }
  })

  return (
    <div style={{ padding: '8px 0' }}>
      <Steps
        size="small"
        current={currentStageIndex}
        items={stepsItems.map((item) => ({
          ...item,
          status: item.status as 'wait' | 'process' | 'finish' | 'error',
        }))}
        style={{ marginBottom: 12 }}
      />

      <Progress
        percent={progress.progress}
        status="active"
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#87d068',
        }}
        style={{ marginBottom: 8 }}
      />

      {showDetail && (
        <Space size={16}>
          {progress.message && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {progress.message}
            </Text>
          )}
          {progress.current_image && progress.total_images && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              图片: {progress.current_image} / {progress.total_images}
            </Text>
          )}
        </Space>
      )}
    </div>
  )
}

export default OCRProgressBar
