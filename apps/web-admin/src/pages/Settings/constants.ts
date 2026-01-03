/**
 * API 服务预设配置
 */

export interface APIProvider {
  key: string
  name: string
  description: string
  icon: string
  color: string
  configKey: string
  testEndpoint: string
  docUrl: string
  placeholder?: string
}

export const API_PROVIDERS: APIProvider[] = [
  {
    key: 'DASHSCOPE',
    name: '通义千问 (DashScope)',
    description: '阿里云大模型服务，支持千问系列模型',
    icon: '🔮',
    color: '#1677ff',
    configKey: 'DASHSCOPE_API_KEY',
    testEndpoint: 'dashscope',
    docUrl: 'https://help.aliyun.com/zh/dashscope/',
    placeholder: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  },
  {
    key: 'ANTHROPIC',
    name: 'Claude (Anthropic)',
    description: 'Anthropic Claude 模型服务',
    icon: '🤖',
    color: '#d97706',
    configKey: 'ANTHROPIC_API_KEY',
    testEndpoint: 'anthropic',
    docUrl: 'https://docs.anthropic.com/',
    placeholder: 'sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  },
  {
    key: 'CAIYUN',
    name: '彩云天气',
    description: '天气预报和气象数据服务',
    icon: '🌤️',
    color: '#06b6d4',
    configKey: 'CAIYUN_API_KEY',
    testEndpoint: 'caiyun',
    docUrl: 'https://docs.caiyunapp.com/',
    placeholder: 'TAkxxxxxxxxxxxxxxxx',
  },
  {
    key: 'AMAP',
    name: '高德地图',
    description: '地图和地理编码服务',
    icon: '🗺️',
    color: '#10b981',
    configKey: 'AMAP_API_KEY',
    testEndpoint: 'amap',
    docUrl: 'https://lbs.amap.com/api/',
    placeholder: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  },
  {
    key: 'SILICONFLOW',
    name: 'SiliconFlow',
    description: '高性能模型推理服务，支持 OCR 等功能',
    icon: '⚡',
    color: '#8b5cf6',
    configKey: 'SILICONFLOW_API_KEY',
    testEndpoint: 'siliconflow',
    docUrl: 'https://docs.siliconflow.cn/',
    placeholder: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  },
]

/**
 * API 密钥状态
 */
export type APIKeyStatus = 'configured' | 'verified' | 'pending' | 'invalid' | 'unconfigured'

export const API_KEY_STATUS_CONFIG: Record<APIKeyStatus, { label: string; color: string; icon: string }> = {
  configured: { label: '已配置', color: 'blue', icon: 'setting' },
  verified: { label: '已验证', color: 'success', icon: 'check-circle' },
  pending: { label: '待验证', color: 'warning', icon: 'clock-circle' },
  invalid: { label: '无效', color: 'error', icon: 'close-circle' },
  unconfigured: { label: '未配置', color: 'default', icon: 'plus-circle' },
}

/**
 * 配置类型定义
 */
export const CONFIG_TYPES = [
  { key: 'api', label: 'API 密钥', color: 'orange' },
  { key: 'agent', label: 'Agent 配置', color: 'blue' },
  { key: 'algorithm', label: '算法参数', color: 'green' },
  { key: 'system', label: '系统配置', color: 'purple' },
] as const

export type ConfigType = typeof CONFIG_TYPES[number]['key']

/**
 * LLM 模型提供商配置
 */
export interface ModelProvider {
  key: string
  name: string
  model: string
  description: string
  apiKeyConfig: string
}

export const MODEL_PROVIDERS: ModelProvider[] = [
  {
    key: 'zhipu',
    name: '智谱 GLM',
    model: 'glm-4-flash',
    description: '智谱清言，低成本高性能（推荐）',
    apiKeyConfig: 'ANTHROPIC_AUTH_TOKEN',
  },
  {
    key: 'qwen',
    name: '通义千问',
    model: 'qwen-plus',
    description: '阿里云大模型，稳定可靠',
    apiKeyConfig: 'DASHSCOPE_API_KEY',
  },
  {
    key: 'doubao',
    name: '字节豆包',
    model: 'doubao-pro',
    description: '字节跳动大模型',
    apiKeyConfig: 'ARK_API_KEY',
  },
  {
    key: 'openai',
    name: 'OpenAI',
    model: 'gpt-3.5-turbo',
    description: 'OpenAI GPT 系列',
    apiKeyConfig: 'OPENAI_API_KEY',
  },
]

/**
 * Agent 配置参数定义
 */
export interface AgentConfigParam {
  key: string
  label: string
  type: 'select' | 'number' | 'slider' | 'switch'
  defaultValue: string | number | boolean
  description: string
  options?: { label: string; value: string }[]
  min?: number
  max?: number
  step?: number
}

export interface AgentConfig {
  key: string
  name: string
  description: string
  icon: string
  color: string
  params: AgentConfigParam[]
}

export const AGENT_CONFIGS: AgentConfig[] = [
  {
    key: 'fishing',
    name: '钓鱼助手 Agent',
    description: '智能钓鱼推荐、天气分析和装备建议',
    icon: '🎣',
    color: '#1677ff',
    params: [
      {
        key: 'FISHING_AGENT_MODEL_PROVIDER',
        label: '模型提供商',
        type: 'select',
        defaultValue: 'zhipu',
        description: '选择 LLM 模型提供商',
        options: MODEL_PROVIDERS.map((p) => ({ label: p.name, value: p.key })),
      },
      {
        key: 'FISHING_AGENT_TIMEOUT',
        label: '请求超时 (秒)',
        type: 'number',
        defaultValue: 60,
        description: 'Agent 请求超时时间',
        min: 10,
        max: 300,
      },
      {
        key: 'FISHING_AGENT_TEMPERATURE',
        label: '模型温度',
        type: 'slider',
        defaultValue: 0.7,
        description: '控制输出的创意度，0=精确，1=创意',
        min: 0,
        max: 1,
        step: 0.1,
      },
      {
        key: 'FISHING_AGENT_MAX_TOKENS',
        label: '最大 Token',
        type: 'number',
        defaultValue: 2048,
        description: '单次输出的最大 Token 数',
        min: 256,
        max: 8192,
      },
    ],
  },
  {
    key: 'equipment_import',
    name: '装备导入 Agent',
    description: 'OCR 识别和装备信息智能提取',
    icon: '📦',
    color: '#52c41a',
    params: [
      {
        key: 'EQUIPMENT_AGENT_MODEL_PROVIDER',
        label: '模型提供商',
        type: 'select',
        defaultValue: 'zhipu',
        description: '选择 LLM 模型提供商',
        options: MODEL_PROVIDERS.map((p) => ({ label: p.name, value: p.key })),
      },
      {
        key: 'EQUIPMENT_AGENT_TIMEOUT',
        label: '请求超时 (秒)',
        type: 'number',
        defaultValue: 60,
        description: 'Agent 请求超时时间',
        min: 10,
        max: 300,
      },
      {
        key: 'EQUIPMENT_AGENT_COMPRESSION',
        label: '启用文本压缩',
        type: 'switch',
        defaultValue: true,
        description: '对长文本进行压缩以减少 Token 消耗',
      },
      {
        key: 'EQUIPMENT_AGENT_COMPRESSION_MIN',
        label: '压缩触发阈值',
        type: 'number',
        defaultValue: 2000,
        description: '文本长度超过此值时触发压缩',
        min: 500,
        max: 10000,
      },
    ],
  },
]
