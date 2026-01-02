/**
 * Article List Page
 *
 * Features:
 * - Type/status filter
 * - Keyword search
 * - Table with actions
 */

import React, { useState, useEffect } from 'react'
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
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { articleApi } from '@/api/services/article'
import type { ArticleListParams } from '@/api/services/article'
import type { ArticleListItem, ArticleType, ArticleStatus } from '@/types/article'
import { ARTICLE_TYPE_CONFIG, ARTICLE_STATUS_CONFIG } from '@/types/article'

const ArticleList: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [articles, setArticles] = useState<ArticleListItem[]>([])
  const [total, setTotal] = useState(0)
  const [params, setParams] = useState<ArticleListParams>({
    page: 1,
    page_size: 20,
  })

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
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/content/articles/create')}
          >
            写文章
          </Button>
        </div>

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
    </div>
  )
}

export default ArticleList
