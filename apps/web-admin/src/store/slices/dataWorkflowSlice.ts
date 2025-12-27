/**
 * 数据处理工作流 Redux Slice
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import type { RootState } from '../store'
import { dataWorkflowApi } from '../../api/services/dataWorkflow'
import type {
  WorkflowStats,
  WorkerInfo,
  OCRTaskItem,
  OCRTaskFilters,
  ReviewTaskItem,
  ReviewTaskFilters,
  ReviewAction,
  WorkflowTab,
  OCRProgressInfo,
  WorkerLogItem,
  WSConnectionStatus,
} from '../../types/dataWorkflow'

// ========== State 定义 ==========

// 日志保留条数限制
const MAX_LOG_ENTRIES = 100

interface DataWorkflowState {
  // 统计数据
  stats: WorkflowStats | null
  statsLoading: boolean
  statsError: string | null

  // Worker 监控
  workers: WorkerInfo[]
  workersLoading: boolean
  workersPanelCollapsed: boolean

  // OCR 任务
  ocrTasks: OCRTaskItem[]
  ocrTasksTotal: number
  ocrTasksLoading: boolean
  ocrFilters: OCRTaskFilters
  ocrSelectedKeys: number[]

  // 审核任务
  reviewTasks: ReviewTaskItem[]
  reviewTasksTotal: number
  reviewTasksLoading: boolean
  reviewFilters: ReviewTaskFilters
  currentReviewTask: ReviewTaskItem | null
  reviewModalVisible: boolean
  reviewAction: 'approve' | 'reject' | null

  // 通用
  activeTab: WorkflowTab

  // ========== WebSocket 实时更新 ==========
  wsConnected: WSConnectionStatus
  taskProgress: Record<number, OCRProgressInfo>
  workerLogs: WorkerLogItem[]
  logsPanelCollapsed: boolean
}

const initialState: DataWorkflowState = {
  stats: null,
  statsLoading: false,
  statsError: null,

  workers: [],
  workersLoading: false,
  workersPanelCollapsed: false,

  ocrTasks: [],
  ocrTasksTotal: 0,
  ocrTasksLoading: false,
  ocrFilters: { page: 1, page_size: 20 },
  ocrSelectedKeys: [],

  reviewTasks: [],
  reviewTasksTotal: 0,
  reviewTasksLoading: false,
  reviewFilters: { page: 1, page_size: 20 },
  currentReviewTask: null,
  reviewModalVisible: false,
  reviewAction: null,

  activeTab: 'ocr',

  // WebSocket
  wsConnected: 'disconnected',
  taskProgress: {},
  workerLogs: [],
  logsPanelCollapsed: true,
}

// ========== Async Thunks ==========

// 获取工作流统计
export const fetchWorkflowStats = createAsyncThunk(
  'dataWorkflow/fetchStats',
  async () => {
    const response = await dataWorkflowApi.getStats()
    return response
  }
)

// 获取 Worker 列表
export const fetchWorkers = createAsyncThunk(
  'dataWorkflow/fetchWorkers',
  async () => {
    const response = await dataWorkflowApi.getWorkers()
    return response.workers
  }
)

// 获取 OCR 任务列表
export const fetchOCRTasks = createAsyncThunk(
  'dataWorkflow/fetchOCRTasks',
  async (params: OCRTaskFilters) => {
    const response = await dataWorkflowApi.getOCRTasks(params)
    return response
  }
)

// 重试 OCR 任务
export const retryOCRTask = createAsyncThunk(
  'dataWorkflow/retryOCRTask',
  async (pendingId: number) => {
    await dataWorkflowApi.retryOCRTask(pendingId)
    return pendingId
  }
)

// 批量重试 OCR 任务
export const batchRetryOCRTasks = createAsyncThunk(
  'dataWorkflow/batchRetryOCRTasks',
  async (pendingIds: number[]) => {
    const response = await dataWorkflowApi.batchRetryOCRTasks(pendingIds)
    return { pendingIds, affectedCount: response.affected_count }
  }
)

// 跳过 OCR 任务
export const skipOCRTask = createAsyncThunk(
  'dataWorkflow/skipOCRTask',
  async (pendingId: number) => {
    await dataWorkflowApi.skipOCRTask(pendingId)
    return pendingId
  }
)

// 设置 OCR 任务优先级
export const setOCRTaskPriority = createAsyncThunk(
  'dataWorkflow/setOCRTaskPriority',
  async ({ pendingId, priority }: { pendingId: number; priority: number }) => {
    await dataWorkflowApi.setOCRTaskPriority(pendingId, priority)
    return { pendingId, priority }
  }
)

// 删除 OCR 任务
export const deleteOCRTask = createAsyncThunk(
  'dataWorkflow/deleteOCRTask',
  async (pendingId: number) => {
    await dataWorkflowApi.deleteOCRTask(pendingId)
    return pendingId
  }
)

// 获取审核任务列表
export const fetchReviewTasks = createAsyncThunk(
  'dataWorkflow/fetchReviewTasks',
  async (params: ReviewTaskFilters) => {
    const response = await dataWorkflowApi.getReviewTasks(params)
    return response
  }
)

// 审核任务
export const reviewTask = createAsyncThunk(
  'dataWorkflow/reviewTask',
  async ({ taskId, action }: { taskId: number; action: ReviewAction }) => {
    await dataWorkflowApi.reviewTask(taskId, action)
    return { taskId, action: action.action }
  }
)

// 删除审核任务
export const deleteReviewTask = createAsyncThunk(
  'dataWorkflow/deleteReviewTask',
  async (taskId: number) => {
    await dataWorkflowApi.deleteReviewTask(taskId)
    return taskId
  }
)

// ========== Slice ==========

const dataWorkflowSlice = createSlice({
  name: 'dataWorkflow',
  initialState,
  reducers: {
    // Tab 切换
    setActiveTab: (state, action: PayloadAction<WorkflowTab>) => {
      state.activeTab = action.payload
    },

    // Worker 面板折叠
    toggleWorkersPanelCollapsed: (state) => {
      state.workersPanelCollapsed = !state.workersPanelCollapsed
    },

    // OCR 筛选
    setOCRFilters: (state, action: PayloadAction<Partial<OCRTaskFilters>>) => {
      state.ocrFilters = { ...state.ocrFilters, ...action.payload }
    },

    setOCRPage: (state, action: PayloadAction<number>) => {
      state.ocrFilters.page = action.payload
    },

    setOCRSelectedKeys: (state, action: PayloadAction<number[]>) => {
      state.ocrSelectedKeys = action.payload
    },

    clearOCRSelectedKeys: (state) => {
      state.ocrSelectedKeys = []
    },

    // 审核筛选
    setReviewFilters: (state, action: PayloadAction<Partial<ReviewTaskFilters>>) => {
      state.reviewFilters = { ...state.reviewFilters, ...action.payload }
    },

    setReviewPage: (state, action: PayloadAction<number>) => {
      state.reviewFilters.page = action.payload
    },

    // 审核弹窗
    showReviewModal: (state, action: PayloadAction<{ task: ReviewTaskItem; action: 'approve' | 'reject' }>) => {
      state.currentReviewTask = action.payload.task
      state.reviewAction = action.payload.action
      state.reviewModalVisible = true
    },

    hideReviewModal: (state) => {
      state.reviewModalVisible = false
      state.currentReviewTask = null
      state.reviewAction = null
    },

    // ========== WebSocket 实时更新 ==========

    // 设置 WebSocket 连接状态
    setWsConnected: (state, action: PayloadAction<WSConnectionStatus>) => {
      state.wsConnected = action.payload
    },

    // 直接更新统计数据（来自 WebSocket）
    updateStats: (state, action: PayloadAction<WorkflowStats>) => {
      state.stats = action.payload
    },

    // 直接更新 Worker 列表（来自 WebSocket）
    updateWorkers: (state, action: PayloadAction<WorkerInfo[]>) => {
      state.workers = action.payload
    },

    // 更新单个 OCR 任务状态
    updateOCRTask: (state, action: PayloadAction<Partial<OCRTaskItem> & { pending_id: number }>) => {
      const { pending_id, ...updates } = action.payload
      const task = state.ocrTasks.find((t) => t.pending_id === pending_id)
      if (task) {
        Object.assign(task, updates)
      }
    },

    // 更新任务进度
    updateTaskProgress: (state, action: PayloadAction<OCRProgressInfo>) => {
      state.taskProgress[action.payload.pending_id] = action.payload
    },

    // 清除任务进度（任务完成/失败时）
    clearTaskProgress: (state, action: PayloadAction<number>) => {
      delete state.taskProgress[action.payload]
    },

    // 追加 Worker 日志
    appendWorkerLog: (state, action: PayloadAction<WorkerLogItem>) => {
      state.workerLogs.push(action.payload)
      // 限制日志条数
      if (state.workerLogs.length > MAX_LOG_ENTRIES) {
        state.workerLogs = state.workerLogs.slice(-MAX_LOG_ENTRIES)
      }
    },

    // 清除所有日志
    clearWorkerLogs: (state) => {
      state.workerLogs = []
    },

    // 日志面板折叠状态
    toggleLogsPanelCollapsed: (state) => {
      state.logsPanelCollapsed = !state.logsPanelCollapsed
    },
  },
  extraReducers: (builder) => {
    // 统计数据
    builder
      .addCase(fetchWorkflowStats.pending, (state) => {
        state.statsLoading = true
        state.statsError = null
      })
      .addCase(fetchWorkflowStats.fulfilled, (state, action) => {
        state.statsLoading = false
        state.stats = action.payload
      })
      .addCase(fetchWorkflowStats.rejected, (state, action) => {
        state.statsLoading = false
        state.statsError = action.error.message || '获取统计数据失败'
      })

    // Worker 列表
    builder
      .addCase(fetchWorkers.pending, (state) => {
        state.workersLoading = true
      })
      .addCase(fetchWorkers.fulfilled, (state, action) => {
        state.workersLoading = false
        state.workers = action.payload
      })
      .addCase(fetchWorkers.rejected, (state) => {
        state.workersLoading = false
      })

    // OCR 任务列表
    builder
      .addCase(fetchOCRTasks.pending, (state) => {
        state.ocrTasksLoading = true
      })
      .addCase(fetchOCRTasks.fulfilled, (state, action) => {
        state.ocrTasksLoading = false
        state.ocrTasks = action.payload.items
        state.ocrTasksTotal = action.payload.total
      })
      .addCase(fetchOCRTasks.rejected, (state) => {
        state.ocrTasksLoading = false
      })

    // 重试 OCR 任务
    builder.addCase(retryOCRTask.fulfilled, (state, action) => {
      const task = state.ocrTasks.find((t) => t.pending_id === action.payload)
      if (task) {
        task.ocr_status = 'pending'
        task.ocr_retry_count = 0
        task.ocr_error_message = null
      }
    })

    // 批量重试
    builder.addCase(batchRetryOCRTasks.fulfilled, (state, action) => {
      action.payload.pendingIds.forEach((id) => {
        const task = state.ocrTasks.find((t) => t.pending_id === id)
        if (task) {
          task.ocr_status = 'pending'
          task.ocr_retry_count = 0
          task.ocr_error_message = null
        }
      })
      state.ocrSelectedKeys = []
    })

    // 跳过 OCR 任务
    builder.addCase(skipOCRTask.fulfilled, (state, action) => {
      const task = state.ocrTasks.find((t) => t.pending_id === action.payload)
      if (task) {
        task.ocr_status = 'skipped'
      }
    })

    // 设置优先级
    builder.addCase(setOCRTaskPriority.fulfilled, (state, action) => {
      const task = state.ocrTasks.find((t) => t.pending_id === action.payload.pendingId)
      if (task) {
        task.ocr_priority = action.payload.priority
      }
    })

    // 删除 OCR 任务
    builder.addCase(deleteOCRTask.fulfilled, (state, action) => {
      state.ocrTasks = state.ocrTasks.filter((t) => t.pending_id !== action.payload)
      state.ocrTasksTotal -= 1
    })

    // 审核任务列表
    builder
      .addCase(fetchReviewTasks.pending, (state) => {
        state.reviewTasksLoading = true
      })
      .addCase(fetchReviewTasks.fulfilled, (state, action) => {
        state.reviewTasksLoading = false
        state.reviewTasks = action.payload.items
        state.reviewTasksTotal = action.payload.total
      })
      .addCase(fetchReviewTasks.rejected, (state) => {
        state.reviewTasksLoading = false
      })

    // 审核任务
    builder.addCase(reviewTask.fulfilled, (state, action) => {
      const task = state.reviewTasks.find((t) => t.id === action.payload.taskId)
      if (task) {
        task.status = action.payload.action === 'approve' ? 'approved' : 'rejected'
      }
      state.reviewModalVisible = false
      state.currentReviewTask = null
      state.reviewAction = null
    })

    // 删除审核任务
    builder.addCase(deleteReviewTask.fulfilled, (state, action) => {
      state.reviewTasks = state.reviewTasks.filter((t) => t.id !== action.payload)
      state.reviewTasksTotal -= 1
    })
  },
})

// ========== Actions ==========

export const {
  setActiveTab,
  toggleWorkersPanelCollapsed,
  setOCRFilters,
  setOCRPage,
  setOCRSelectedKeys,
  clearOCRSelectedKeys,
  setReviewFilters,
  setReviewPage,
  showReviewModal,
  hideReviewModal,
  // WebSocket 相关
  setWsConnected,
  updateStats,
  updateWorkers,
  updateOCRTask,
  updateTaskProgress,
  clearTaskProgress,
  appendWorkerLog,
  clearWorkerLogs,
  toggleLogsPanelCollapsed,
} = dataWorkflowSlice.actions

// ========== Selectors ==========

export const selectWorkflowStats = (state: RootState) => state.dataWorkflow.stats
export const selectStatsLoading = (state: RootState) => state.dataWorkflow.statsLoading

export const selectWorkers = (state: RootState) => state.dataWorkflow.workers
export const selectWorkersLoading = (state: RootState) => state.dataWorkflow.workersLoading
export const selectWorkersPanelCollapsed = (state: RootState) => state.dataWorkflow.workersPanelCollapsed

export const selectOCRTasks = (state: RootState) => state.dataWorkflow.ocrTasks
export const selectOCRTasksTotal = (state: RootState) => state.dataWorkflow.ocrTasksTotal
export const selectOCRTasksLoading = (state: RootState) => state.dataWorkflow.ocrTasksLoading
export const selectOCRFilters = (state: RootState) => state.dataWorkflow.ocrFilters
export const selectOCRSelectedKeys = (state: RootState) => state.dataWorkflow.ocrSelectedKeys

export const selectReviewTasks = (state: RootState) => state.dataWorkflow.reviewTasks
export const selectReviewTasksTotal = (state: RootState) => state.dataWorkflow.reviewTasksTotal
export const selectReviewTasksLoading = (state: RootState) => state.dataWorkflow.reviewTasksLoading
export const selectReviewFilters = (state: RootState) => state.dataWorkflow.reviewFilters
export const selectCurrentReviewTask = (state: RootState) => state.dataWorkflow.currentReviewTask
export const selectReviewModalVisible = (state: RootState) => state.dataWorkflow.reviewModalVisible
export const selectReviewAction = (state: RootState) => state.dataWorkflow.reviewAction

export const selectActiveTab = (state: RootState) => state.dataWorkflow.activeTab

// WebSocket 相关
export const selectWsConnected = (state: RootState) => state.dataWorkflow.wsConnected
export const selectTaskProgress = (state: RootState) => state.dataWorkflow.taskProgress
export const selectWorkerLogs = (state: RootState) => state.dataWorkflow.workerLogs
export const selectLogsPanelCollapsed = (state: RootState) => state.dataWorkflow.logsPanelCollapsed

// 获取单个任务的进度
export const selectTaskProgressById = (pendingId: number) => (state: RootState) =>
  state.dataWorkflow.taskProgress[pendingId]

export default dataWorkflowSlice.reducer
