/**
 * OCR Worker 管理页面
 */

import React, { useEffect, useCallback, useState } from 'react'
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
  Popconfirm,
} from 'antd'
import {
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { AppDispatch } from '../../store/store'
import type { OCRTaskItem } from '../../types/ocrWorker'
import { OCR_PRIORITY_OPTIONS } from '../../types/ocrWorker'
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
  retryOCRTask,
  retryOCRTasksBatch,
  skipOCRTask,
  setOCRTaskPriority,
  deleteOCRTask,
} from '../../store/slices/ocrWorkerSlice'

const { Title, Text } = Typography

const OCRWorkerPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const tasks = useSelector(selectOCRTasks)
  const stats = useSelector(selectOCRStats)
  const loading = useSelector(selectOCRLoading)
  const pagination = useSelector(selectOCRPagination)
  const filters = useSelector(selectOCRFilters)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

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

  // ========== 管理员操作 ==========

  // 重试任务
  const handleRetry = async (pendingId: number) => {
    const result = await dispatch(retryOCRTask(pendingId))
    if (retryOCRTask.fulfilled.match(result)) {
      message.success('任务已重新加入队列（重试次数已重置）')
      loadData()
    } else {
      message.error('重试失败')
    }
  }

  // 批量重试
  const handleBatchRetry = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要重试的任务')
      return
    }
    const result = await dispatch(retryOCRTasksBatch({
      pending_ids: selectedRowKeys as number[],
    }))
    if (retryOCRTasksBatch.fulfilled.match(result)) {
      message.success(`成功重试 ${result.payload.retried_count} 个任务`)
      setSelectedRowKeys([])
      loadData()
    } else {
      message.error('批量重试失败')
    }
  }

  // 跳过任务
  const handleSkip = async (pendingId: number) => {
    const result = await dispatch(skipOCRTask(pendingId))
    if (skipOCRTask.fulfilled.match(result)) {
      message.success('任务已跳过')
      loadData()
    } else {
      message.error('跳过失败')
    }
  }

  // 设置优先级
  const handlePriorityChange = async (pendingId: number, priority: number) => {
    const result = await dispatch(setOCRTaskPriority({ pendingId, priority }))
    if (setOCRTaskPriority.fulfilled.match(result)) {
      message.success('优先级已更新')
      loadData()
    } else {
      message.error('设置优先级失败')
    }
  }

  // 删除任务
  const handleDelete = async (pendingId: number) => {
    const result = await dispatch(deleteOCRTask(pendingId))
    if (deleteOCRTask.fulfilled.match(result)) {
      message.success('任务已删除')
      // 无需刷新，Redux已处理
    } else {
      message.error('删除失败')
    }
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
      width: 180,
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
      width: 70,
      align: 'center',
    },
    {
      title: '状态',
      dataIndex: 'ocr_status',
      key: 'ocr_status',
      width: 90,
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
      title: '优先级',
      dataIndex: 'ocr_priority',
      key: 'ocr_priority',
      width: 100,
      render: (priority: number, record: OCRTaskItem) => {
        return (
          <Select
            size="small"
            value={priority}
            style={{ width: '100%' }}
            onChange={(value) => handlePriorityChange(record.pending_id, value)}
            options={OCR_PRIORITY_OPTIONS.map(opt => ({
              label: opt.label,
              value: opt.value,
            }))}
          />
        )
      },
    },
    {
      title: 'Worker',
      dataIndex: 'ocr_worker_id',
      key: 'ocr_worker_id',
      width: 100,
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '耗时',
      dataIndex: 'ocr_processing_time_ms',
      key: 'ocr_processing_time_ms',
      width: 80,
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
      width: 50,
      align: 'center',
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record: OCRTaskItem) => (
        <Space size="small">
          {/* 重试按钮 */}
          {['failed', 'skipped', 'completed'].includes(record.ocr_status) && (
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => handleRetry(record.pending_id)}
            >
              重试
            </Button>
          )}
          {/* 跳过按钮 */}
          {['pending', 'failed'].includes(record.ocr_status) && (
            <Button
              type="link"
              size="small"
              onClick={() => handleSkip(record.pending_id)}
            >
              跳过
            </Button>
          )}
          {/* 删除按钮 - 仅pending/failed/skipped可删除 */}
          {!['processing', 'completed'].includes(record.ocr_status) && (
            <Popconfirm
              title="确定要删除这个任务吗？"
              onConfirm={() => handleDelete(record.pending_id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
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

      {/* 批量操作栏 */}
      {selectedRowKeys.length > 0 && (
        <Card style={{ marginBottom: 16 }}>
          <Space>
            <Text strong>已选择 {selectedRowKeys.length} 项</Text>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={handleBatchRetry}
            >
              批量重试（重置次数）
            </Button>
            <Button onClick={() => setSelectedRowKeys([])}>
              取消选择
            </Button>
          </Space>
        </Card>
      )}

      {/* 任务列表 */}
      <Card>
        <Table
          rowKey="pending_id"
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            getCheckboxProps: (record: OCRTaskItem) => ({
              disabled: !['failed', 'skipped', 'completed'].includes(record.ocr_status),
            }),
          }}
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
