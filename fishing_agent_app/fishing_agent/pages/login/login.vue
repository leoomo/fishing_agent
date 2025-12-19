<template>
  <view class="login-container">
    <view class="login-header">
      <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      <text class="app-name">路亚AI智能助手</text>
      <text class="app-desc">专业的路亚钓鱼AI助手</text>
    </view>
    
    <view class="login-content">
      <!-- 微信小程序登录 -->
      <!-- #ifdef MP-WEIXIN -->
      <view class="login-section">
        <button 
          class="wechat-login-btn"
          :disabled="loading"
          @click="handleWechatLogin"
        >
          <text class="btn-text">{{ loading ? '登录中...' : '微信快速登录' }}</text>
        </button>
      </view>
      <!-- #endif -->
      
      <!-- H5/App登录 -->
      <!-- #ifndef MP-WEIXIN -->
      <view class="login-section">
        <view class="form-item">
          <input 
            class="form-input"
            type="text"
            v-model="loginForm.username"
            placeholder="请输入用户名/邮箱"
          />
        </view>
        <view class="form-item">
          <input 
            class="form-input"
            type="password"
            v-model="loginForm.password"
            placeholder="请输入密码"
          />
        </view>
        <button 
          class="login-btn"
          :disabled="loading"
          @click="handleLogin"
        >
          <text class="btn-text">{{ loading ? '登录中...' : '登录' }}</text>
        </button>
        
        <view class="register-link">
          <text>还没有账号？</text>
          <text class="link-text" @click="goToRegister">立即注册</text>
        </view>
      </view>
      <!-- #endif -->
      
      <!-- 游客模式 -->
      <view class="guest-section">
        <text class="guest-text" @click="handleGuestLogin">游客体验</text>
      </view>
    </view>
    
    <!-- 协议 -->
    <view class="agreement">
      <text class="agreement-text">登录即表示同意</text>
      <text class="link-text">《用户协议》</text>
      <text class="agreement-text">和</text>
      <text class="link-text">《隐私政策》</text>
    </view>
  </view>
</template>

<script>
import auth from '../../api/auth.js'
import userStore from '../../store/user.js'

export default {
  data() {
    return {
      loading: false,
      loginForm: {
        username: '',
        password: ''
      }
    }
  },
  
  methods: {
    // 微信登录
    async handleWechatLogin() {
      if (this.loading) return
      
      this.loading = true
      
      try {
        // 重要：先触发获取用户信息（必须在点击手势同步周期内发起）
        const userInfoPromise = auth.wxGetUserProfile()
        
        // 并行获取登录 code（不阻塞手势周期）
        const code = await auth.wxLogin()
        
        // 等待用户信息结果
        const userInfo = await userInfoPromise
        
        // 调用后端登录接口（通过 userStore 以更新登录状态）
        const response = await userStore.wechatLogin({
          code: code,
          nickname: userInfo.nickName,
          avatar_url: userInfo.avatarUrl
        })
        
        uni.showToast({
          title: '登录成功',
          icon: 'success'
        })
        
        // 登录成功后跳转到聊天页（无 tabBar，用 reLaunch）
        setTimeout(() => {
          uni.reLaunch({
            url: '/pages/chat/chat'
          })
        }, 1500)
        
      } catch (error) {
        console.error('微信登录失败:', error)
        uni.showToast({
          title: error.message || '登录失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },
    
    // 账号密码登录
    async handleLogin() {
      if (this.loading) return
      
      if (!this.loginForm.username || !this.loginForm.password) {
        uni.showToast({
          title: '请输入用户名和密码',
          icon: 'none'
        })
        return
      }
      
      this.loading = true
      
      try {
        // 通过 userStore 登录以更新登录状态
        const response = await userStore.login(this.loginForm)

        uni.showToast({
          title: '登录成功',
          icon: 'success'
        })

        // 登录成功后跳转到聊天页（无 tabBar，用 reLaunch）
        setTimeout(() => {
          uni.reLaunch({
            url: '/pages/chat/chat'
          })
        }, 1500)

      } catch (error) {
        console.error('登录失败:', error)
        uni.showToast({
          title: error.message || '登录失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },
    
    // 游客登录
    handleGuestLogin() {
      uni.showModal({
        title: '游客体验',
        content: '游客模式下部分功能受限，建议登录后使用完整功能',
        success: (res) => {
          if (res.confirm) {
            // 跳转到聊天页（无 tabBar，用 reLaunch）
            uni.reLaunch({
              url: '/pages/chat/chat'
            })
          }
        }
      })
    },
    
    // 跳转到注册页
    goToRegister() {
      uni.navigateTo({
        url: '/pages/register/register'
      })
    }
  }
}
</script>

<style>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  padding: 80rpx 60rpx;
  box-sizing: border-box;
}

.login-header {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 80rpx;
}

.logo {
  width: 160rpx;
  height: 160rpx;
  margin-bottom: 40rpx;
}

.app-name {
  font-size: 48rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 20rpx;
}

.app-desc {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

.login-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.login-section {
  margin-bottom: 60rpx;
}

.form-item {
  margin-bottom: 30rpx;
}

.form-input {
  width: 100%;
  height: 88rpx;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 44rpx;
  padding: 0 40rpx;
  font-size: 32rpx;
  color: #333333;
  box-sizing: border-box;
}

.wechat-login-btn, .login-btn {
  width: 100%;
  height: 88rpx;
  background: #07c160;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30rpx;
}

.wechat-login-btn:disabled, .login-btn:disabled {
  opacity: 0.6;
}

.btn-text {
  font-size: 32rpx;
  color: #ffffff;
  font-weight: bold;
}

.register-link {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

.link-text {
  color: #ffffff;
  margin: 0 10rpx;
  text-decoration: underline;
}

.guest-section {
  display: flex;
  justify-content: center;
  margin-top: 40rpx;
}

.guest-text {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: underline;
}

.agreement {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 60rpx;
}

.agreement-text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
}

.agreement .link-text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: underline;
}
</style>
