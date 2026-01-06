/**
 * 审核任务列表组件
 *
 * 包含：
 * - 任务列表表格
 * - 审核弹窗
 * - 详情弹窗（OCR文本 + 可编辑装备信息）
 */

import React, { useState, useEffect, useCallback } from 'react'
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
  Row,
  Col,
  Spin,
  App,
  Timeline,
  Image,
} from 'antd'
import {
  EyeOutlined,
  DeleteOutlined,
  ShoppingOutlined,
  GlobalOutlined,
  MessageOutlined,
  FileTextOutlined,
  FileExcelOutlined,
  ThunderboltOutlined,
  SaveOutlined,
  PictureOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import type { ColumnsType } from 'antd/es/table'
import type {
  ReviewTaskItem,
  ReviewStatus,
  ReviewAction,
  ExtractedEquipmentItem,
  ReviewHistoryItem,
  ImageInfo,
} from '../../../types/dataWorkflow'
import { REVIEW_STATUS_CONFIG, EQUIPMENT_TYPE_CONFIG } from '../../../types/dataWorkflow'
import { dataWorkflowApi } from '../../../api/services/dataWorkflow'
import EquipmentEditForm from './EquipmentEditForm'

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
  // 刷新列表
  onRefresh?: () => void
}

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  ecommerce: <ShoppingOutlined />,
  official: <GlobalOutlined />,
  forum: <MessageOutlined />,
  excel_import: <FileExcelOutlined />,
  unknown: <FileTextOutlined />,
}

