/**
 * OCR 任务列表组件
 */

import React from 'react'
import {
  Table,
  Tag,
  Space,
  Button,
  Select,
  Tooltip,
  Popconfirm,
  Card,
  Typography,
  Descriptions,
} from 'antd'
import {
  ReloadOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { OCRTaskItem, OCRStatus, OCRProgressInfo } from '../../../types/dataWorkflow'
import { OCR_STATUS_CONFIG, OCR_PRIORITY_OPTIONS } from '../../../types/dataWorkflow'
import OCRProgressBar from './OCRProgressBar'

const { Text } = Typography

interface OCRTaskListProps {
  tasks: OCRTaskItem[]
  total: number
  loading?: boolean
  page: number
  pageSize: number
  selectedKeys: number[]
  /** 任务进度信息（按 pending_id 索引） */
  taskProgress?: Record<number, OCRProgressInfo>
  onPageChange: (page: number, pageSize: number) => void
  onSelectChange: (keys: number[]) => void
  onRetry: (pendingId: number) => void
  onBatchRetry: (pendingIds: number[]) => void
  onSkip: (pendingId: number) => void
  onSetPriority: (pendingId: number, priority: number) => void
  onDelete: (pendingId: number) => void
}

const STATUS_ICONS: Record<OCRStatus, React.ReactNode> = {
  pending: <ClockCircleOutlined />,
  processing: <SyncOutlined spin />,
  completed: <CheckCircleOutlined />,
  failed: <CloseCircleOutlined />,
  skipped: <ExclamationCircleOutlined />,
}

const OCRTaskList: React.FC<OCRTaskListProps> = ({
  tasks,
  total,
  loading,
  page,
  pageSize,
  selectedKeys,
  taskProgress = {},
  onPageChange,
  onSelectChange,
  onRetry,
  onBatchRetry,
  onSkip,
  onSetPriority,
  onDelete,
}) => {
  // 格式化时间
  const formatTime = (ms: number | null): string => {
    if (!ms) return '-'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  // 可展开行内容
  const expandedRowRender = (record: OCRTaskItem) => {
    const progress = taskProgress[record.pending_id]
    const showProgress = record.ocr_status === 'processing' && progress

    return (
      <div>
        {/* 处理进度条 */}
        {showProgress && (
          <div style={{ marginBottom: 16 }}>
            <OCRProgressBar progress={progress} showDetail />
          </div>
        )}

        {/* 详细信息 */}
        <Descriptions size="small" column={4} style={{ marginBottom: 0 }}>
          <Descriptions.Item label="任务ID">{record.pending_id}</Descriptions.Item>
          <Descriptions.Item label="Worker">{record.ocr_worker_id || '-'}</Descriptions.Item>
          <Descriptions.Item label="开始时间">
            {record.ocr_started_at?.replace('T', ' ').substring(0, 19) || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="处理耗时">
            {formatTime(record.ocr_processing_time_ms)}
          </Descriptions.Item>
          <Descriptions.Item label="OCR提供商">{record.ocr_provider || '-'}</Descriptions.Item>
          <Descriptions.Item label="重试次数">{record.ocr_retry_count}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {record.created_at?.replace('T', ' ').substring(0, 19) || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="图片数量">{record.images_count}</Descriptions.Item>
          {record.ocr_error_message && (
            <Descriptions.Item label="错误信息" span={4}>
              <Text type="danger" style={{ fontSize: 12 }}>
                {record.ocr_error_message}
              </Text>
            </Descriptions.Item>
          )}
        </Descriptions>
      </div>
    )
  }

  // 表格列定义
  const columns: ColumnsType<OCRTaskItem> = [
    {
      title: '产品信息',
      key: 'product',
      width: 300,
      render: (_, record) => (
        <div>
          <Tooltip title={record.product_name}>
            <Text strong ellipsis style={{ maxWidth: 250, display: 'block' }}>
              {record.product_name || '-'}
            </Text>
          </Tooltip>
          <Text type="secondary" style={{ fontSize: 12 }}>
            品牌: {record.brand_name || '-'} | 图片: {record.images_count}
          </Text>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'ocr_status',
      key: 'ocr_status',
      width: 180,
      render: (status: OCRStatus, record: OCRTaskItem) => {
        const config = OCR_STATUS_CONFIG[status]
        const progress = taskProgress[record.pending_id]

        // 处理中状态显示进度条
        if (status === 'processing' && progress) {
          return (
            <div style={{ minWidth: 150 }}>
              <OCRProgressBar progress={progress} compact />
            </div>
          )
        }

        return (
          <Tag color={config.color} icon={STATUS_ICONS[status]}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '优先级',
      dataIndex: 'ocr_priority',
      key: 'ocr_priority',
      width: 100,
      render: (priority: number, record: OCRTaskItem) => (
        <Select
          size="small"
          value={priority}
          style={{ width: '100%' }}
          onChange={(value) => onSetPriority(record.pending_id, value)}
          options={OCR_PRIORITY_OPTIONS.map((opt) => ({
            label: opt.label,
            value: opt.value,
          }))}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record: OCRTaskItem) => {
        const status = record.ocr_status

        if (status === 'processing') {
          return (
            <Popconfirm
              title="确定要取消这个正在处理的任务吗？"
              onConfirm={() => onSkip(record.pending_id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small" danger>
                取消
              </Button>
            </Popconfirm>
          )
        }

        return (
          <Space size="small">
            {['failed', 'skipped', 'completed'].includes(status) && (
              <Button
                type="link"
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => onRetry(record.pending_id)}
              >
                重试
              </Button>
            )}
            {['pending', 'failed'].includes(status) && (
              <Button
                type="link"
                size="small"
                onClick={() => onSkip(record.pending_id)}
              >
                跳过
              </Button>
            )}
            {['pending', 'failed', 'skipped'].includes(status) && (
              <Popconfirm
                title="确定要删除这个任务吗？"
                onConfirm={() => onDelete(record.pending_id)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            )}
          </Space>
        )
      },
    },
  ]

  return (
    <>
      {/* 批量操作栏 */}
      {selectedKeys.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space>
            <Text strong>已选择 {selectedKeys.length} 项</Text>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={() => onBatchRetry(selectedKeys)}
            >
              批量重试
            </Button>
            <Button onClick={() => onSelectChange([])}>取消选择</Button>
          </Space>
        </Card>
      )}

      {/* 任务列表 */}
      <Table
        rowKey="pending_id"
        rowSelection={{
          selectedRowKeys: selectedKeys,
          onChange: (keys) => onSelectChange(keys as number[]),
          getCheckboxProps: (record: OCRTaskItem) => ({
            disabled: !['failed', 'skipped', 'completed'].includes(record.ocr_status),
          }),
        }}
        columns={columns}
        dataSource={tasks}
        loading={loading}
        expandable={{
          expandedRowRender,
          expandRowByClick: true,
        }}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: onPageChange,
        }}
        size="middle"
      />
    </>
  )
}

export default OCRTaskList
