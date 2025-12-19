import chatApi from '../api/chat.js'
import userStore from './user.js'

// 聊天状态
const state = {
  // 当前会话ID
  currentSessionId: null,
  // 消息列表
  messages: [],
  // 会话列表
  sessions: [],
  // 加载状态
  loading: false,
  // 发送消息状态
  sending: false,
  // 建议问题
  suggestedQuestions: [],
  // 是否正在流式接收消息
  streaming: false,
  // 当前流式消息内容
  streamingMessage: ''
}

// 监听器列表
const listeners = []

// 添加监听器
function addListener(listener) {
  listeners.push(listener)
}

// 移除监听器
function removeListener(listener) {
  const index = listeners.indexOf(listener)
  if (index > -1) {
    listeners.splice(index, 1)
  }
}

// 通知所有监听器
function notifyListeners() {
  listeners.forEach(listener => {
    if (typeof listener === 'function') {
      listener(getChatState())
    }
  })
}

// 获取聊天状态
function getChatState() {
  return {
    ...state
  }
}

// 准备新会话（不立即创建，延迟到发送第一条消息时）
async function createNewSession(title = '新对话') {
  // 清空当前会话状态，但不立即调用API创建
  // 会话会在发送第一条消息时自动创建
  state.currentSessionId = null
  state.messages = []
  state.streamingMessage = ''
  state.streaming = false
  state.sending = false

  // 触发页面更新
  notifyListeners()

  return null  // 返回null表示会话尚未创建
}

// 实际创建会话（内部方法，由发送消息时调用）
async function _createSessionOnServer(title = '新对话') {
  try {
    const sessionData = {
      title: title,
      user_id: userStore.getUserInfo()?.id || 1
    }

    const response = await chatApi.createSession(sessionData)

    // 更新当前会话ID
    state.currentSessionId = response.id

    // 添加到会话列表
    state.sessions.unshift(response)

    return response
  } catch (error) {
    console.error('创建会话失败:', error)
    throw error
  }
}

// 获取会话列表
async function fetchSessions() {
  try {
    state.loading = true

    const response = await chatApi.getUserSessions()
    // API 返回格式: {sessions: [...], total: N}
    const sessions = response?.sessions || response?.items || response
    state.sessions = Array.isArray(sessions) ? sessions : []

    // 如果没有当前会话且有会话列表，设置第一个为当前会话
    if (!state.currentSessionId && state.sessions.length > 0) {
      state.currentSessionId = state.sessions[0].id
      // 获取该会话的消息
      fetchMessages(state.currentSessionId)
    }

    // 触发页面更新
    notifyListeners()

    return response
  } catch (error) {
    console.error('获取会话列表失败:', error)
    throw error
  } finally {
    state.loading = false
  }
}

// 获取消息列表
async function fetchMessages(sessionId) {
  try {
    state.loading = true

    const response = await chatApi.getSessionHistory(sessionId)
    // API 返回格式: {messages: [...], total: N}
    const messages = response?.messages || response?.items || response
    state.messages = Array.isArray(messages) ? messages : []

    // 触发页面更新
    notifyListeners()

    return response
  } catch (error) {
    console.error('获取消息列表失败:', error)
    throw error
  } finally {
    state.loading = false
  }
}

// 发送消息
async function sendMessage(content) {
  if (!content.trim()) return

  // 如果没有当前会话，创建新会话
  if (!state.currentSessionId) {
    await _createSessionOnServer()
  }
  
  try {
    state.sending = true
    
    // 添加用户消息到列表
    const userMessage = {
      id: Date.now(), // 临时ID
      role: 'user',
      content: content.trim(),
      created_at: new Date().toISOString()
    }
    
    state.messages.push(userMessage)
    
    // 触发页面更新
    notifyListeners()
    
    // 准备消息数据
    const messageData = {
      message: content.trim(),
      session_id: state.currentSessionId,
      user_id: userStore.getUserInfo()?.id || 1
    }
    
    // 发送消息
    const response = await chatApi.sendMessage(messageData)
    
    // 添加AI回复到列表
    const aiMessage = {
      id: response.id || Date.now() + 1,
      role: 'assistant',
      content: response.message,
      created_at: response.created_at || new Date().toISOString()
    }
    
    state.messages.push(aiMessage)
        
        // 自动生成会话标题（如果当前会话是默认标题）
        generateSessionTitleIfNeeded()    
    // 触发页面更新
    notifyListeners()
    
    return response
  } catch (error) {
    console.error('发送消息失败:', error)
    
    // 移除用户消息
    if (state.messages.length > 0 && state.messages[state.messages.length - 1].role === 'user') {
      state.messages.pop()
      notifyListeners()
    }
    
    throw error
  } finally {
    state.sending = false
  }
}

