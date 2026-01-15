/**
 * 拟饵类型相关类型定义
 */

// ========== 分类枚举和配置 ==========

export type LureCategory = 'hard' | 'soft' | 'metal' | 'fly' | 'other'

export interface LureCategoryConfig {
  label: string
  icon: string
  color: string
  description: string
}

export const LURE_CATEGORY_CONFIG: Record<LureCategory, LureCategoryConfig> = {
  hard: {
    label: '硬饵',
    icon: '🎯',
    color: '#1890ff',
    description: '米诺、波趴、VIB等',
  },
  soft: {
    label: '软饵',
    icon: '🐛',
    color: '#52c41a',
    description: '卷尾蛆、T尾等',
  },
  metal: {
    label: '金属饵',
    icon: '✨',
    color: '#faad14',
    description: '亮片、铁板等',
  },
  fly: {
    label: '飞蝇',
    icon: '🦋',
    color: '#722ed1',
    description: '干蝇、湿蝇等',
  },
  other: {
    label: '其他',
    icon: '🎣',
    color: '#8c8c8c',
    description: '其他类型',
  },
}

// 分类选项列表
export const LURE_CATEGORY_OPTIONS = Object.entries(LURE_CATEGORY_CONFIG).map(
  ([value, config]) => ({
    value: value as LureCategory,
    icon: config.icon,
    color: config.color,
    label: `${config.icon} ${config.label}`,
  })
)

// ========== 拟饵类型接口 ==========

// 扩展信息接口（存储在 best_conditions JSON 中）
export interface LureTypeExtendedInfo {
  usage_tips?: string[]
  pros?: string[]
  cons?: string[]
  recommended_rod_power?: string[]
  recommended_line?: string
  retrieve_techniques?: string[]
  best_seasons?: string[]
  best_water_conditions?: string
  color_selection?: string
}

export interface LureType {
  lure_type_id: number
  name: string
  name_en?: string
  category: LureCategory
  description?: string
  action_description?: string
  best_conditions?: string
  target_species?: string
  typical_weight_min?: number
  typical_weight_max?: number
  image_url?: string
  created_at?: string
  updated_at?: string
}

export interface LureTypeListItem {
  lure_type_id: number
  name: string
  name_en?: string
  category: LureCategory
  target_species?: string
  typical_weight_min?: number
  typical_weight_max?: number
}

export interface LureTypeListResponse {
  items: LureTypeListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ========== 请求类型 ==========

export interface LureTypeCreateRequest {
  name: string
  category: LureCategory
  description?: string
  action_description?: string
  best_conditions?: string
  target_species?: string
  typical_weight_min?: number
  typical_weight_max?: number
  image_url?: string
}

export interface LureTypeUpdateRequest {
  name?: string
  category?: LureCategory
  description?: string
  action_description?: string
  best_conditions?: string
  target_species?: string
  typical_weight_min?: number
  typical_weight_max?: number
  image_url?: string
}

export interface LureTypeListParams {
  page?: number
  page_size?: number
  category?: LureCategory
  keyword?: string
}

// ========== 分类统计 ==========

export interface CategoryStats {
  category: string
  count: number
  label: string
  icon: string
  color: string
}

export interface CategoryStatsResponse {
  categories: CategoryStats[]
  total: number
}

// ========== 初始化数据响应 ==========

export interface InitDataResponse {
  created_count: number
  message: string
}

// ========== LLM增强进度 ==========

export interface EnrichProgressItem {
  lure_type_id: number
  name: string
  status: 'pending' | 'enriching' | 'completed' | 'failed' | 'skipped'
  error?: string
  updated_at?: string
}

export interface EnrichProgressStats {
  total: number
  pending: number
  enriching: number
  completed: number
  failed: number
  skipped: number
}

export interface EnrichProgressResponse {
  is_running: boolean
  stats: EnrichProgressStats
  items: EnrichProgressItem[]
}

// ========== 网页采集进度 ==========

export interface CrawlProgressResponse {
  is_running: boolean
  status: 'idle' | 'crawling' | 'translating' | 'completed' | 'failed'
  message: string
  crawled_count: number
  translated_count: number
  total_count: number
  error?: string | null
}
