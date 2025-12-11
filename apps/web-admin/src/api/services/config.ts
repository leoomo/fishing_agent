import client from '../client'
import type { Config, ConfigCreate, ConfigUpdate, TestAPIKeyResult } from '@/types/config'

export const configApi = {
  // 查询配置列表
  list: (configType?: string): Promise<Config[]> => {
    return client.get('/admin/config/configs', {
      params: configType ? { config_type: configType } : {},
    })
  },

  // 获取配置
  get: (configKey: string): Promise<Config> => {
    return client.get(`/admin/config/configs/${configKey}`)
  },

  // 创建配置
  create: (data: ConfigCreate): Promise<Config> => {
    return client.post('/admin/config/configs', data)
  },

  // 更新配置
  update: (configKey: string, data: ConfigUpdate): Promise<Config> => {
    return client.put(`/admin/config/configs/${configKey}`, data)
  },

  // 删除配置
  delete: (configKey: string): Promise<void> => {
    return client.delete(`/admin/config/configs/${configKey}`)
  },

  // 测试 API 密钥
  testApiKey: (apiProvider: string, apiKey: string): Promise<TestAPIKeyResult> => {
    return client.post('/admin/config/configs/test-api-key', {
      api_provider: apiProvider,
      api_key: apiKey,
    })
  },
}
