import React, { useEffect, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Space,
  Typography,
  Table,
  Tag,
  Tooltip,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Progress,
  Descriptions,
  Divider,
} from 'antd'
import {
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  ShoppingOutlined,
  GlobalOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import { useAppDispatch, useAppSelector } from '../../store/hooks'
import type { ColumnsType } from 'antd/es/table'

import {
  fetchPendingEquipmentList,
  fetchPendingEquipmentStats,
  reviewPendingEquipment,
  deletePendingEquipment,
  setFilters,
  clearFilters,
  setPagination,
  showDetailModal,
  hideDetailModal,
  showReviewModal,
  hideReviewModal,
  clearAllErrors,
  selectItems,
  selectStats,
  selectLoading,
  selectErrors,
  selectFilters,
  selectPagination,
  selectUI,
  selectCurrentItem,
} from '../../store/slices/pendingEquipmentSlice'
import type { PendingEquipment, ExtractedEquipmentData } from '../../types/pendingEquipment'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TextArea } = Input

// 状态颜色映射
const statusColorMap: Record<string, string> = {
  pending: 'processing',
  approved: 'success',
  rejected: 'error',
}

// 状态文本映射
const statusTextMap: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
}

// 来源类型图标映射
const sourceTypeIconMap: Record<string, React.ReactNode> = {
  ecommerce: <ShoppingOutlined />,
  official: <GlobalOutlined />,
  forum: <MessageOutlined />,
  unknown: <FileTextOutlined />,
}

// 来源类型文本映射
const sourceTypeTextMap: Record<string, string> = {
  ecommerce: '电商平台',
  official: '官方网站',
  forum: '论坛',
  unknown: '未知',
}

// 装备类型文本映射
const equipmentTypeTextMap: Record<string, string> = {
  rod: '鱼竿',
  reel: '渔轮',
  line: '鱼线',
  lure: '拟饵',
  accessory: '配件',
  unknown: '未知',
}

