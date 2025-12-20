import React, { useEffect, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Space,
  Typography,
  Alert,
  Spin,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
} from 'antd'
import {
  PlusOutlined,
  ReloadOutlined,
  SyncOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'

import {
  fetchTasks,
  fetchTaskStats,
  createTask,
  showTaskForm,
  hideTaskForm,
  clearAllErrors,
  selectTasks,
  selectStats,
  selectLoading,
  selectErrors,
  selectFilters,
  selectUI,
  setFilters,
  clearFilters,
  resetCrawlerState,
} from '../../store/slices/crawlerSlice'

import TaskList from '../../components/Crawler/TaskList'
import TaskForm from '../../components/Crawler/TaskForm'
import TaskFilters from '../../components/Crawler/TaskFilters'

const { Title, Text } = Typography
const { Option } = Select

const CrawlerPage: React.FC = () => {
  const dispatch = useDispatch()

  // 选择器
  const tasks = useSelector(selectTasks)
  const stats = useSelector(selectStats)
  const loading = useSelector(selectLoading)
  const errors = useSelector(selectErrors)
  const filters = useSelector(selectFilters)
  const ui = useSelector(selectUI)

  const [form] = Form.useForm()

  // 初始化数据
  useEffect(() => {
    dispatch(fetchTasks())
    dispatch(fetchTaskStats())
  }, [dispatch])

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
    dispatch(fetchTasks())
    dispatch(fetchTaskStats())
  }, [dispatch])

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
      await dispatch(createTask(values)).unwrap()
      dispatch(hideTaskForm())
      form.resetFields()
      handleRefresh()
    } catch (error) {
      // 错误已在slice中处理
    }
  }, [dispatch, form, handleRefresh])

  // 重置状态（用于调试或刷新）
  const handleReset = useCallback(() => {
    dispatch(resetCrawlerState())
    handleRefresh()
  }, [dispatch, handleRefresh])

  // 计算统计数据
  const getStatValue = useCallback((key: string, defaultValue: any = 0) => {
    if (!stats) return defaultValue
    return stats[key] || defaultValue
  }, [stats])

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0 }}>
              爬虫管理
            </Title>
            <Text type="secondary">
              管理和监控爬虫任务的执行状态
            </Text>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<FilterOutlined />}
                onClick={() => dispatch({ type: 'crawler/toggleFilters' })}
              >
                {ui.showFilters ? '隐藏筛选' : '显示筛选'}
              </Button>
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
          </Col>
        </Row>
      </div>

      {/* 错误提示 */}
      {Object.values(errors).some(error => error) && (
        <Alert
          message="操作错误"
          description="请检查网络连接或联系管理员"
          type="error"
          showIcon
          closable
          onClose={() => dispatch(clearAllErrors())}
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={getStatValue('total_tasks', tasks.length)}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中"
              value={getStatValue('running_tasks', 0)}
              prefix={<SyncOutlined spin={loading.tasks} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功任务"
              value={getStatValue('success_tasks', 0)}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败任务"
              value={getStatValue('failed_tasks', 0)}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选器 */}
      {ui.showFilters && (
        <Card style={{ marginBottom: 16 }}>
          <TaskFilters
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
        title="创建爬虫任务"
        open={ui.showTaskForm}
        onCancel={() => dispatch(hideTaskForm())}
        footer={null}
        width={600}
        destroyOnClose
      >
        <TaskForm
          form={form}
          onSubmit={handleCreateTask}
          onCancel={() => dispatch(hideTaskForm())}
          loading={loading.createTask}
        />
      </Modal>

      {/* 开发环境调试按钮 */}
      {import.meta.env.DEV && (
        <Card style={{ marginTop: 16, border: '1px dashed #d9d9d9' }}>
          <Text type="secondary">调试工具：</Text>
          <Space>
            <Button size="small" onClick={handleReset}>
              重置状态
            </Button>
            <Button size="small" onClick={() => console.log('State:', { tasks, stats, loading, errors, filters, ui })}>
              打印状态
            </Button>
          </Space>
        </Card>
      )}
    </div>
  )
}

export default CrawlerPage