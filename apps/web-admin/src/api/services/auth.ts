import client from '../client'
import type { UserInfo } from '@/utils/auth'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserInfo
  permissions: string[]
}

export const authApi = {
  // 登录
  login: (data: LoginRequest): Promise<LoginResponse> => {
    return client.post('/auth/login', data)
  },

  // 获取当前用户信息
  me: (): Promise<UserInfo> => {
    return client.get('/auth/me')
  },
}
