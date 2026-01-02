import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit'
import { message } from 'antd'
import { crawlerApi } from '../../api/services/crawler'
import type { CrawlerTask, TaskFilters, PaginationState, TaskStats } from '../../types/crawler'

// 登录状态类型
export type LoginStatus =
  | 'idle'
  | 'generating_qr'
  | 'qr_ready'
  | 'waiting_scan'
  | 'scan_detected'
  | 'verifying'
  | 'login_success'
  | 'login_failed'
  | 'qr_expired'

// 登录状态接口
export interface LoginState {
  taskId: number
  platform: 'taobao' | 'jd' | 'pdd' | 'other'
  status: LoginStatus
  qrCode?: string | null
  expiresAt?: number | null
  userInfo?: any | null
  errorMessage?: string | null
  platformName?: string
}

// Crawler状态接口
export interface CrawlerState {
  // 任务相关
  tasks: CrawlerTask[]
  currentTask: CrawlerTask | null
  selectedTasks: number[]

  // 分页和筛选
  pagination: PaginationState
  filters: TaskFilters

  // 统计数据
  stats: TaskStats | null

  // 加载状态
  loading: {
    tasks: boolean
    createTask: boolean
    deleteTask: boolean
    stats: boolean
    bulkOperations: boolean
    [key: string]: boolean
  }

  // 错误状态
  errors: {
    tasks: string | null
    createTask: string | null
    deleteTask: string | null
    stats: string | null
    [key: string]: string | null
  }

  // WebSocket连接状态
  wsConnections: Record<number, boolean>

  // 登录状态管理
  loginStates: Record<number, LoginState>

  // UI状态
  ui: {
    viewMode: 'table' | 'card'
    showFilters: boolean
    showTaskDetail: boolean
    showTaskForm: boolean
    selectedTaskId: number | null
  }
}

// 初始状态
const initialState: CrawlerState = {
  tasks: [],
  currentTask: null,
  selectedTasks: [],

  pagination: {
    current: 1,
    pageSize: 20,
    total: 0,
  },

  filters: {
    status: undefined,
    task_type: undefined,
    platform: undefined,
    date_range: undefined,
  },

  stats: null,

  loading: {
    tasks: false,
    createTask: false,
    deleteTask: false,
    stats: false,
    bulkOperations: false,
  },

  errors: {
    tasks: null,
    createTask: null,
    updateTask: null,
    deleteTask: null,
    stats: null,
  },

  wsConnections: {},
  loginStates: {},

  ui: {
    viewMode: 'card',
    showFilters: false,
    showTaskDetail: false,
    showTaskForm: false,
    selectedTaskId: null,
  },
}

