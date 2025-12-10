import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { message } from 'antd'
import { getToken, clearToken } from '@/utils/auth'

// 创建 axios 实例
const client: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：添加 token
client.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
client.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    // 401: token 过期或无效
    if (error.response?.status === 401) {
      message.error('登录已过期，请重新登录')
      clearToken()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // 403: 权限不足
    if (error.response?.status === 403) {
      message.error('权限不足')
      return Promise.reject(error)
    }

    // 500: 服务器错误
    if (error.response?.status >= 500) {
      message.error('服务器错误，请稍后重试')
      return Promise.reject(error)
    }

    // 其他错误
    const errorMessage = error.response?.data?.detail || error.message
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

export default client
