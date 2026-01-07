// 用户类型定义

// ========== 常量 ==========
export const USER_LEVELS = ['新手', '进阶', '高手'] as const
export type UserLevel = (typeof USER_LEVELS)[number]

export const FISHING_METHODS = ['路亚', '台钓', '矶钓', '筏钓', '海钓', '飞蝇'] as const
export type FishingMethod = (typeof FISHING_METHODS)[number]

// ========== 搜索筛选 ==========
export interface UserSearchFilters {
  keyword?: string
  user_level?: string
  fishing_experience_min?: number
  fishing_experience_max?: number
  preferred_fishing_method?: string
  created_after?: string
  created_before?: string
}

// ========== 用户数据 ==========
export interface User {
  user_id: number
  username: string
  email?: string
  phone?: string
  user_level: string
  fishing_experience_years?: number
  favorite_fish_species?: string
  preferred_fishing_method?: string
  location?: string
  created_at: string
  updated_at: string
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  page_size: number
}

// ========== 更新数据 ==========
export interface UserUpdateData {
  email?: string
  phone?: string
  user_level?: string
  fishing_experience_years?: number
  preferred_fish?: string
  preferred_scenarios?: string
  nickname?: string
}

export interface BatchUpdateData {
  user_ids: number[]
  user_level?: string
}

export interface BatchUpdateResponse {
  success: boolean
  updated_count: number
  message: string
}

// ========== 统计数据 ==========
export interface UserStats {
  equipment_count: number
  favorite_count: number
  equipment_total_cost: number
  fishing_logs_count: number
  total_fish_caught: number
  total_weight: number
}

// ========== 用户装备 ==========
export interface UserEquipment {
  user_equipment_id: number
  user_id: number
  equipment_id: number
  equipment_name?: string
  category?: string
  brand_name?: string
  purchase_date?: string
  purchase_price?: number
  condition?: string
  notes?: string
  is_favorite: boolean
  created_at: string
}

export interface FishingLog {
  log_id: number
  user_id: number
  fishing_date: string
  location?: string
  weather_condition?: string
  temperature?: number
  fish_species?: string
  fish_count?: number
  fish_total_weight?: number
  equipment_used?: string
  lure_used?: string
  notes?: string
  created_at: string
}
