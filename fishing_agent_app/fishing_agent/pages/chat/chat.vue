<template>
  <view class="chat-container">
    <!-- 顶部导航栏 -->
    <view class="chat-header">
      <view class="header-left">
        <text class="header-title">路亚小助理</text>
      </view>
      <view class="header-right">
      <text class="new-chat" @click="createNewChat">新对话</text>
      <text class="new-chat" style="margin-left: 20rpx;" @click="toggleSessions">最近会话</text>
      </view>
    </view>
    
    <!-- 聊天内容区域 -->
    <!-- #ifdef APP -->
    <!-- <scroll-view class="chat-content" scroll-y :scroll-top="scrollTop" scroll-with-animation> -->
    <!-- #endif -->
    <!-- #ifndef APP -->
    <scroll-view class="chat-content" scroll-y :scroll-top="scrollTop" scroll-with-animation>
    <!-- #endif -->
      <!-- 消息列表 -->
      <view class="message-list">
        <!-- 欢迎消息 -->
        <view v-if="messages.length === 0" class="welcome-message">
          <view class="welcome-avatar">
            <image class="avatar-img" src="/static/icons/chat.png" mode="aspectFit"></image>
          </view>
          <view class="welcome-content">
            <text class="welcome-title">你好！我是路亚小助理</text>
            <text class="welcome-desc">我可以帮你解答路亚钓鱼的各种问题，包括装备选择、钓技技巧、鱼种习性等</text>
            
            <!-- 建议问题 -->
            <view class="suggested-questions" v-if="suggestedQuestions.length > 0">
              <text class="suggested-title">你可以问我：</text>
              <view class="question-list">
                <text 
                  class="question-item" 
                  v-for="(question, index) in suggestedQuestions" 
                  :key="index"
                  @click="askQuestion(question)"
                >
                  {{ question }}
                </text>
              </view>
            </view>
          </view>
        </view>
        
        <!-- 消息项 -->
        <view 
          v-for="(message, index) in messages" 
          :key="message.id || index"
          class="message-item"
          :class="message.role === 'user' ? 'user-message' : 'ai-message'"
        >
          <!-- 用户消息头像：放在前面，配合 row-reverse 使其显示在右侧 -->
          <view v-if="message.role === 'user'" class="message-avatar">
            <image 
              class="avatar-img" 
              :src="userInfo?.avatar || '/static/default-avatar.png'" 
              mode="aspectFit"
            ></image>
          </view>

          <!-- AI消息头像：在正常 row 布局下显示在左侧 -->
          <view v-if="message.role === 'assistant'" class="message-avatar">
            <image class="avatar-img" src="/static/logo.png" mode="aspectFit"></image>
          </view>
          
          <!-- 消息内容 -->
          <view class="message-content">
            <view class="message-bubble">
              <text class="message-text" user-select="text">{{ message.content }}</text>
            </view>
            <text class="message-time">{{ formatTime(message.created_at) }}</text>
          </view>
        </view>
        
        <!-- 流式消息 -->
        <view v-if="streaming" class="message-item ai-message">
          <view class="message-avatar">
            <image class="avatar-img" src="/static/icons/chat.png" mode="aspectFit"></image>
          </view>
          <view class="message-content">
            <view class="message-bubble">
              <text v-if="!streamingMessage" class="typing-text">路亚小助理正在思考中...</text><text v-else class="message-text" user-select="text">{{ streamingMessage }}</text>
              <text class="typing-cursor">|</text>
            </view>
          </view>
        </view>
        
        <!-- 加载中状态 -->
        <view v-if="sending && !streaming" class="message-item ai-message">
          <view class="message-avatar">
            <image class="avatar-img" src="/static/icons/chat.png" mode="aspectFit"></image>
          </view>
          <view class="message-content">
            <view class="message-bubble">
              <text class="typing-text">路亚小助理正在思考中...</text>
            </view>
          </view>
        </view>

      </view>
    </scroll-view>

  <!-- 会话列表遮罩，点击空白处关闭 -->
  <view v-if="showSessions && filteredSessions && filteredSessions.length > 0" class="session-mask" @click="showSessions = false"></view>

  <!-- 会话列表抽屉 -->
  <view v-if="showSessions && filteredSessions && filteredSessions.length > 0" class="session-drawer" @click.stop>
    <view class="session-header">
      <text class="session-title">最近会话</text>
      <text class="session-close-btn" @click="showSessions = false">✕</text>
    </view>
    <scroll-view scroll-y class="session-list">
      <view v-for="item in filteredSessions" :key="item.id" class="session-item">
        <view class="session-info" @click="selectSession(item.id)">
          <text class="session-title-text">{{ item.title || '新对话' }}</text>
          <text class="session-sub">{{ formatSessionTime(item.updated_at || item.created_at) }}</text>
        </view>
        <text class="session-delete-btn" @click.stop="removeSession(item.id)">🗑</text>
      </view>
      <view v-if="!filteredSessions || filteredSessions.length === 0" class="session-empty">暂无会话</view>
    </scroll-view>
  </view>
    
    <!-- 输入区域 -->
    <view class="input-area">
      <view class="input-container">
        <input 
          class="message-input"
          v-model="inputMessage"
          placeholder="问我路亚相关问题..."
          :disabled="sending"
          @confirm="sendMessage"
          confirm-type="send"
        />
        <button 
          class="send-button"
          :disabled="sending || inputMessage.trim().length === 0"
          @click="sendMessage"
        >
          <text class="send-text">发送</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import chatStore from '../../store/chat.js'