// 流式发送消息
async function sendMessageStream(content, onChunk) {
  if (!content.trim()) return

  // 如果没有当前会话，创建新会话
  if (!state.currentSessionId) {
    await _createSessionOnServer()
  }
  
  try {
    state.sending = true
    state.streaming = true
    state.streamingMessage = ''
    
    // 添加用户消息到列表
    const userMessage = {
      id: Date.now(), // 临时ID
      role: 'user',
      content: content.trim(),
      created_at: new Date().toISOString()
    }
    
    state.messages.push(userMessage)
    
    // 触发页面更新
    notifyListeners()
    
    // 准备消息数据
    const messageData = {
      message: content.trim(),
      session_id: state.currentSessionId,
      user_id: userStore.getUserInfo()?.id || 1
    }
    
    // 发送流式消息
    await chatApi.sendMessageStream(
      messageData,
      // onMessage - 每次收到流式增量时触发
      (chunk) => {
        const delta = chunk.content || ''
        if (delta) {
          state.streamingMessage += delta
          // 调用回调函数
          if (onChunk) onChunk(chunk)
          // 触发页面更新
          notifyListeners()
        }
      },
      // onError
      (error) => {
        console.error('流式消息错误:', error)
        throw error
      },
      // onComplete
      () => {
        // 添加完整的AI回复到列表
        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: state.streamingMessage,
          created_at: new Date().toISOString()
        }
        
        state.messages.push(aiMessage)
        
        // 自动生成会话标题（如果当前会话是默认标题）
        generateSessionTitleIfNeeded()        
        // 重置流式状态
        state.streaming = false
        // 立即结束发送态，避免出现额外“思考中”占位
        state.sending = false
        state.streamingMessage = ''
        
        // 触发页面更新
        notifyListeners()
      }
    )
    
    return state.streamingMessage
  } catch (error) {
    console.error('发送流式消息失败:', error)
    
    // 移除用户消息
    if (state.messages.length > 0 && state.messages[state.messages.length - 1].role === 'user') {
      state.messages.pop()
      notifyListeners()
    }
    
    // 重置流式状态
    state.streaming = false
    state.streamingMessage = ''
    
    throw error
  } finally {
    state.sending = false
  }
}

// 切换会话
async function switchSession(sessionId) {
  if (sessionId === state.currentSessionId) return
  
  state.currentSessionId = sessionId
  
  // 获取该会话的消息
  await fetchMessages(sessionId)
  
  // 触发页面更新
  notifyListeners()
}

// 删除会话
async function deleteSession(sessionId) {
  try {
    await chatApi.deleteSession(sessionId)
    
    // 从会话列表中移除
    state.sessions = state.sessions.filter(session => session.id !== sessionId)
    
    // 如果删除的是当前会话，切换到第一个会话
    if (sessionId === state.currentSessionId) {
      if (state.sessions.length > 0) {
        state.currentSessionId = state.sessions[0].id
        await fetchMessages(state.currentSessionId)
      } else {
        state.currentSessionId = null
        state.messages = []
      }
    }
    
    // 触发页面更新
    notifyListeners()
  } catch (error) {
    console.error('删除会话失败:', error)
    throw error
  }
}

// 清空当前会话消息
async function clearCurrentSession() {
  if (!state.currentSessionId) return
  
  try {
    await chatApi.clearSessionMessages(state.currentSessionId)
    
    // 清空消息列表
    state.messages = []
    
    // 触发页面更新
    notifyListeners()
  } catch (error) {
    console.error('清空会话消息失败:', error)
    throw error
  }
}

// 获取建议问题
async function fetchSuggestedQuestions(category = '') {
  try {
    const response = await chatApi.getSuggestedQuestions(category)
    // API 返回格式: {suggestions: [...]}
    const suggestions = response?.suggestions || response?.items || response
    state.suggestedQuestions = Array.isArray(suggestions) ? suggestions : []

    // 触发页面更新
    notifyListeners()

    return response
  } catch (error) {
    console.error('获取建议问题失败:', error)
    throw error
  }
}

// 重置状态
function resetState() {
  state.currentSessionId = null
  state.messages = []
  state.sessions = []
  state.loading = false
  state.sending = false
  state.suggestedQuestions = []
  state.streaming = false
  state.streamingMessage = ''
  
  // 触发页面更新
  notifyListeners()
}

// 获取当前会话ID
function getCurrentSessionId() {
  return state.currentSessionId
}

// 获取消息列表
function getMessages() {
  return state.messages
}

// 获取会话列表
function getSessions() {
  return state.sessions
}

// 获取加载状态
function getLoading() {
  return state.loading
}

// 获取发送状态
function getSending() {
  return state.sending
}

// 获取建议问题
function getSuggestedQuestions() {
  return state.suggestedQuestions
}

// 获取流式状态
function getStreaming() {
  return state.streaming
}

// 获取当前流式消息
function getStreamingMessage() {
  return state.streamingMessage
}


// 自动生成会话标题（如果需要）
async function generateSessionTitleIfNeeded() {
  if (!state.currentSessionId) return
  
  // 查找当前会话
  const currentSession = state.sessions.find(s => s.id === state.currentSessionId)
  if (!currentSession) return
  
  // 如果不是默认标题，则跳过
  if (currentSession.title && currentSession.title.trim() !== "新对话") return
  
  try {
    // 获取第一轮对话内容来生成标题
    const userMessage = state.messages.find(m => m.role === "user")
    const aiMessage = state.messages.find(m => m.role === "assistant")
    
    if (userMessage && aiMessage) {
      // 使用用户的问题作为标题，截取前20个字符
      let title = userMessage.content.substring(0, 20)
      if (userMessage.content.length > 20) {
        title += "..."
      }
      
      // 更新会话标题
      await chatApi.updateSessionTitle(state.currentSessionId, title)
      
      // 更新本地状态
      currentSession.title = title
      notifyListeners()
    }
  } catch (error) {
    console.error("生成会话标题失败:", error)
  }
}

export default {
  // 方法
  createNewSession,
  fetchSessions,
  fetchMessages,
  sendMessage,
  sendMessageStream,
  switchSession,
  deleteSession,
  clearCurrentSession,
  fetchSuggestedQuestions,
  resetState,
  generateSessionTitleIfNeeded,  
  // 状态获取
  getChatState,
  getCurrentSessionId,
  getMessages,
  getSessions,
  getLoading,
  getSending,
  getSuggestedQuestions,
  getStreaming,
  getStreamingMessage,
  
  // 监听器
  addListener,
  removeListener
}
