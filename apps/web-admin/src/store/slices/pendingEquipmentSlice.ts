import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit'
import { message } from 'antd'
import { pendingEquipmentApi } from '../../api/services/pendingEquipment'
import type {
  PendingEquipment,
  PendingEquipmentFilters,
  PendingEquipmentPagination,
  PendingEquipmentStats,
  ReviewRequest,
} from '../../types/pendingEquipment'

// 状态接口
export interface PendingEquipmentState {
  // 数据
  items: PendingEquipment[]
  currentItem: PendingEquipment | null
  selectedIds: number[]

  // 分页和筛选
  pagination: PendingEquipmentPagination
  filters: PendingEquipmentFilters

  // 统计
  stats: PendingEquipmentStats | null

  // 加载状态
  loading: {
    list: boolean
    detail: boolean
    review: boolean
    delete: boolean
    stats: boolean
  }

  // 错误状态
  errors: {
    list: string | null
    detail: string | null
    review: string | null
    delete: string | null
    stats: string | null
  }

  // UI状态
  ui: {
    showDetailModal: boolean
    showReviewModal: boolean
    reviewAction: 'approve' | 'reject' | null
  }
}

// 初始状态
const initialState: PendingEquipmentState = {
  items: [],
  currentItem: null,
  selectedIds: [],

  pagination: {
    current: 1,
    pageSize: 20,
    total: 0,
  },

  filters: {},

  stats: null,

  loading: {
    list: false,
    detail: false,
    review: false,
    delete: false,
    stats: false,
  },

  errors: {
    list: null,
    detail: null,
    review: null,
    delete: null,
    stats: null,
  },

  ui: {
    showDetailModal: false,
    showReviewModal: false,
    reviewAction: null,
  },
}

// 异步Actions
export const fetchPendingEquipmentList = createAsyncThunk(
  'pendingEquipment/fetchList',
  async (
    params: { page?: number; pageSize?: number; filters?: PendingEquipmentFilters },
    { rejectWithValue }
  ) => {
    try {
      const response = await pendingEquipmentApi.list({
        page: params.page || 1,
        page_size: params.pageSize || 20,
        status: params.filters?.status,
        source_type: params.filters?.source_type,
        equipment_type: params.filters?.equipment_type,
      })
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取待审核列表失败'
      return rejectWithValue(errorMessage)
    }
  }
)

export const fetchPendingEquipmentDetail = createAsyncThunk(
  'pendingEquipment/fetchDetail',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await pendingEquipmentApi.getDetail(id)
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取详情失败'
      return rejectWithValue(errorMessage)
    }
  }
)

