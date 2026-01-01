/**
 * 鱼百科相关类型定义
 */

// ========== 分类枚举和配置 ==========

export type FishCategory = 'freshwater' | 'saltwater' | 'brackish'

export type Season = 'spring' | 'summer' | 'fall' | 'winter'

export type ActivityLevel = '低' | '中' | '高'

export interface FishCategoryConfig {
  label: string
  icon: string
  color: string
  description: string
}

export const FISH_CATEGORY_CONFIG: Record<FishCategory, FishCategoryConfig> = {
  freshwater: {
    label: '淡水鱼',
    icon: '🐟',
    color: '#1890ff',
    description: '生活在淡水中的鱼类',
  },
  saltwater: {
    label: '海水鱼',
    icon: '🐠',
    color: '#13c2c2',
    description: '生活在海水中的鱼类',
  },
  brackish: {
    label: '广盐鱼',
    icon: '🐡',
    color: '#722ed1',
    description: '可在淡水和海水中生活的鱼类',
  },
}

// 分类选项列表
export const FISH_CATEGORY_OPTIONS = Object.entries(FISH_CATEGORY_CONFIG).map(
  ([value, config]) => ({
    value: value as FishCategory,
    label: `${config.icon} ${config.label}`,
    ...config,
  })
)

// 季节配置
export interface SeasonConfig {
  label: string
  icon: string
  color: string
}

export const SEASON_CONFIG: Record<Season, SeasonConfig> = {
  spring: { label: '春季', icon: '🌸', color: '#52c41a' },
  summer: { label: '夏季', icon: '☀️', color: '#faad14' },
  fall: { label: '秋季', icon: '🍂', color: '#fa8c16' },
  winter: { label: '冬季', icon: '❄️', color: '#1890ff' },
}

export const SEASON_OPTIONS = Object.entries(SEASON_CONFIG).map(([value, config]) => ({
  value: value as Season,
  label: `${config.icon} ${config.label}`,
  ...config,
}))

// 活跃度配置
export const ACTIVITY_LEVEL_CONFIG: Record<ActivityLevel, { label: string; color: string }> = {
  低: { label: '低', color: '#8c8c8c' },
  中: { label: '中', color: '#faad14' },
  高: { label: '高', color: '#52c41a' },
}

export const ACTIVITY_LEVEL_OPTIONS = Object.entries(ACTIVITY_LEVEL_CONFIG).map(
  ([value, config]) => ({
    value: value as ActivityLevel,
    label: config.label,
    ...config,
  })
)

// ========== 知识库接口 ==========

export interface FishKnowledge {
  id: number
  species_id: number
  topic: string
  content: string
  source?: string
  tags?: string
  created_at?: string
  updated_at?: string
}

export interface FishKnowledgeCreate {
  topic: string
  content: string
  source?: string
  tags?: string
}

export interface FishKnowledgeUpdate {
  topic?: string
  content?: string
  source?: string
  tags?: string
}

// ========== 季节活动接口 ==========

export interface FishSeasonActivity {
  id: number
  species_id: number
  season: Season
  activity_level: ActivityLevel
  best_time?: string
  recommended_lures?: string
  fishing_tips?: string
  created_at?: string
  updated_at?: string
}

export interface FishSeasonActivityCreate {
  season: Season
  activity_level: ActivityLevel
  best_time?: string
  recommended_lures?: string
  fishing_tips?: string
}

export interface FishSeasonActivityUpdate {
  season?: Season
  activity_level?: ActivityLevel
  best_time?: string
  recommended_lures?: string
  fishing_tips?: string
}

// ========== 装备推荐接口 ==========

export interface EquipmentRecommendation {
  recommended_lures?: string[]
  recommended_rigs?: string[]
  recommended_rod_power?: string[]
  recommended_line_lb_min?: number
  recommended_line_lb_max?: number
  lure_difficulty?: string
  fight_intensity?: string
}

// ========== 鱼种接口 ==========

export interface FishSpecies {
  species_id: number
  name_cn: string
  name_en?: string
  scientific_name?: string
  category: FishCategory
  habitat?: string
  description?: string
  image_url?: string
  min_weight?: number
  max_weight?: number
  min_length?: number
  max_length?: number
  created_at?: string
  updated_at?: string
  knowledge: FishKnowledge[]
  season_activity: FishSeasonActivity[]
}

export interface FishSpeciesListItem {
  species_id: number
  name_cn: string
  name_en?: string
  category: FishCategory
  habitat?: string
  knowledge_count: number
  season_count: number
  created_at?: string
}

export interface FishSpeciesListResponse {
  items: FishSpeciesListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ========== 请求类型 ==========

export interface FishSpeciesCreateRequest {
  name_cn: string
  name_en?: string
  scientific_name?: string
  category: FishCategory
  habitat?: string
  description?: string
  image_url?: string
  min_weight?: number
  max_weight?: number
  min_length?: number
  max_length?: number
}

export interface FishSpeciesUpdateRequest {
  name_cn?: string
  name_en?: string
  scientific_name?: string
  category?: FishCategory
  habitat?: string
  description?: string
  image_url?: string
  min_weight?: number
  max_weight?: number
  min_length?: number
  max_length?: number
}

export interface FishSpeciesListParams {
  page?: number
  page_size?: number
  category?: FishCategory
  keyword?: string
  habitat?: string
}

// ========== 分类统计 ==========

export interface FishCategoryStats {
  category: string
  count: number
  label: string
  icon: string
  color: string
}

export interface FishCategoryStatsResponse {
  categories: FishCategoryStats[]
  total: number
}

// ========== 初始化数据响应 ==========

export interface FishInitDataResponse {
  created_count: number
  message: string
}
