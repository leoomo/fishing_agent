/**
 * Article List Page
 *
 * Features:
 * - Type/status filter
 * - Keyword search
 * - Table with actions
 * - Web scraping with progress tracking
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table,
  Button,
  Space,
  Tag,
  Input,
  Select,
  Popconfirm,
  message,
  Card,
  Progress,
  Modal,
  Tooltip,
  Badge,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  CloudDownloadOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  ClearOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { articleApi } from '@/api/services/article'
import type { ArticleListParams } from '@/api/services/article'
import type {
  ArticleListItem,
  ArticleType,
  ArticleStatus,
  ArticleFetchProgress,
  ArticleFetchProgressItem,
  FetchStatus,
} from '@/types/article'
import { ARTICLE_TYPE_CONFIG, ARTICLE_STATUS_CONFIG, FETCH_STATUS_CONFIG } from '@/types/article'

const ArticleList: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [articles, setArticles] = useState<ArticleListItem[]>([])
  const [total, setTotal] = useState(0)
  const [params, setParams] = useState<ArticleListParams>({
    page: 1,
    page_size: 20,
  })

  // Fetch state
  const [fetchProgress, setFetchProgress] = useState<ArticleFetchProgress | null>(null)
  const [fetchModalVisible, setFetchModalVisible] = useState(false)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  // Load articles
  const loadArticles = async () => {
    setLoading(true)
    try {
      const response = await articleApi.list(params)
      setArticles(response.items)
      setTotal(response.total)
    } catch (err) {
      message.error('加载文章列表失败')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadArticles()
  }, [params])

  // Load fetch progress
  const loadFetchProgress = useCallback(async () => {
    try {
      const progress = await articleApi.getFetchProgress()
      setFetchProgress(progress)
      return progress.is_running
    } catch (err) {
      console.error('Failed to load fetch progress:', err)
      return false
    }
  }, [])

  // Start polling when modal is open or fetch is running
  useEffect(() => {
    const startPolling = async () => {
      const isRunning = await loadFetchProgress()
      if (isRunning || fetchModalVisible) {
        pollingRef.current = setInterval(async () => {
          const stillRunning = await loadFetchProgress()
          if (!stillRunning && !fetchModalVisible) {
            if (pollingRef.current) {
              clearInterval(pollingRef.current)
              pollingRef.current = null
            }
            // Refresh article list after fetch completes
            loadArticles()
          }
        }, 2000)
      }
    }

    startPolling()

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [fetchModalVisible, loadFetchProgress])

  // Fetch handlers
  const handleStartFetch = async () => {
    try {
      await articleApi.startFetch()
      message.success('开始采集')
      loadFetchProgress()
    } catch (err) {
      message.error('启动采集失败')
      console.error(err)
    }
  }

  const handlePauseFetch = async () => {
    try {
      await articleApi.pauseFetch()
      message.success('正在暂停...')
      loadFetchProgress()
    } catch (err) {
      message.error('暂停失败')
      console.error(err)
    }
  }

  const handleRetryFailed = async () => {
    try {
      await articleApi.retryFailed()
      message.success('已重置失败项')
      loadFetchProgress()
    } catch (err) {
      message.error('重试失败')
      console.error(err)
    }
  }

  const handleResetProgress = async () => {
    try {
      await articleApi.resetProgress()
      message.success('已重置进度')
      loadFetchProgress()
    } catch (err) {
      message.error('重置失败')
      console.error(err)
    }
  }

  // Delete article
  const handleDelete = async (id: number) => {
    try {
      await articleApi.delete(id)
      message.success('删除成功')
      loadArticles()
    } catch (err) {
      message.error('删除失败')
      console.error(err)
    }
  }

  // Table columns
  const columns: ColumnsType<ArticleListItem> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title, record) => (
        <a onClick={() => navigate(`/content/articles/edit/${record.id}`)}>{title}</a>
      ),
    },
    {
      title: '类型',
      dataIndex: 'article_type',
      key: 'article_type',
      width: 120,
      render: (type: ArticleType) => {
        const config = ARTICLE_TYPE_CONFIG[type]
        return config ? (
          <Tag color={config.color}>
            {config.icon} {config.label}
          </Tag>
        ) : (
          type
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: ArticleStatus) => {
        const config = ARTICLE_STATUS_CONFIG[status]
        return config ? <Tag color={config.color}>{config.label}</Tag> : status
      },
    },
    {
      title: '作者',
      dataIndex: 'author_name',
      key: 'author_name',
      width: 100,
    },
    {
      title: '阅读',
      dataIndex: 'view_count',
      key: 'view_count',
      width: 80,
      align: 'right',
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => navigate(`/content/articles/edit/${record.id}`)}
          />
          <Popconfirm
            title="确定删除这篇文章吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Card>
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 24,
          }}
        >
          <h2 style={{ margin: 0 }}>文章管理</h2>
          <Space>
            <Badge
              dot={fetchProgress?.is_running}
              offset={[-5, 5]}
            >
              <Button
                icon={<CloudDownloadOutlined />}
                onClick={() => setFetchModalVisible(true)}
              >
                网络采集
              </Button>
            </Badge>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/content/articles/create')}
            >
              写文章
            </Button>
          </Space>
        </div>

        {/* Fetch Progress Banner (when running) */}
        {fetchProgress?.is_running && (
          <div
            style={{
              marginBottom: 16,
              padding: '12px 16px',
              background: '#e6f7ff',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <Space>
              <CloudDownloadOutlined style={{ color: '#1890ff' }} />
              <span>正在采集文章...</span>
              <Progress
                percent={Math.round(
                  ((fetchProgress.stats.completed + fetchProgress.stats.failed + fetchProgress.stats.skipped) /
                    fetchProgress.stats.total) *
                    100
                )}
                size="small"
                style={{ width: 120 }}
              />
              <span style={{ color: '#666' }}>
                {fetchProgress.stats.completed}/{fetchProgress.stats.total}
              </span>
            </Space>
            <Button
              size="small"
              icon={<PauseCircleOutlined />}
              onClick={handlePauseFetch}
            >
              暂停
            </Button>
          </div>
        )}

        {/* Filters */}
        <Space wrap style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索标题..."
            prefix={<SearchOutlined />}
            allowClear
            style={{ width: 200 }}
            onChange={(e) =>
              setParams((prev) => ({ ...prev, keyword: e.target.value, page: 1 }))
            }
          />
          <Select
            placeholder="文章类型"
            allowClear
            style={{ width: 140 }}
            onChange={(value) =>
              setParams((prev) => ({ ...prev, article_type: value, page: 1 }))
            }
            options={Object.entries(ARTICLE_TYPE_CONFIG).map(([value, config]) => ({
              value,
              label: `${config.icon} ${config.label}`,
            }))}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 120 }}
            onChange={(value) =>
              setParams((prev) => ({ ...prev, status: value, page: 1 }))
            }
            options={Object.entries(ARTICLE_STATUS_CONFIG).map(([value, config]) => ({
              value,
              label: config.label,
            }))}
          />
        </Space>

        {/* Table */}
        <Table
          columns={columns}
          dataSource={articles}
          rowKey="id"
          loading={loading}
          pagination={{
            current: params.page,
            pageSize: params.page_size,
            total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 篇文章`,
            onChange: (page, pageSize) =>
              setParams((prev) => ({ ...prev, page, page_size: pageSize })),
          }}
        />
      </Card>

      {/* Fetch Progress Modal */}
      <FetchProgressModal
        visible={fetchModalVisible}
        onClose={() => setFetchModalVisible(false)}
        progress={fetchProgress}
        onStart={handleStartFetch}
        onPause={handlePauseFetch}
        onRetry={handleRetryFailed}
        onReset={handleResetProgress}
      />
    </div>
  )
}

// Fetch Progress Modal Component
const FetchProgressModal: React.FC<{
  visible: boolean
  onClose: () => void
  progress: ArticleFetchProgress | null
  onStart: () => void
  onPause: () => void
  onRetry: () => void
  onReset: () => void
}> = ({ visible, onClose, progress, onStart, onPause, onRetry, onReset }) => {
  if (!progress) return null

  const { stats, items, is_running } = progress
  const completedPercent = Math.round(
    ((stats.completed + stats.failed + stats.skipped) / stats.total) * 100
  )

  // Progress item columns
  const progressColumns: ColumnsType<ArticleFetchProgressItem> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title, record) => (
        <Tooltip title={record.source_url}>
          <span>{title || record.source_url}</span>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: FetchStatus) => {
        const config = FETCH_STATUS_CONFIG[status]
        return config ? <Tag color={config.color}>{config.label}</Tag> : status
      },
    },
    {
      title: '文章ID',
      dataIndex: 'article_id',
      key: 'article_id',
      width: 80,
      render: (id) => id || '-',
    },
    {
      title: '错误',
      dataIndex: 'error',
      key: 'error',
      width: 150,
      ellipsis: true,
      render: (error) =>
        error ? (
          <Tooltip title={error}>
            <span style={{ color: '#ff4d4f' }}>{error}</span>
          </Tooltip>
        ) : (
          '-'
        ),
    },
  ]

  return (
    <Modal
      title="网络采集"
      open={visible}
      onCancel={onClose}
      width={800}
      footer={null}
    >
      {/* Stats */}
      <div style={{ marginBottom: 16 }}>
        <Space size="large">
          <span>总计: {stats.total}</span>
          <span style={{ color: '#52c41a' }}>完成: {stats.completed}</span>
          <span style={{ color: '#1890ff' }}>进行中: {stats.fetching + stats.enriching}</span>
          <span style={{ color: '#ff4d4f' }}>失败: {stats.failed}</span>
          <span>待处理: {stats.pending}</span>
        </Space>
      </div>

      {/* Progress bar */}
      <Progress
        percent={completedPercent}
        status={is_running ? 'active' : 'normal'}
        style={{ marginBottom: 16 }}
      />

      {/* Actions */}
      <Space style={{ marginBottom: 16 }}>
        {is_running ? (
          <Button icon={<PauseCircleOutlined />} onClick={onPause}>
            暂停采集
          </Button>
        ) : (
          <Button type="primary" icon={<CloudDownloadOutlined />} onClick={onStart}>
            {stats.pending > 0 ? '继续采集' : '开始采集'}
          </Button>
        )}
        <Button
          icon={<ReloadOutlined />}
          onClick={onRetry}
          disabled={is_running || stats.failed === 0}
        >
          重试失败 ({stats.failed})
        </Button>
        <Popconfirm
          title="确定要重置所有进度吗？"
          onConfirm={onReset}
          disabled={is_running}
        >
          <Button icon={<ClearOutlined />} disabled={is_running} danger>
            重置进度
          </Button>
        </Popconfirm>
      </Space>

      {/* Progress table */}
      <Table
        columns={progressColumns}
        dataSource={items}
        rowKey="source_url"
        size="small"
        pagination={{ pageSize: 10, showSizeChanger: false }}
        scroll={{ y: 300 }}
      />
    </Modal>
  )
}

export default ArticleList
