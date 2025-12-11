import client from '../client'
import type { User, UserListResponse, UserEquipment, FishingLog } from '@/types/user'

export const usersApi = {
  // 查询用户列表
  list: (params: {
    page: number
    page_size: number
    user_level?: string
    fishing_experience_years?: number
    location?: string
  }): Promise<UserListResponse> => {
    return client.get('/admin/users', { params })
  },

  // 获取用户详情
  get: (userId: number): Promise<User> => {
    return client.get(`/admin/users/${userId}`)
  },

  // 获取用户装备库
  getEquipment: (
    userId: number,
    params?: { category?: string; is_favorite?: boolean }
  ): Promise<UserEquipment[]> => {
    return client.get(`/admin/users/${userId}/equipment`, { params })
  },

  // 获取用户钓鱼记录
  getFishingLogs: (
    userId: number,
    params?: { limit?: number; offset?: number }
  ): Promise<FishingLog[]> => {
    return client.get(`/admin/users/${userId}/fishing-logs`, { params })
  },
}
