/**
 * 采集任务 Tab 组件
 *
 * 整合原 Crawler 页面的功能到 DataWorkflow 页面
 */

import React, { useEffect, useCallback } from 'react'
import {
  Card,
  Button,
  Space,
  Form,
  Modal,
  message,
} from 'antd'
import {
  PlusOutlined,
  ReloadOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import { useAppDispatch, useAppSelector } from '../../../store/hooks'

import {
  fetchTasks,
  fetchTaskStats,
  createTask,
  showTaskForm,
  hideTaskForm,
  hideTaskDetail,
  clearAllErrors,
  selectTasks,
  selectLoading,
  selectErrors,
  selectFilters,
  selectUI,
  setFilters,
  clearFilters,
} from '../../../store/slices/crawlerSlice'

import TaskList from '../../../components/Crawler/TaskList'
import TaskForm from '../../../components/Crawler/TaskForm'
import TaskFiltersComponent from '../../../components/Crawler/TaskFilters'
import TaskDetail from '../../../components/Crawler/TaskDetail'
import { useWebSocket } from '@/hooks/useWebSocket'

interface CollectionTabProps {
  onRefresh?: () => void
}

const CollectionTab: React.FC<CollectionTabProps> = ({ onRefresh }) => {
  const dispatch = useAppDispatch()

  // 选择器
  const tasks = useAppSelector(selectTasks)
  const loading = useAppSelector(selectLoading)
  const errors = useAppSelector(selectErrors)
  const filters = useAppSelector(selectFilters)
  const ui = useAppSelector(selectUI)

  const [form] = Form.useForm()

  // WebSocket 实时状态更新
  useWebSocket(
    '/api/v1/admin/crawler/ws/crawler-status',
    {
      onMessage: (data) => {
        try {
          const message = JSON.parse(data)
          if (message.type === 'status_update') {
            // 直接分发 fulfilled action，避免触发 API 调用
            dispatch({
              type: 'crawler/fetchTasks/fulfilled',
              payload: {
                tasks: message.tasks,
                total: message.total,
              }
            })
            dispatch({
              type: 'crawler/fetchTaskStats/fulfilled',
              payload: message.stats
            })
          }
        } catch (e) {
          console.error('[Collection] WebSocket 消息解析失败:', e)
        }
      },
      onConnect: () => {
        console.log('[Collection] WebSocket 已连接')
        // 连接后立即获取一次初始数据
        dispatch(fetchTasks({}))
        dispatch(fetchTaskStats())
      },
      reconnect: true,
      heartbeat: true,
    }
  )

  // 错误处理
  useEffect(() => {
    if (errors.tasks) {
      message.error(errors.tasks)
      dispatch(clearAllErrors())
    }
    if (errors.stats) {
      message.error(errors.stats)
      dispatch(clearAllErrors())
    }
  }, [errors, dispatch])

  // 刷新数据
  const handleRefresh = useCallback(() => {
    dispatch(fetchTasks({}))
    dispatch(fetchTaskStats())
    onRefresh?.()
  }, [dispatch, onRefresh])

  // 显示创建任务表单
  const handleShowCreateTask = useCallback(() => {
    dispatch(showTaskForm())
  }, [dispatch])

  // 处理筛选
  const handleFilterChange = useCallback((newFilters: any) => {
    dispatch(setFilters(newFilters))
  }, [dispatch])

  // 清除筛选
  const handleClearFilters = useCallback(() => {
    dispatch(clearFilters())
  }, [dispatch])

  // 创建任务
  const handleCreateTask = useCallback(async (values: any) => {
    try {
      // 转换表单值为API期望的格式
      const requestData = {
        task_type: values.task_type,
        keywords: values.keywords
          ? values.keywords.split(/[,，]+/).map((k: string) => k.trim()).filter(Boolean)
          : undefined,
        max_pages: values.max_pages || 5,
        proxy: values.proxy || undefined,
        shop_url: values.shop_url || undefined,
      }
      await dispatch(createTask(requestData)).unwrap()
      dispatch(hideTaskForm())
      form.resetFields()
      handleRefresh()
    } catch (error) {
      // 错误已在slice中处理
    }
  }, [dispatch, form, handleRefresh])

  // 获取当前选中的任务
  const getCurrentTask = () => {
    if (!ui.selectedTaskId) return null
    return tasks.find(task => task.task_id === ui.selectedTaskId) || null
  }

  return (
    <>
      {/* 操作栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <Space>
            <Button
              icon={<FilterOutlined />}
              onClick={() => dispatch({ type: 'crawler/toggleFilters' })}
            >
              {ui.showFilters ? '隐藏筛选' : '显示筛选'}
            </Button>
          </Space>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={loading.tasks || loading.stats}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleShowCreateTask}
            >
              创建任务
            </Button>
          </Space>
        </Space>
      </Card>

      {/* 筛选器 */}
      {ui.showFilters && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <TaskFiltersComponent
            filters={filters}
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
          />
        </Card>
      )}

      {/* 任务列表 */}
      <Card>
        <TaskList
          filters={filters}
          onRefresh={handleRefresh}
        />
      </Card>

      {/* 创建任务表单弹窗 */}
      <Modal
        title="创建数据采集任务"
        open={ui.showTaskForm}
        onCancel={() => dispatch(hideTaskForm())}
        footer={null}
        width={600}
        forceRender
      >
        <TaskForm
          form={form}
          onSubmit={handleCreateTask}
          onCancel={() => dispatch(hideTaskForm())}
          loading={loading.createTask}
        />
      </Modal>

      {/* 任务详情弹窗 */}
      <TaskDetail
        visible={ui.showTaskDetail}
        task={getCurrentTask()}
        onClose={() => dispatch(hideTaskDetail())}
      />
    </>
  )
}

export default CollectionTab
