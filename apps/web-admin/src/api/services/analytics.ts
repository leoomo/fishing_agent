import client from '../client'
import type {
  EquipmentStats,
  EquipmentTrend,
  PriceDistribution,
  BrandStats,
  UserActivity,
  BusinessReport,
  ReportListResponse,
  UserRetention,
  QueryHotspot,
} from '@/types/analytics'

export const analyticsApi = {
  // 装备数据统计总览
  getEquipmentStats: (): Promise<EquipmentStats> => {
    return client.get('/admin/analytics/equipment/stats')
  },

  // 装备数量趋势（按月）
  getEquipmentTrends: (months: number = 12): Promise<EquipmentTrend[]> => {
    return client.get('/admin/analytics/equipment/trends', { params: { months } })
  },

  // 价格分布统计
  getPriceDistribution: (category?: string): Promise<PriceDistribution[]> => {
    return client.get('/admin/analytics/equipment/price-distribution', {
      params: { category },
    })
  },

  // 品牌统计排行
  getBrandStats: (topN: number = 10): Promise<BrandStats[]> => {
    return client.get('/admin/analytics/equipment/brand-stats', {
      params: { top_n: topN },
    })
  },

  // 获取装备类别列表
  getCategories: (): Promise<string[]> => {
    return client.get('/admin/analytics/categories')
  },

  // 用户活跃度统计
  getUserActivity: (days: number = 30): Promise<UserActivity[]> => {
    return client.get('/admin/analytics/users/activity', { params: { days } })
  },

  // 用户留存率分析
  getUserRetention: (days: number = 30): Promise<UserRetention> => {
    return client.get('/admin/analytics/users/retention', { params: { days } })
  },

  // 查询热点分析
  getQueryHotspots: (topN: number = 20, days: number = 7): Promise<QueryHotspot[]> => {
    return client.get('/admin/analytics/query/hotspots', {
      params: { top_n: topN, days },
    })
  },

  // 生成业务报表
  generateReport: (params: {
    report_type: string
    start_date?: string
    end_date?: string
  }): Promise<BusinessReport> => {
    return client.post('/admin/analytics/reports/generate', params)
  },

  // 查询报表列表
  listReports: (params: {
    page: number
    page_size: number
    report_type?: string
  }): Promise<ReportListResponse> => {
    return client.get('/admin/analytics/reports/list', { params })
  },
}
