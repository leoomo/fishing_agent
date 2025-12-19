// API配置
const config = {
  // 开发环境（baseURL 将在 getConfig 中动态计算）
  development: {
    baseURL: '',
    timeout: 120000 // 小程序降级非流式，生成可能较慢，适当放大超时
  },
  // 生产环境
  production: {
    baseURL: 'https://api.lure-ai.com/api/v1',
    timeout: 10000
  }
}

// 计算开发环境 baseURL（H5 使用浏览器主机名；小程序优先用本地存储配置，回退到局域网IP）
function computeDevBaseURL() {
  // #ifdef H5
  try {
    const protocol = window?.location?.protocol || 'http:'
    const hostname = window?.location?.hostname || 'localhost'
    return `${protocol}//${hostname}:8000/api/v1`
  } catch (_) {
    return 'http://localhost:8000/api/v1'
  }
  // #endif

  // #ifdef MP-WEIXIN
  try {
    const saved = uni.getStorageSync('api_base_url')
    if (saved && typeof saved === 'string') {
      return saved
    }
  } catch (_) {}
  // 根据本机网络环境调整为你的局域网IP（例如 192.168.x.x）
  // 如果在同一台电脑上测试，使用 localhost
  return 'http://localhost:8000/api/v1'
  // #endif

  // #ifdef APP-PLUS
  try {
    const saved = uni.getStorageSync('api_base_url')
    if (saved && typeof saved === 'string') {
      return saved
    }
  } catch (_) {}
  return 'http://localhost:8000/api/v1'
  // #endif
}

// 获取当前环境配置
function getConfig() {
  const env = 'development'
  if (env === 'development') {
    const baseURL = computeDevBaseURL()
    return { ...config.development, baseURL }
  }
  return config.production
}

// 运行时设置/覆盖 baseURL（便于在设置页或调试页修改）
function setDevBaseURL(newURL) {
  try {
    if (newURL && typeof newURL === 'string') {
      // #ifdef MP-WEIXIN || APP-PLUS
      uni.setStorageSync('api_base_url', newURL)
      // #endif
    }
  } catch (e) {
    console.error('保存 api_base_url 失败', e)
  }
}

// Token管理
const tokenManager = {
  // 获取token
  getToken() {
    try {
      return uni.getStorageSync('access_token')
    } catch (e) {
      console.error('获取token失败', e)
      return null
    }
  },
  
  // 设置token
  setToken(token) {
    try {
      uni.setStorageSync('access_token', token)
      return true
    } catch (e) {
      console.error('保存token失败', e)
      return false
    }
  },
  
  // 清除token
  clearToken() {
    try {
      uni.removeStorageSync('access_token')
      return true
    } catch (e) {
      console.error('清除token失败', e)
      return false
    }
  },
  
  // 检查token是否有效
  isValidToken() {
    const token = this.getToken()
    if (!token) return false
    
    try {
      // 简单的token格式检查
      const parts = token.split('.')
      return parts.length === 3
    } catch (e) {
      return false
    }
  }
}

export default {
  getConfig,
  setDevBaseURL,
  tokenManager
}
