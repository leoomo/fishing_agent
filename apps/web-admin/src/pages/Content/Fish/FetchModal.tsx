/**
 * 鱼类知识网络采集弹窗
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Modal,
  Progress,
  List,
  Tag,
  Button,
  Checkbox,
  Space,
  message,
  Popconfirm,
  Typography,
} from 'antd'
import {
  CloudDownloadOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { fishApi } from '@/api/services/fish'
import type { FetchProgressResponse, FetchProgressItem, FetchStatus } from '@/types/fish'
import { FETCH_STATUS_CONFIG } from '@/types/fish'

const { Text } = Typography

interface FetchModalProps {
  open: boolean
  onClose: () => void
  onComplete?: () => void
}

export default function FetchModal({ open, onClose, onComplete }: FetchModalProps) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<FetchProgressResponse | null>(null)
  const [useLLM, setUseLLM] = useState(true)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  // 加载进度
  const loadProgress = useCallback(async () => {
    try {
      const data = await fishApi.getFetchProgress()
      setProgress(data)
      return data
    } catch (error) {
      console.error('加载进度失败:', error)
      return null
    }
  }, [])

  // 开始轮询
  const startPolling = useCallback(() => {
    if (pollingRef.current) return

    pollingRef.current = setInterval(async () => {
      const data = await loadProgress()
      if (data && !data.is_running) {
        // 采集完成，停止轮询
        stopPolling()
        if (data.stats.completed > 0) {
          onComplete?.()
        }
      }
    }, 2000)
  }, [loadProgress, onComplete])

  // 停止轮询
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  // 初始化加载
  useEffect(() => {
    if (open) {
      loadProgress()
    }
    return () => stopPolling()
  }, [open, loadProgress, stopPolling])

  // 根据运行状态控制轮询
  useEffect(() => {
    if (progress?.is_running) {
      startPolling()
    } else {
      stopPolling()
    }
  }, [progress?.is_running, startPolling, stopPolling])

  // 开始采集
  const handleStart = async () => {
    setLoading(true)
    try {
      const result = await fishApi.startFetch({ use_llm: useLLM })
      if (result.success) {
        message.success(result.message)
        await loadProgress()
      } else {
        message.warning(result.message)
      }
    } catch (error) {
      message.error('启动采集失败')
    } finally {
      setLoading(false)
    }
  }

  // 暂停采集
  const handlePause = async () => {
    setLoading(true)
    try {
      const result = await fishApi.pauseFetch()
      if (result.success) {
        message.success(result.message)
        await loadProgress()
      } else {
        message.warning(result.message)
      }
    } catch (error) {
      message.error('暂停采集失败')
    } finally {
      setLoading(false)
    }
  }

  // 重试失败项
  const handleRetry = async (name?: string) => {
    setLoading(true)
    try {
      const result = await fishApi.retryFetch({ names: name ? [name] : undefined })
      if (result.success) {
        message.success(result.message)
        await loadProgress()
      } else {
        message.warning(result.message)
      }
    } catch (error) {
      message.error('重试失败')
    } finally {
      setLoading(false)
    }
  }

  // 重置进度
  const handleReset = async () => {
    setLoading(true)
    try {
      const result = await fishApi.resetFetch()
      if (result.success) {
        message.success(result.message)
        await loadProgress()
      } else {
        message.warning(result.message)
      }
    } catch (error) {
      message.error('重置失败')
    } finally {
      setLoading(false)
    }
  }

  // 计算进度百分比
  const getProgressPercent = () => {
    if (!progress) return 0
    const { total, completed, skipped, failed } = progress.stats
    if (total === 0) return 0
    return Math.round(((completed + skipped + failed) / total) * 100)
  }

  // 渲染状态标签
  const renderStatusTag = (status: FetchStatus, error?: string) => {
    const config = FETCH_STATUS_CONFIG[status]
    return (
      <Tag color={config.color} title={error}>
        {config.icon} {config.label}
        {error && <Text type="secondary" style={{ marginLeft: 4, fontSize: 12 }}>({error})</Text>}
      </Tag>
    )
  }

  // 渲染列表项
  const renderItem = (item: FetchProgressItem) => (
    <List.Item
      actions={
        item.status === 'failed'
          ? [
              <Button
                key="retry"
                type="link"
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => handleRetry(item.name)}
                disabled={progress?.is_running}
              >
                重试
              </Button>,
            ]
          : undefined
      }
    >
      <List.Item.Meta
        title={<Text>{item.name}</Text>}
        description={renderStatusTag(item.status, item.error)}
      />
    </List.Item>
  )

  const stats = progress?.stats
  const isRunning = progress?.is_running

  return (
    <Modal
      title={
        <Space>
          <CloudDownloadOutlined />
          网络采集鱼类知识
        </Space>
      }
      open={open}
      onCancel={onClose}
      width={600}
      footer={null}
      destroyOnClose
    >
      {/* 进度统计 */}
      {stats && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text>
              采集进度：{stats.completed + stats.skipped + stats.failed} / {stats.total}
            </Text>
            <Space>
              <Tag color="#52c41a">完成 {stats.completed}</Tag>
              <Tag color="#faad14">跳过 {stats.skipped}</Tag>
              <Tag color="#ff4d4f">失败 {stats.failed}</Tag>
              <Tag color="#8c8c8c">等待 {stats.pending}</Tag>
            </Space>
          </div>
          <Progress
            percent={getProgressPercent()}
            status={isRunning ? 'active' : stats.failed > 0 ? 'exception' : 'success'}
          />
        </div>
      )}

      {/* 控制按钮 */}
      <div style={{ marginBottom: 16 }}>
        <Space>
          {!isRunning ? (
            <>
              <Checkbox checked={useLLM} onChange={(e) => setUseLLM(e.target.checked)}>
                使用 LLM 增强钓鱼知识
              </Checkbox>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleStart}
                loading={loading}
              >
                {stats && stats.pending < stats.total ? '继续采集' : '开始采集'}
              </Button>
            </>
          ) : (
            <Button
              icon={<PauseCircleOutlined />}
              onClick={handlePause}
              loading={loading}
            >
              暂停
            </Button>
          )}

          {stats && stats.failed > 0 && !isRunning && (
            <Button
              icon={<ReloadOutlined />}
              onClick={() => handleRetry()}
              loading={loading}
            >
              重试全部失败项
            </Button>
          )}

          <Popconfirm
            title="确定要重置所有采集进度吗？"
            description="这将清除所有采集记录，重新开始采集。"
            onConfirm={handleReset}
            okText="确定"
            cancelText="取消"
          >
            <Button
              icon={<DeleteOutlined />}
              danger
              disabled={isRunning}
              loading={loading}
            >
              重置
            </Button>
          </Popconfirm>
        </Space>
      </div>

      {/* 鱼种列表 */}
      <List
        size="small"
        bordered
        dataSource={progress?.items || []}
        renderItem={renderItem}
        style={{ maxHeight: 400, overflow: 'auto' }}
        locale={{ emptyText: '暂无数据' }}
      />
    </Modal>
  )
}
