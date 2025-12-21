import React from 'react'
import {
  Modal,
  Descriptions,
  Tag,
  Progress,
  Typography,
  Space,
  Button,
} from 'antd'
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  PauseCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

import type { CrawlerTask } from '../../types/crawler'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text, Title } = Typography

interface TaskDetailProps {
  visible: boolean
  task: CrawlerTask | null
  onClose: () => void
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

const TaskDetail: React.FC<TaskDetailProps> = ({ visible, task, onClose }) => {
  if (!task) {
    return null
  }

  const statusConfigItem = statusConfig[task.status as keyof typeof statusConfig] || statusConfig.pending

  // 计算进度百分比
  const getProgressPercent = () => {
    if (!task.total_items) return 0
    return Math.round((task.success_items / task.total_items) * 100)
  }

  // 格式化时间
  const formatTime = (time: string) => {
    return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
  }

  // 获取相对时间
  const getRelativeTime = (time: string) => {
    return dayjs(time).fromNow()
  }

  return (
    <Modal
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>
            任务详情
          </Title>
          <Tag color={statusConfigItem.color} icon={statusConfigItem.icon}>
            {statusConfigItem.text}
          </Tag>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      <Descriptions column={2} bordered size="small">
        {/* 基本信息 */}
        <Descriptions.Item label="任务ID" span={1}>
          <Text code>{task.task_id}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="任务名称" span={1}>
          <Text strong>{task.task_name}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="任务类型" span={1}>
          <Tag color="blue">{task.task_type}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="目标平台" span={1}>
          <Tag color="purple">{task.platform || '未知'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="优先级" span={1}>
          <Tag color={task.priority === 'high' ? 'red' : 'default'}>
            {task.priority === 'high' ? '高优先级' : task.priority || '普通'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="状态" span={1}>
          <Tag color={statusConfigItem.color} icon={statusConfigItem.icon}>
            {statusConfigItem.text}
          </Tag>
        </Descriptions.Item>

        {/* 执行进度 */}
        <Descriptions.Item label="执行进度" span={2}>
          <div style={{ width: '100%' }}>
            <div style={{ marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">进度</Text>
              <Text>{task.success_items} / {task.total_items || 0}</Text>
            </div>
            <Progress
              percent={getProgressPercent()}
              status={task.status === 'failed' ? 'exception' : 'normal'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
          </div>
        </Descriptions.Item>

        <Descriptions.Item label="成功项目" span={1}>
          <Text style={{ color: '#52c41a' }}>{task.success_items}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="失败项目" span={1}>
          <Text style={{ color: '#ff4d4f' }}>{task.failed_items || 0}</Text>
        </Descriptions.Item>

        {/* 时间信息 */}
        <Descriptions.Item label="创建时间" span={1}>
          <Space direction="vertical" size={0}>
            <Text>{formatTime(task.created_at)}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {getRelativeTime(task.created_at)}
            </Text>
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="开始时间" span={1}>
          {task.start_time ? (
            <Space direction="vertical" size={0}>
              <Text>{formatTime(task.start_time)}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {getRelativeTime(task.start_time)}
              </Text>
            </Space>
          ) : (
            <Text type="secondary">未开始</Text>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="结束时间" span={1}>
          {task.end_time ? (
            <Space direction="vertical" size={0}>
              <Text>{formatTime(task.end_time)}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {getRelativeTime(task.end_time)}
              </Text>
            </Space>
          ) : (
            <Text type="secondary">未结束</Text>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="执行时长" span={1}>
          <Text>{task.duration ? `${task.duration}s` : '-'}</Text>
        </Descriptions.Item>

        
        {task.error_message && (
          <Descriptions.Item label="错误信息" span={2}>
            <Text type="danger" code>
              {task.error_message}
            </Text>
          </Descriptions.Item>
        )}

        {task.result_summary && (
          <Descriptions.Item label="执行摘要" span={2}>
            <pre style={{
              background: '#f5f5f5',
              padding: '8px',
              borderRadius: '4px',
              fontSize: '12px',
              maxHeight: '200px',
              overflow: 'auto'
            }}>
              {task.result_summary}
            </pre>
          </Descriptions.Item>
        )}
      </Descriptions>
    </Modal>
  )
}

export default TaskDetail