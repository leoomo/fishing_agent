/**
 * Worker 日志面板组件
 *
 * 终端风格的日志显示，支持：
 * - 实时日志流
 * - 按级别着色
 * - 自动滚动到最新
 * - 可折叠面板
 */

import React, { useEffect, useRef, useCallback } from 'react'
import { Card, Button, Space, Tag, Typography, Empty, Tooltip } from 'antd'
import {
  ClearOutlined,
  DownOutlined,
  UpOutlined,
  CodeOutlined,
} from '@ant-design/icons'
import type { WorkerLogItem, WorkerLogLevel } from '../../../types/dataWorkflow'
import { LOG_LEVEL_CONFIG } from '../../../types/dataWorkflow'

const { Text } = Typography

interface WorkerLogPanelProps {
  /** 日志列表 */
  logs: WorkerLogItem[]
  /** 是否折叠 */
  collapsed: boolean
  /** 切换折叠状态 */
  onToggleCollapse: () => void
  /** 清除日志 */
  onClear: () => void
  /** 面板最大高度 */
  maxHeight?: number
}

// 格式化时间戳
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return timestamp
  }
}

// 日志级别标签
const LogLevelTag: React.FC<{ level: WorkerLogLevel }> = ({ level }) => {
  const config = LOG_LEVEL_CONFIG[level]
  return (
    <Tag
      color={config.color}
      style={{
        fontSize: 10,
        padding: '0 4px',
        lineHeight: '16px',
        marginRight: 4,
      }}
    >
      {config.tag}
    </Tag>
  )
}

// 单条日志
const LogEntry: React.FC<{ log: WorkerLogItem }> = ({ log }) => {
  const config = LOG_LEVEL_CONFIG[log.level]

  return (
    <div
      style={{
        padding: '2px 8px',
        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
        fontSize: 12,
        lineHeight: '20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      }}
    >
      <Text
        style={{
          color: 'rgba(255, 255, 255, 0.45)',
          marginRight: 8,
        }}
      >
        {formatTimestamp(log.timestamp)}
      </Text>
      <LogLevelTag level={log.level} />
      <Text
        style={{
          color: 'rgba(255, 255, 255, 0.65)',
          marginRight: 8,
        }}
      >
        [{log.worker_id}]
      </Text>
      {log.pending_id && (
        <Tooltip title="任务 ID">
          <Text
            style={{
              color: '#1890ff',
              marginRight: 8,
            }}
          >
            #{log.pending_id}
          </Text>
        </Tooltip>
      )}
      <Text style={{ color: config.color }}>{log.message}</Text>
    </div>
  )
}

const WorkerLogPanel: React.FC<WorkerLogPanelProps> = ({
  logs,
  collapsed,
  onToggleCollapse,
  onClear,
  maxHeight = 300,
}) => {
  const logContainerRef = useRef<HTMLDivElement>(null)
  const shouldAutoScrollRef = useRef(true)

  // 自动滚动到底部
  const scrollToBottom = useCallback(() => {
    if (logContainerRef.current && shouldAutoScrollRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [])

  // 日志更新时自动滚动
  useEffect(() => {
    scrollToBottom()
  }, [logs, scrollToBottom])

  // 检测用户是否手动滚动
  const handleScroll = useCallback(() => {
    if (logContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current
      // 如果滚动到接近底部，启用自动滚动
      shouldAutoScrollRef.current = scrollHeight - scrollTop - clientHeight < 50
    }
  }, [])

  const title = (
    <Space>
      <CodeOutlined />
      <span>Worker 日志</span>
      <Tag color="blue">{logs.length}</Tag>
    </Space>
  )

  const extra = (
    <Space>
      <Button
        type="text"
        size="small"
        icon={<ClearOutlined />}
        onClick={onClear}
        disabled={logs.length === 0}
      >
        清空
      </Button>
      <Button
        type="text"
        size="small"
        icon={collapsed ? <DownOutlined /> : <UpOutlined />}
        onClick={onToggleCollapse}
      >
        {collapsed ? '展开' : '折叠'}
      </Button>
    </Space>
  )

  return (
    <Card
      title={title}
      extra={extra}
      size="small"
      bodyStyle={{
        padding: 0,
        display: collapsed ? 'none' : 'block',
      }}
      style={{
        backgroundColor: '#1e1e1e',
        borderColor: '#333',
      }}
      headStyle={{
        backgroundColor: '#2d2d2d',
        borderColor: '#333',
        color: '#fff',
        minHeight: 40,
        padding: '0 12px',
      }}
    >
      {!collapsed && (
        <div
          ref={logContainerRef}
          onScroll={handleScroll}
          style={{
            maxHeight,
            overflowY: 'auto',
            backgroundColor: '#1e1e1e',
          }}
        >
          {logs.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Text style={{ color: 'rgba(255, 255, 255, 0.45)' }}>
                  暂无日志
                </Text>
              }
              style={{ padding: '24px 0' }}
            />
          ) : (
            logs.map((log, index) => <LogEntry key={`${log.timestamp}-${index}`} log={log} />)
          )}
        </div>
      )}
    </Card>
  )
}

export default WorkerLogPanel