// 异步Actions
export const fetchTasks = createAsyncThunk(
  'crawler/fetchTasks',
  async (params: { page?: number; pageSize?: number; filters?: TaskFilters }, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.listTasks({
        page: params.page || 1,
        page_size: params.pageSize || 20,
        ...params.filters,
      })
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取任务列表失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const createTask = createAsyncThunk(
  'crawler/createTask',
  async (taskData: any, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.triggerCrawler(taskData)
      message.success('任务创建成功')
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '创建任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const deleteTask = createAsyncThunk(
  'crawler/deleteTask',
  async (taskId: number, { rejectWithValue }) => {
    try {
      await crawlerApi.deleteTask(taskId)
      message.success('任务删除成功')
      return taskId
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '删除任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const retryTask = createAsyncThunk(
  'crawler/retryTask',
  async (taskId: number, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.retryTask(taskId)
      message.success('任务重试成功')
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '重试任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const rerunTask = createAsyncThunk(
  'crawler/rerunTask',
  async (taskId: number, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.rerunTask(taskId)
      message.success('任务已重新运行')
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '重新运行任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const startTask = createAsyncThunk(
  'crawler/startTask',
  async (taskId: number, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.startTask(taskId)
      message.success('任务启动成功')
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '启动任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const stopTask = createAsyncThunk(
  'crawler/stopTask',
  async (taskId: number, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.stopTask(taskId)
      message.success('任务已停止')
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '停止任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const updateTask = createAsyncThunk(
  'crawler/updateTask',
  async ({ taskId, taskData }: { taskId: number; taskData: Partial<CrawlerTask> }, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.updateTask(taskId, taskData)
      message.success('任务更新成功')
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '更新任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const fetchTaskStats = createAsyncThunk(
  'crawler/fetchTaskStats',
  async (_, { rejectWithValue }) => {
    try {
      const response = await crawlerApi.getSyncStatus()
      return response
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '获取统计数据失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

export const bulkDeleteTasks = createAsyncThunk(
  'crawler/bulkDeleteTasks',
  async (taskIds: number[], { rejectWithValue }) => {
    try {
      // 这里假设有批量删除API，如果没有就逐个删除
      const promises = taskIds.map(id => crawlerApi.deleteTask(id))
      await Promise.all(promises)
      message.success(`成功删除 ${taskIds.length} 个任务`)
      return taskIds
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '批量删除任务失败'
      message.error(errorMessage)
      return rejectWithValue(errorMessage)
    }
  }
)

// Slice定义
const crawlerSlice = createSlice({
  name: 'crawler',
  initialState,
  reducers: {
    // UI状态管理
    setViewMode: (state, action: PayloadAction<'table' | 'card'>) => {
      state.ui.viewMode = action.payload
    },

    toggleFilters: (state) => {
      state.ui.showFilters = !state.ui.showFilters
    },

    setFilters: (state, action: PayloadAction<Partial<TaskFilters>>) => {
      state.filters = { ...state.filters, ...action.payload }
      state.pagination.current = 1 // 重置到第一页
    },

    clearFilters: (state) => {
      state.filters = {}
      state.pagination.current = 1
    },

    setPagination: (state, action: PayloadAction<Partial<PaginationState>>) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },

    // 任务选择管理
    setSelectedTasks: (state, action: PayloadAction<number[]>) => {
      state.selectedTasks = action.payload
    },

    toggleTaskSelection: (state, action: PayloadAction<number>) => {
      const taskId = action.payload
      const index = state.selectedTasks.indexOf(taskId)
      if (index > -1) {
        state.selectedTasks.splice(index, 1)
      } else {
        state.selectedTasks.push(taskId)
      }
    },

    selectAllTasks: (state) => {
      state.selectedTasks = state.tasks.map(task => task.task_id)
    },

    clearSelection: (state) => {
      state.selectedTasks = []
    },

    // 任务详情管理
    setCurrentTask: (state, action: PayloadAction<CrawlerTask | null>) => {
      state.currentTask = action.payload
    },

    showTaskDetail: (state, action: PayloadAction<number>) => {
      state.ui.selectedTaskId = action.payload
      state.ui.showTaskDetail = true
    },

    hideTaskDetail: (state) => {
      state.ui.showTaskDetail = false
      state.ui.selectedTaskId = null
    },

    showTaskForm: (state) => {
      state.ui.showTaskForm = true
    },

    hideTaskForm: (state) => {
      state.ui.showTaskForm = false
    },

    // WebSocket连接管理
    setWSConnectionStatus: (state, action: PayloadAction<{ taskId: number; connected: boolean }>) => {
      const { taskId, connected } = action.payload
      state.wsConnections[taskId] = connected
    },

    clearWSConnection: (state, action: PayloadAction<number>) => {
      delete state.wsConnections[action.payload]
    },

    // 任务状态更新（通过WebSocket）
    updateTaskStatus: (state, action: PayloadAction<{ taskId: number; updates: Partial<CrawlerTask> }>) => {
      const { taskId, updates } = action.payload
      const taskIndex = state.tasks.findIndex(task => task.task_id === taskId)
      if (taskIndex > -1) {
        state.tasks[taskIndex] = { ...state.tasks[taskIndex], ...updates }
      }

      // 如果是当前任务，也更新currentTask
      if (state.currentTask?.task_id === taskId) {
        state.currentTask = { ...state.currentTask, ...updates }
      }
    },

    // 登录状态管理
    setLoginState: (state, action: PayloadAction<{ taskId: number; loginState: LoginState }>) => {
      const { taskId, loginState } = action.payload
      state.loginStates[taskId] = loginState
    },

    updateLoginStatus: (state, action: PayloadAction<{ taskId: number; status: LoginStatus; data?: any }>) => {
      const { taskId, status, data } = action.payload
      if (state.loginStates[taskId]) {
        state.loginStates[taskId] = {
          ...state.loginStates[taskId],
          status,
          ...data,
        }
      }
    },

    clearLoginState: (state, action: PayloadAction<number>) => {
      delete state.loginStates[action.payload]
    },

    clearAllLoginStates: (state) => {
      state.loginStates = {}
    },

    // 错误管理
    clearError: (state, action: PayloadAction<string>) => {
      state.errors[action.payload] = null
    },

    clearAllErrors: (state) => {
      Object.keys(state.errors).forEach(key => {
        state.errors[key] = null
      })
    },

    // 重置状态
    resetCrawlerState: () => initialState,
  },

  extraReducers: (builder) => {
    // fetchTasks
    builder
      .addCase(fetchTasks.pending, (state) => {
        state.loading.tasks = true
        state.errors.tasks = null
      })
      .addCase(fetchTasks.fulfilled, (state, action) => {
        state.loading.tasks = false
        state.tasks = action.payload.tasks
        state.pagination.total = action.payload.total
      })
      .addCase(fetchTasks.rejected, (state, action) => {
        state.loading.tasks = false
        state.errors.tasks = action.payload as string
      })

    // createTask
    builder
      .addCase(createTask.pending, (state) => {
        state.loading.createTask = true
        state.errors.createTask = null
      })
      .addCase(createTask.fulfilled, (state, action) => {
        state.loading.createTask = false
        state.tasks.unshift(action.payload)
        state.pagination.total += 1
        state.ui.showTaskForm = false
      })
      .addCase(createTask.rejected, (state, action) => {
        state.loading.createTask = false
        state.errors.createTask = action.payload as string
      })

    // deleteTask
    builder
      .addCase(deleteTask.pending, (state) => {
        state.loading.deleteTask = true
        state.errors.deleteTask = null
      })
      .addCase(deleteTask.fulfilled, (state, action) => {
        state.loading.deleteTask = false
        const taskId = action.payload
        state.tasks = state.tasks.filter(task => task.task_id !== taskId)
        state.selectedTasks = state.selectedTasks.filter(id => id !== taskId)
        state.pagination.total = Math.max(0, state.pagination.total - 1)

        // 如果删除的是当前任务，关闭详情
        if (state.ui.selectedTaskId === taskId) {
          state.ui.showTaskDetail = false
          state.ui.selectedTaskId = null
        }
      })
      .addCase(deleteTask.rejected, (state, action) => {
        state.loading.deleteTask = false
        state.errors.deleteTask = action.payload as string
      })

    // retryTask
    builder
      .addCase(retryTask.fulfilled, (state, action) => {
        const updatedTask = action.payload
        const taskIndex = state.tasks.findIndex(task => task.task_id === updatedTask.task_id)
        if (taskIndex > -1) {
          state.tasks[taskIndex] = updatedTask
        }
      })

    // rerunTask
    builder
      .addCase(rerunTask.fulfilled, (state, action) => {
        const updatedTask = action.payload
        const taskIndex = state.tasks.findIndex(task => task.task_id === updatedTask.task_id)
        if (taskIndex > -1) {
          state.tasks[taskIndex] = updatedTask
        }
      })

    // startTask
    builder
      .addCase(startTask.fulfilled, (state, action) => {
        const updatedTask = action.payload
        const taskIndex = state.tasks.findIndex(task => task.task_id === updatedTask.task_id)
        if (taskIndex > -1) {
          state.tasks[taskIndex] = updatedTask
        }
      })

    // stopTask
    builder
      .addCase(stopTask.fulfilled, (state, action) => {
        const updatedTask = action.payload
        const taskIndex = state.tasks.findIndex(task => task.task_id === updatedTask.task_id)
        if (taskIndex > -1) {
          state.tasks[taskIndex] = updatedTask
        }
      })

    // updateTask
    builder
      .addCase(updateTask.pending, (state) => {
        state.loading.updateTask = true
        state.errors.updateTask = null
      })
      .addCase(updateTask.fulfilled, (state, action) => {
        state.loading.updateTask = false
        const updatedTask = action.payload
        const taskIndex = state.tasks.findIndex(task => task.task_id === updatedTask.task_id)
        if (taskIndex > -1) {
          state.tasks[taskIndex] = updatedTask
        }
      })
      .addCase(updateTask.rejected, (state, action) => {
        state.loading.updateTask = false
        state.errors.updateTask = action.payload as string
      })

    // fetchTaskStats
    builder
      .addCase(fetchTaskStats.pending, (state) => {
        state.loading.stats = true
        state.errors.stats = null
      })
      .addCase(fetchTaskStats.fulfilled, (state, action) => {
        state.loading.stats = false
        // 转换 SyncStatus 到 TaskStats
        const syncStatus = action.payload
        state.stats = {
          total_tasks: syncStatus.total_tasks || 0,
          pending_tasks: syncStatus.pending_tasks || 0,
          running_tasks: syncStatus.running_tasks || 0,
          success_tasks: syncStatus.success_tasks || 0,
          failed_tasks: syncStatus.failed_tasks || 0,
          cancelled_tasks: 0,
          paused_tasks: 0,
          last_sync_time: syncStatus.last_sync_time,
        }
      })
      .addCase(fetchTaskStats.rejected, (state, action) => {
        state.loading.stats = false
        state.errors.stats = action.payload as string
      })

    // bulkDeleteTasks
    builder
      .addCase(bulkDeleteTasks.pending, (state) => {
        state.loading.bulkOperations = true
      })
      .addCase(bulkDeleteTasks.fulfilled, (state, action) => {
        state.loading.bulkOperations = false
        const deletedIds = action.payload
        state.tasks = state.tasks.filter(task => !deletedIds.includes(task.task_id))
        state.selectedTasks = []
        state.pagination.total = Math.max(0, state.pagination.total - deletedIds.length)
      })
      .addCase(bulkDeleteTasks.rejected, (state) => {
        state.loading.bulkOperations = false
      })
  },
})

// 导出Actions
export const {
  setViewMode,
  toggleFilters,
  setFilters,
  clearFilters,
  setPagination,
  setSelectedTasks,
  toggleTaskSelection,
  selectAllTasks,
  clearSelection,
  setCurrentTask,
  showTaskDetail,
  hideTaskDetail,
  showTaskForm,
  hideTaskForm,
  setWSConnectionStatus,
  clearWSConnection,
  updateTaskStatus,
  setLoginState,
  updateLoginStatus,
  clearLoginState,
  clearAllLoginStates,
  clearError,
  clearAllErrors,
  resetCrawlerState,
} = crawlerSlice.actions

// 导出Reducer
export default crawlerSlice.reducer

// 选择器
export const selectCrawlerState = (state: { crawler: CrawlerState }) => state.crawler

export const selectTasks = (state: { crawler: CrawlerState }) => state.crawler.tasks

export const selectCurrentTask = (state: { crawler: CrawlerState }) => state.crawler.currentTask

export const selectSelectedTasks = (state: { crawler: CrawlerState }) => state.crawler.selectedTasks

export const selectPagination = (state: { crawler: CrawlerState }) => state.crawler.pagination

export const selectFilters = (state: { crawler: CrawlerState }) => state.crawler.filters

export const selectStats = (state: { crawler: CrawlerState }) => state.crawler.stats

export const selectLoading = (state: { crawler: CrawlerState }) => state.crawler.loading

export const selectErrors = (state: { crawler: CrawlerState }) => state.crawler.errors

export const selectUI = (state: { crawler: CrawlerState }) => state.crawler.ui

export const selectLoginStates = (state: { crawler: CrawlerState }) => state.crawler.loginStates

export const selectLoginStateByTaskId = (taskId: number) => (state: { crawler: CrawlerState }) =>
  state.crawler.loginStates[taskId]

export const selectWSConnections = (state: { crawler: CrawlerState }) => state.crawler.wsConnections