const SOURCE_LABELS: Record<string, string> = {
  ecommerce: '电商平台',
  official: '官方网站',
  forum: '论坛',
  excel_import: 'Excel导入',
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
  onRefresh,
}) => {
  const { modal, message } = App.useApp()
  const [form] = Form.useForm()
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [detailTask, setDetailTask] = useState<ReviewTaskItem | null>(null)

  // 提取和编辑相关状态
  const [extracting, setExtracting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editedItems, setEditedItems] = useState<ExtractedEquipmentItem[]>([])
  const [originalItems, setOriginalItems] = useState<ExtractedEquipmentItem[]>([])
  const [hasChanges, setHasChanges] = useState(false)

  // 图片查看相关状态
  const [images, setImages] = useState<ImageInfo[]>([])
  const [imagesLoading, setImagesLoading] = useState(false)

  // 给图片 URL 添加 token（因为 img 标签无法携带 Authorization header）
  const getImageUrlWithToken = useCallback((url: string): string => {
    const token = localStorage.getItem('fishing_admin_token')
    if (!token) return url
    const separator = url.includes('?') ? '&' : '?'
    return `${url}${separator}token=${token}`
  }, [])

  // 解析已有的 extracted_data
  const parseExtractedData = useCallback((data: unknown): ExtractedEquipmentItem[] => {
    if (!data) return []
    if (Array.isArray(data)) {
      return data as ExtractedEquipmentItem[]
    }
    // 兼容旧格式（单个对象）
    if (typeof data === 'object') {
      return [data as ExtractedEquipmentItem]
    }
    return []
  }, [])

  // 当详情弹窗打开时，初始化编辑数据
  useEffect(() => {
    if (detailTask) {
      const items = parseExtractedData(detailTask.extracted_data)
      setEditedItems(items)
      setOriginalItems(items)
      setHasChanges(false)
    }
  }, [detailTask, parseExtractedData])

  // 加载任务图片
  useEffect(() => {
    if (detailTask && detailTask.images_count > 0) {
      setImagesLoading(true)
      dataWorkflowApi
        .getTaskImages(detailTask.id)
        .then((res) => {
          setImages(res.images)
        })
        .catch((err) => {
          console.error('加载图片失败:', err)
          setImages([])
        })
        .finally(() => {
          setImagesLoading(false)
        })
    } else {
      setImages([])
    }
  }, [detailTask])

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

  // 关闭详情弹窗
  const handleCloseDetail = () => {
    if (hasChanges) {
      modal.confirm({
        title: '确定要关闭吗？',
        content: '您有未保存的修改，关闭后将丢失这些更改。',
        okText: '确定关闭',
        cancelText: '继续编辑',
        onOk: () => {
          setDetailModalVisible(false)
          setDetailTask(null)
          setHasChanges(false)
          setImages([])
        },
      })
    } else {
      setDetailModalVisible(false)
      setDetailTask(null)
      setImages([])
    }
  }

  // 一键提取
  const handleExtract = async () => {
    if (!detailTask) return

    setExtracting(true)
    try {
      const response = await dataWorkflowApi.extractEquipment(detailTask.id)
      if (response.success) {
        message.success(response.message)
        setEditedItems(response.items)
        setOriginalItems(response.items)
        setHasChanges(false)
        // 更新 detailTask 的 extracted_data
        setDetailTask({
          ...detailTask,
          extracted_data: response.items as unknown as Record<string, unknown>,
        })
      } else {
        message.warning(response.message)
      }
    } catch (error) {
      message.error('提取失败，请重试')
      console.error('Extract error:', error)
    } finally {
      setExtracting(false)
    }
  }

  // 保存编辑
  const handleSave = async () => {
    if (!detailTask) return

    setSaving(true)
    try {
      const response = await dataWorkflowApi.saveExtractedData(detailTask.id, {
        items: editedItems,
      })
      if (response.success) {
        message.success(response.message)
        setOriginalItems(editedItems)
        setHasChanges(false)
        // 更新 detailTask 的 extracted_data
        setDetailTask({
          ...detailTask,
          extracted_data: editedItems as unknown as Record<string, unknown>,
        })
        // 刷新列表
        onRefresh?.()
      } else {
        message.error(response.message)
      }
    } catch (error) {
      message.error('保存失败，请重试')
      console.error('Save error:', error)
    } finally {
      setSaving(false)
    }
  }

  // 重置编辑
  const handleReset = () => {
    setEditedItems([...originalItems])
    setHasChanges(false)
  }

  // 编辑项变化
  const handleItemsChange = (items: ExtractedEquipmentItem[]) => {
    setEditedItems(items)
    setHasChanges(true)
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
      width: 120,
      render: (_, record: ReviewTaskItem) => (
        <Space size="small">
          <Tooltip title="查看详情并审核">
            <Button
              type="primary"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            >
              审核
            </Button>
          </Tooltip>
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
        forceRender
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

      {/* 详情弹窗 - 增强版 */}
      <Modal
        title={
          <Space>
            <span>审核详情</span>
            {detailTask?.product_name && (
              <Text type="secondary">- {detailTask.product_name}</Text>
            )}
          </Space>
        }
        open={detailModalVisible}
        onCancel={handleCloseDetail}
        destroyOnHidden
        maskClosable={!hasChanges}
        keyboard={!hasChanges}
        footer={
          <Space>
            <Button onClick={handleCloseDetail}>关闭</Button>
            {detailTask?.status === 'pending' && hasChanges && (
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={saving}
              >
                保存修改
              </Button>
            )}
            <Button
              danger
              onClick={() => {
                setDetailModalVisible(false)
                if (detailTask) onShowReviewModal(detailTask, 'reject')
              }}
            >
              {detailTask?.status === 'pending' ? '拒绝' : '重新审核为拒绝'}
            </Button>
            <Button
              type="primary"
              onClick={() => {
                setDetailModalVisible(false)
                if (detailTask) onShowReviewModal(detailTask, 'approve')
              }}
            >
              {detailTask?.status === 'pending' ? '通过并导入' : '重新审核为通过'}
            </Button>
          </Space>
        }
        width={1200}
        style={{ top: 20 }}
        styles={{ body: { maxHeight: 'calc(100vh - 200px)', overflow: 'auto' } }}
      >
        {detailTask && (
          <>
            {/* 基本信息 */}
            <Descriptions column={4} size="small" bordered style={{ marginBottom: 16 }}>
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
              <Descriptions.Item label="图片数量">{detailTask.images_count} 张</Descriptions.Item>
            </Descriptions>

            {/* 双栏布局 */}
            <Row gutter={16}>
              {/* 左侧：OCR 识别原文 */}
              <Col span={12}>
                <Card
                  title="OCR 识别原文"
                  size="small"
                  style={{ height: 500 }}
                  styles={{ body: { height: 440, overflow: 'auto' } }}
                >
                  {detailTask.ocr_text ? (
                    <div className="markdown-content">
                      <ReactMarkdown>{detailTask.ocr_text}</ReactMarkdown>
                    </div>
                  ) : (
                    <Text type="secondary">暂无 OCR 文本</Text>
                  )}
                </Card>
              </Col>

              {/* 右侧：提取的装备信息 */}
              <Col span={12}>
                <Card
                  title={
                    <Space>
                      <span>提取的装备信息</span>
                      {hasChanges && <Tag color="orange">有未保存的修改</Tag>}
                    </Space>
                  }
                  size="small"
                  style={{ height: 500 }}
                  styles={{ body: { height: 440, overflow: 'auto' } }}
                  extra={
                    <Space>
                      <Button
                        type="primary"
                        icon={<ThunderboltOutlined />}
                        onClick={handleExtract}
                        loading={extracting}
                        size="small"
                      >
                        {editedItems.length > 0 ? '重新提取' : '一键提取'}
                      </Button>
                      {hasChanges && (
                        <Button
                          icon={<SaveOutlined />}
                          onClick={handleSave}
                          loading={saving}
                          size="small"
                        >
                          保存
                        </Button>
                      )}
                    </Space>
                  }
                >
                  <Spin spinning={extracting} tip="正在提取装备信息...">
                    <EquipmentEditForm
                      items={editedItems}
                      onChange={handleItemsChange}
                      onReset={handleReset}
                      disabled={false}
                    />
                  </Spin>
                </Card>
              </Col>
            </Row>

            {/* 审核信息 */}
            {detailTask.reviewed_at && (
              <>
                <Divider style={{ margin: '16px 0' }} />
                <Descriptions column={3} size="small">
                  <Descriptions.Item label="审核时间">
                    {detailTask.reviewed_at?.replace('T', ' ').substring(0, 19)}
                  </Descriptions.Item>
                  <Descriptions.Item label="审核人">
                    用户 ID: {detailTask.reviewed_by}
                  </Descriptions.Item>
                  {detailTask.review_notes && (
                    <Descriptions.Item label="审核备注">
                      {detailTask.review_notes}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </>
            )}

            {/* 审核历史 */}
            {detailTask.review_history && detailTask.review_history.length > 0 && (
              <>
                <Divider style={{ margin: '16px 0' }} />
                <Card title="审核历史" size="small">
                  <Timeline
                    items={detailTask.review_history.map((item: ReviewHistoryItem, index: number) => ({
                      color: item.action === 'approve' ? 'green' : 'red',
                      children: (
                        <div key={index}>
                          <div>
                            <Tag color={item.action === 'approve' ? 'success' : 'error'}>
                              {item.action === 'approve' ? '通过' : '拒绝'}
                            </Tag>
                            <Text type="secondary" style={{ marginLeft: 8 }}>
                              {item.reviewed_at?.replace('T', ' ').substring(0, 19)}
                            </Text>
                          </div>
                          <div style={{ marginTop: 4 }}>
                            <Text type="secondary">
                              审核人: 用户 {item.reviewed_by} | 原状态:{' '}
                              {REVIEW_STATUS_CONFIG[item.previous_status as ReviewStatus]?.text || item.previous_status}
                            </Text>
                          </div>
                          {item.review_notes && (
                            <div style={{ marginTop: 4, color: '#666' }}>
                              备注: {item.review_notes}
                            </div>
                          )}
                        </div>
                      ),
                    }))}
                  />
                </Card>
              </>
            )}

            {/* 图片预览区域 */}
            {detailTask.images_count > 0 && (
              <>
                <Divider style={{ margin: '16px 0' }} />
                <Card
                  title={
                    <Space>
                      <PictureOutlined />
                      <span>原始图片</span>
                      <Tag>{detailTask.images_count} 张</Tag>
                    </Space>
                  }
                  size="small"
                >
                  {imagesLoading ? (
                    <div style={{ textAlign: 'center', padding: 20 }}>
                      <Spin tip="加载图片中..." />
                    </div>
                  ) : images.length > 0 ? (
                    <Image.PreviewGroup>
                      <Space wrap size={[8, 8]}>
                        {images.map((img, index) => (
                          <Image
                            key={index}
                            src={getImageUrlWithToken(img.url)}
                            alt={img.filename}
                            width={120}
                            height={160}
                            style={{
                              objectFit: 'cover',
                              borderRadius: 4,
                              border: '1px solid #d9d9d9',
                            }}
                            placeholder={
                              <div
                                style={{
                                  width: 120,
                                  height: 160,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  background: '#f5f5f5',
                                }}
                              >
                                <Spin size="small" />
                              </div>
                            }
                          />
                        ))}
                      </Space>
                    </Image.PreviewGroup>
                  ) : (
                    <Text type="secondary">暂无图片</Text>
                  )}
                </Card>
              </>
            )}
          </>
        )}
      </Modal>

      {/* Markdown 样式 */}
      <style>{`
        .markdown-content {
          font-size: 13px;
          line-height: 1.6;
        }
        .markdown-content table {
          border-collapse: collapse;
          width: 100%;
          margin: 8px 0;
        }
        .markdown-content th,
        .markdown-content td {
          border: 1px solid #d9d9d9;
          padding: 4px 8px;
          text-align: left;
        }
        .markdown-content th {
          background: #fafafa;
        }
        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3 {
          margin: 12px 0 8px;
          font-size: 14px;
          font-weight: 600;
        }
        .markdown-content p {
          margin: 4px 0;
        }
        .markdown-content ul,
        .markdown-content ol {
          padding-left: 20px;
          margin: 4px 0;
        }
      `}</style>
    </>
  )
}

export default ReviewTaskList
