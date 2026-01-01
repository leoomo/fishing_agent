// 数据分析类型定义

// ========== 装备数据分析 ==========

export interface PriceDistribution {
  price_range: string
  count: number
  percentage: number
}

export interface BrandStats {
  brand_id: number
  brand_name: string
  equipment_count: number
  avg_price: number
  total_value: number
  percentage: number
}

export interface EquipmentStats {
  total_equipment: number
  total_brands: number
  avg_price: number
  price_distribution: PriceDistribution[]
  top_brands: BrandStats[]
  by_category: Record<string, number>
}

export interface EquipmentTrend {
  date: string  // YYYY-MM
  total_count: number
  by_category: Record<string, number>
}

// ========== 用户行为分析 ==========

export interface UserActivity {
  date: string
  dau: number  // 日活跃用户数
  new_users: number  // 新增用户数
  active_rate: number  // 活跃率
}

export interface QueryHotspot {
  keyword: string
  count: number
  category?: string
}

export interface UserPreference {
  category: string
  user_count: number
  avg_equipment_count: number
}

export interface UserBehaviorStats {
  total_users: number
  active_users_7d: number
  active_users_30d: number
  retention_rate_7d: number
  retention_rate_30d: number
  query_hotspots: QueryHotspot[]
  category_preferences: UserPreference[]
}

// ========== 业务报表 ==========

export interface BusinessReportRequest {
  report_type: 'weekly' | 'monthly' | 'custom'
  start_date: string  // YYYY-MM-DD
  end_date: string    // YYYY-MM-DD
}

export interface BusinessReportData {
  equipment: {
    new_count: number
    total_count: number
    avg_price: number
    by_category: Record<string, number>
  }
  users: {
    new_count: number
    active_count: number
    total_count: number
  }
  api: {
    total_requests: number
    success_rate: number
    avg_response_time: number
  }
  llm: {
    total_calls: number
    total_tokens: number
    avg_latency: number
  }
}

export interface BusinessReport {
  report_id: number
  report_type: string
  start_date: string
  end_date: string
  report_data: BusinessReportData
  generated_at: string
  generated_by: string
}

export interface ReportListResponse {
  total: number
  reports: BusinessReport[]
}
