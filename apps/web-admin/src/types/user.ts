// 用户类型定义

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