import userStore from '../../store/user.js'

export default {
  data() {
    return {
      inputMessage: '',
      scrollTop: 0,
      messages: [],
      sessions: [],
      filteredSessions: [],
      sending: false,
      streaming: false,
      streamingMessage: '',
      suggestedQuestions: [],
      userInfo: null,
      showSessions: false
    }
  },
  
  onLoad() {
    // 检查登录状态
    if (!userStore.isLoggedIn()) {
      this.redirectToLogin()
      return
    }
    
    // 初始化数据
    this.initData()
    
    // 添加状态监听
    chatStore.addListener(this.onChatStateChange)
    userStore.addListener(this.onUserStateChange)
    
    // 获取建议问题
    this.fetchSuggestedQuestions()
  },
  
  onUnload() {
    // 移除状态监听
    chatStore.removeListener(this.onChatStateChange)
    userStore.removeListener(this.onUserStateChange)
  },
  
  methods: {
    // 初始化数据
    async initData() {
      // 获取聊天状态
      const chatState = chatStore.getChatState()
      this.messages = Array.isArray(chatState.messages) ? chatState.messages : []
      const sessions = chatStore.getSessions()
      this.sessions = Array.isArray(sessions) ? sessions : []
      this.filteredSessions = this.sessions.filter(s => (s.title || '').trim() !== '新对话')
      this.sending = chatState.sending || false
      this.streaming = chatState.streaming || false
      this.streamingMessage = chatState.streamingMessage || ''
      const questions = chatStore.getSuggestedQuestions()
      this.suggestedQuestions = Array.isArray(questions) ? questions : []

      // 获取用户信息
      this.userInfo = userStore.getUserInfo()

      // 如果没有消息，获取会话列表
      if (this.messages.length === 0) {
        try {
          await chatStore.fetchSessions()
          const updatedSessions = chatStore.getSessions()
          this.sessions = Array.isArray(updatedSessions) ? updatedSessions : []
          this.filteredSessions = this.sessions.filter(s => (s.title || '').trim() !== '新对话')
        } catch (e) {
          // 未登录或 token 失效时，提示并跳转登录
          console.error('获取会话失败:', e)
          this.redirectToLogin()
          return
        }
      }
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
    },
    
    // 聊天状态变化回调
    onChatStateChange(chatState) {
      this.messages = Array.isArray(chatState.messages) ? chatState.messages : []
      const sessions = chatStore.getSessions()
      this.sessions = Array.isArray(sessions) ? sessions : []
      this.filteredSessions = this.sessions.filter(s => (s.title || '').trim() !== '新对话')
      this.sending = chatState.sending || false
      this.streaming = chatState.streaming || false
      this.streamingMessage = chatState.streamingMessage || ''
      // 从 store 获取建议问题，避免从 state 对象上取不存在的方法
      const questions = chatStore.getSuggestedQuestions()
      this.suggestedQuestions = Array.isArray(questions) ? questions : []

      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
    },
    
    // 用户状态变化回调
    onUserStateChange(userState) {
      this.userInfo = userState.userInfo
    },
    
    // 发送消息
    async sendMessage() {
      if (this.sending || this.inputMessage.trim().length === 0) return
      
      const message = this.inputMessage.trim()
      this.inputMessage = ''
      
      try {
        // 使用流式发送消息
        await chatStore.sendMessageStream(message, (chunk) => {
          // 流式回调，已在状态管理中处理
        })
      } catch (error) {
        console.error('发送消息失败:', error)
        uni.showToast({
          title: error.message || '发送失败',
          icon: 'none'
        })
      }
    },
    
    // 创建新对话
    async createNewChat() {
      try {
        await chatStore.createNewSession()
        uni.showToast({
          title: '新对话已创建',
          icon: 'success'
        })
        await chatStore.fetchSessions()
        this.sessions = chatStore.getSessions() || []
        this.filteredSessions = this.sessions.filter(s => (s.title || '').trim() !== '新对话')
      } catch (error) {
        console.error('创建新对话失败:', error)
        uni.showToast({
          title: error.message || '创建失败',
          icon: 'none'
        })
      }
    },

    // 切换会话
    // 切换会话
    async selectSession(sessionId) {
      if (!sessionId) return
      
      // 检查是否已经在当前会话中
      if (sessionId === chatStore.getCurrentSessionId()) {
        this.showSessions = false
        return
      }
      
      uni.showLoading({ title: "切换中..." })
      try {
        await chatStore.switchSession(sessionId)
        this.sessions = chatStore.getSessions() || []
        this.filteredSessions = this.sessions.filter(s => s.id !== undefined && !s.is_deleted)
        // 按最后更新时间排序（最新的在前）
        this.filteredSessions.sort((a, b) => {
          const timeA = new Date(a.updated_at || a.created_at).getTime()
          const timeB = new Date(b.updated_at || b.created_at).getTime()
          return timeB - timeA
        })
        this.showSessions = false
        uni.showToast({ title: "已切换", icon: "success" })
      } catch (error) {
        console.error("切换会话失败:", error)
        uni.showToast({ title: "切换失败", icon: "none" })
      } finally {
        uni.hideLoading()
      }
    }        console.error('切换会话失败:', error)
        uni.showToast({ title: '切换失败', icon: 'none' })
      }
    },

    // 删除会话
    // 删除会话
    async removeSession(sessionId) {
      const session = this.sessions.find(s => s.id === sessionId)
      const sessionTitle = session?.title || "新对话"
      
      uni.showModal({
        title: "确认删除",
        content: `确定要删除会话「${sessionTitle}」吗？删除后无法恢复。`,
        confirmText: "删除",
        confirmColor: "#ff4d4f",
        success: async (res) => {
          if (res.confirm) {
            try {
              await chatStore.deleteSession(sessionId)
              this.sessions = chatStore.getSessions() || []
              this.filteredSessions = this.sessions.filter(s => s.id !== undefined && !s.is_deleted)
              // 按最后更新时间排序（最新的在前）
              this.filteredSessions.sort((a, b) => {
                const timeA = new Date(a.updated_at || a.created_at).getTime()
                const timeB = new Date(b.updated_at || b.created_at).getTime()
                return timeB - timeA
              })
              uni.showToast({ title: "已删除", icon: "success" })
            } catch (error) {
              console.error("删除会话失败:", error)
              uni.showToast({ title: "删除失败", icon: "none" })
            }
          }
        }
      })
    }      } catch (error) {
        console.error('删除会话失败:', error)
        uni.showToast({ title: '删除失败', icon: 'none' })
      }
    },

    // 切换抽屉显示（空列表不显示）
    toggleSessions() {
      if (!this.sessions || this.sessions.length === 0) {
        this.showSessions = false
        return
      }
      this.showSessions = !this.showSessions
    },
    
    // 提问建议问题
    askQuestion(question) {
      this.inputMessage = question
      this.sendMessage()
    },
    
    // 获取建议问题
    async fetchSuggestedQuestions() {
      // 小程序端直接使用本地建议，避免 404 噪音
      // #ifdef MP-WEIXIN
      this.suggestedQuestions = [
        '路亚新手应该选什么竿子和线？',
        '秋季黑鲈常用拟饵与走饵技巧？',
        '水库钓翘嘴怎么找鱼层与标点？',
        '通用路亚盒里必备的饵型有哪些？'
      ]
      return
      // #endif

      try {
        await chatStore.fetchSuggestedQuestions('lure_fishing')
      } catch (error) {
        // 后端未提供该接口或 404 时，回退到本地默认建议
        console.warn('获取建议问题失败，使用本地默认问题:', error)
        this.suggestedQuestions = [
          '路亚新手应该选什么竿子和线？',
          '秋季黑鲈常用拟饵与走饵技巧？',
          '水库钓翘嘴怎么找鱼层与标点？',
          '通用路亚盒里必备的饵型有哪些？'
        ]
      }
    },
    
    // 滚动到底部
    scrollToBottom() {
      this.scrollTop = 999999
    },
    
    // 格式化时间
    // 格式化时间（用于会话列表）
    formatSessionTime(timeStr) {
      if (!timeStr) return ""
      
      const date = new Date(timeStr)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffSec = Math.floor(diffMs / 1000)
      const diffMin = Math.floor(diffSec / 60)
      const diffHour = Math.floor(diffMin / 60)
      const diffDay = Math.floor(diffHour / 24)
      
n      if (diffSec < 60) return "刚刚"
      if (diffMin < 60) return `${diffMin}分钟前`
      if (diffHour < 24) return `${diffHour}小时前`
      if (diffDay === 1) return "昨天"
      if (diffDay < 7) return `${diffDay}天前`
      
n      // 超过一周显示具体日期
      const md = date.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" })
      return md
    },        const h = diffHour
        const m = diffMin % 60
        return m > 0 ? `${h}小时${m}分钟前` : `${h}小时前`
      }

      // 昨天 hh:mm（24h制）
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      if (date.toDateString() === yesterday.toDateString()) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
          hour: '2-digit', 
          minute: '2-digit' 
        })
      }
      
      // 48小时内（跨天但非昨天），继续用相对（小时+分钟）
      if (diffHour < 48) {
        const h = diffHour
        const m = diffMin % 60
        return m > 0 ? `${h}小时${m}分钟前` : `${h}小时前`
      }

      // 其他日期：MM-DD HH:mm（24h制）
      const md = date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
      const hm = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      return `${md} ${hm}`
    },
    
    // 跳转到登录页
    redirectToLogin() {
      uni.showModal({
        title: '提示',
        content: '请先登录后再使用聊天功能',
        confirmText: '去登录',
        success: (res) => {
          if (res.confirm) {
            uni.navigateTo({
              url: '/pages/login/login'
            })
          } else {
            // 返回上一页
            uni.navigateBack()
          }
        }
      })
    }
  }
}
</script>

