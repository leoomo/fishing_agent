/**
 * 钓鱼配件相关类型定义
 */

// ========== 分类枚举和配置 ==========

export type AccessoryCategory = 'hook' | 'sinker' | 'swivel' | 'leader' | 'float' | 'snap' | 'other'

export type UserLevel = 'beginner' | 'intermediate' | 'advanced'

export interface AccessoryCategoryConfig {
  label: string
  icon: string
  color: string
  description: string
}

export const ACCESSORY_CATEGORY_CONFIG: Record<AccessoryCategory, AccessoryCategoryConfig> = {
  hook: {
    label: '钩子',
    icon: '🪝',
    color: '#1890ff',
    description: '曲柄钩、铅头钩、虫钩等',
  },
  sinker: {
    label: '铅坠',
    icon: '⚓',
    color: '#722ed1',
    description: '子弹铅、钨钢铅、夹铅等',
  },
  swivel: {
    label: '转环',
    icon: '🔗',
    color: '#52c41a',
    description: '八字环、滚珠轴承转环等',
  },
  leader: {
    label: '前导线',
    icon: '〰️',
    color: '#faad14',
    description: '碳素前导线、钢丝前导线等',
  },
  float: {
    label: '浮漂',
    icon: '🔴',
    color: '#eb2f96',
    description: '路亚浮漂、水滴浮漂等',
  },
  snap: {
    label: '别针',
    icon: '📎',
    color: '#13c2c2',
    description: '快速别针、O型环等',
  },
  other: {
    label: '其他',
    icon: '🎣',
    color: '#8c8c8c',
    description: '其他配件',
  },
}

// 分类选项列表
export const ACCESSORY_CATEGORY_OPTIONS = Object.entries(ACCESSORY_CATEGORY_CONFIG).map(
  ([value, config]) => ({
    value: value as AccessoryCategory,
    icon: config.icon,
    color: config.color,
    label: `${config.icon} ${config.label}`,
  })
)

// 用户等级配置
export const USER_LEVEL_CONFIG: Record<UserLevel, { label: string; color: string }> = {
  beginner: { label: '新手', color: '#52c41a' },
  intermediate: { label: '进阶', color: '#1890ff' },
  advanced: { label: '高级', color: '#722ed1' },
}

export const USER_LEVEL_OPTIONS = Object.entries(USER_LEVEL_CONFIG).map(([value, config]) => ({
  value: value as UserLevel,
  color: config.color,
  label: config.label,
}))

// ========== 配件接口 ==========

export interface Accessory {
  accessory_id: number
  name: string
  category: AccessoryCategory
  description?: string
  features?: string

  // 规格参数
  size?: string
  weight?: number
  material?: string
  color?: string
  quantity_per_pack?: number

  // 应用场景
  target_species?: string
  applicable_rigs?: string
  best_conditions?: string

  // 商业信息
  brand?: string
  price_min?: number
  price_max?: number
  user_level?: UserLevel

  // 媒体
  image_url?: string

  // 时间戳
  created_at?: string
  updated_at?: string
}

export interface AccessoryListItem {
  accessory_id: number
  name: string
  category: AccessoryCategory
  size?: string
  material?: string
  brand?: string
  price_min?: number
  price_max?: number
  user_level?: UserLevel
}

export interface AccessoryListResponse {
  items: AccessoryListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ========== 请求类型 ==========

export interface AccessoryCreateRequest {
  name: string
  category: AccessoryCategory
  description?: string
  features?: string
  size?: string
  weight?: number
  material?: string
  color?: string
  quantity_per_pack?: number
  target_species?: string
  applicable_rigs?: string
  best_conditions?: string
  brand?: string
  price_min?: number
  price_max?: number
  user_level?: UserLevel
  image_url?: string
}

export interface AccessoryUpdateRequest {
  name?: string
  category?: AccessoryCategory
  description?: string
  features?: string
  size?: string
  weight?: number
  material?: string
  color?: string
  quantity_per_pack?: number
  target_species?: string
  applicable_rigs?: string
  best_conditions?: string
  brand?: string
  price_min?: number
  price_max?: number
  user_level?: UserLevel
  image_url?: string
}

export interface AccessoryListParams {
  page?: number
  page_size?: number
  category?: AccessoryCategory
  keyword?: string
  user_level?: UserLevel
}

// ========== 分类统计 ==========

export interface AccessoryCategoryStats {
  category: string
  count: number
  label: string
  icon: string
  color: string
}

export interface AccessoryCategoryStatsResponse {
  categories: AccessoryCategoryStats[]
  total: number
}

// ========== 表单选项 ==========

export interface AccessoryOptionsResponse {
  categories: Array<{
    value: string
    label: string
    icon: string
    color: string
  }>
  user_levels: Array<{
    value: string
    label: string
    color: string
  }>
  materials: string[]
}

// ========== 初始化数据响应 ==========

export interface AccessoryInitDataResponse {
  created_count: number
  message: string
}
