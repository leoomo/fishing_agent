/**
 * 采集任务卡片组件
 *
 * 美化版本 - 增强视觉效果：
 * 1. 状态左边框颜色标识
 * 2. 高优先级渐变背景
 * 3. 运行中脉冲动画
 * 4. 核心指标突出显示
 */

import React, { useState, useCallback } from 'react'
import {
  Card,
  Tag,
  Progress,
  Button,
  Space,
  Typography,
  Tooltip,
  Dropdown,
  Modal,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  MoreOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  EditOutlined,
  HourglassOutlined,
  FireOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useDispatch } from 'react-redux'
import { message } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

import type { CrawlerTask } from '../../types/crawler'
import type { AppDispatch } from '../../store/store'
import {
  showTaskDetail,
  deleteTask,
  rerunTask,
  startTask,
  stopTask,
  updateTask,
} from '../../store/slices/crawlerSlice'
import LoginInteraction from './LoginInteraction'
import TaskEdit from './TaskEdit'
import './TaskCard.css'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text } = Typography

interface TaskCardProps {
  task: CrawlerTask
  isSelected?: boolean
}

// 状态配置
const statusConfig = {
  pending: {
    color: 'default',
    icon: <ClockCircleOutlined />,
    text: '待启动',
  },
  queued: {
    color: 'warning',
    icon: <HourglassOutlined />,
    text: '等待领取',
  },
  running: {
    color: 'processing',
    icon: <LoadingOutlined spin />,
    text: '执行中',
  },
  success: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    text: '成功',
  },
  failed: {
    color: 'error',
    icon: <CloseCircleOutlined />,
    text: '失败',
  },
  cancelled: {
    color: 'default',
    icon: <PauseCircleOutlined />,
    text: '已停止',
  },
  paused: {
    color: 'warning',
    icon: <PauseCircleOutlined />,
    text: '已暂停',
  },
}

