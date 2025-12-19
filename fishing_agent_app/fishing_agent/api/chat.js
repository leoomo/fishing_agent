import request from './request.js'
import config from './config.js'

// 发送消息
async function sendMessage(messageData) {
  try {
    const response = await request.post('/chat/message', messageData)
    return response
  } catch (error) {
    console.error('发送消息失败:', error)
    throw error
  }
}

// 获取会话历史
async function getSessionHistory(sessionId) {
  try {
    const response = await request.get(`/chat/sessions/${sessionId}/messages`)
    return response
  } catch (error) {
    console.error('获取会话历史失败:', error)
    throw error
  }
}

// 获取用户会话列表
async function getUserSessions(params = {}) {
  try {
    const response = await request.get('/chat/sessions', params)
    return response
  } catch (error) {
    console.error('获取会话列表失败:', error)
    throw error
  }
}

// 创建新会话
async function createSession(sessionData) {
  try {
    const response = await request.post('/chat/sessions', sessionData)
    return response
  } catch (error) {
    console.error('创建会话失败:', error)
    throw error
  }
}

// 更新会话标题
async function updateSessionTitle(sessionId, title) {
  try {
    const response = await request.put(`/chat/sessions/${sessionId}`, { title })
    return response
  } catch (error) {
    console.error('更新会话标题失败:', error)
    throw error
  }
}

// 删除会话
async function deleteSession(sessionId) {
  try {
    const response = await request.delete(`/chat/sessions/${sessionId}`)
    return response
  } catch (error) {
    console.error('删除会话失败:', error)
    throw error
  }
}

// 清空会话消息
async function clearSessionMessages(sessionId) {
  try {
    const response = await request.delete(`/chat/sessions/${sessionId}/messages`)
    return response
  } catch (error) {
    console.error('清空会话消息失败:', error)
    throw error
  }
}

// 获取消息详情
async function getMessageDetail(messageId) {
  try {
    const response = await request.get(`/chat/messages/${messageId}`)
    return response
  } catch (error) {
    console.error('获取消息详情失败:', error)
    throw error
  }
}

// 删除消息
async function deleteMessage(messageId) {
  try {
    const response = await request.delete(`/chat/messages/${messageId}`)
    return response
  } catch (error) {
    console.error('删除消息失败:', error)
    throw error
  }
}

// 点赞/取消点赞消息
async function toggleMessageLike(messageId) {
  try {
    const response = await request.post(`/chat/messages/${messageId}/like`)
    return response
  } catch (error) {
    console.error('点赞消息失败:', error)
    throw error
  }
}

// 举报消息
async function reportMessage(messageId, reason) {
  try {
    const response = await request.post(`/chat/messages/${messageId}/report`, { reason })
    return response
  } catch (error) {
    console.error('举报消息失败:', error)
    throw error
  }
}

// 获取聊天建议问题
async function getSuggestedQuestions(category = '') {
  try {
    const params = category ? { category } : {}
    const response = await request.get('/chat/suggestions', params)
    return response
  } catch (error) {
    console.error('获取建议问题失败:', error)
    throw error
  }
}

