import client from '../client'
import type {
  PendingEquipment,
  PendingEquipmentListResponse,
  ReviewRequest,
  ReviewResponse,
  PendingEquipmentStats,
} from '@/types/pendingEquipment'

export const pendingEquipmentApi = {
  // 获取待审核装备列表
  list: (params: {
    page?: number
    page_size?: number
    status?: string
    source_type?: string
    equipment_type?: string
  }): Promise<PendingEquipmentListResponse> => {
    return client.get('/admin/crawler/pending-equipment', { params })
  },

  // 获取待审核装备详情
  getDetail: (id: number): Promise<PendingEquipment> => {
    return client.get(`/admin/crawler/pending-equipment/${id}`)
  },

  // 审核待审核装备 (通过/拒绝)
  review: (id: number, data: ReviewRequest): Promise<ReviewResponse> => {
    return client.post(`/admin/crawler/pending-equipment/${id}/review`, data)
  },

  // 删除待审核记录
  delete: (id: number): Promise<{ success: boolean; message: string }> => {
    return client.delete(`/admin/crawler/pending-equipment/${id}`)
  },

  // 批量审核
  batchReview: (
    ids: number[],
    action: 'approve' | 'reject',
    review_notes?: string
  ): Promise<{ success: boolean; processed: number; failed: number }> => {
    return client.post('/admin/crawler/pending-equipment/batch-review', {
      ids,
      action,
      review_notes,
    })
  },

  // 获取统计数据
  getStats: (): Promise<PendingEquipmentStats> => {
    return client.get('/admin/crawler/pending-equipment/stats')
  },
}