export const reviewPendingEquipment = createAsyncThunk(
  'pendingEquipment/review',
  async ({ id, data }: { id: number; data: ReviewRequest }, { rejectWithValue }) => {
    try {
      const response = await pendingEquipmentApi.review(id, data)
      message.success(data.action === 'approve' ? '审核通过成功' : '已拒绝')
      return { id, response, action: data.action }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '审核操作失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const deletePendingEquipment = createAsyncThunk(
  'pendingEquipment/delete',
  async (id: number, { rejectWithValue }) => {
    try {
      await pendingEquipmentApi.delete(id)
      message.success('删除成功')
      return id
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '删除失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const fetchPendingEquipmentStats = createAsyncThunk(
  'pendingEquipment/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      const response = await pendingEquipmentApi.getStats()
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取统计数据失败'
      return rejectWithValue(errorMessage)
    }
  }
)

// Slice定义
const pendingEquipmentSlice = createSlice({
  name: 'pendingEquipment',
  initialState,
  reducers: {
    // 筛选器
    setFilters: (state, action: PayloadAction<Partial<PendingEquipmentFilters>>) => {
      state.filters = { ...state.filters, ...action.payload }
      state.pagination.current = 1
    },

    clearFilters: (state) => {
      state.filters = {}
      state.pagination.current = 1
    },

    // 分页
    setPagination: (state, action: PayloadAction<Partial<PendingEquipmentPagination>>) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },

    // 选择
    setSelectedIds: (state, action: PayloadAction<number[]>) => {
      state.selectedIds = action.payload
    },

    toggleSelection: (state, action: PayloadAction<number>) => {
      const id = action.payload
      const index = state.selectedIds.indexOf(id)
      if (index > -1) {
        state.selectedIds.splice(index, 1)
      } else {
        state.selectedIds.push(id)
      }
    },

    selectAll: (state) => {
      state.selectedIds = state.items.map((item) => item.id)
    },

    clearSelection: (state) => {
      state.selectedIds = []
    },

    // UI状态
    showDetailModal: (state, action: PayloadAction<PendingEquipment>) => {
      state.currentItem = action.payload
      state.ui.showDetailModal = true
    },

    hideDetailModal: (state) => {
      state.ui.showDetailModal = false
    },

    showReviewModal: (state, action: PayloadAction<{ item: PendingEquipment; action: 'approve' | 'reject' }>) => {
      state.currentItem = action.payload.item
      state.ui.reviewAction = action.payload.action
      state.ui.showReviewModal = true
    },

    hideReviewModal: (state) => {
      state.ui.showReviewModal = false
      state.ui.reviewAction = null
    },

    // 清除错误
    clearError: (state, action: PayloadAction<keyof PendingEquipmentState['errors']>) => {
      state.errors[action.payload] = null
    },

    clearAllErrors: (state) => {
      Object.keys(state.errors).forEach((key) => {
        state.errors[key as keyof PendingEquipmentState['errors']] = null
      })
    },

    // 重置
    resetState: () => initialState,
  },

  extraReducers: (builder) => {
    // fetchList
    builder
      .addCase(fetchPendingEquipmentList.pending, (state) => {
        state.loading.list = true
        state.errors.list = null
      })
      .addCase(fetchPendingEquipmentList.fulfilled, (state, action) => {
        state.loading.list = false
        state.items = action.payload.items
        state.pagination.total = action.payload.total
        state.pagination.current = action.payload.page
      })
      .addCase(fetchPendingEquipmentList.rejected, (state, action) => {
        state.loading.list = false
        state.errors.list = action.payload as string
      })

    // fetchDetail
    builder
      .addCase(fetchPendingEquipmentDetail.pending, (state) => {
        state.loading.detail = true
        state.errors.detail = null
      })
      .addCase(fetchPendingEquipmentDetail.fulfilled, (state, action) => {
        state.loading.detail = false
        state.currentItem = action.payload
      })
      .addCase(fetchPendingEquipmentDetail.rejected, (state, action) => {
        state.loading.detail = false
        state.errors.detail = action.payload as string
      })

    // review
    builder
      .addCase(reviewPendingEquipment.pending, (state) => {
        state.loading.review = true
        state.errors.review = null
      })
      .addCase(reviewPendingEquipment.fulfilled, (state, action) => {
        state.loading.review = false
        state.ui.showReviewModal = false
        state.ui.reviewAction = null
        // 更新列表中的项目状态
        const index = state.items.findIndex((item) => item.id === action.payload.id)
        if (index > -1) {
          state.items[index].status = action.payload.action === 'approve' ? 'approved' : 'rejected'
        }
        // 如果当前查看的是这个项目，也更新它
        if (state.currentItem?.id === action.payload.id) {
          state.currentItem.status = action.payload.action === 'approve' ? 'approved' : 'rejected'
        }
      })
      .addCase(reviewPendingEquipment.rejected, (state, action) => {
        state.loading.review = false
        state.errors.review = action.payload as string
      })

    // delete
    builder
      .addCase(deletePendingEquipment.pending, (state) => {
        state.loading.delete = true
        state.errors.delete = null
      })
      .addCase(deletePendingEquipment.fulfilled, (state, action) => {
        state.loading.delete = false
        state.items = state.items.filter((item) => item.id !== action.payload)
        state.selectedIds = state.selectedIds.filter((id) => id !== action.payload)
        state.pagination.total = Math.max(0, state.pagination.total - 1)
        if (state.currentItem?.id === action.payload) {
          state.ui.showDetailModal = false
          state.currentItem = null
        }
      })
      .addCase(deletePendingEquipment.rejected, (state, action) => {
        state.loading.delete = false
        state.errors.delete = action.payload as string
      })

    // fetchStats
    builder
      .addCase(fetchPendingEquipmentStats.pending, (state) => {
        state.loading.stats = true
        state.errors.stats = null
      })
      .addCase(fetchPendingEquipmentStats.fulfilled, (state, action) => {
        state.loading.stats = false
        state.stats = action.payload
      })
      .addCase(fetchPendingEquipmentStats.rejected, (state, action) => {
        state.loading.stats = false
        state.errors.stats = action.payload as string
      })
  },
})

// 导出Actions
export const {
  setFilters,
  clearFilters,
  setPagination,
  setSelectedIds,
  toggleSelection,
  selectAll,
  clearSelection,
  showDetailModal,
  hideDetailModal,
  showReviewModal,
  hideReviewModal,
  clearError,
  clearAllErrors,
  resetState,
} = pendingEquipmentSlice.actions

// 导出Reducer
export default pendingEquipmentSlice.reducer

// 选择器
export const selectPendingEquipmentState = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment

export const selectItems = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.items

export const selectCurrentItem = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.currentItem

export const selectSelectedIds = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.selectedIds

export const selectPagination = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.pagination

export const selectFilters = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.filters

export const selectStats = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.stats

export const selectLoading = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.loading

export const selectErrors = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.errors

export const selectUI = (state: { pendingEquipment: PendingEquipmentState }) =>
  state.pendingEquipment.ui
