// 数据分析类型定义

export interface EquipmentStats {
  total_equipment: number
  total_brands: number
  avg_price: number
  by_category: Record<string, number>
  by_user_level: Record<string, number>
}

export interface EquipmentTrend {
  month: string
  count: number
  category?: string
}

export interface PriceDistribution {
  range: string
  count: number
  percentage: number
}

export interface BrandStats {
  brand_id: number
  brand_name: string
  equipment_count: number
  avg_price: number
}

export interface UserActivity {
  date: string
  active_users: number
  new_users: number
  queries: number
}

export interface BusinessReport {
  report_id: string
  report_type: string
  title: string
  content: string
  generated_at: string
  generated_by: string
}

export interface ReportListResponse {
  reports: BusinessReport[]
  total: number
  page: number
  page_size: number
}
