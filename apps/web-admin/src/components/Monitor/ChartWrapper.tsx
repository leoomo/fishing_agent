import React from 'react'
import { Alert, Button, Empty, Spin } from 'antd'
import { ReloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'

export interface ChartWrapperProps {
  option: any
  style?: React.CSSProperties
  error?: Error | string | null
  loading?: boolean
  onRetry?: () => void
  notMerge?: boolean
  lazyUpdate?: boolean
}

/**
 * 统一的图表包装组件
 * 区分 error / loading / empty 三种状态
 */
export const ChartWrapper: React.FC<ChartWrapperProps> = ({
  option,
  style,
  error,
  loading,
  onRetry,
  notMerge = true,
  lazyUpdate = true,
}) => {
  // 加载状态
  if (loading) {
    return (
      <div
        style={{
          ...style,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Spin size="large" />
      </div>
    )
  }

  // 错误状态
  if (error) {
    const errorMessage = error instanceof Error ? error.message : error
    return (
      <Alert
        type="error"
        message="加载失败"
        description={errorMessage || '请检查网络连接后重试'}
        showIcon
        icon={<ExclamationCircleOutlined />}
        action={
          onRetry && (
            <Button size="small" icon={<ReloadOutlined />} onClick={onRetry}>
              重试
            </Button>
          )
        }
        style={{
          ...style,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      />
    )
  }

  // 空数据状态
  if (!option || typeof option !== 'object') {
    return (
      <div
        style={{
          ...style,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Empty description="暂无数据" />
      </div>
    )
  }

  // 检查 series 是否为空
  const hasData =
    option.series &&
    Array.isArray(option.series) &&
    option.series.length > 0 &&
    option.series.some(
      (s: any) => s.data && Array.isArray(s.data) && s.data.length > 0
    )

  if (!hasData && !option.graphic) {
    return (
      <div
        style={{
          ...style,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Empty description="暂无数据" />
      </div>
    )
  }

  // 正常渲染图表
  return (
    <ReactECharts
      option={option}
      style={style}
      notMerge={notMerge}
      lazyUpdate={lazyUpdate}
    />
  )
}

export default ChartWrapper
