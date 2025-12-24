/**
 * OCR Worker Redux Slice
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import { ocrWorkerApi } from '../../api/services/ocrWorker'
import type { OCRStats, OCRTaskItem, OCRTaskFilters } from '../../types/ocrWorker'

interface OCRWorkerState {
  tasks: OCRTaskItem[]
  stats: OCRStats | null
  loading: boolean
  error: string | null
  pagination: {
    page: number
    pageSize: number
    total: number
  }
  filters: OCRTaskFilters
}

const initialState: OCRWorkerState = {
  tasks: [],
  stats: null,
  loading: false,
  error: null,
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  filters: {},
}

// 获取统计数据
export const fetchOCRStats = createAsyncThunk(
  'ocrWorker/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      const response = await ocrWorkerApi.getStats()
      return response
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      return rejectWithValue(err.response?.data?.detail || '获取统计数据失败')
    }
  }
)

// 获取任务列表
export const fetchOCRTasks = createAsyncThunk(
  'ocrWorker/fetchTasks',
  async (params: OCRTaskFilters, { rejectWithValue }) => {
    try {
      const response = await ocrWorkerApi.getTasks(params)
      return response
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      return rejectWithValue(err.response?.data?.detail || '获取任务列表失败')
    }
  }
)

const ocrWorkerSlice = createSlice({
  name: 'ocrWorker',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<OCRTaskFilters>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = {}
    },
    setPage: (state, action: PayloadAction<number>) => {
      state.pagination.page = action.payload
    },
  },
  extraReducers: (builder) => {
    // 获取统计
    builder
      .addCase(fetchOCRStats.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchOCRStats.fulfilled, (state, action) => {
        state.loading = false
        state.stats = action.payload
      })
      .addCase(fetchOCRStats.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // 获取任务列表
    builder
      .addCase(fetchOCRTasks.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchOCRTasks.fulfilled, (state, action) => {
        state.loading = false
        state.tasks = action.payload.tasks
        state.pagination.total = action.payload.total
        state.pagination.page = action.payload.page
        state.pagination.pageSize = action.payload.page_size
      })
      .addCase(fetchOCRTasks.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { setFilters, clearFilters, setPage } = ocrWorkerSlice.actions

// 选择器
export const selectOCRTasks = (state: { ocrWorker: OCRWorkerState }) => state.ocrWorker.tasks
export const selectOCRStats = (state: { ocrWorker: OCRWorkerState }) => state.ocrWorker.stats
export const selectOCRLoading = (state: { ocrWorker: OCRWorkerState }) => state.ocrWorker.loading
export const selectOCRError = (state: { ocrWorker: OCRWorkerState }) => state.ocrWorker.error
export const selectOCRPagination = (state: { ocrWorker: OCRWorkerState }) => state.ocrWorker.pagination
export const selectOCRFilters = (state: { ocrWorker: OCRWorkerState }) => state.ocrWorker.filters

export default ocrWorkerSlice.reducer
