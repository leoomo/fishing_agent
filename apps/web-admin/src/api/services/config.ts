import client from '../client'
import type {
  Config,
  ConfigCreate,
  ConfigUpdate,
  TestAPIKeyResult,
  ConfigListResponse,
  ConfigCreateRequest,
  ConfigUpdateRequest,
  TestApiKeyResponse,
} from '@/types/config'

export const configApi = {
  // 查询配置列表
  list: (configType?: string): Promise<Config[]> => {
    return client.get('/admin/config/configs', {
      params: configType ? { config_type: configType } : {},
    })
  },

  // 获取配置（支持分页和过滤）
  getConfigs: (params?: {
    config_type?: string
    page?: number
    page_size?: number
  }): Promise<ConfigListResponse> => {
    return client.get('/admin/config/configs', { params })
  },

  // 获取配置
  get: (configKey: string): Promise<Config> => {
    return client.get(`/admin/config/configs/${configKey}`)
  },

  // 创建配置
  create: (data: ConfigCreate): Promise<Config> => {
    return client.post('/admin/config/configs', data)
  },

  // 创建配置（新版）
  createConfig: (data: ConfigCreateRequest): Promise<Config> => {
    return client.post('/admin/config/configs', data)
  },

  // 更新配置
  update: (configKey: string, data: ConfigUpdate): Promise<Config> => {
    return client.put(`/admin/config/configs/${configKey}`, data)
  },

  // 更新配置（通过 ID）
  updateConfig: (configId: number, data: ConfigUpdateRequest): Promise<Config> => {
    return client.put(`/admin/config/configs/${configId}`, data)
  },

  // 删除配置
  delete: (configKey: string): Promise<void> => {
    return client.delete(`/admin/config/configs/${configKey}`)
  },

  // 删除配置（通过 ID）
  deleteConfig: (configId: number): Promise<void> => {
    return client.delete(`/admin/config/configs/${configId}`)
  },

  // 测试 API 密钥（旧版）
  testApiKey: (apiProvider: string, apiKey?: string): Promise<TestAPIKeyResult & TestApiKeyResponse> => {
    return client.post('/admin/config/configs/test-api-key', {
      api_provider: apiProvider,
      api_key: apiKey,
    })
  },
}
