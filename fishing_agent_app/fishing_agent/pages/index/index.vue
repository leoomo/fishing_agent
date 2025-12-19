<template>
  <view class="chat-container">
    <!-- 顶部导航栏 -->
    <view class="chat-header">
      <view class="header-left">
        <text class="header-title">路亚AI助手</text>
      </view>
      <view class="header-right">
        <text class="new-chat" @click="createNewChat">新对话</text>
      </view>
    </view>
    
    <!-- 聊天内容区域 -->
    <!-- #ifdef APP -->
    <scroll-view class="chat-content" scroll-y :scroll-top="scrollTop" scroll-with-animation>
    <!-- #endif -->
    <!-- #ifndef APP -->
    <scroll-view class="chat-content" scroll-y :scroll-top="scrollTop" scroll-with-animation>
    <!-- #endif -->
      <!-- 消息列表 -->
      <view class="message-list">
        <!-- 欢迎消息 -->
        <view v-if="messages.length === 0" class="welcome-message">
          <view class="welcome-avatar">
            <image class="avatar-img" src="/static/logo.png" mode="aspectFit"></image>
          </view>
          <view class="welcome-content">
            <text class="welcome-title">你好！我是路亚AI助手</text>
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
          <!-- AI消息头像 -->
          <view v-if="message.role === 'assistant'" class="message-avatar">
            <image class="avatar-img" src="/static/logo.png" mode="aspectFit"></image>
          </view>
          
          <!-- 消息内容 -->
          <view class="message-content">
            <view class="message-bubble">
              <text class="message-text">{{ message.content }}</text>
            </view>
            <text class="message-time">{{ formatTime(message.created_at) }}</text>
          </view>
          
          <!-- 用户消息头像 -->
          <view v-if="message.role === 'user'" class="message-avatar">
            <image 
              class="avatar-img" 
              src="/static/default-avatar.png" 
              mode="aspectFit"
            ></image>
          </view>
        </view>
        
        <!-- 流式消息 -->
        <view v-if="streaming" class="message-item ai-message">
          <view class="message-avatar">
            <image class="avatar-img" src="/static/logo.png" mode="aspectFit"></image>
          </view>
          <view class="message-content">
            <view class="message-bubble">
              <text class="message-text">{{ streamingMessage }}</text>
              <text class="typing-cursor">|</text>
            </view>
          </view>
        </view>
        
        <!-- 加载中 -->
        <view v-if="sending && !streaming" class="message-item ai-message">
          <view class="message-avatar">
            <image class="avatar-img" src="/static/logo.png" mode="aspectFit"></image>
          </view>
          <view class="message-content">
            <view class="message-bubble">
              <text class="typing-text">路亚AI正在思考中...</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>
    
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

export default {
  data() {
    return {
      inputMessage: '',
      scrollTop: 0,
      messages: [],
      sending: false,
      streaming: false,
      streamingMessage: '',
      suggestedQuestions: []
    }
  },
  
  onLoad() {
    // 初始化数据
    this.initData()
    
    // 添加状态监听
    chatStore.addListener(this.onChatStateChange)
    
    // 获取建议问题
    this.fetchSuggestedQuestions()
  },
  
  onUnload() {
    // 移除状态监听
    chatStore.removeListener(this.onChatStateChange)
  },
  
  methods: {
    // 初始化数据
    initData() {
      // 获取聊天状态
      const chatState = chatStore.getChatState()
      this.messages = chatState.messages || []
      this.sending = chatState.sending || false
      this.streaming = chatState.streaming || false
      this.streamingMessage = chatState.streamingMessage || ''
      this.suggestedQuestions = chatStore.getSuggestedQuestions() || []
      
      // 如果没有消息，获取会话列表
      if (this.messages.length === 0) {
        chatStore.fetchSessions()
      }
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
    },
    
    // 聊天状态变化回调
    onChatStateChange(chatState) {
      this.messages = chatState.messages || []
      this.sending = chatState.sending || false
      this.streaming = chatState.streaming || false
      this.streamingMessage = chatState.streamingMessage || ''
      this.suggestedQuestions = chatStore.getSuggestedQuestions() || []
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
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
      } catch (error) {
        console.error('创建新对话失败:', error)
        uni.showToast({
          title: error.message || '创建失败',
          icon: 'none'
        })
      }
    },
    
    // 提问建议问题
    askQuestion(question) {
      this.inputMessage = question
      this.sendMessage()
    },
    
    // 获取建议问题
    async fetchSuggestedQuestions() {
      try {
        await chatStore.fetchSuggestedQuestions('lure_fishing')
      } catch (error) {
        console.error('获取建议问题失败:', error)
      }
    },
    
    // 滚动到底部
    scrollToBottom() {
      this.scrollTop = 999999
    },
    
    // 格式化时间
    formatTime(timeStr) {
      if (!timeStr) return ''
      
      const date = new Date(timeStr)
      const now = new Date()
      
      // 如果是今天
      if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString('zh-CN', { 
          hour: '2-digit', 
          minute: '2-digit' 
        })
      }
      
      // 如果是昨天
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      if (date.toDateString() === yesterday.toDateString()) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
          hour: '2-digit', 
          minute: '2-digit' 
        })
      }
      
      // 其他日期
      return date.toLocaleDateString('zh-CN', { 
        month: '2-digit', 
        day: '2-digit' 
      }) + ' ' + date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
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
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 40rpx;
  background-color: white;
  border-radius: 20rpx;
  margin-bottom: 30rpx;
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
}

.suggested-questions {
  width: 100%;
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
}

.message-item {
  display: flex;
  margin-bottom: 30rpx;
}

.user-message {
  flex-direction: row-reverse;
}

.ai-message {
  flex-direction: row;
}

.message-avatar {
  width: 80rpx;
  height: 80rpx;
  margin: 0 20rpx;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.message-bubble {
  padding: 20rpx 30rpx;
  border-radius: 20rpx;
  margin-bottom: 10rpx;
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
}

.send-button:disabled {
  background-color: #ccc;
}

.send-text {
  font-size: 28rpx;
  color: white;
}
</style>
