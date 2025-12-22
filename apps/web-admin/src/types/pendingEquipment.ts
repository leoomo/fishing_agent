// 待审核装备类型定义

// 待审核装备状态
export type PendingEquipmentStatus = 'pending' | 'approved' | 'rejected'

// 来源类型
export type SourceType = 'ecommerce' | 'official' | 'forum' | 'unknown'

// 装备类型
export type EquipmentType = 'rod' | 'reel' | 'line' | 'lure' | 'accessory' | 'unknown'

// 提取的装备数据
export interface ExtractedEquipmentData {
  equipment_type?: string
  brand_name?: string
  model_name?: string
  product_name?: string
  specifications?: Record<string, unknown>
  price?: number
  description?: string
  features?: string[]
  [key: string]: unknown
}

// 待审核装备
export interface PendingEquipment {
  id: number
  status: PendingEquipmentStatus
  ocr_text: string
  source_type: SourceType
  source_url?: string
  extracted_data?: ExtractedEquipmentData
  confidence: number
  equipment_type?: string
  brand_name?: string
  model_name?: string
  product_name?: string
  reviewed_by?: number
  reviewed_at?: string
  review_notes?: string
  equipment_id?: number
  created_at: string
  updated_at: string
}

// 待审核装备列表响应
export interface PendingEquipmentListResponse {
  total: number
  page: number
  page_size: number
  items: PendingEquipment[]
}

// 审核请求
export interface ReviewRequest {
  action: 'approve' | 'reject'
  review_notes?: string
  corrected_data?: ExtractedEquipmentData
}

// 审核响应
export interface ReviewResponse {
  success: boolean
  message: string
  equipment_id?: number
}

// 筛选器
export interface PendingEquipmentFilters {
  status?: PendingEquipmentStatus
  source_type?: SourceType
  equipment_type?: string
  date_range?: [string, string]
}

// 分页状态
export interface PendingEquipmentPagination {
  current: number
  pageSize: number
  total: number
}

// 统计数据
export interface PendingEquipmentStats {
  total: number
  pending: number
  approved: number
  rejected: number
}
