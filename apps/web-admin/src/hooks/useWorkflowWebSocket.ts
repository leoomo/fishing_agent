/**
 * 数据工作流 WebSocket Hook
 *
 * 用于接收工作流实时状态更新、OCR 进度、Worker 日志等
 */

import { useEffect, useCallback, useRef } from 'react'
import { useDispatch } from 'react-redux'
import { useWebSocket } from './useWebSocket'
import type { AppDispatch } from '../store/store'
import {
  setWsConnected,
  updateStats,
  updateWorkers,
  updateOCRTask,
  updateTaskProgress,
  clearTaskProgress,
  appendWorkerLog,
} from '../store/slices/dataWorkflowSlice'
import type {
  WorkflowWSEvent,
  WorkflowStats,
  WorkerInfo,
  OCRProgressInfo,
  WorkerLogItem,
  OCRStage,
} from '../types/dataWorkflow'

// WebSocket 端点
const WS_WORKFLOW_URL = '/api/v1/admin/workflow/ws/workflow'

export interface UseWorkflowWebSocketOptions {
  /** 是否自动连接 */
  autoConnect?: boolean
  /** 连接成功回调 */
  onConnected?: () => void
  /** 断开连接回调 */
  onDisconnected?: () => void
  /** 接收到事件回调 */
  onEvent?: (event: WorkflowWSEvent) => void
}

export const useWorkflowWebSocket = (options: UseWorkflowWebSocketOptions = {}) => {
  const {
    autoConnect = true,
    onConnected,
    onDisconnected,
    onEvent,
  } = options

  const dispatch = useDispatch<AppDispatch>()
  const eventHandlerRef = useRef(onEvent)
  eventHandlerRef.current = onEvent

  // 处理 WebSocket 消息
  const handleMessage = useCallback(
    (data: string) => {
      try {
        const event = JSON.parse(data) as WorkflowWSEvent

        // 调用外部事件处理器
        eventHandlerRef.current?.(event)

        // 根据事件类型分发到对应 reducer
        switch (event.type) {
          case 'init':
            // 初始化数据
            if (event.data) {
              const initData = event.data as { stats?: WorkflowStats; workers?: WorkerInfo[] }
              if (initData.stats) {
                dispatch(updateStats(initData.stats))
              }
              if (initData.workers) {
                dispatch(updateWorkers(initData.workers))
              }
            }
            break

          case 'stats_update':
            // 统计数据更新
            if (event.data) {
              dispatch(updateStats(event.data as WorkflowStats))
            }
            break

          case 'worker_update':
            // Worker 列表更新
            if (event.data) {
              dispatch(updateWorkers(event.data as WorkerInfo[]))
            }
            break

          case 'task_claimed':
            // 任务被领取
            if (event.pending_id && event.data) {
              const claimData = event.data as { worker_id: string; ocr_provider: string | null }
              dispatch(
                updateOCRTask({
                  pending_id: event.pending_id,
                  ocr_status: 'processing',
                  ocr_worker_id: claimData.worker_id,
                  ocr_provider: claimData.ocr_provider,
                  ocr_started_at: event.timestamp,
                })
              )
            }
            break

          case 'ocr_started':
            // OCR 处理开始
            if (event.pending_id) {
              dispatch(
                updateOCRTask({
                  pending_id: event.pending_id,
                  ocr_status: 'processing',
                })
              )
            }
            break

          case 'ocr_progress':
            // OCR 处理进度
            if (event.pending_id && event.data) {
              const progressData = event.data as {
                stage: OCRStage
                progress: number
                message?: string
                current_image?: number
                total_images?: number
              }
              const progressInfo: OCRProgressInfo = {
                pending_id: event.pending_id,
                stage: progressData.stage,
                progress: progressData.progress,
                message: progressData.message || null,
                current_image: progressData.current_image ?? null,
                total_images: progressData.total_images ?? null,
                timestamp: event.timestamp,
              }
              dispatch(updateTaskProgress(progressInfo))
            }
            break

          case 'ocr_completed':
            // OCR 处理完成
            if (event.pending_id && event.data) {
              const completedData = event.data as {
                success: boolean
                processing_time_ms: number
                ocr_text_length?: number
                extracted_count?: number
              }
              dispatch(
                updateOCRTask({
                  pending_id: event.pending_id,
                  ocr_status: 'completed',
                  ocr_processing_time_ms: completedData.processing_time_ms,
                })
              )
              // 清除进度信息
              dispatch(clearTaskProgress(event.pending_id))
            }
            break

          case 'ocr_failed':
            // OCR 处理失败
            if (event.pending_id && event.data) {
              const failedData = event.data as {
                error_code: string
                error_message: string
                retry_count: number
              }
              dispatch(
                updateOCRTask({
                  pending_id: event.pending_id,
                  ocr_status: 'failed',
                  ocr_error_message: failedData.error_message,
                  ocr_retry_count: failedData.retry_count,
                })
              )
              // 清除进度信息
              dispatch(clearTaskProgress(event.pending_id))
            }
            break

          case 'worker_log':
            // Worker 日志
            if (event.data) {
              const logData = event.data as {
                worker_id: string
                level: string
                message: string
                pending_id?: number
                timestamp: string
              }
              const logItem: WorkerLogItem = {
                timestamp: logData.timestamp,
                worker_id: logData.worker_id,
                level: logData.level as 'debug' | 'info' | 'warning' | 'error',
                message: logData.message,
                pending_id: logData.pending_id ?? null,
              }
              dispatch(appendWorkerLog(logItem))
            }
            break

          case 'review_update':
            // 审核状态更新（可扩展）
            // 暂时不处理，需要时可以添加
            break

          default:
            console.warn('未知的 WebSocket 事件类型:', event.type)
        }
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error, data)
      }
    },
    [dispatch]
  )

  // 处理连接状态变化
  const handleConnect = useCallback(() => {
    dispatch(setWsConnected('connected'))
    onConnected?.()
  }, [dispatch, onConnected])

  const handleDisconnect = useCallback(() => {
    dispatch(setWsConnected('disconnected'))
    onDisconnected?.()
  }, [dispatch, onDisconnected])

  const handleError = useCallback(() => {
    dispatch(setWsConnected('error'))
  }, [dispatch])

  // 使用基础 WebSocket Hook
  const { isConnected, isConnecting, error, send, disconnect } = useWebSocket(
    autoConnect ? WS_WORKFLOW_URL : '',
    {
      onMessage: handleMessage,
      onConnect: handleConnect,
      onDisconnect: handleDisconnect,
      onError: handleError,
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      heartbeat: true,
      heartbeatInterval: 30000,
    }
  )

  // 更新连接状态
  useEffect(() => {
    if (isConnecting) {
      dispatch(setWsConnected('connecting'))
    }
  }, [isConnecting, dispatch])

  // 发送订阅任务命令（可选功能）
  const subscribeTask = useCallback(
    (pendingId: number) => {
      if (isConnected) {
        send(JSON.stringify({ action: 'subscribe_task', pending_id: pendingId }))
      }
    },
    [isConnected, send]
  )

  // 取消订阅任务（可选功能）
  const unsubscribeTask = useCallback(
    (pendingId: number) => {
      if (isConnected) {
        send(JSON.stringify({ action: 'unsubscribe_task', pending_id: pendingId }))
      }
    },
    [isConnected, send]
  )

  return {
    isConnected,
    isConnecting,
    error,
    disconnect,
    subscribeTask,
    unsubscribeTask,
  }
}

export default useWorkflowWebSocket
