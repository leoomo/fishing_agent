/**
 * 审核任务列表组件
 */

import React from 'react'
import {
  Table,
  Tag,
  Space,
  Button,
  Tooltip,
  Popconfirm,
  Progress,
  Typography,
  Descriptions,
  Modal,
  Form,
  Input,
  Card,
  Divider,
} from 'antd'
import {
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  ShoppingOutlined,
  GlobalOutlined,
  MessageOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { ReviewTaskItem, ReviewStatus, ReviewAction } from '../../../types/dataWorkflow'
import { REVIEW_STATUS_CONFIG, EQUIPMENT_TYPE_CONFIG } from '../../../types/dataWorkflow'

const { Text } = Typography
const { TextArea } = Input

interface ReviewTaskListProps {
  tasks: ReviewTaskItem[]
  total: number
  loading?: boolean
  page: number
  pageSize: number
  onPageChange: (page: number, pageSize: number) => void
  onReview: (taskId: number, action: ReviewAction) => void
  onDelete: (taskId: number) => void
  // Modal 相关
  currentTask: ReviewTaskItem | null
  modalVisible: boolean
  reviewAction: 'approve' | 'reject' | null
  onShowReviewModal: (task: ReviewTaskItem, action: 'approve' | 'reject') => void
  onHideReviewModal: () => void
}

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  ecommerce: <ShoppingOutlined />,
  official: <GlobalOutlined />,
  forum: <MessageOutlined />,
  unknown: <FileTextOutlined />,
}

const SOURCE_LABELS: Record<string, string> = {
  ecommerce: '电商平台',
  official: '官方网站',
  forum: '论坛',
  unknown: '未知',
}

