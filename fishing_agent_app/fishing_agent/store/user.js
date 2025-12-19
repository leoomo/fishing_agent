import auth from '../api/auth.js'
import config from '../api/config.js'

// 用户状态
const state = {
  isLoggedIn: false,
  userInfo: null,
  loading: false
}

// 初始化用户状态
function initUserState() {
  // 检查本地是否有token
  const token = config.tokenManager.getToken()
  if (token && config.tokenManager.isValidToken()) {
    state.isLoggedIn = true
    // 获取用户信息
    fetchUserInfo()
  }
}

// 获取用户信息
async function fetchUserInfo() {
  if (!state.isLoggedIn) return
  
  try {
    state.loading = true
    const userInfo = await auth.getCurrentUser()
    state.userInfo = userInfo
    
    // 触发页面更新
    notifyListeners()
  } catch (error) {
    // 获取失败，可能token已过期，清除登录状态（401是预期行为，不打印错误）
    logout()
  } finally {
    state.loading = false
  }
}

// 登录
async function login(loginData) {
  try {
    state.loading = true
    
    // 调用登录API
    const response = await auth.login(loginData)
    
    // 更新状态
    state.isLoggedIn = true
    state.userInfo = response.user
    
    // 触发页面更新
    notifyListeners()
    
    return response
  } catch (error) {
    console.error('登录失败:', error)
    throw error
  } finally {
    state.loading = false
  }
}

// 微信登录
async function wechatLogin(loginData) {
  try {
    state.loading = true
    
    // 调用微信登录API
    const response = await auth.wechatLogin(loginData)
    
    // 更新状态
    state.isLoggedIn = true
    state.userInfo = response.user
    
    // 触发页面更新
    notifyListeners()
    
    return response
  } catch (error) {
    console.error('微信登录失败:', error)
    throw error
  } finally {
    state.loading = false
  }
}

// 注册
async function register(registerData) {
  try {
    state.loading = true
    
    // 调用注册API
    const response = await auth.register(registerData)
    
    // 更新状态
    state.isLoggedIn = true
    state.userInfo = response.user
    
    // 触发页面更新
    notifyListeners()
    
    return response
  } catch (error) {
    console.error('注册失败:', error)
    throw error
  } finally {
    state.loading = false
  }
}

// 登出
async function logout() {
  try {
    // 调用登出API
    await auth.logout()
  } catch (error) {
    console.error('登出失败:', error)
  } finally {
    // 无论API是否成功，都清除本地状态
    state.isLoggedIn = false
    state.userInfo = null
    
    // 触发页面更新
    notifyListeners()
  }
}

// 更新用户信息
function updateUserInfo(userInfo) {
  state.userInfo = { ...state.userInfo, ...userInfo }
  notifyListeners()
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
      listener(getUserState())
    }
  })
}

// 获取用户状态
function getUserState() {
  return {
    ...state
  }
}

// 检查是否登录
function isLoggedIn() {
  return state.isLoggedIn
}

// 获取用户信息
function getUserInfo() {
  return state.userInfo
}

// 获取加载状态
function getLoading() {
  return state.loading
}

// 初始化
initUserState()

export default {
  // 方法
  login,
  wechatLogin,
  register,
  logout,
  updateUserInfo,
  fetchUserInfo,
  
  // 状态获取
  getUserState,
  isLoggedIn,
  getUserInfo,
  getLoading,
  
  // 监听器
  addListener,
  removeListener
}
