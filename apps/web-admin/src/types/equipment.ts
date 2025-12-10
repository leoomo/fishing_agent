export interface Equipment {
  equipment_id: number
  name: string
  category: string
  brand_id: number
  brand_name?: string
  model?: string
  price_min?: number
  price_max?: number
  description?: string
  features?: string
  user_level: string
  specs?: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Brand {
  brand_id: number
  name_cn: string
  name_en?: string
  logo_url?: string
  website?: string
  country?: string
}

export interface EquipmentListResponse {
  items: Equipment[]
  total: number
  page: number
  page_size: number
}
