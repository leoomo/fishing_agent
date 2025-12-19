import config from './config.js'

// 请求拦截器
function request(options) {
  return new Promise((resolve, reject) => {
    // 获取配置
    const apiConfig = config.getConfig()
    
    // 获取token
    const token = config.tokenManager.getToken()
    
    // 合并请求配置（先展开 options，再用计算值覆盖，避免被覆盖回简短路径）
    const requestOptions = {
      ...options,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(options.header || {})
      },
      timeout: options.timeout || apiConfig.timeout,
      url: `${apiConfig.baseURL}${options.url}`
    }
    
    // 添加认证头
    if (token) {
      requestOptions.header.Authorization = `Bearer ${token}`
    }
    
    // 发起请求
    uni.request({
      ...requestOptions,
      success: (res) => {
        // 请求成功
        if (res.statusCode === 200) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // 未授权，清除token并跳转到登录页
          config.tokenManager.clearToken()
          uni.showToast({
            title: '请先登录',
            icon: 'none'
          })
          
          // 跳转到登录页
          setTimeout(() => {
            uni.navigateTo({
              url: '/pages/login/login'
            })
          }, 1500)
          
          reject(new Error('未授权'))
        } else {
          // 其他错误
          const errorMsg = res.data?.message || '请求失败'
          const err = new Error(errorMsg)
          // 附带状态码，便于上层处理
          err.statusCode = res.statusCode
          uni.showToast({
            title: errorMsg,
            icon: 'none'
          })
          reject(err)
        }
      },
      fail: (err) => {
        // 网络错误
        console.error('请求失败:', err)
        uni.showToast({
          title: '网络错误，请检查网络连接',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

// GET请求
function get(url, params = {}, options = {}) {
  // 将参数拼接到URL
  let queryString = ''
  if (Object.keys(params).length > 0) {
    queryString = '?' + Object.keys(params)
      .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join('&')
  }
  
  return request({
    url: url + queryString,
    method: 'GET',
    ...options
  })
}

// POST请求
function post(url, data = {}, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

// PUT请求
function put(url, data = {}, options = {}) {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

// DELETE请求
function del(url, data = {}, options = {}) {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  })
}

// 文件上传
function upload(url, filePath, formData = {}, options = {}) {
  return new Promise((resolve, reject) => {
    const apiConfig = config.getConfig()
    const token = config.tokenManager.getToken()
    
    uni.uploadFile({
      url: `${apiConfig.baseURL}${url}`,
      filePath,
      name: options.name || 'file',
      formData,
      header: {
        // 文件上传不设置Content-Type，让浏览器自动设置
        ...(token && { Authorization: `Bearer ${token}` })
      },
      success: (res) => {
        if (res.statusCode === 200) {
          try {
            const data = JSON.parse(res.data)
            resolve(data)
          } catch (e) {
            resolve(res.data)
          }
        } else {
          reject(new Error('上传失败'))
        }
      },
      fail: (err) => {
        console.error('上传失败:', err)
        uni.showToast({
          title: '上传失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

export default {
  request,
  get,
  post,
  put,
  delete: del,
  upload
}
