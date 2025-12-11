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
