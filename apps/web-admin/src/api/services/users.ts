import client from '../client'
import type {
  User,
  UserListResponse,
  UserEquipment,
  FishingLog,
  UserUpdateData,
  BatchUpdateData,
  BatchUpdateResponse,
  UserStats,
} from '@/types/user'

export const usersApi = {
  // 查询用户列表
  list: (params: {
    page: number
    page_size: number
    user_level?: string
    fishing_experience_years?: number
    location?: string
    keyword?: string
    fishing_experience_min?: number
    fishing_experience_max?: number
    preferred_fishing_method?: string
    created_after?: string
    created_before?: string
  }): Promise<UserListResponse> => {
    return client.get('/admin/users', { params })
  },

  // 获取用户详情
  get: (userId: number): Promise<User> => {
    return client.get(`/admin/users/${userId}`)
  },

  // 更新用户
  update: (userId: number, data: UserUpdateData): Promise<User> => {
    return client.put(`/admin/users/${userId}`, data)
  },

  // 批量更新用户
  batchUpdate: (data: BatchUpdateData): Promise<BatchUpdateResponse> => {
    return client.post('/admin/users/batch-update', data)
  },

  // 获取用户统计
  getStats: (userId: number): Promise<UserStats> => {
    return client.get(`/admin/users/${userId}/stats`)
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

  // 获取选项数据
  getOptions: (): Promise<{ user_levels: string[]; fishing_methods: string[] }> => {
    return client.get('/admin/users/options')
  },

  // 导出用户列表
  exportCSV: async (params?: {
    user_level?: string
    user_ids?: string
  }): Promise<Blob> => {
    const response = await client.get('/admin/users/export', {
      params,
      responseType: 'blob',
    })
    return response as unknown as Blob
  },
}
