import { useEffect, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { message } from 'antd'
import { useLoginWebSocket } from './useWebSocket'
import {
  setLoginState,
  updateLoginStatus,
  clearLoginState,
  selectLoginStateByTaskId,
  LoginStatus,
} from '../store/slices/crawlerSlice'
import { crawlerApi } from '../api/services/crawler'

export interface UseLoginInteractionOptions {
  onComplete?: (userInfo: any) => void
  onError?: (error: string) => void
  onStatusChange?: (status: LoginStatus) => void
}

export const useLoginInteraction = (
  taskId: number,
  platform: string,
  options: UseLoginInteractionOptions = {}
) => {
  const { onComplete, onError, onStatusChange } = options

  const dispatch = useDispatch()
  const loginState = useSelector(selectLoginStateByTaskId(taskId))

  // WebSocket连接
  const { isConnected, lastMessage, error: wsError } = useLoginWebSocket(taskId, {
    onConnect: () => {
      console.log(`登录WebSocket已连接 - 任务 ${taskId}`)
    },
    onDisconnect: () => {
      console.log(`登录WebSocket已断开 - 任务 ${taskId}`)
    },
    onError: (error) => {
      console.error(`登录WebSocket连接错误 - 任务 ${taskId}:`, error)
      message.error('登录连接失败，请刷新页面重试')
    },
  })

  // 处理WebSocket消息
  useEffect(() => {
    if (!lastMessage) return

    try {
      const event = JSON.parse(lastMessage)
      handleLoginEvent(event)
    } catch (error) {
      console.error('解析登录WebSocket消息失败:', error)
    }
  }, [lastMessage])

  // 处理登录事件
  const handleLoginEvent = useCallback((event: any) => {
    const { type, data } = event

    switch (type) {
      case 'qr_code_ready':
        dispatch(updateLoginStatus({
          taskId,
          status: 'qr_ready',
          data: {
            qrCode: data.qrCode,
            expiresAt: data.expiresAt,
          },
        }))
        onStatusChange?.('qr_ready')
        break

      case 'waiting_scan':
        dispatch(updateLoginStatus({
          taskId,
          status: 'waiting_scan',
          data: { message: data.message },
        }))
        onStatusChange?.('waiting_scan')
        break

      case 'scan_detected':
        dispatch(updateLoginStatus({
          taskId,
          status: 'scan_detected',
          data: { message: data.message },
        }))
        onStatusChange?.('scan_detected')
        break

      case 'verifying':
        dispatch(updateLoginStatus({
          taskId,
          status: 'verifying',
          data: { message: data.message },
        }))
        onStatusChange?.('verifying')
        break

      case 'login_success':
        dispatch(updateLoginStatus({
          taskId,
          status: 'login_success',
          data: {
            userInfo: data.userInfo,
          },
        }))
        onStatusChange?.('login_success')
        onComplete?.(data.userInfo)
        message.success('登录成功！')
        break

      case 'login_failed':
        dispatch(updateLoginStatus({
          taskId,
          status: 'login_failed',
          data: {
            errorMessage: data.reason,
            retryable: data.retryable,
          },
        }))
        onStatusChange?.('login_failed')
        onError?.(data.reason)
        message.error(`登录失败: ${data.reason}`)
        break

      case 'qr_code_expired':
        dispatch(updateLoginStatus({
          taskId,
          status: 'qr_expired',
          data: { message: data.message },
        }))
        onStatusChange?.('qr_expired')
        message.warning('二维码已过期，请刷新后重新扫码')
        break

      default:
        console.log('未知登录事件:', event)
    }
  }, [taskId, dispatch, onComplete, onError, onStatusChange])

  // 开始登录流程
  const startLogin = useCallback(async () => {
    try {
      // 初始化登录状态
      dispatch(setLoginState({
        taskId,
        loginState: {
          taskId,
          platform: platform as any,
          status: 'generating_qr',
        },
      }))

      // 调用API开始登录
      const response = await crawlerApi.startLogin(taskId)

      dispatch(setLoginState({
        taskId,
        loginState: {
          taskId,
          platform: platform as any,
          status: 'qr_ready',
          qrCode: response.qr_code,
          expiresAt: response.expires_at,
        },
      }))

      onStatusChange?.('qr_ready')
      return response

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '启动登录失败'

      dispatch(updateLoginStatus({
        taskId,
        status: 'login_failed',
        data: {
          errorMessage,
        },
      }))

      onStatusChange?.('login_failed')
      onError?.(errorMessage)
      message.error(errorMessage)
      throw error
    }
  }, [taskId, platform, dispatch, onStatusChange, onError])

  // 刷新二维码
  const refreshQRCode = useCallback(async () => {
    try {
      dispatch(updateLoginStatus({
        taskId,
        status: 'generating_qr',
      }))

      const response = await crawlerApi.refreshQRCode(taskId)

      dispatch(updateLoginStatus({
        taskId,
        status: 'qr_ready',
        data: {
          qrCode: response.qr_code,
          expiresAt: response.expires_at,
        },
      }))

      onStatusChange?.('qr_ready')
      return response

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '刷新二维码失败'

      dispatch(updateLoginStatus({
        taskId,
        status: 'login_failed',
        data: {
          errorMessage,
        },
      }))

      onError?.(errorMessage)
      message.error(errorMessage)
      throw error
    }
  }, [taskId, dispatch, onStatusChange, onError])

  // 重试登录
  const retryLogin = useCallback(() => {
    dispatch(setLoginState({
      taskId,
      loginState: {
        taskId,
        platform: platform as any,
        status: 'idle',
      },
    }))
    onStatusChange?.('idle')
  }, [taskId, platform, dispatch, onStatusChange])

  // 取消登录
  const cancelLogin = useCallback(() => {
    dispatch(clearLoginState(taskId))
    onStatusChange?.('idle')
  }, [taskId, dispatch, onStatusChange])

  // 检查二维码是否过期
  const isQRCodeExpired = useCallback(() => {
    if (!loginState?.expiresAt) return false
    return Date.now() > loginState.expiresAt
  }, [loginState])

  // 获取剩余有效时间（毫秒）
  const getQRCodeRemainingTime = useCallback(() => {
    if (!loginState?.expiresAt) return 0
    return Math.max(0, loginState.expiresAt - Date.now())
  }, [loginState])

  // 格式化剩余时间
  const formatRemainingTime = useCallback((ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }, [])

  return {
    // 状态
    loginState,
    isConnected,
    wsError,

    // 计算属性
    isLoading: ['generating_qr', 'verifying'].includes(loginState?.status || 'idle'),
    isReadyForScan: loginState?.status === 'qr_ready',
    isWaitingScan: loginState?.status === 'waiting_scan',
    isScanDetected: loginState?.status === 'scan_detected',
    isSuccess: loginState?.status === 'login_success',
    isFailed: ['login_failed', 'qr_expired'].includes(loginState?.status || 'idle'),
    isExpired: loginState?.status === 'qr_expired' || isQRCodeExpired(),
    remainingTime: formatRemainingTime(getQRCodeRemainingTime()),

    // 操作方法
    startLogin,
    refreshQRCode,
    retryLogin,
    cancelLogin,

    // 工具方法
    isQRCodeExpired,
    getQRCodeRemainingTime,
    formatRemainingTime,
  }
}

export default useLoginInteraction