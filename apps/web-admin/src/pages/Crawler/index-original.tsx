import { useState, useEffect, useRef } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Popconfirm,
  Progress,
  Descriptions,
  Timeline,
  Row,
  Col,
  Statistic,
} from 'antd'
import {
  PlayCircleOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import { crawlerApi } from '@/api/services/crawler'
import type { CrawlerTask, CrawlerLog, SyncStatus } from '@/types/crawler'
import type { ColumnsType } from 'antd/es/table'

const Crawler = () => {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<CrawlerTask[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState<string>()
  const [typeFilter, setTypeFilter] = useState<string>()

  const [triggerModalVisible, setTriggerModalVisible] = useState(false)
  const [triggerLoading, setTriggerLoading] = useState(false)
  const [form] = Form.useForm()

  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [currentTask, setCurrentTask] = useState<CrawlerTask | null>(null)
  const [taskLogs, setTaskLogs] = useState<CrawlerLog[]>([])
  const [logsLoading, setLogsLoading] = useState(false)

  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null)

  // WebSocket 连接
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    fetchTasks()
    fetchSyncStatus()
  }, [page, pageSize, statusFilter, typeFilter])

  useEffect(() => {
    // 清理 WebSocket
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const response = await crawlerApi.listTasks({
        page,
        page_size: pageSize,
        status: statusFilter,
        task_type: typeFilter,
      })
      setTasks(response.tasks)
      setTotal(response.total)
    } catch {
      message.error('加载任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchSyncStatus = async () => {
    try {
      const status = await crawlerApi.getSyncStatus()
      setSyncStatus(status)
    } catch {
      // 忽略错误
    }
  }

  const handleTrigger = async () => {
    try {
      const values = await form.validateFields()
      setTriggerLoading(true)

      const keywords = values.keywords
        ? values.keywords.split(',').map((k: string) => k.trim())
        : undefined

      await crawlerApi.triggerCrawler({
        task_type: values.task_type,
        keywords,
        max_pages: values.max_pages,
        proxy: values.proxy,
      })

      message.success('任务已触发')
      setTriggerModalVisible(false)
      form.resetFields()
      fetchTasks()
      fetchSyncStatus()
    } catch {
      message.error('触发任务失败')
    } finally {
      setTriggerLoading(false)
    }
  }

  const handleRetry = async (taskId: number) => {
    try {
      await crawlerApi.retryTask(taskId)
      message.success('重试任务已创建')
      fetchTasks()
    } catch {
      message.error('重试失败')
    }
  }

  const handleDelete = async (taskId: number) => {
    try {
      await crawlerApi.deleteTask(taskId)
      message.success('删除成功')
      fetchTasks()
      fetchSyncStatus()
    } catch {
      message.error('删除失败')
    }
  }

  const handleViewDetail = async (task: CrawlerTask) => {
    setCurrentTask(task)
    setDetailModalVisible(true)
    setLogsLoading(true)

    try {
      const logs = await crawlerApi.getTaskLogs(task.id)
      setTaskLogs(logs)
    } catch {
      message.error('加载日志失败')
    } finally {
      setLogsLoading(false)
    }

    // 如果任务正在运行，建立 WebSocket 连接
    if (task.status === 'running') {
      connectWebSocket(task.id)
    }
  }

  const connectWebSocket = (taskId: number) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const ws = new WebSocket(`ws://${window.location.host}/api/v1/admin/crawler/ws/crawler/${taskId}`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.error) {
        message.error(data.error)
        return
      }

      // 更新当前任务进度
      setCurrentTask((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          status: data.status,
          success_items: data.success_items,
          failed_items: data.failed_items,
        }
      })

      // 如果任务完成，刷新列表
      if (data.status === 'success' || data.status === 'failed') {
        fetchTasks()
        fetchSyncStatus()
      }
    }

    ws.onerror = () => {
      message.error('WebSocket 连接失败')
    }

    wsRef.current = ws
  }

  const getStatusTag = (status: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      pending: { color: 'default', icon: <ClockCircleOutlined /> },
      running: { color: 'processing', icon: <LoadingOutlined /> },
      success: { color: 'success', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', icon: <CloseCircleOutlined /> },
    }
    const { color, icon } = config[status] || { color: 'default', icon: null }
    return (
      <Tag color={color} icon={icon}>
        {status}
      </Tag>
    )
  }

  const columns: ColumnsType<CrawlerTask> = [
    { title: 'ID', dataIndex: 'id', width: 70 },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      width: 120,
      render: (type) => {
        const labels: Record<string, string> = {
          taobao: '淘宝爬虫',
          jd: '京东爬虫',
          forum: '论坛爬虫',
        }
        return labels[type] || type
      },
    },
    {
      title: '任务名称',
      dataIndex: 'task_name',
      width: 200,
      ellipsis: true,
      render: (name) => name || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: getStatusTag,
    },
    {
      title: '进度',
      width: 180,
      render: (_, record) => {
        if (record.total_items === 0) return '-'
        const percent = Math.round((record.success_items / record.total_items) * 100)
        return (
          <Space direction="vertical" size={0} style={{ width: '100%' }}>
            <Progress percent={percent} size="small" status={record.status === 'failed' ? 'exception' : undefined} />
            <span style={{ fontSize: 12, color: '#999' }}>
              {record.success_items}/{record.total_items} (失败: {record.failed_items})
            </span>
          </Space>
        )
      },
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      width: 180,
      render: (time) => (time ? new Date(time).toLocaleString('zh-CN') : '-'),
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      width: 180,
      render: (time) => (time ? new Date(time).toLocaleString('zh-CN') : '-'),
    },
    {
      title: '操作',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'failed' && (
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => handleRetry(record.id)}
            >
              重试
            </Button>
          )}
          {record.status !== 'running' && (
            <Popconfirm
              title="确定删除此任务？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const getLogColor = (level: string) => {
    const colors: Record<string, string> = {
      info: 'blue',
      warning: 'orange',
      error: 'red',
    }
    return colors[level] || 'gray'
  }

  return (
    <div>
      {/* 同步状态概览 */}
      {syncStatus && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={24}>
            <Col span={4}>
              <Statistic title="总任务数" value={syncStatus.total_tasks} />
            </Col>
            <Col span={4}>
              <Statistic title="待处理" value={syncStatus.pending_tasks} valueStyle={{ color: '#999' }} />
            </Col>
            <Col span={4}>
              <Statistic
                title="运行中"
                value={syncStatus.running_tasks}
                valueStyle={{ color: '#1890ff' }}
                prefix={<SyncOutlined spin={syncStatus.running_tasks > 0} />}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="成功"
                value={syncStatus.success_tasks}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="失败"
                value={syncStatus.failed_tasks}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Col>
            <Col span={4}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#999', marginBottom: 8 }}>最后同步</div>
                <div>{syncStatus.last_sync_time ? new Date(syncStatus.last_sync_time).toLocaleString('zh-CN') : '-'}</div>
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* 任务列表 */}
      <Card title="爬虫任务管理">
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Select
              placeholder="任务类型"
              style={{ width: 130 }}
              allowClear
              value={typeFilter}
              onChange={(v) => {
                setTypeFilter(v)
                setPage(1)
              }}
            >
              <Select.Option value="taobao">淘宝爬虫</Select.Option>
              <Select.Option value="jd">京东爬虫</Select.Option>
              <Select.Option value="forum">论坛爬虫</Select.Option>
            </Select>

            <Select
              placeholder="状态"
              style={{ width: 120 }}
              allowClear
              value={statusFilter}
              onChange={(v) => {
                setStatusFilter(v)
                setPage(1)
              }}
            >
              <Select.Option value="pending">待处理</Select.Option>
              <Select.Option value="running">运行中</Select.Option>
              <Select.Option value="success">成功</Select.Option>
              <Select.Option value="failed">失败</Select.Option>
            </Select>

            <Button icon={<ReloadOutlined />} onClick={fetchTasks}>
              刷新
            </Button>

            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => setTriggerModalVisible(true)}
            >
              触发任务
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={tasks}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1300 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

      {/* 触发任务弹窗 */}
      <Modal
        title="触发爬虫任务"
        open={triggerModalVisible}
        onOk={handleTrigger}
        onCancel={() => {
          setTriggerModalVisible(false)
          form.resetFields()
        }}
        confirmLoading={triggerLoading}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="task_type"
            label="任务类型"
            rules={[{ required: true, message: '请选择任务类型' }]}
          >
            <Select placeholder="选择任务类型">
              <Select.Option value="taobao">淘宝爬虫</Select.Option>
              <Select.Option value="jd">京东爬虫</Select.Option>
              <Select.Option value="forum">论坛爬虫</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="keywords" label="搜索关键词" extra="多个关键词用逗号分隔">
            <Input placeholder="如: 路亚竿, 纺车轮, 鱼线" />
          </Form.Item>

          <Form.Item name="max_pages" label="最大爬取页数" initialValue={10}>
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="proxy" label="代理服务器" extra="可选，格式: http://host:port">
            <Input placeholder="http://127.0.0.1:7890" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务详情弹窗 */}
      <Modal
        title="任务详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false)
          setCurrentTask(null)
          setTaskLogs([])
          if (wsRef.current) {
            wsRef.current.close()
          }
        }}
        width={800}
        footer={null}
      >
        {currentTask && (
          <div>
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="任务ID">{currentTask.id}</Descriptions.Item>
              <Descriptions.Item label="状态">{getStatusTag(currentTask.status)}</Descriptions.Item>
              <Descriptions.Item label="任务类型">{currentTask.task_type}</Descriptions.Item>
              <Descriptions.Item label="任务名称">{currentTask.task_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="进度">
                {currentTask.success_items}/{currentTask.total_items} (失败: {currentTask.failed_items})
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {currentTask.start_time ? new Date(currentTask.start_time).toLocaleString('zh-CN') : '-'}
              </Descriptions.Item>
              {currentTask.error_message && (
                <Descriptions.Item label="错误信息" span={2}>
                  <span style={{ color: '#ff4d4f' }}>{currentTask.error_message}</span>
                </Descriptions.Item>
              )}
              {currentTask.result_summary && (
                <Descriptions.Item label="结果摘要" span={2}>
                  {currentTask.result_summary}
                </Descriptions.Item>
              )}
            </Descriptions>

            <Card title="运行日志" size="small" style={{ marginTop: 16 }} loading={logsLoading}>
              {taskLogs.length > 0 ? (
                <Timeline style={{ maxHeight: 300, overflow: 'auto' }}>
                  {taskLogs.map((log) => (
                    <Timeline.Item key={log.id} color={getLogColor(log.level)}>
                      <div>
                        <Tag color={getLogColor(log.level)}>{log.level.toUpperCase()}</Tag>
                        <span style={{ color: '#999', marginLeft: 8 }}>
                          {new Date(log.created_at).toLocaleTimeString('zh-CN')}
                        </span>
                      </div>
                      <div style={{ marginTop: 4 }}>{log.message}</div>
                      {log.details && (
                        <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>{log.details}</div>
                      )}
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>暂无日志</div>
              )}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Crawler
