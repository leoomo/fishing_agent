import React, { useEffect, useRef, useCallback } from 'react'
import {
  Row,
  Col,
  Empty,
  Spin,
  Checkbox,
  Button,
  Space,
  Typography,
  Alert,
  Pagination,
  Card,
} from 'antd'
import {
  AppstoreOutlined,
  TableOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { message } from 'antd'

import type { CrawlerTask } from '../../types/crawler'
import type { AppDispatch } from '../../store/store'
import {
  selectTasks,
  selectPagination,
  selectLoading,
  selectSelectedTasks,
  fetchTasks,
  setPagination,
  selectAllTasks,
  clearSelection,
  bulkDeleteTasks,
  setViewMode,
  selectUI,
} from '../../store/slices/crawlerSlice'
import TaskCard from './TaskCard'

const { Text } = Typography

interface TaskListProps {
  filters?: any
  onRefresh?: () => void
}

const TaskList: React.FC<TaskListProps> = ({ filters, onRefresh }) => {
  const dispatch = useDispatch<AppDispatch>()

  // 选择器
  const tasks = useSelector(selectTasks)
  const pagination = useSelector(selectPagination)
  const loading = useSelector(selectLoading)
  const selectedTasks = useSelector(selectSelectedTasks)
  const ui = useSelector(selectUI)

  // 刷新任务列表的函数
  const refreshTasks = useCallback(() => {
    const params = {
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    }
    dispatch(fetchTasks(params))
  }, [dispatch, pagination.current, pagination.pageSize, filters])

  // 获取任务列表
  useEffect(() => {
    refreshTasks()
  }, [refreshTasks])

  // 自动刷新：检测是否有运行中或等待中的任务
  const hasActiveTasksRef = useRef(false)
  useEffect(() => {
    const hasActiveTasks = tasks.some(
      (task: CrawlerTask) => ['queued', 'running'].includes(task.status.toLowerCase())
    )
    hasActiveTasksRef.current = hasActiveTasks

    // 如果有活跃任务，每5秒刷新一次
    if (hasActiveTasks) {
      const intervalId = setInterval(() => {
        if (hasActiveTasksRef.current) {
          refreshTasks()
        }
      }, 5000)

      return () => clearInterval(intervalId)
    }
  }, [tasks, refreshTasks])

  // 处理页码变化
  const handlePageChange = (page: number, pageSize?: number) => {
    dispatch(setPagination({ current: page, pageSize }))
  }

  // 处理全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      dispatch(selectAllTasks())
    } else {
      dispatch(clearSelection())
    }
  }

  // 批量删除
  const handleBulkDelete = async () => {
    console.log('handleBulkDelete called with tasks:', selectedTasks)
    if (selectedTasks.length === 0) {
      message.warning('请选择要删除的任务')
      return
    }

    // 由于Modal.confirm在React 19 + Antd 5.x中的兼容性问题，暂时直接执行删除
    // 在实际生产环境中，可以考虑使用其他弹窗库或自定义确认组件
    const shouldDelete = window.confirm(`确定要删除选中的 ${selectedTasks.length} 个任务吗？此操作不可恢复。`)
    if (shouldDelete) {
      console.log('User confirmed bulk delete')
      try {
        await dispatch(bulkDeleteTasks(selectedTasks)).unwrap()
        message.success('批量删除成功')
      } catch (error: any) {
        console.error('批量删除失败:', error)
      }
    } else {
      console.log('User cancelled bulk delete')
    }
  }

  // 切换视图模式
  const handleViewModeChange = (mode: 'table' | 'card') => {
    dispatch(setViewMode(mode))
  }

  // 全选状态计算
  const isAllSelected = tasks.length > 0 && selectedTasks.length === tasks.length
  const isIndeterminate = selectedTasks.length > 0 && selectedTasks.length < tasks.length

  // 渲染加载状态
  if (loading.tasks && tasks.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">正在加载任务列表...</Text>
        </div>
      </div>
    )
  }

  // 渲染空状态
  if (tasks.length === 0 && !loading.tasks) {
    return (
      <Card>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无数据采集任务"
        >
          <Button type="primary" onClick={onRefresh}>
            刷新列表
          </Button>
        </Empty>
      </Card>
    )
  }

  return (
    <div>
      {/* 工具栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Checkbox
                indeterminate={isIndeterminate}
                checked={isAllSelected}
                onChange={(e) => handleSelectAll(e.target.checked)}
              >
                全选
              </Checkbox>
              {selectedTasks.length > 0 && (
                <>
                  <Text type="secondary">
                    已选择 {selectedTasks.length} 项
                  </Text>
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={handleBulkDelete}
                    loading={loading.bulkOperations}
                  >
                    批量删除
                  </Button>
                </>
              )}
            </Space>
          </Col>
          <Col>
            <Space>
              <Button.Group>
                <Button
                  type={ui.viewMode === 'card' ? 'primary' : 'default'}
                  icon={<AppstoreOutlined />}
                  onClick={() => handleViewModeChange('card')}
                >
                  卡片视图
                </Button>
                <Button
                  type={ui.viewMode === 'table' ? 'primary' : 'default'}
                  icon={<TableOutlined />}
                  onClick={() => handleViewModeChange('table')}
                >
                  表格视图
                </Button>
              </Button.Group>
              <Button
                icon={<ReloadOutlined />}
                onClick={onRefresh}
                loading={loading.tasks}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 错误提示 */}
      {loading.tasks && (
        <Alert
          message="正在加载任务列表..."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 任务列表 - 卡片视图 */}
      {ui.viewMode === 'card' && (
        <Row gutter={[16, 16]}>
          {tasks.map((task: CrawlerTask) => (
            <Col key={task.task_id} xs={24} sm={24} md={12} lg={8} xl={6}>
              <TaskCard
                task={task}
                isSelected={selectedTasks.includes(task.task_id)}
              />
            </Col>
          ))}
        </Row>
      )}

      {/* 任务列表 - 表格视图（简化版本） */}
      {ui.viewMode === 'table' && (
        <div>
          {tasks.map((task: CrawlerTask) => (
            <div key={task.task_id} style={{ marginBottom: 8 }}>
              <TaskCard
                task={task}
                isSelected={selectedTasks.includes(task.task_id)}
              />
            </div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {pagination.total > 0 && (
        <Card size="small" style={{ marginTop: 16 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Text type="secondary">
                共 {pagination.total} 条记录，当前显示第 {(pagination.current - 1) * pagination.pageSize + 1} -{' '}
                {Math.min(pagination.current * pagination.pageSize, pagination.total)} 条
              </Text>
            </Col>
            <Col>
              <Pagination
                current={pagination.current}
                pageSize={pagination.pageSize}
                total={pagination.total}
                showSizeChanger
                showQuickJumper
                showTotal={(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`}
                onChange={handlePageChange}
                onShowSizeChange={(current, size) => handlePageChange(current, size)}
              />
            </Col>
          </Row>
        </Card>
      )}
    </div>
  )
}

export default TaskList