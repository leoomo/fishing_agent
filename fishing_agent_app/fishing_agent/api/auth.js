import request from './request.js'
import config from './config.js'

// 微信登录
async function wechatLogin(loginData) {
  try {
    const response = await request.post('/auth/wechat/login', loginData)
    
    // 保存token
    if (response.access_token) {
      config.tokenManager.setToken(response.access_token)
    }
    
    return response
  } catch (error) {
    console.error('微信登录失败:', error)
    throw error
  }
}

// 用户注册
async function register(registerData) {
  try {
    const response = await request.post('/auth/register', registerData)
    
    // 保存token
    if (response.access_token) {
      config.tokenManager.setToken(response.access_token)
    }
    
    return response
  } catch (error) {
    console.error('注册失败:', error)
    throw error
  }
}

// 用户登录
async function login(loginData) {
  try {
    const response = await request.post('/auth/login', loginData)
    
    // 保存token
    if (response.access_token) {
      config.tokenManager.setToken(response.access_token)
    }
    
    return response
  } catch (error) {
    console.error('登录失败:', error)
    throw error
  }
}

// 刷新token
async function refreshToken() {
  try {
    const response = await request.post('/auth/refresh')
    
    // 保存新token
    if (response.access_token) {
      config.tokenManager.setToken(response.access_token)
    }
    
    return response
  } catch (error) {
    console.error('刷新token失败:', error)
    // 刷新失败，清除token
    config.tokenManager.clearToken()
    throw error
  }
}

// 登出
async function logout() {
  try {
    await request.post('/auth/logout')
  } catch (error) {
    console.error('登出失败:', error)
  } finally {
    // 无论请求是否成功，都清除本地token
    config.tokenManager.clearToken()
  }
}

// 获取当前用户信息
async function getCurrentUser() {
  const response = await request.get('/auth/me')
  return response
}

// 验证token是否有效
async function verifyToken() {
  try {
    const response = await request.get('/auth/verify')
    return response
  } catch (error) {
    console.error('验证token失败:', error)
    // 验证失败，清除token
    config.tokenManager.clearToken()
    throw error
  }
}

// 微信小程序登录辅助函数
async function wxLogin() {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    uni.login({
      provider: 'weixin',
      success: (loginRes) => {
        if (loginRes.code) {
          resolve(loginRes.code)
        } else {
          reject(new Error('获取微信登录code失败'))
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
    // #endif
    
    // #ifndef MP-WEIXIN
    reject(new Error('当前环境不支持微信登录'))
    // #endif
  })
}

// 获取微信用户信息
async function wxGetUserProfile() {
  return new Promise((resolve, reject) => {
    // #ifdef MP-WEIXIN
    uni.getUserProfile({
      desc: '用于完善用户资料',
      success: (profileRes) => {
        resolve(profileRes.userInfo)
      },
      fail: (err) => {
        reject(err)
      }
    })
    // #endif
    
    // #ifndef MP-WEIXIN
    reject(new Error('当前环境不支持获取微信用户信息'))
    // #endif
  })
}

export default {
  wechatLogin,
  register,
  login,
  refreshToken,
  logout,
  getCurrentUser,
  verifyToken,
  wxLogin,
  wxGetUserProfile
}
