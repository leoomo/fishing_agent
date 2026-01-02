/**
 * Article content types
 */

export type ArticleType = 'strategy' | 'tips' | 'review' | 'spot'
export type ArticleStatus = 'draft' | 'published' | 'archived'

export interface Article {
  id: number
  title: string
  content: string
  article_type: ArticleType
  status: ArticleStatus
  author_id?: number
  author_name?: string
  cover_image?: string
  summary?: string
  tags: string[]
  extensions?: Record<string, unknown>
  view_count: number
  like_count: number
  created_at: string
  updated_at: string
  published_at?: string
}

export interface ArticleListItem {
  id: number
  title: string
  article_type: ArticleType
  status: ArticleStatus
  author_id?: number
  author_name?: string
  cover_image?: string
  summary?: string
  tags: string[]
  view_count: number
  created_at: string
  updated_at: string
}

export interface ArticleListResponse {
  total: number
  page: number
  page_size: number
  items: ArticleListItem[]
}

export interface ArticleCreateRequest {
  title: string
  article_type: ArticleType
  content?: string
  cover_image?: string
  summary?: string
  tags?: string
  extensions?: Record<string, unknown>
}

export interface ArticleUpdateRequest {
  title?: string
  content?: string
  article_type?: ArticleType
  cover_image?: string
  summary?: string
  tags?: string
  extensions?: Record<string, unknown>
}

export interface ArticlePublishRequest {
  summary?: string
  tags?: string
}

export interface ArticleSearchResult {
  id: number
  title: string
  article_type: ArticleType
  summary?: string
  score: number
}

export interface ArticleSearchResponse {
  query: string
  results: ArticleSearchResult[]
  total: number
}

// Article type configurations
export const ARTICLE_TYPE_CONFIG: Record<ArticleType, {
  label: string
  icon: string
  color: string
  description: string
}> = {
  strategy: {
    label: '钓鱼攻略',
    icon: '🎯',
    color: 'blue',
    description: '针对特定鱼种/水域/季节的完整指南',
  },
  tips: {
    label: '技巧分享',
    icon: '💡',
    color: 'green',
    description: '短小精悍的技巧Tips',
  },
  review: {
    label: '装备评测',
    icon: '⭐',
    color: 'gold',
    description: '装备使用体验和对比',
  },
  spot: {
    label: '钓点推荐',
    icon: '📍',
    color: 'purple',
    description: '钓点信息和经验',
  },
}

export const ARTICLE_STATUS_CONFIG: Record<ArticleStatus, {
  label: string
  color: string
}> = {
  draft: {
    label: '草稿',
    color: 'default',
  },
  published: {
    label: '已发布',
    color: 'success',
  },
  archived: {
    label: '已归档',
    color: 'default',
  },
}