// 流式发送消息 (SSE over chunked HTTP)
async function sendMessageStream(messageData, onMessage, onError, onComplete) {
  // #ifdef MP-WEIXIN
  const cfg = config.getConfig()
  const token = config.tokenManager.getToken()

  return new Promise((resolve, reject) => {
    const url = `${cfg.baseURL}/chat/message/stream`

    // 增量解码 ArrayBuffer 为 UTF-8 文本
    let buffer = ''
    let lastText = '' // 参照实践：缓存上一次未完整的片段
    let completed = false

    // 安全回调：过滤特定伪错误，避免重复触发
    function safeOnError(err) {
      if (completed) return
      const msg = (err && (err.errMsg || err.message)) || ''
      if (msg.includes('No active exception to reraise')) {
        if (!completed && onComplete) onComplete()
        completed = true
        return
      }
      if (onError) onError(err)
    }
    function safeOnComplete() {
      if (completed) return
      if (onComplete) onComplete()
      completed = true
    }
    function ab2str(ab) {
      try {
        // 优先使用 TextDecoder（基础库 2.10+ 支持）
        const dec = typeof TextDecoder !== 'undefined' ? new TextDecoder('utf-8') : null
        if (dec) return dec.decode(ab)
      } catch (_) {}
      // 兼容降级
      const arr = new Uint8Array(ab)
      let result = ''
      const chunk = 0x8000
      for (let i = 0; i < arr.length; i += chunk) {
        result += String.fromCharCode.apply(null, arr.subarray(i, i + chunk))
      }
      try { return decodeURIComponent(escape(result)) } catch (_) { return result }
    }

    const requestTask = wx.request({
      url,
      method: 'POST',
      data: messageData,
      enableChunked: true,
      responseType: 'arraybuffer',
      timeout: cfg.timeout || 120000,
      header: {
        'content-type': 'application/json',
        'Accept': 'text/event-stream',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      success: (res) => {
        // 若未通过 chunk 收齐，也在此兜底完成
        safeOnComplete()
        resolve(res)
      },
      fail: (err) => {
        // 后端生成器在结束时可能触发伪错误，safeOnError会忽略
        safeOnError(err)
        reject(err)
      }
    })

    // 头信息回调（可选）
    if (requestTask && requestTask.onHeadersReceived) {
      requestTask.onHeadersReceived(() => {})
    }

    // 分块接收回调：解析 SSE 行
    if (requestTask && requestTask.onChunkReceived) {
      requestTask.onChunkReceived((resp) => {
        try {
          const chunkText = ab2str(resp.data)
          if (!chunkText) return
          // 累加到上次尾部，提升鲁棒性（参考实践）
          let text = lastText + chunkText
          lastText = ''

          // 以空行分段（兼容 \r\n 与 \n）
          let parts = text.split(/\r?\n\r?\n/).filter(Boolean)

          // 预判最后一段是否可能是未完整 JSON，尝试整体 JSON.parse 校验
          try {
            parts.every(item => {
              const idx = item.indexOf('{')
              if (idx === -1) return true
              JSON.parse(item.slice(idx))
              return true
            })
          } catch (_) {
            // 将最后一段缓存到 lastText，下次拼接
            lastText = parts.pop() || ''
          }

          // 处理可解析的完整段
          for (const part of parts) {
            const lines = part.split(/\r?\n/)
            for (const raw of lines) {
              const line = raw.trim()
              if (!line.toLowerCase().startsWith('data:')) continue

              // 兼容 data: / data:data: 前缀，定位第一个 '{' 更稳妥
              const braceIdx = line.indexOf('{')
              const payload = braceIdx > -1 ? line.slice(braceIdx) : line.replace(/^data:\s*/i, '')

              if (payload === '[DONE]' || payload === '{"done":true}' || payload === '{\"done\": true}') {
                safeOnComplete()
                continue
              }
              try {
                const json = JSON.parse(payload)
                if (json && json.error) {
                  safeOnError(new Error(json.error))
                  continue
                }
                // 统一 { content } - 优先使用 delta（增量），否则使用 content（全文）
                const textDelta = (json && (json.delta || json.content || json.message)) || ''
                if (textDelta && onMessage) {
                  console.log('[SSE] delta:', textDelta.substring(0, 30))
                  onMessage({ content: textDelta })
                }
              } catch (_) {
                // 纯文本增量兜底
                if (payload && onMessage) onMessage({ content: payload })
              }
            }
          }
        } catch (e) {
          safeOnError(e)
        }
      })
    }
  })
  // #endif

  // #ifndef MP-WEIXIN
  // 其他端维持非流式兜底
  try {
    const resp = await sendMessage(messageData)
    const text = (resp && (resp.message || resp.content)) || ''
    if (onMessage) onMessage({ content: text })
    if (onComplete) onComplete()
    return resp
  } catch (e) {
    if (onError) onError(e)
    throw e
  }
  // #endif
}

export default {
  sendMessage,
  getSessionHistory,
  getUserSessions,
  createSession,
  updateSessionTitle,
  deleteSession,
  clearSessionMessages,
  getMessageDetail,
  deleteMessage,
  toggleMessageLike,
  reportMessage,
  getSuggestedQuestions,
  sendMessageStream
}