const PendingEquipmentPage: React.FC = () => {
  const dispatch = useAppDispatch()
  const [reviewForm] = Form.useForm()

  // 选择器
  const items = useAppSelector(selectItems)
  const stats = useAppSelector(selectStats)
  const loading = useAppSelector(selectLoading)
  const errors = useAppSelector(selectErrors)
  const filters = useAppSelector(selectFilters)
  const pagination = useAppSelector(selectPagination)
  const ui = useAppSelector(selectUI)
  const currentItem = useAppSelector(selectCurrentItem)

  // 初始化数据
  useEffect(() => {
    dispatch(fetchPendingEquipmentList({ page: 1, pageSize: 20, filters }))
    dispatch(fetchPendingEquipmentStats())
  }, [dispatch])

  // 错误处理
  useEffect(() => {
    if (errors.list) {
      message.error(errors.list)
      dispatch(clearAllErrors())
    }
  }, [errors, dispatch])

  // 刷新数据
  const handleRefresh = useCallback(() => {
    dispatch(fetchPendingEquipmentList({ page: pagination.current, pageSize: pagination.pageSize, filters }))
    dispatch(fetchPendingEquipmentStats())
  }, [dispatch, pagination, filters])

  // 筛选变化
  const handleFilterChange = useCallback(
    (key: string, value: any) => {
      dispatch(setFilters({ [key]: value || undefined }))
      dispatch(fetchPendingEquipmentList({ page: 1, pageSize: pagination.pageSize, filters: { ...filters, [key]: value || undefined } }))
    },
    [dispatch, pagination.pageSize, filters]
  )

  // 清除筛选
  const handleClearFilters = useCallback(() => {
    dispatch(clearFilters())
    dispatch(fetchPendingEquipmentList({ page: 1, pageSize: pagination.pageSize, filters: {} }))
  }, [dispatch, pagination.pageSize])

  // 分页变化
  const handleTableChange = useCallback(
    (pag: any) => {
      dispatch(setPagination({ current: pag.current, pageSize: pag.pageSize }))
      dispatch(fetchPendingEquipmentList({ page: pag.current, pageSize: pag.pageSize, filters }))
    },
    [dispatch, filters]
  )

  // 查看详情
  const handleViewDetail = useCallback(
    (record: PendingEquipment) => {
      dispatch(showDetailModal(record))
    },
    [dispatch]
  )

  // 审核操作
  const handleReview = useCallback(
    (record: PendingEquipment, action: 'approve' | 'reject') => {
      dispatch(showReviewModal({ item: record, action }))
      reviewForm.resetFields()
    },
    [dispatch, reviewForm]
  )

  // 提交审核
  const handleSubmitReview = useCallback(async () => {
    if (!currentItem || !ui.reviewAction) return

    try {
      const values = await reviewForm.validateFields()
      await dispatch(
        reviewPendingEquipment({
          id: currentItem.id,
          data: {
            action: ui.reviewAction,
            review_notes: values.review_notes,
          },
        })
      ).unwrap()
      handleRefresh()
    } catch (error) {
      // 错误已在slice中处理
    }
  }, [dispatch, currentItem, ui.reviewAction, reviewForm, handleRefresh])

  // 删除
  const handleDelete = useCallback(
    async (id: number) => {
      try {
        await dispatch(deletePendingEquipment(id)).unwrap()
        handleRefresh()
      } catch (error) {
        // 错误已在slice中处理
      }
    },
    [dispatch, handleRefresh]
  )

  // 表格列定义
  const columns: ColumnsType<PendingEquipment> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={statusColorMap[status]}>{statusTextMap[status] || status}</Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 100,
      render: (sourceType: string) => (
        <Space>
          {sourceTypeIconMap[sourceType]}
          <span>{sourceTypeTextMap[sourceType] || sourceType}</span>
        </Space>
      ),
    },
    {
      title: '装备类型',
      dataIndex: 'equipment_type',
      key: 'equipment_type',
      width: 100,
      render: (type: string) => equipmentTypeTextMap[type] || type || '-',
    },
    {
      title: '品牌',
      dataIndex: 'brand_name',
      key: 'brand_name',
      width: 120,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 200,
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span>{text || '-'}</span>
        </Tooltip>
      ),
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
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => text?.replace('T', ' ').substring(0, 19) || '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)} />
          </Tooltip>
          {record.status === 'pending' && (
            <>
              <Tooltip title="通过">
                <Button
                  type="link"
                  size="small"
                  icon={<CheckCircleOutlined />}
                  style={{ color: '#52c41a' }}
                  onClick={() => handleReview(record, 'approve')}
                />
              </Tooltip>
              <Tooltip title="拒绝">
                <Button
                  type="link"
                  size="small"
                  icon={<CloseCircleOutlined />}
                  danger
                  onClick={() => handleReview(record, 'reject')}
                />
              </Tooltip>
            </>
          )}
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => handleDelete(record.id)}
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

  // 渲染提取的数据
  const renderExtractedData = (data: ExtractedEquipmentData | undefined) => {
    if (!data) return <Text type="secondary">暂无提取数据</Text>

    return (
      <Descriptions column={2} size="small" bordered>
        {data.equipment_type && (
          <Descriptions.Item label="装备类型">
            {equipmentTypeTextMap[data.equipment_type] || data.equipment_type}
          </Descriptions.Item>
        )}
        {data.brand_name && <Descriptions.Item label="品牌">{data.brand_name}</Descriptions.Item>}
        {data.model_name && <Descriptions.Item label="型号">{data.model_name}</Descriptions.Item>}
        {data.product_name && <Descriptions.Item label="产品名称" span={2}>{data.product_name}</Descriptions.Item>}
        {data.price && <Descriptions.Item label="价格">¥{data.price}</Descriptions.Item>}
        {data.description && (
          <Descriptions.Item label="描述" span={2}>
            <Paragraph ellipsis={{ rows: 2, expandable: true }}>{data.description}</Paragraph>
          </Descriptions.Item>
        )}
        {data.features && data.features.length > 0 && (
          <Descriptions.Item label="特性" span={2}>
            <Space wrap>
              {data.features.map((f, i) => (
                <Tag key={i}>{f}</Tag>
              ))}
            </Space>
          </Descriptions.Item>
        )}
        {data.specifications && Object.keys(data.specifications).length > 0 && (
          <Descriptions.Item label="规格参数" span={2}>
            <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(data.specifications, null, 2)}</pre>
          </Descriptions.Item>
        )}
      </Descriptions>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0 }}>
              待审核装备
            </Title>
            <Text type="secondary">审核爬虫采集的装备数据，通过后将入库</Text>
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading.list}>
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总数量"
              value={stats?.total || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待审核"
              value={stats?.pending || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已通过"
              value={stats?.approved || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已拒绝"
              value={stats?.rejected || 0}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选器 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 120 }}
            value={filters.status}
            onChange={(value) => handleFilterChange('status', value)}
          >
            <Option value="pending">待审核</Option>
            <Option value="approved">已通过</Option>
            <Option value="rejected">已拒绝</Option>
          </Select>
          <Select
            placeholder="来源类型"
            allowClear
            style={{ width: 120 }}
            value={filters.source_type}
            onChange={(value) => handleFilterChange('source_type', value)}
          >
            <Option value="ecommerce">电商平台</Option>
            <Option value="official">官方网站</Option>
            <Option value="forum">论坛</Option>
            <Option value="unknown">未知</Option>
          </Select>
          <Select
            placeholder="装备类型"
            allowClear
            style={{ width: 120 }}
            value={filters.equipment_type}
            onChange={(value) => handleFilterChange('equipment_type', value)}
          >
            <Option value="rod">鱼竿</Option>
            <Option value="reel">渔轮</Option>
            <Option value="line">鱼线</Option>
            <Option value="lure">拟饵</Option>
            <Option value="accessory">配件</Option>
          </Select>
          <Button onClick={handleClearFilters}>清除筛选</Button>
        </Space>
      </Card>

      {/* 数据表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading.list}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title="待审核装备详情"
        open={ui.showDetailModal}
        onCancel={() => dispatch(hideDetailModal())}
        footer={
          currentItem?.status === 'pending' ? (
            <Space>
              <Button onClick={() => dispatch(hideDetailModal())}>关闭</Button>
              <Button danger onClick={() => handleReview(currentItem, 'reject')}>
                拒绝
              </Button>
              <Button type="primary" onClick={() => handleReview(currentItem, 'approve')}>
                通过
              </Button>
            </Space>
          ) : (
            <Button onClick={() => dispatch(hideDetailModal())}>关闭</Button>
          )
        }
        width={800}
      >
        {currentItem && (
          <>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="ID">{currentItem.id}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusColorMap[currentItem.status]}>{statusTextMap[currentItem.status]}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="来源类型">
                <Space>
                  {sourceTypeIconMap[currentItem.source_type]}
                  {sourceTypeTextMap[currentItem.source_type]}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="置信度">
                <Progress percent={Math.round(currentItem.confidence * 100)} size="small" style={{ width: 100 }} />
              </Descriptions.Item>
              {currentItem.source_url && (
                <Descriptions.Item label="来源URL" span={2}>
                  <a href={currentItem.source_url} target="_blank" rel="noopener noreferrer">
                    {currentItem.source_url}
                  </a>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="创建时间">{currentItem.created_at?.replace('T', ' ').substring(0, 19)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{currentItem.updated_at?.replace('T', ' ').substring(0, 19)}</Descriptions.Item>
              {currentItem.reviewed_at && (
                <>
                  <Descriptions.Item label="审核时间">{currentItem.reviewed_at?.replace('T', ' ').substring(0, 19)}</Descriptions.Item>
                  <Descriptions.Item label="审核人ID">{currentItem.reviewed_by}</Descriptions.Item>
                </>
              )}
              {currentItem.review_notes && (
                <Descriptions.Item label="审核备注" span={2}>
                  {currentItem.review_notes}
                </Descriptions.Item>
              )}
              {currentItem.equipment_id && (
                <Descriptions.Item label="关联装备ID" span={2}>
                  <Tag color="blue">{currentItem.equipment_id}</Tag>
                </Descriptions.Item>
              )}
            </Descriptions>

            <Divider>OCR识别原文</Divider>
            <Card size="small" style={{ maxHeight: 200, overflow: 'auto', backgroundColor: '#f5f5f5' }}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: 12 }}>
                {currentItem.ocr_text}
              </pre>
            </Card>

            <Divider>提取的结构化数据</Divider>
            {renderExtractedData(currentItem.extracted_data)}
          </>
        )}
      </Modal>

      {/* 审核弹窗 */}
      <Modal
        title={ui.reviewAction === 'approve' ? '审核通过' : '审核拒绝'}
        open={ui.showReviewModal}
        onCancel={() => dispatch(hideReviewModal())}
        onOk={handleSubmitReview}
        okText={ui.reviewAction === 'approve' ? '通过' : '拒绝'}
        okButtonProps={{
          danger: ui.reviewAction === 'reject',
          loading: loading.review,
        }}
        cancelText="取消"
      >
        <Form form={reviewForm} layout="vertical">
          <Form.Item name="review_notes" label="审核备注">
            <TextArea rows={4} placeholder="请输入审核备注（可选）" />
          </Form.Item>
        </Form>
        {currentItem && (
          <Card size="small" style={{ marginTop: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="品牌">{currentItem.brand_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="产品">{currentItem.product_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="类型">
                {equipmentTypeTextMap[currentItem.equipment_type || ''] || currentItem.equipment_type || '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Modal>
    </div>
  )
}

export default PendingEquipmentPage
