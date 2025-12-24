/**
 * OCR Worker 管理页面
 */

import React, { useEffect, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Statistic,
  Row,
  Col,
  Select,
  Typography,
  Tooltip,
  message,
} from 'antd'
import {
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { AppDispatch } from '../../store/store'
import type { OCRTaskItem } from '../../types/ocrWorker'
import {
  fetchOCRStats,
  fetchOCRTasks,
  selectOCRTasks,
  selectOCRStats,
  selectOCRLoading,
  selectOCRPagination,
  selectOCRFilters,
  setFilters,
  setPage,
} from '../../store/slices/ocrWorkerSlice'

const { Title, Text } = Typography

const OCRWorkerPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const tasks = useSelector(selectOCRTasks)
  const stats = useSelector(selectOCRStats)
  const loading = useSelector(selectOCRLoading)
  const pagination = useSelector(selectOCRPagination)
  const filters = useSelector(selectOCRFilters)

  // 加载数据
  const loadData = useCallback(() => {
    dispatch(fetchOCRStats())
    dispatch(fetchOCRTasks({
      ...filters,
      page: pagination.page,
      page_size: pagination.pageSize,
    }))
  }, [dispatch, filters, pagination.page, pagination.pageSize])

  useEffect(() => {
    loadData()
  }, [loadData])

  // 刷新
  const handleRefresh = () => {
    loadData()
    message.success('已刷新')
  }

  // 状态筛选
  const handleStatusChange = (value: string | undefined) => {
    dispatch(setFilters({ ocr_status: value }))
    dispatch(setPage(1))
  }

  // 分页
  const handlePageChange = (page: number, pageSize: number) => {
    dispatch(setPage(page))
    dispatch(fetchOCRTasks({
      ...filters,
      page,
      page_size: pageSize,
    }))
  }

  // 状态标签配置
  const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
    pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
    processing: { color: 'processing', icon: <SyncOutlined spin />, text: '处理中' },
    completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
    failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
    skipped: { color: 'warning', icon: <ExclamationCircleOutlined />, text: '跳过' },
  }

  // 表格列定义
  const columns: ColumnsType<OCRTaskItem> = [
    {
      title: 'ID',
      dataIndex: 'pending_id',
      key: 'pending_id',
      width: 80,
    },
    {
      title: '品牌',
      dataIndex: 'brand_name',
      key: 'brand_name',
      width: 120,
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 200,
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <span>{text || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '图片数',
      dataIndex: 'images_count',
      key: 'images_count',
      width: 80,
      align: 'center',
    },
    {
      title: '状态',
      dataIndex: 'ocr_status',
      key: 'ocr_status',
      width: 100,
      render: (status: string) => {
        const config = statusConfig[status] || statusConfig.pending
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: 'Worker',
      dataIndex: 'ocr_worker_id',
      key: 'ocr_worker_id',
      width: 120,
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '提供商',
      dataIndex: 'ocr_provider',
      key: 'ocr_provider',
      width: 100,
      render: (text) => text ? <Tag>{text}</Tag> : '-',
    },
    {
      title: '耗时',
      dataIndex: 'ocr_processing_time_ms',
      key: 'ocr_processing_time_ms',
      width: 100,
      render: (ms: number | undefined) => {
        if (!ms) return '-'
        if (ms < 1000) return `${ms}ms`
        return `${(ms / 1000).toFixed(1)}s`
      },
    },
    {
      title: '重试',
      dataIndex: 'ocr_retry_count',
      key: 'ocr_retry_count',
      width: 60,
      align: 'center',
    },
    {
      title: '错误信息',
      dataIndex: 'ocr_error_message',
      key: 'ocr_error_message',
      width: 150,
      ellipsis: true,
      render: (text) => text ? (
        <Tooltip title={text}>
          <Text type="danger" ellipsis>{text}</Text>
        </Tooltip>
      ) : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => text ? new Date(text).toLocaleString() : '-',
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>OCR Worker 管理</Title>
        <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
          刷新
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="总任务"
              value={stats?.total || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="待处理"
              value={stats?.pending || 0}
              valueStyle={{ color: '#666' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="处理中"
              value={stats?.processing || 0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<SyncOutlined spin={!!stats?.processing} />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="已完成"
              value={stats?.completed || 0}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="失败"
              value={stats?.failed || 0}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="跳过"
              value={stats?.skipped || 0}
              valueStyle={{ color: '#faad14' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选器 */}
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>状态筛选:</span>
          <Select
            style={{ width: 150 }}
            placeholder="全部状态"
            allowClear
            value={filters.ocr_status}
            onChange={handleStatusChange}
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

      {/* 任务列表 */}
      <Card>
        <Table
          rowKey="pending_id"
          columns={columns}
          dataSource={tasks}
          loading={loading}
          pagination={{
            current: pagination.page,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: handlePageChange,
          }}
          scroll={{ x: 1400 }}
          size="middle"
        />
      </Card>
    </div>
  )
}

export default OCRWorkerPage