const ReviewTaskList: React.FC<ReviewTaskListProps> = ({
  tasks,
  total,
  loading,
  page,
  pageSize,
  onPageChange,
  onReview,
  onDelete,
  currentTask,
  modalVisible,
  reviewAction,
  onShowReviewModal,
  onHideReviewModal,
}) => {
  const [form] = Form.useForm()
  const [detailModalVisible, setDetailModalVisible] = React.useState(false)
  const [detailTask, setDetailTask] = React.useState<ReviewTaskItem | null>(null)

  // 处理审核提交
  const handleReviewSubmit = async () => {
    if (!currentTask || !reviewAction) return

    try {
      const values = await form.validateFields()
      onReview(currentTask.id, {
        action: reviewAction,
        review_notes: values.review_notes,
      })
      form.resetFields()
    } catch {
      // 表单验证失败
    }
  }

  // 查看详情
  const handleViewDetail = (task: ReviewTaskItem) => {
    setDetailTask(task)
    setDetailModalVisible(true)
  }

  // 可展开行内容
  const expandedRowRender = (record: ReviewTaskItem) => (
    <Descriptions size="small" column={4} style={{ marginBottom: 0 }}>
      <Descriptions.Item label="任务ID">{record.id}</Descriptions.Item>
      <Descriptions.Item label="来源类型">
        <Space size={4}>
          {SOURCE_ICONS[record.source_type || 'unknown']}
          {SOURCE_LABELS[record.source_type || 'unknown']}
        </Space>
      </Descriptions.Item>
      <Descriptions.Item label="装备类型">
        {EQUIPMENT_TYPE_CONFIG[record.equipment_type || 'unknown'] || record.equipment_type || '-'}
      </Descriptions.Item>
      <Descriptions.Item label="图片数量">{record.images_count}</Descriptions.Item>
      <Descriptions.Item label="创建时间">
        {record.created_at?.replace('T', ' ').substring(0, 19) || '-'}
      </Descriptions.Item>
      {record.reviewed_at && (
        <Descriptions.Item label="审核时间">
          {record.reviewed_at?.replace('T', ' ').substring(0, 19)}
        </Descriptions.Item>
      )}
      {record.source_url && (
        <Descriptions.Item label="来源URL" span={2}>
          <a href={record.source_url} target="_blank" rel="noopener noreferrer">
            {record.source_url.length > 50
              ? record.source_url.substring(0, 50) + '...'
              : record.source_url}
          </a>
        </Descriptions.Item>
      )}
      {record.review_notes && (
        <Descriptions.Item label="审核备注" span={4}>
          {record.review_notes}
        </Descriptions.Item>
      )}
    </Descriptions>
  )

  // 表格列定义
  const columns: ColumnsType<ReviewTaskItem> = [
    {
      title: '产品信息',
      key: 'product',
      width: 280,
      render: (_, record) => (
        <div>
          <Tooltip title={record.product_name}>
            <Text strong ellipsis style={{ maxWidth: 230, display: 'block' }}>
              {record.product_name || '-'}
            </Text>
          </Tooltip>
          <Text type="secondary" style={{ fontSize: 12 }}>
            品牌: {record.brand_name || '-'} |{' '}
            {EQUIPMENT_TYPE_CONFIG[record.equipment_type || 'unknown'] || '-'}
          </Text>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: ReviewStatus) => {
        const config = REVIEW_STATUS_CONFIG[status]
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 100,
      render: (confidence: number) => (
        <Progress
          percent={Math.round(confidence * 100)}
          size="small"
          status={confidence >= 0.8 ? 'success' : confidence >= 0.5 ? 'normal' : 'exception'}
          style={{ width: 80 }}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record: ReviewTaskItem) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          {record.status === 'pending' && (
            <>
              <Tooltip title="通过">
                <Button
                  type="link"
                  size="small"
                  icon={<CheckCircleOutlined />}
                  style={{ color: '#52c41a' }}
                  onClick={() => onShowReviewModal(record, 'approve')}
                />
              </Tooltip>
              <Tooltip title="拒绝">
                <Button
                  type="link"
                  size="small"
                  icon={<CloseCircleOutlined />}
                  danger
                  onClick={() => onShowReviewModal(record, 'reject')}
                />
              </Tooltip>
            </>
          )}
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => onDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="link" size="small" icon={<DeleteOutlined />} danger />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      {/* 任务列表 */}
      <Table
        rowKey="id"
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

      {/* 审核弹窗 */}
      <Modal
        title={reviewAction === 'approve' ? '审核通过' : '审核拒绝'}
        open={modalVisible}
        onCancel={() => {
          onHideReviewModal()
          form.resetFields()
        }}
        onOk={handleReviewSubmit}
        okText={reviewAction === 'approve' ? '通过' : '拒绝'}
        okButtonProps={{ danger: reviewAction === 'reject' }}
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="review_notes" label="审核备注">
            <TextArea rows={4} placeholder="请输入审核备注（可选）" />
          </Form.Item>
        </Form>
        {currentTask && (
          <Card size="small" style={{ marginTop: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="品牌">{currentTask.brand_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="产品">{currentTask.product_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="类型">
                {EQUIPMENT_TYPE_CONFIG[currentTask.equipment_type || ''] ||
                  currentTask.equipment_type ||
                  '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="装备详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={
          detailTask?.status === 'pending' ? (
            <Space>
              <Button onClick={() => setDetailModalVisible(false)}>关闭</Button>
              <Button
                danger
                onClick={() => {
                  setDetailModalVisible(false)
                  onShowReviewModal(detailTask, 'reject')
                }}
              >
                拒绝
              </Button>
              <Button
                type="primary"
                onClick={() => {
                  setDetailModalVisible(false)
                  onShowReviewModal(detailTask, 'approve')
                }}
              >
                通过
              </Button>
            </Space>
          ) : (
            <Button onClick={() => setDetailModalVisible(false)}>关闭</Button>
          )
        }
        width={800}
      >
        {detailTask && (
          <>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="ID">{detailTask.id}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={REVIEW_STATUS_CONFIG[detailTask.status].color}>
                  {REVIEW_STATUS_CONFIG[detailTask.status].text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="来源类型">
                <Space>
                  {SOURCE_ICONS[detailTask.source_type || 'unknown']}
                  {SOURCE_LABELS[detailTask.source_type || 'unknown']}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="置信度">
                <Progress
                  percent={Math.round(detailTask.confidence * 100)}
                  size="small"
                  style={{ width: 100 }}
                />
              </Descriptions.Item>
              <Descriptions.Item label="品牌">{detailTask.brand_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="产品名称">
                {detailTask.product_name || '-'}
              </Descriptions.Item>
              {detailTask.source_url && (
                <Descriptions.Item label="来源URL" span={2}>
                  <a href={detailTask.source_url} target="_blank" rel="noopener noreferrer">
                    {detailTask.source_url}
                  </a>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="创建时间">
                {detailTask.created_at?.replace('T', ' ').substring(0, 19)}
              </Descriptions.Item>
              {detailTask.reviewed_at && (
                <Descriptions.Item label="审核时间">
                  {detailTask.reviewed_at?.replace('T', ' ').substring(0, 19)}
                </Descriptions.Item>
              )}
            </Descriptions>

            <Divider>OCR识别原文</Divider>
            <Card
              size="small"
              style={{ maxHeight: 200, overflow: 'auto', backgroundColor: '#f5f5f5' }}
            >
              <pre
                style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: 12 }}
              >
                {detailTask.ocr_text || '暂无数据'}
              </pre>
            </Card>

            {detailTask.extracted_data && (
              <>
                <Divider>提取的结构化数据</Divider>
                <Descriptions column={2} size="small" bordered>
                  {Object.entries(detailTask.extracted_data).map(([key, value]) => (
                    <Descriptions.Item label={key} key={key}>
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </>
            )}
          </>
        )}
      </Modal>
    </>
  )
}

export default ReviewTaskList
