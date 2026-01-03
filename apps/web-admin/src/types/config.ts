// 配置管理类型定义

export interface Config {
  config_key: string
  config_value: string
  config_type: string
  description?: string
  is_encrypted: boolean
  created_at: string
  updated_at: string
}

export interface ConfigCreate {
  config_key: string
  config_value: string
  config_type: string
  description?: string
  is_encrypted?: boolean
}

export interface ConfigUpdate {
  config_value?: string
  description?: string
}

export interface TestAPIKeyResult {
  valid: boolean
  message: string
  latency_ms?: number
}

// 新增类型定义 - 用于 APIKeyManager 组件

export interface ConfigItem {
  id: number
  config_key: string
  config_value: string
  config_type: string
  description?: string
  is_secret: boolean
  is_verified?: boolean
  created_at: string
  updated_at: string
}

export interface ConfigListResponse {
  items: ConfigItem[]
  total: number
}

export interface ConfigCreateRequest {
  config_key: string
  config_value: string
  config_type: string
  description?: string
  is_secret?: boolean
}

export interface ConfigUpdateRequest {
  config_value?: string
  description?: string
  is_verified?: boolean
}

export interface TestApiKeyResponse {
  success: boolean
  message?: string
  latency_ms?: number
}