const TaskCard: React.FC<TaskCardProps> = ({
  task,
  isSelected = false,
}) => {
  const dispatch = useDispatch<AppDispatch>()
  const [loginModalVisible, setLoginModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)

  const statusKey = task.status.toLowerCase() as keyof typeof statusConfig
  const statusConfigItem = statusConfig[statusKey] || statusConfig.pending
  const isHighPriority = task.priority === 'high'
  const isRunning = ['queued', 'running'].includes(statusKey)

  // 计算卡片类名
  const getCardClassName = useCallback(() => {
    const classes = ['task-card']
    classes.push(`task-card-${statusKey}`)
    if (isHighPriority) classes.push('task-card-high-priority')
    if (isSelected) classes.push('selected')
    return classes.join(' ')
  }, [statusKey, isHighPriority, isSelected])

  // 格式化执行时长
  const formatDuration = useCallback((seconds?: number) => {
    if (!seconds) return '-'
    if (seconds < 60) return `${seconds}s`
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }, [])

  // 查看任务详情
  const handleViewDetail = useCallback(() => {
    dispatch(showTaskDetail(task.task_id))
  }, [dispatch, task.task_id])

  // 重新运行任务
  const handleRerun = useCallback(async () => {
    try {
      await dispatch(rerunTask(task.task_id)).unwrap()
    } catch (error: unknown) {
      console.error('重新运行任务失败:', error)
    }
  }, [dispatch, task.task_id])

  // 启动任务
  const handleStart = useCallback(async () => {
    try {
      await dispatch(startTask(task.task_id)).unwrap()
      message.success('任务启动成功')
    } catch (error: unknown) {
      console.error('启动任务失败:', error)
    }
  }, [dispatch, task.task_id])

  // 停止任务
  const handleStop = useCallback(async () => {
    try {
      await dispatch(stopTask(task.task_id)).unwrap()
    } catch (error: unknown) {
      console.error('停止任务失败:', error)
    }
  }, [dispatch, task.task_id])

  // 删除任务
  const handleDelete = useCallback(() => {
    const shouldDelete = window.confirm(`确定要删除任务 "${task.task_name}" 吗？此操作不可恢复。`)
    if (shouldDelete) {
      try {
        dispatch(deleteTask(task.task_id)).unwrap()
        message.success('任务删除成功')
      } catch (error: unknown) {
        console.error('删除任务失败:', error)
      }
    }
  }, [dispatch, task.task_id, task.task_name])

  // 显示登录交互
  const handleShowLogin = useCallback(() => {
    setLoginModalVisible(true)
  }, [])

  // 编辑任务
  const handleEdit = useCallback(() => {
    setEditModalVisible(true)
  }, [])

  // 保存编辑的任务
  const handleSaveEdit = useCallback(async (taskData: Partial<CrawlerTask>) => {
    try {
      await dispatch(updateTask({ taskId: task.task_id, taskData })).unwrap()
    } catch (error) {
      console.error('更新任务失败:', error)
      throw error
    }
  }, [dispatch, task.task_id])

  // 关闭编辑弹窗
  const handleCloseEdit = useCallback(() => {
    setEditModalVisible(false)
  }, [])

  // 处理菜单项点击
  const handleMenuClick = useCallback((key: string) => {
    switch (key) {
      case 'detail':
        handleViewDetail()
        break
      case 'edit':
        handleEdit()
        break
      case 'start':
        handleStart()
        break
      case 'stop':
        handleStop()
        break
      case 'rerun':
        handleRerun()
        break
      case 'login':
        handleShowLogin()
        break
      case 'delete':
        handleDelete()
        break
      default:
        break
    }
  }, [handleViewDetail, handleEdit, handleStart, handleStop, handleRerun, handleShowLogin, handleDelete])

  // 更多操作菜单
  const moreMenuItems: MenuProps['items'] = [
    {
      key: 'edit',
      label: '编辑任务',
      icon: <EditOutlined />,
      disabled: isRunning,
    },
    {
      key: 'login',
      label: '登录处理',
      icon: <PlayCircleOutlined />,
      disabled: !['pending', 'failed'].includes(statusKey),
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      label: '删除任务',
      icon: <DeleteOutlined />,
      danger: true,
      disabled: isRunning,
    },
  ]

  // 计算进度百分比
  const progressPercent = task.total_items
    ? Math.round((task.success_items / task.total_items) * 100)
    : 0

  // 获取相对时间
  const relativeTime = dayjs(task.created_at).fromNow()
  const fullTime = dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss')

  return (
    <>
      <Card
        className={getCardClassName()}
        size="small"
        style={{ marginBottom: 16 }}
        actions={[
          // 启动/停止按钮
          isRunning ? (
            <Tooltip title="停止任务" key="stop">
              <Button
                type="text"
                danger
                icon={<PauseCircleOutlined />}
                onClick={handleStop}
                className="action-btn-danger"
              >
                停止
              </Button>
            </Tooltip>
          ) : (
            <Tooltip title="启动任务" key="start">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={handleStart}
                disabled={!['pending', 'failed', 'cancelled'].includes(statusKey)}
                className="action-btn-primary"
              >
                启动
              </Button>
            </Tooltip>
          ),
          // 重新运行
          <Tooltip title="重新运行" key="rerun">
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={handleRerun}
              disabled={isRunning}
            >
              重运行
            </Button>
          </Tooltip>,
          // 查看详情
          <Tooltip title="查看详情" key="detail">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={handleViewDetail}
            >
              详情
            </Button>
          </Tooltip>,
          // 更多菜单
          <Dropdown
            menu={{
              items: moreMenuItems,
              onClick: ({ key }) => handleMenuClick(key)
            }}
            trigger={['click']}
            placement="bottomRight"
            key="more"
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>,
        ]}
      >
        {/* 头部：标题 + 状态 */}
        <div className="task-card-header">
          <div className="task-card-title-section">
            <div className="task-card-title">
              {isHighPriority && (
                <span className="priority-badge-high">
                  <FireOutlined style={{ marginRight: 2 }} />
                  高优
                </span>
              )}
              <Tooltip title={task.task_name}>
                <span className="task-card-title-text">
                  {task.task_name}
                </span>
              </Tooltip>
            </div>
            <div className="task-card-subtitle">
              {task.platform} · {task.task_type}
            </div>
          </div>
          <Tag color={statusConfigItem.color} icon={statusConfigItem.icon}>
            {statusConfigItem.text}
          </Tag>
        </div>

        {/* 核心指标行 */}
        <div className="stats-row">
          <div className="stat-item">
            <div className="stat-value stat-value-success">
              <CheckCircleOutlined />
              {task.success_items || 0}
            </div>
            <div className="stat-label">成功</div>
          </div>
          <div className="stat-item">
            <div className="stat-value stat-value-failed">
              <CloseCircleOutlined />
              {task.failed_items || 0}
            </div>
            <div className="stat-label">失败</div>
          </div>
          <div className="stat-item">
            <div className="stat-value stat-value-default">
              <ClockCircleOutlined />
              {formatDuration(task.duration)}
            </div>
            <div className="stat-label">耗时</div>
          </div>
        </div>

        {/* 进度条 */}
        <div className="progress-section">
          <div className="progress-header">
            <span className="progress-label">执行进度</span>
            <span className="progress-value">
              {task.success_items || 0} / {task.total_items || 0}
            </span>
          </div>
          <Progress
            percent={progressPercent}
            status={task.status === 'failed' ? 'exception' : 'normal'}
            size="small"
            showInfo={false}
          />
        </div>

        {/* 底部信息 */}
        <div className="task-card-footer">
          <Tooltip title={fullTime}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              创建于 {relativeTime}
            </Text>
          </Tooltip>
        </div>
      </Card>

      {/* 登录交互弹窗 */}
      <Modal
        title={`${task.platform} 登录验证`}
        open={loginModalVisible}
        onCancel={() => setLoginModalVisible(false)}
        footer={null}
        width={900}
      >
        <LoginInteraction
          taskId={task.task_id}
          platform={task.platform}
          platformName={task.platform_name}
          onComplete={() => {
            setLoginModalVisible(false)
            message.success('登录成功，任务将开始执行')
          }}
          onError={(error) => {
            console.error('登录失败:', error)
          }}
          onCancel={() => {
            setLoginModalVisible(false)
          }}
        />
      </Modal>

      {/* 编辑任务弹窗 */}
      <TaskEdit
        visible={editModalVisible}
        task={task}
        onClose={handleCloseEdit}
        onSave={handleSaveEdit}
        loading={false}
      />
    </>
  )
}

export default TaskCard
