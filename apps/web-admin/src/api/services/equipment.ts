import client from '../client'
import type { Equipment, EquipmentListResponse, Brand } from '@/types/equipment'

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

export const equipmentApi = {
  // 查询装备列表
  list: (params: {
    page: number
    page_size: number
    category?: string
    brand_id?: number
    keyword?: string
  }): Promise<EquipmentListResponse> => {
    return client.get('/admin/equipment', { params })
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
}
