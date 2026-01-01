import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketOptions {
  onMessage?: (data: string) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeat?: boolean
  heartbeatInterval?: number
}

export interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  reconnectAttempts: number
  lastMessage: string | null
}

export const useWebSocket = (
  url: string,
  options: WebSocketOptions = {}
): WebSocketState & { send: (data: string) => void; disconnect: () => void } => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeat = true,
    heartbeatInterval = 30000,
  } = options

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
    lastMessage: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const heartbeatIntervalRef = useRef<number | null>(null)
  const manualCloseRef = useRef<boolean>(false)
  const reconnectAttemptsRef = useRef<number>(0)

  // Use refs for options to avoid recreating connect when they change
  const optionsRef = useRef({
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnect,
    reconnectInterval,
    maxReconnectAttempts,
    heartbeat,
    heartbeatInterval,
  })

  // Update options ref when values change
  optionsRef.current = {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnect,
    reconnectInterval,
    maxReconnectAttempts,
    heartbeat,
    heartbeatInterval,
  }

  // 构建完整的WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}${url.startsWith('/') ? url : `/${url}`}`
  }, [url])

  // 清理重连定时器
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  // 清理心跳定时器
  const clearHeartbeatInterval = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
  }, [])

  // 开始心跳
  const startHeartbeat = useCallback(() => {
    if (!optionsRef.current.heartbeat || !wsRef.current) return

    clearHeartbeatInterval()
    heartbeatIntervalRef.current = window.setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        try {
          wsRef.current.send(JSON.stringify({ type: 'ping' }))
        } catch (error) {
          console.error('WebSocket心跳发送失败:', error)
        }
      }
    }, optionsRef.current.heartbeatInterval) as unknown as number
  }, [clearHeartbeatInterval])

  // 建立WebSocket连接
  const connect = useCallback(() => {
    // 如果已手动关闭，不再尝试连接
    if (manualCloseRef.current) {
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setState(prev => ({
      ...prev,
      isConnecting: true,
      error: null,
    }))

    try {
      const wsUrl = getWebSocketUrl()
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0,
        }))

        manualCloseRef.current = false
        startHeartbeat()
        optionsRef.current.onConnect?.()
      }

      ws.onmessage = (event) => {
        const data = event.data.toString()

        // 处理心跳响应
        if (data === 'pong') {
          return
        }

        setState(prev => ({
          ...prev,
          lastMessage: data,
        }))

        optionsRef.current.onMessage?.(data)
      }

      ws.onclose = (event) => {
        const wasClean = event.wasClean
        const code = event.code
        const reason = event.reason

        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }))

        clearHeartbeatInterval()
        optionsRef.current.onDisconnect?.()

        // 如果不是手动关闭且启用了重连
        if (!manualCloseRef.current && optionsRef.current.reconnect && reconnectAttemptsRef.current < optionsRef.current.maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1
          setState(prev => ({
            ...prev,
            reconnectAttempts: reconnectAttemptsRef.current,
            error: `连接断开，正在尝试重连 (${reconnectAttemptsRef.current}/${optionsRef.current.maxReconnectAttempts})`,
          }))

          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect()
          }, optionsRef.current.reconnectInterval) as unknown as number
        } else if (!manualCloseRef.current) {
          setState(prev => ({
            ...prev,
            error: `连接已断开且无法重连 (${wasClean ? '正常关闭' : `异常关闭: ${code} ${reason}`})`,
          }))
        }
      }

      ws.onerror = (error) => {
        // 如果是手动关闭，不记录错误（避免 StrictMode 双重渲染导致的警告）
        if (manualCloseRef.current) {
          return
        }

        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          error: 'WebSocket连接错误',
        }))

        console.error('WebSocket错误:', error)
        optionsRef.current.onError?.(error)
      }

    } catch (error) {
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: `无法建立WebSocket连接: ${error}`,
      }))

      console.error('WebSocket连接失败:', error)
    }
  }, [
    getWebSocketUrl,
    startHeartbeat,
    clearHeartbeatInterval,
  ])

  // 发送消息
  const send = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(data)
        return true
      } catch (error) {
        console.error('WebSocket发送消息失败:', error)
        setState(prev => ({
          ...prev,
          error: '发送消息失败',
        }))
        return false
      }
    } else {
      const errorMsg = 'WebSocket未连接，无法发送消息'
      console.error(errorMsg)
      setState(prev => ({
        ...prev,
        error: errorMsg,
      }))
      return false
    }
  }, [])

  // 断开连接
  const disconnect = useCallback(() => {
    manualCloseRef.current = true
    clearReconnectTimeout()
    clearHeartbeatInterval()

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    reconnectAttemptsRef.current = 0
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      reconnectAttempts: 0,
    }))
  }, [clearReconnectTimeout, clearHeartbeatInterval])

  // 组件挂载时建立连接（延迟一帧，避免 StrictMode 双重渲染导致的连接取消警告）
  useEffect(() => {
    // 重置手动关闭标志
    manualCloseRef.current = false

    // 使用 requestAnimationFrame 延迟连接，让 StrictMode 的 cleanup 先执行
    const rafId = requestAnimationFrame(() => {
      if (!manualCloseRef.current) {
        connect()
      }
    })

    return () => {
      cancelAnimationFrame(rafId)
      disconnect()
    }
  }, [connect, disconnect])

  // 处理页面可见性变化，优化重连逻辑
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面隐藏时暂停心跳
        clearHeartbeatInterval()
      } else {
        // 页面显示时检查连接状态
        // 只有当没有活跃连接且不在连接过程中时才尝试重连
        if (!wsRef.current && optionsRef.current.reconnect) {
          connect()
        } else if (wsRef.current?.readyState === WebSocket.OPEN) {
          startHeartbeat()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [connect, startHeartbeat, clearHeartbeatInterval])

  // 处理网络状态变化
  useEffect(() => {
    const handleOnline = () => {
      if (!wsRef.current && optionsRef.current.reconnect) {
        setState(prev => ({
          ...prev,
          error: '网络已恢复，正在重连...',
        }))
        connect()
      }
    }

    const handleOffline = () => {
      setState(prev => ({
        ...prev,
        error: '网络连接已断开',
      }))
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [connect])

  return {
    ...state,
    send,
    disconnect,
  }
}

// 专门用于数据采集任务的WebSocket Hook
export const useCrawlerWebSocket = (taskId: number) => {
  return useWebSocket(`/api/v1/admin/crawler/ws/crawler/${taskId}`, {
    reconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeat: true,
  })
}

// 专门用于登录的WebSocket Hook
export const useLoginWebSocket = (taskId: number) => {
  return useWebSocket(`/api/v1/admin/crawler/login/${taskId}`, {
    reconnect: true,
    reconnectInterval: 2000,
    maxReconnectAttempts: 10, // 登录重连次数更多
    heartbeat: false, // 登录不需要心跳
  })
}

// 通用WebSocket连接池管理
class WebSocketPool {
  private connections: Map<string, WebSocket> = new Map()
  private subscribers: Map<string, Set<(message: string) => void>> = new Map()

  connect(url: string): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      if (this.connections.has(url)) {
        const existing = this.connections.get(url)!
        if (existing.readyState === WebSocket.OPEN) {
          resolve(existing)
          return
        }
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}${url.startsWith('/') ? url : `/${url}`}`

      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        this.connections.set(url, ws)
        resolve(ws)
      }

      ws.onmessage = (event) => {
        const subscribers = this.subscribers.get(url)
        if (subscribers) {
          subscribers.forEach(callback => callback(event.data))
        }
      }

      ws.onclose = () => {
        this.connections.delete(url)
        this.subscribers.delete(url)
      }

      ws.onerror = (error) => {
        reject(error)
      }
    })
  }

  subscribe(url: string, callback: (message: string) => void): () => void {
    if (!this.subscribers.has(url)) {
      this.subscribers.set(url, new Set())
    }
    this.subscribers.get(url)!.add(callback)

    // 返回取消订阅函数
    return () => {
      const subscribers = this.subscribers.get(url)
      if (subscribers) {
        subscribers.delete(callback)
        if (subscribers.size === 0) {
          this.subscribers.delete(url)
        }
      }
    }
  }

  disconnect(url: string): void {
    const ws = this.connections.get(url)
    if (ws) {
      ws.close()
      this.connections.delete(url)
    }
    this.subscribers.delete(url)
  }

  disconnectAll(): void {
    this.connections.forEach(ws => ws.close())
    this.connections.clear()
    this.subscribers.clear()
  }
}

// 导出全局WebSocket连接池实例
export const wsPool = new WebSocketPool()

export default useWebSocket