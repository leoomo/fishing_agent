import client from '../client'
import type { Equipment, EquipmentListResponse, Brand } from '@/types/equipment'

// 重新导出类型供其他模块使用
export type { Brand }

export interface EquipmentCreateRequest {
  name: string
  category: string
  brand_id: number
  model?: string
  price_min?: number
  price_max?: number
  description?: string
  features?: string
  user_level: string
  specs?: Record<string, unknown>
}

// 批量创建相关类型
export interface BatchRodTemplate {
  brand_id: number
  product_line: string
  sections?: number
  guide_type?: string
  handle_type?: string
  material?: string
  price_min?: number
  price_max?: number
  user_level?: string
  description?: string
  features?: string
}

export interface RodVariantSpec {
  model: string
  length: number
  power: 'UL' | 'L' | 'ML' | 'M' | 'MH' | 'H' | 'XH'
  action?: 'Fast' | 'Medium' | 'Slow'
  weight?: number
  lure_weight_min?: number
  lure_weight_max?: number
  line_weight_min?: number
  line_weight_max?: number
  closed_length?: number
  price_min?: number
  price_max?: number
}

export interface BatchEquipmentCreateRequest {
  category: string
  template: Record<string, unknown>
  variants: Record<string, unknown>[]
  skip_duplicates?: boolean
}

export interface BatchRodCreateRequest {
  template: BatchRodTemplate
  variants: RodVariantSpec[]
  skip_duplicates?: boolean
}

export interface BatchEquipmentCreateResponse {
  success_count: number
  skip_count: number
  error_count: number
  created_ids: number[]
  skipped_models: string[]
  errors: Array<{ model: string; error: string }>
}

export interface TextParseRequest {
  text: string
  category: string
  delimiter?: string
}

export interface TextParseResponse {
  success: boolean
  template: Record<string, unknown>
  variants: Record<string, unknown>[]
  warnings: string[]
  raw_headers: string[]
  row_count: number
}

export const equipmentApi = {
  // 查询装备列表
  list: (params: {
    page: number
    page_size: number
    category?: string
    brand_id?: number
    keyword?: string
    // 通用高级筛选
    price_min?: number
    price_max?: number
    user_level?: string
    is_active?: boolean
    // 鱼竿专属筛选
    power?: string
    action?: string
    length_min?: number
    length_max?: number
  }): Promise<EquipmentListResponse> => {
    // 过滤掉 undefined 值
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    )
    return client.get('/admin/equipment', { params: cleanParams })
  },

  // 获取装备详情
  get: (id: number): Promise<Equipment> => {
    return client.get(`/admin/equipment/${id}`)
  },

  // 创建装备
  create: (data: EquipmentCreateRequest): Promise<Equipment> => {
    return client.post('/admin/equipment', data)
  },

  // 更新装备
  update: (id: number, data: Partial<EquipmentCreateRequest>): Promise<Equipment> => {
    return client.put(`/admin/equipment/${id}`, data)
  },

  // 删除装备
  delete: (id: number): Promise<void> => {
    return client.delete(`/admin/equipment/${id}`)
  },

  // 查询品牌列表
  listBrands: (): Promise<Brand[]> => {
    return client.get('/admin/brands')
  },

  // 创建品牌
  createBrand: (data: { name_cn: string; name_en?: string }): Promise<Brand> => {
    return client.post('/admin/brands', data)
  },

  // 导出 CSV
  exportCSV: (params: { category?: string }): Promise<Blob> => {
    return client.get('/admin/import-export/export/csv', {
      params,
      responseType: 'blob',
    })
  },

  // 导入 CSV
  importCSV: (file: File): Promise<unknown> => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/admin/import-export/import/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // 批量创建装备（通用）
  batchCreate: (data: BatchEquipmentCreateRequest): Promise<BatchEquipmentCreateResponse> => {
    return client.post('/admin/equipment/batch', data)
  },

  // 批量创建鱼竿（强类型）
  batchCreateRods: (data: BatchRodCreateRequest): Promise<BatchEquipmentCreateResponse> => {
    return client.post('/admin/equipment/batch/rods', data)
  },

  // 解析规格表文本
  parseText: (data: TextParseRequest): Promise<TextParseResponse> => {
    return client.post('/admin/equipment/parse-text', data)
  },
}
