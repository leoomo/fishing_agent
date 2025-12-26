/**
 * 数据处理工作流页面
 *
 * 整合 OCR Worker 和待审核装备管理
 */

import React, { useEffect, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Typography, Button, Card, Tabs, Space, Select, message } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import type { AppDispatch } from '../../store/store'
import type { WorkflowTab, OCRStatus, ReviewStatus } from '../../types/dataWorkflow'

// 组件
import WorkflowPipeline from './components/WorkflowPipeline'
import WorkerMonitorPanel from './components/WorkerMonitorPanel'
import OCRTaskList from './components/OCRTaskList'
import ReviewTaskList from './components/ReviewTaskList'

// Redux
import {
  fetchWorkflowStats,
  fetchWorkers,
  fetchOCRTasks,
  fetchReviewTasks,
  retryOCRTask,
  batchRetryOCRTasks,
  skipOCRTask,
  setOCRTaskPriority,
  deleteOCRTask,
  reviewTask,
  deleteReviewTask,
  setActiveTab,
  toggleWorkersPanelCollapsed,
  setOCRFilters,
  setOCRSelectedKeys,
  setReviewFilters,
  showReviewModal,
  hideReviewModal,
  // Selectors
  selectWorkflowStats,
  selectStatsLoading,
  selectWorkers,
  selectWorkersLoading,
  selectWorkersPanelCollapsed,
  selectOCRTasks,
  selectOCRTasksTotal,
  selectOCRTasksLoading,
  selectOCRFilters,
  selectOCRSelectedKeys,
  selectReviewTasks,
  selectReviewTasksTotal,
  selectReviewTasksLoading,
  selectReviewFilters,
  selectCurrentReviewTask,
  selectReviewModalVisible,
  selectReviewAction,
  selectActiveTab,
} from '../../store/slices/dataWorkflowSlice'

const { Title } = Typography

const DataWorkflowPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()

  // Stats
  const stats = useSelector(selectWorkflowStats)
  const statsLoading = useSelector(selectStatsLoading)

  // Workers
  const workers = useSelector(selectWorkers)
  const workersLoading = useSelector(selectWorkersLoading)
  const workersPanelCollapsed = useSelector(selectWorkersPanelCollapsed)

  // OCR Tasks
  const ocrTasks = useSelector(selectOCRTasks)
  const ocrTasksTotal = useSelector(selectOCRTasksTotal)
  const ocrTasksLoading = useSelector(selectOCRTasksLoading)
  const ocrFilters = useSelector(selectOCRFilters)
  const ocrSelectedKeys = useSelector(selectOCRSelectedKeys)

  // Review Tasks
  const reviewTasks = useSelector(selectReviewTasks)
  const reviewTasksTotal = useSelector(selectReviewTasksTotal)
  const reviewTasksLoading = useSelector(selectReviewTasksLoading)
  const reviewFilters = useSelector(selectReviewFilters)
  const currentReviewTask = useSelector(selectCurrentReviewTask)
  const reviewModalVisible = useSelector(selectReviewModalVisible)
  const reviewAction = useSelector(selectReviewAction)

  // Active Tab
  const activeTab = useSelector(selectActiveTab)

  // 初始化数据
  useEffect(() => {
    dispatch(fetchWorkflowStats())
    dispatch(fetchWorkers())
    dispatch(fetchOCRTasks(ocrFilters))
    dispatch(fetchReviewTasks(reviewFilters))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // 刷新所有数据
  const handleRefresh = useCallback(() => {
    dispatch(fetchWorkflowStats())
    dispatch(fetchWorkers())
    if (activeTab === 'ocr') {
      dispatch(fetchOCRTasks(ocrFilters))
    } else if (activeTab === 'review') {
      dispatch(fetchReviewTasks(reviewFilters))
    }
    message.success('已刷新')
  }, [dispatch, activeTab, ocrFilters, reviewFilters])

  // Tab 切换
  const handleTabChange = (key: string) => {
    dispatch(setActiveTab(key as WorkflowTab))
    if (key === 'ocr') {
      dispatch(fetchOCRTasks(ocrFilters))
    } else if (key === 'review') {
      dispatch(fetchReviewTasks(reviewFilters))
    }
  }

  // 从 Pipeline 点击跳转
  const handlePipelineStageClick = (tab: WorkflowTab) => {
    dispatch(setActiveTab(tab))
    if (tab === 'ocr') {
      dispatch(fetchOCRTasks(ocrFilters))
    } else if (tab === 'review') {
      dispatch(fetchReviewTasks(reviewFilters))
    }
  }

  // ========== OCR 操作 ==========

  const handleOCRStatusFilterChange = (value: OCRStatus | undefined) => {
    const newFilters = { ...ocrFilters, ocr_status: value, page: 1 }
    dispatch(setOCRFilters(newFilters))
    dispatch(fetchOCRTasks(newFilters))
  }

  const handleOCRPageChange = (page: number, pageSize: number) => {
    const newFilters = { ...ocrFilters, page, page_size: pageSize }
    dispatch(setOCRFilters(newFilters))
    dispatch(fetchOCRTasks(newFilters))
  }

  const handleOCRRetry = async (pendingId: number) => {
    const result = await dispatch(retryOCRTask(pendingId))
    if (retryOCRTask.fulfilled.match(result)) {
      message.success('任务已重新加入队列')
      dispatch(fetchWorkflowStats())
    } else {
      message.error('重试失败')
    }
  }

  const handleOCRBatchRetry = async (pendingIds: number[]) => {
    if (pendingIds.length === 0) {
      message.warning('请先选择要重试的任务')
      return
    }
    const result = await dispatch(batchRetryOCRTasks(pendingIds))
    if (batchRetryOCRTasks.fulfilled.match(result)) {
      message.success(`成功重试 ${result.payload.affectedCount} 个任务`)
      dispatch(fetchWorkflowStats())
    } else {
      message.error('批量重试失败')
    }
  }

  const handleOCRSkip = async (pendingId: number) => {
    const result = await dispatch(skipOCRTask(pendingId))
    if (skipOCRTask.fulfilled.match(result)) {
      message.success('任务已跳过')
      dispatch(fetchWorkflowStats())
    } else {
      message.error('跳过失败')
    }
  }

  const handleOCRSetPriority = async (pendingId: number, priority: number) => {
    const result = await dispatch(setOCRTaskPriority({ pendingId, priority }))
    if (setOCRTaskPriority.fulfilled.match(result)) {
      message.success('优先级已更新')
    } else {
      message.error('设置优先级失败')
    }
  }

  const handleOCRDelete = async (pendingId: number) => {
    const result = await dispatch(deleteOCRTask(pendingId))
    if (deleteOCRTask.fulfilled.match(result)) {
      message.success('任务已删除')
      dispatch(fetchWorkflowStats())
    } else {
      message.error('删除失败')
    }
  }

  // ========== 审核操作 ==========

  const handleReviewStatusFilterChange = (value: ReviewStatus | undefined) => {
    const newFilters = { ...reviewFilters, status: value, page: 1 }
    dispatch(setReviewFilters(newFilters))
    dispatch(fetchReviewTasks(newFilters))
  }

  const handleReviewPageChange = (page: number, pageSize: number) => {
    const newFilters = { ...reviewFilters, page, page_size: pageSize }
    dispatch(setReviewFilters(newFilters))
    dispatch(fetchReviewTasks(newFilters))
  }

  const handleReview = async (
    taskId: number,
    action: { action: 'approve' | 'reject'; review_notes?: string }
  ) => {
    const result = await dispatch(reviewTask({ taskId, action }))
    if (reviewTask.fulfilled.match(result)) {
      message.success(`任务已${action.action === 'approve' ? '通过' : '拒绝'}`)
      dispatch(fetchWorkflowStats())
      dispatch(fetchReviewTasks(reviewFilters))
    } else {
      message.error('操作失败')
    }
  }

  const handleReviewDelete = async (taskId: number) => {
    const result = await dispatch(deleteReviewTask(taskId))
    if (deleteReviewTask.fulfilled.match(result)) {
      message.success('任务已删除')
      dispatch(fetchWorkflowStats())
    } else {
      message.error('删除失败')
    }
  }

  // Tab items
  const tabItems = [
    {
      key: 'ocr',
      label: (
        <span>
          OCR处理
          {stats && (
            <span style={{ marginLeft: 4, color: '#999' }}>
              ({stats.ocr_pending + stats.ocr_processing})
            </span>
          )}
        </span>
      ),
      children: (
        <>
          {/* OCR 筛选器 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Space>
              <span>状态筛选:</span>
              <Select
                style={{ width: 150 }}
                placeholder="全部状态"
                allowClear
                value={ocrFilters.ocr_status}
                onChange={handleOCRStatusFilterChange}
                options={[
                  { value: 'pending', label: '待处理' },
                  { value: 'processing', label: '处理中' },
                  { value: 'completed', label: '已完成' },
                  { value: 'failed', label: '失败' },
                  { value: 'skipped', label: '跳过' },
                ]}
              />
            </Space>
          </Card>

          {/* OCR 任务列表 */}
          <Card>
            <OCRTaskList
              tasks={ocrTasks}
              total={ocrTasksTotal}
              loading={ocrTasksLoading}
              page={ocrFilters.page || 1}
              pageSize={ocrFilters.page_size || 20}
              selectedKeys={ocrSelectedKeys}
              onPageChange={handleOCRPageChange}
              onSelectChange={(keys) => dispatch(setOCRSelectedKeys(keys))}
              onRetry={handleOCRRetry}
              onBatchRetry={handleOCRBatchRetry}
              onSkip={handleOCRSkip}
              onSetPriority={handleOCRSetPriority}
              onDelete={handleOCRDelete}
            />
          </Card>
        </>
      ),
    },
    {
      key: 'review',
      label: (
        <span>
          待审核
          {stats && (
            <span style={{ marginLeft: 4, color: '#999' }}>({stats.review_pending})</span>
          )}
        </span>
      ),
      children: (
        <>
          {/* 审核筛选器 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Space>
              <span>状态筛选:</span>
              <Select
                style={{ width: 150 }}
                placeholder="全部状态"
                allowClear
                value={reviewFilters.status}
                onChange={handleReviewStatusFilterChange}
                options={[
                  { value: 'pending', label: '待审核' },
                  { value: 'approved', label: '已通过' },
                  { value: 'rejected', label: '已拒绝' },
                ]}
              />
            </Space>
          </Card>

          {/* 审核任务列表 */}
          <Card>
            <ReviewTaskList
              tasks={reviewTasks}
              total={reviewTasksTotal}
              loading={reviewTasksLoading}
              page={reviewFilters.page || 1}
              pageSize={reviewFilters.page_size || 20}
              onPageChange={handleReviewPageChange}
              onReview={handleReview}
              onDelete={handleReviewDelete}
              currentTask={currentReviewTask}
              modalVisible={reviewModalVisible}
              reviewAction={reviewAction}
              onShowReviewModal={(task, action) =>
                dispatch(showReviewModal({ task, action }))
              }
              onHideReviewModal={() => dispatch(hideReviewModal())}
            />
          </Card>
        </>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div
        style={{
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          数据处理工作流
        </Title>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleRefresh}
          loading={statsLoading}
        >
          刷新
        </Button>
      </div>

      {/* 工作流管道 */}
      <div style={{ marginBottom: 16 }}>
        <WorkflowPipeline
          stats={stats}
          loading={statsLoading}
          onStageClick={handlePipelineStageClick}
        />
      </div>

      {/* Worker 监控面板 */}
      <div style={{ marginBottom: 16 }}>
        <WorkerMonitorPanel
          workers={workers}
          stats={stats}
          loading={workersLoading}
          collapsed={workersPanelCollapsed}
          onToggleCollapse={() => dispatch(toggleWorkersPanelCollapsed())}
        />
      </div>

      {/* 任务列表 Tabs */}
      <Tabs activeKey={activeTab} onChange={handleTabChange} items={tabItems} />
    </div>
  )
}

export default DataWorkflowPage
