/**
 * 爬虫任务进度监控 Hook
 *
 * 专门用于监控爬虫任务的实时进度，与 Redux store 集成
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import { useDispatch } from 'react-redux'
import { message } from 'antd'
import type { AppDispatch } from '../store/store'
import { fetchTasks } from '../store/slices/crawlerSlice'

export interface CrawlerProgressMessage {
  type: 'init' | 'progress' | 'completion'
  task_id: number
  status: string
  progress: number
  message?: string
  items_processed?: number
  items_success?: number
  items_failed?: number
  total_items?: number
  timestamp: string
}

export interface CrawlerProgressState {
  isConnected: boolean
  progress: number
  status: string
  message: string
  lastUpdate: string | null
}

interface UseCrawlerProgressOptions {
  /** 任务完成时的回调 */
  onComplete?: (status: string) => void
  /** 连接错误时的回调 */
  onError?: (error: string) => void
  /** 是否自动重连 */
  autoReconnect?: boolean
  /** 重连间隔（毫秒） */
  reconnectInterval?: number
}

export function useCrawlerProgress(
  taskId: number | null,
  options: UseCrawlerProgressOptions = {}
) {
  const {
    onComplete,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
  } = options

  const dispatch = useDispatch<AppDispatch>()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const [state, setState] = useState<CrawlerProgressState>({
    isConnected: false,
    progress: 0,
    status: 'PENDING',
    message: '',
    lastUpdate: null,
  })

  // 清理重连定时器
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  // 处理消息
  const handleMessage = useCallback((data: string) => {
    // 处理 ping/pong
    if (data === 'ping' || data === 'pong') {
      if (data === 'ping' && wsRef.current) {
        wsRef.current.send('pong')
      }
      return
    }

    try {
      const msg: CrawlerProgressMessage = JSON.parse(data)

      setState((prev) => ({
        ...prev,
        progress: msg.progress ?? prev.progress,
        status: msg.status ?? prev.status,
        message: msg.message ?? prev.message,
        lastUpdate: msg.timestamp,
      }))

      // 任务完成时刷新列表
      if (msg.type === 'completion' || msg.status === 'SUCCESS' || msg.status === 'FAILED') {
        dispatch(fetchTasks({ page: 1, pageSize: 20 }))
        onComplete?.(msg.status)

        if (msg.status === 'SUCCESS') {
          message.success('任务执行完成')
        } else if (msg.status === 'FAILED') {
          message.error(`任务执行失败: ${msg.message || '未知错误'}`)
        }
      }
    } catch (e) {
      console.error('解析 WebSocket 消息失败:', e)
    }
  }, [dispatch, onComplete])

  // 建立连接
  const connect = useCallback(() => {
    if (!taskId) return

    // 关闭现有连接
    if (wsRef.current) {
      wsRef.current.close()
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/admin/crawler/ws/crawler/${taskId}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setState((prev) => ({ ...prev, isConnected: true }))
        clearReconnectTimeout()
        console.log(`[CrawlerProgress] WebSocket 已连接: task_id=${taskId}`)
      }

      ws.onmessage = (event) => {
        handleMessage(event.data)
      }

      ws.onclose = () => {
        setState((prev) => ({ ...prev, isConnected: false }))
        console.log(`[CrawlerProgress] WebSocket 已断开: task_id=${taskId}`)

        // 自动重连（仅在任务未完成时）
        if (autoReconnect && state.status !== 'SUCCESS' && state.status !== 'FAILED') {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      ws.onerror = (error) => {
        console.error('[CrawlerProgress] WebSocket 错误:', error)
        onError?.('WebSocket 连接错误')
      }
    } catch (error) {
      console.error('[CrawlerProgress] 建立连接失败:', error)
      onError?.('无法建立 WebSocket 连接')
    }
  }, [taskId, autoReconnect, reconnectInterval, handleMessage, onError, clearReconnectTimeout, state.status])

  // 断开连接
  const disconnect = useCallback(() => {
    clearReconnectTimeout()
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setState((prev) => ({ ...prev, isConnected: false }))
  }, [clearReconnectTimeout])

  // 当 taskId 变化时重新连接
  useEffect(() => {
    if (taskId) {
      // 重置状态
      setState({
        isConnected: false,
        progress: 0,
        status: 'PENDING',
        message: '',
        lastUpdate: null,
      })
      connect()
    }

    return () => {
      disconnect()
    }
  }, [taskId, connect, disconnect])

  return {
    ...state,
    disconnect,
    reconnect: connect,
  }
}

export default useCrawlerProgress
