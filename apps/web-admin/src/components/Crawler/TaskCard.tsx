import React, { useState, useCallback } from 'react'
import {
  Card,
  Tag,
  Progress,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Tooltip,
  Dropdown,
  Modal,
  Badge,
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
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useDispatch, useSelector } from 'react-redux'
import { message } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

import type { CrawlerTask } from '../../types/crawler'
import {
  showTaskDetail,
  deleteTask,
  retryTask,
} from '../../store/slices/crawlerSlice'
import LoginInteraction from './LoginInteraction'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text, Title } = Typography
const { Meta } = Card

interface TaskCardProps {
  task: CrawlerTask
  isSelected?: boolean
  onSelectionChange?: (taskId: number, selected: boolean) => void
  showLoginInteraction?: boolean
}

// 状态配置
const statusConfig = {
  pending: {
    color: 'default',
    icon: <ClockCircleOutlined />,
    text: '等待中',
  },
  running: {
    color: 'processing',
    icon: <LoadingOutlined spin />,
    text: '运行中',
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
    color: 'warning',
    icon: <ExclamationCircleOutlined />,
    text: '已取消',
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
  onSelectionChange,
  showLoginInteraction = false,
}) => {
  const dispatch = useDispatch()
  const [loginModalVisible, setLoginModalVisible] = useState(false)

  const statusConfigItem = statusConfig[task.status as keyof typeof statusConfig] || statusConfig.pending

  // 查看任务详情
  const handleViewDetail = useCallback(() => {
    dispatch(showTaskDetail(task.task_id))
  }, [dispatch, task.task_id])

  // 重试任务
  const handleRetry = useCallback(async () => {
    try {
      await dispatch(retryTask(task.task_id)).unwrap()
    } catch (error: any) {
      console.error('重试任务失败:', error)
    }
  }, [dispatch, task.task_id])

  // 删除任务
  const handleDelete = useCallback(() => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除任务 "${task.task_name}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await dispatch(deleteTask(task.task_id)).unwrap()
        } catch (error: any) {
          console.error('删除任务失败:', error)
        }
      },
    })
  }, [dispatch, task.task_id, task.task_name])

  // 显示登录交互
  const handleShowLogin = useCallback(() => {
    setLoginModalVisible(true)
  }, [])

  // 更多操作菜单
  const moreMenuItems: MenuProps['items'] = [
    {
      key: 'detail',
      label: '查看详情',
      icon: <EyeOutlined />,
      onClick: handleViewDetail,
    },
    {
      key: 'retry',
      label: '重试任务',
      icon: <ReloadOutlined />,
      onClick: handleRetry,
      disabled: task.status !== 'failed',
    },
    {
      type: 'divider',
    },
    {
      key: 'login',
      label: '登录处理',
      icon: <PlayCircleOutlined />,
      onClick: handleShowLogin,
      disabled: !['pending', 'failed'].includes(task.status),
    },
    {
      type: 'divider',
    },
    {
      key: 'delete',
      label: '删除任务',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: handleDelete,
      disabled: task.status === 'running',
    },
  ]

  // 计算进度百分比
  const getProgressPercent = useCallback(() => {
    if (!task.total_items) return 0
    return Math.round((task.success_items / task.total_items) * 100)
  }, [task.success_items, task.total_items])

  // 格式化时间
  const formatTime = useCallback((time: string) => {
    return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
  }, [])

  // 获取相对时间
  const getRelativeTime = useCallback((time: string) => {
    return dayjs(time).fromNow()
  }, [])

  return (
    <>
      <Card
        hoverable
        className={`task-card ${isSelected ? 'selected' : ''}`}
        size="small"
        bordered
        style={{
          marginBottom: 16,
          border: isSelected ? '2px solid #1890ff' : undefined,
        }}
        actions={[
          <Tooltip title="查看详情" key="detail">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={handleViewDetail}
            />
          </Tooltip>,
          <Tooltip title="重试任务" key="retry">
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={handleRetry}
              disabled={task.status !== 'failed'}
            />
          </Tooltip>,
          <Dropdown menu={{ items: moreMenuItems }} key="more">
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>,
        ]}
      >
        {/* 头部信息 */}
        <div style={{ marginBottom: 12 }}>
          <Row justify="space-between" align="middle">
            <Col flex="auto">
              <Meta
                avatar={
                  <Badge
                    status={statusConfigItem.color as any}
                    text={statusConfigItem.icon}
                  />
                }
                title={
                  <Text strong ellipsis={{ tooltip: task.task_name }}>
                    {task.task_name}
                  </Text>
                }
                description={
                  <Space size="small">
                    <Tag color="blue">{task.platform}</Tag>
                    <Tag color="purple">{task.task_type}</Tag>
                    {task.priority && (
                      <Tag color={task.priority === 'high' ? 'red' : 'default'}>
                        {task.priority === 'high' ? '高优先级' : task.priority}
                      </Tag>
                    )}
                  </Space>
                }
              />
            </Col>
            <Col>
              <Tag color={statusConfigItem.color} icon={statusConfigItem.icon}>
                {statusConfigItem.text}
              </Tag>
            </Col>
          </Row>
        </div>

        {/* 进度信息 */}
        <div style={{ marginBottom: 12 }}>
          <Row justify="space-between" align="middle" style={{ marginBottom: 4 }}>
            <Col>
              <Text type="secondary" style={{ fontSize: 12 }}>
                执行进度
              </Text>
            </Col>
            <Col>
              <Text style={{ fontSize: 12 }}>
                {task.success_items} / {task.total_items || 0}
              </Text>
            </Col>
          </Row>
          <Progress
            percent={getProgressPercent()}
            status={task.status === 'failed' ? 'exception' : 'normal'}
            size="small"
          />
        </div>

        {/* 详细信息 */}
        <Row gutter={16}>
          <Col span={8}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              创建时间
            </Text>
            <br />
            <Tooltip title={formatTime(task.created_at)}>
              <Text style={{ fontSize: 12 }}>
                {getRelativeTime(task.created_at)}
              </Text>
            </Tooltip>
          </Col>
          <Col span={8}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              执行时长
            </Text>
            <br />
            <Text style={{ fontSize: 12 }}>
              {task.duration ? `${task.duration}s` : '-'}
            </Text>
          </Col>
          <Col span={8}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              错误数
            </Text>
            <br />
            <Text style={{ fontSize: 12 }}>
              {task.failed_items || 0}
            </Text>
          </Col>
        </Row>

        {/* 操作按钮 */}
        {task.status === 'pending' && (
          <div style={{ marginTop: 12, textAlign: 'center' }}>
            <Space>
              <Button
                type="primary"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={handleShowLogin}
              >
                开始执行
              </Button>
              <Button
                size="small"
                icon={<DeleteOutlined />}
                onClick={handleDelete}
              >
                删除
              </Button>
            </Space>
          </div>
        )}
      </Card>

      {/* 登录交互弹窗 */}
      <Modal
        title={`${task.platform} 登录验证`}
        open={loginModalVisible}
        onCancel={() => setLoginModalVisible(false)}
        footer={null}
        width={900}
        destroyOnClose
      >
        <LoginInteraction
          taskId={task.task_id}
          platform={task.platform}
          platformName={task.platform_name}
          onComplete={(userInfo) => {
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
    </>
  )
}

export default TaskCard