<style>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 30rpx;
  background-color: #667eea;
  color: white;
  position: sticky;
  top: 0;
  z-index: 100;
}

/* 会话抽屉样式 */
.session-mask {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.35);
  z-index: 998;
}

.session-drawer {
  position: fixed;
  right: 0;
  top: 96rpx;
  bottom: 0;
  width: 540rpx;
  background: #ffffff;
  border-left: 1rpx solid #e0e0e0;
  z-index: 999;
  display: flex;
  flex-direction: column;
}

.session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 28rpx;
  border-bottom: 1rpx solid #e0e0e0;
}

.session-title {
  font-size: 32rpx;
  font-weight: bold;
}

.session-close {
  font-size: 28rpx;
  color: #667eea;
}

.session-close-btn {
  font-size: 28rpx;
  color: #334155; /* slate-700 */
  background: #e2e8f0; /* slate-200 */
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
}

.session-list {
  flex: 1;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 28rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.session-info {
  display: flex;
  flex-direction: column;
}

.session-title-text {
  font-size: 30rpx;
  color: #333;
}

.session-sub {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

.session-delete-btn {
  font-size: 28rpx;
  color: #e11d48; /* red-600 */
  background: #fee2e2; /* red-100 */
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
}

.session-empty {
  text-align: center;
  color: #999;
  padding: 40rpx 0;
}

.header-title {
  font-size: 36rpx;
  font-weight: bold;
}

.new-chat {
  font-size: 28rpx;
  padding: 10rpx 20rpx;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 30rpx;
}

.chat-content {
  flex: 1;
  padding: 20rpx;
  background-color: #f5f5f5;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
  min-height: 100%;
  background-color: #f5f5f5;
}

.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 40rpx;
  background-color: white;
  border-radius: 20rpx;
  margin-bottom: 30rpx;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.welcome-avatar {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: 30rpx;
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 60rpx;
}

.welcome-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.welcome-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.welcome-desc {
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
  margin-bottom: 40rpx;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.suggested-questions {
  width: 100%;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.suggested-title {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 20rpx;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.question-item {
  padding: 20rpx 30rpx;
  background-color: #f0f0f0;
  border-radius: 15rpx;
  font-size: 28rpx;
  color: #333;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  line-height: 1.5;
  box-sizing: border-box;
}

.message-item {
  display: flex;
  margin-bottom: 30rpx;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
  justify-content: flex-start;
}

.ai-message {
  flex-direction: row;
  justify-content: flex-start;
}

.message-avatar {
  width: 80rpx;
  height: 80rpx;
  margin: 0 20rpx;
  flex-shrink: 0; /* 防止头像被压缩 */
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  min-width: 0; /* 允许内容收缩 */
  word-wrap: break-word;
  word-break: break-all;
  overflow-wrap: break-word;
}

.message-bubble {
  padding: 20rpx 30rpx;
  border-radius: 20rpx;
  margin-bottom: 10rpx;
  min-width: 0; /* 允许内容收缩 */
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  box-sizing: border-box;
}

.user-message .message-bubble {
  background-color: #667eea;
  color: white;
}

.ai-message .message-bubble {
  background-color: white;
  color: #333;
}

.message-text {
  font-size: 30rpx;
  line-height: 1.5;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  display: block;
  width: 100%;
  box-sizing: border-box;
}

.typing-cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.typing-text {
  font-size: 30rpx;
  color: #999;
}

.message-time {
  font-size: 24rpx;
  color: #999;
  align-self: flex-end;
}

.user-message .message-time {
  align-self: flex-end;
}

.ai-message .message-time {
  align-self: flex-start;
}

.input-area {
  padding: 20rpx;
  background-color: white;
  border-top: 1rpx solid #e0e0e0;
}

.input-container {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.message-input {
  flex: 1;
  height: 80rpx;
  padding: 0 30rpx;
  background-color: #f5f5f5;
  border-radius: 40rpx;
  font-size: 30rpx;
}

.send-button {
  width: 120rpx;
  height: 80rpx;
  background-color: #667eea;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff; /* 确保按钮中文字为白色（高对比）*/
}

.send-button:disabled {
  background-color: #e5e5e5; /* 提升禁用态对比度 */
  color: #666666; /* 禁用态文字使用深灰，避免白底看不清 */
}

.send-text {
  font-size: 28rpx;
  color: inherit; /* 跟随按钮颜色，保证正常/禁用态可读性 */
}
</style>
