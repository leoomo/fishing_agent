/**
 * Article Editor - Jobs-style minimalist design
 *
 * Features:
 * - Type selector + title in one row
 * - Large content area with markdown support
 * - Auto-save with status indicator
 * - Optional fields via expandable buttons
 * - Preview drawer
 */

import React, { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Input,
  Select,
  Button,
  Drawer,
  Space,
  Tag,
  message,
  Spin,
  Typography,
} from 'antd'
import {
  PictureOutlined,
  TagsOutlined,
  SettingOutlined,
  EyeOutlined,
  CheckOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons'
import { articleApi } from '@/api/services/article'
import { useAutoSave } from './hooks/useAutoSave'
import type { SaveStatus } from './hooks/useAutoSave'
import type {
  Article,
  ArticleType,
  ArticleCreateRequest,
  ArticleUpdateRequest,
} from '@/types/article'
import { ARTICLE_TYPE_CONFIG } from '@/types/article'
import styles from './Editor.module.css'

const { TextArea } = Input
const { Text } = Typography

// Save status indicator component
const SaveIndicator: React.FC<{ status: SaveStatus; lastSavedAt: Date | null }> = ({
  status,
  lastSavedAt,
}) => {
  const config = {
    idle: { icon: null, text: '', color: 'default' },
    saving: { icon: <LoadingOutlined />, text: '保存中...', color: 'processing' },
    saved: { icon: <CheckOutlined />, text: '已保存', color: 'success' },
    error: { icon: <ExclamationCircleOutlined />, text: '保存失败', color: 'error' },
  }

  const current = config[status]
  if (!current.text && !lastSavedAt) return null

  return (
    <Space size={4}>
      {current.icon}
      <Text type={current.color === 'error' ? 'danger' : 'secondary'} style={{ fontSize: 12 }}>
        {current.text || (lastSavedAt ? `上次保存: ${lastSavedAt.toLocaleTimeString()}` : '')}
      </Text>
    </Space>
  )
}

// Tags input component
const TagsInput: React.FC<{
  value: string
  onChange: (value: string) => void
}> = ({ value, onChange }) => {
  const [inputValue, setInputValue] = useState('')
  const tags = value ? value.split(',').filter(Boolean) : []

  const handleAdd = () => {
    if (inputValue.trim() && !tags.includes(inputValue.trim())) {
      const newTags = [...tags, inputValue.trim()]
      onChange(newTags.join(','))
      setInputValue('')
    }
  }

  const handleRemove = (tag: string) => {
    const newTags = tags.filter((t) => t !== tag)
    onChange(newTags.join(','))
  }

  return (
    <div>
      <Space wrap style={{ marginBottom: 8 }}>
        {tags.map((tag) => (
          <Tag key={tag} closable onClose={() => handleRemove(tag)}>
            {tag}
          </Tag>
        ))}
      </Space>
      <Input
        placeholder="输入标签后按回车"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onPressEnter={handleAdd}
        style={{ width: 200 }}
      />
    </div>
  )
}

const ArticleEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // Form state
  const [article, setArticle] = useState<Partial<Article>>({
    title: '',
    content: '',
    article_type: 'strategy',
    tags: [],
    cover_image: '',
    summary: '',
  })
  const [loading, setLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [articleId, setArticleId] = useState<number | null>(id ? parseInt(id) : null)

  // Drawer states
  const [coverDrawerOpen, setCoverDrawerOpen] = useState(false)
  const [tagsDrawerOpen, setTagsDrawerOpen] = useState(false)
  const [previewDrawerOpen, setPreviewDrawerOpen] = useState(false)

  // Load article if editing
  useEffect(() => {
    if (id) {
      setLoading(true)
      articleApi
        .get(parseInt(id))
        .then((data) => {
          setArticle({
            ...data,
          })
        })
        .catch((err) => {
          message.error('加载文章失败')
          console.error(err)
        })
        .finally(() => setLoading(false))
    }
  }, [id])

  // Save data for auto-save
  const saveData = useMemo(
    () => ({
      title: article.title || '',
      content: article.content || '',
      article_type: article.article_type as ArticleType,
      cover_image: article.cover_image,
      summary: article.summary,
      tags: Array.isArray(article.tags) ? article.tags.join(',') : article.tags,
    }),
    [article]
  )

  // Auto-save handler
  const handleAutoSave = async (data: typeof saveData) => {
    if (!data.title?.trim()) return // Don't save without title

    if (articleId) {
      // Update existing
      await articleApi.update(articleId, data as ArticleUpdateRequest)
    } else {
      // Create new
      const created = await articleApi.create(data as ArticleCreateRequest)
      setArticleId(created.id)
      // Update URL without navigation
      window.history.replaceState(null, '', `/content/articles/edit/${created.id}`)
    }
  }

  // Auto-save hook
  const { status, lastSavedAt, saveNow } = useAutoSave({
    data: saveData,
    onSave: handleAutoSave,
    debounceMs: 2000,
    enabled: Boolean(article.title?.trim()),
  })

  // Update form field
  const updateField = <K extends keyof Article>(field: K, value: Article[K]) => {
    setArticle((prev) => ({ ...prev, [field]: value }))
  }

  // Publish article
  const handlePublish = async () => {
    if (!article.title?.trim()) {
      message.warning('请输入文章标题')
      return
    }
    if (!article.content?.trim()) {
      message.warning('请输入文章内容')
      return
    }

    setPublishing(true)
    try {
      // First save
      await saveNow()

      if (articleId) {
        await articleApi.publish(articleId, {
          summary: article.summary,
          tags: Array.isArray(article.tags) ? article.tags.join(',') : article.tags,
        })
        message.success('发布成功')
        navigate('/content/articles')
      }
    } catch (err) {
      message.error('发布失败')
      console.error(err)
    } finally {
      setPublishing(false)
    }
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/content/articles')}
        >
          返回
        </Button>
        <div className={styles.headerRight}>
          <SaveIndicator status={status} lastSavedAt={lastSavedAt} />
        </div>
      </div>

      {/* Title row: Type selector + Title */}
      <div className={styles.titleRow}>
        <Select
          value={article.article_type}
          onChange={(value) => updateField('article_type', value)}
          className={styles.typeSelect}
          options={Object.entries(ARTICLE_TYPE_CONFIG).map(([value, config]) => ({
            value,
            label: (
              <span>
                {config.icon} {config.label}
              </span>
            ),
          }))}
        />
        <Input
          placeholder="输入文章标题..."
          value={article.title}
          onChange={(e) => updateField('title', e.target.value)}
          className={styles.titleInput}
          variant="borderless"
        />
      </div>

      {/* Content area */}
      <TextArea
        placeholder="开始写作..."
        value={article.content}
        onChange={(e) => updateField('content', e.target.value)}
        className={styles.contentArea}
        autoSize={{ minRows: 20 }}
        variant="borderless"
      />

      {/* Action bar */}
      <div className={styles.actionBar}>
        <Space>
          <Button
            icon={<PictureOutlined />}
            onClick={() => setCoverDrawerOpen(true)}
            type={article.cover_image ? 'primary' : 'default'}
            ghost={Boolean(article.cover_image)}
          >
            封面
          </Button>
          <Button
            icon={<TagsOutlined />}
            onClick={() => setTagsDrawerOpen(true)}
            type={article.tags?.length ? 'primary' : 'default'}
            ghost={Boolean(article.tags?.length)}
          >
            标签
          </Button>
          <Button icon={<SettingOutlined />} disabled>
            更多
          </Button>
        </Space>
        <Space>
          <Button icon={<EyeOutlined />} onClick={() => setPreviewDrawerOpen(true)}>
            预览
          </Button>
          <Button
            type="primary"
            onClick={handlePublish}
            loading={publishing}
            disabled={!article.title?.trim() || !article.content?.trim()}
          >
            发布
          </Button>
        </Space>
      </div>

      {/* Cover Drawer */}
      <Drawer
        title="设置封面图"
        open={coverDrawerOpen}
        onClose={() => setCoverDrawerOpen(false)}
        width={400}
      >
        <Input
          placeholder="输入图片 URL"
          value={article.cover_image || ''}
          onChange={(e) => updateField('cover_image', e.target.value)}
        />
        {article.cover_image && (
          <div style={{ marginTop: 16 }}>
            <img
              src={article.cover_image}
              alt="cover"
              style={{ maxWidth: '100%', borderRadius: 8 }}
            />
          </div>
        )}
      </Drawer>

      {/* Tags Drawer */}
      <Drawer
        title="设置标签"
        open={tagsDrawerOpen}
        onClose={() => setTagsDrawerOpen(false)}
        width={400}
      >
        <TagsInput
          value={Array.isArray(article.tags) ? article.tags.join(',') : (article.tags || '')}
          onChange={(value) => updateField('tags', value.split(',').filter(Boolean))}
        />
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">添加标签可以帮助用户更快找到你的文章</Text>
        </div>
      </Drawer>

      {/* Preview Drawer */}
      <Drawer
        title="预览"
        open={previewDrawerOpen}
        onClose={() => setPreviewDrawerOpen(false)}
        width={600}
      >
        <div className={styles.preview}>
          {article.cover_image && (
            <img
              src={article.cover_image}
              alt="cover"
              style={{ width: '100%', borderRadius: 8, marginBottom: 16 }}
            />
          )}
          <h1>{article.title || '无标题'}</h1>
          {article.tags && article.tags.length > 0 && (
            <Space wrap style={{ marginBottom: 16 }}>
              {(Array.isArray(article.tags) ? article.tags : String(article.tags).split(',')).map(
                (tag: string) => (
                  <Tag key={tag}>{tag}</Tag>
                )
              )}
            </Space>
          )}
          <div style={{ whiteSpace: 'pre-wrap' }}>{article.content}</div>
        </div>
      </Drawer>
    </div>
  )
}

export default ArticleEditor
