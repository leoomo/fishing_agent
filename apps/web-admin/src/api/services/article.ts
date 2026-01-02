/**
 * Article API service
 */

import client from '../client'
import type {
  Article,
  ArticleListResponse,
  ArticleCreateRequest,
  ArticleUpdateRequest,
  ArticlePublishRequest,
  ArticleSearchResponse,
  ArticleType,
  ArticleStatus,
} from '@/types/article'

export interface ArticleListParams {
  page?: number
  page_size?: number
  article_type?: ArticleType
  status?: ArticleStatus
  keyword?: string
  author_id?: number
}

export const articleApi = {
  /**
   * List articles with filters
   */
  list: (params: ArticleListParams = {}): Promise<ArticleListResponse> => {
    return client.get('/admin/articles', { params })
  },

  /**
   * Get article by ID
   */
  get: (id: number): Promise<Article> => {
    return client.get(`/admin/articles/${id}`)
  },

  /**
   * Create article (draft)
   */
  create: (data: ArticleCreateRequest): Promise<Article> => {
    return client.post('/admin/articles', data)
  },

  /**
   * Update article (used for auto-save)
   */
  update: (id: number, data: ArticleUpdateRequest): Promise<Article> => {
    return client.put(`/admin/articles/${id}`, data)
  },

  /**
   * Delete article
   */
  delete: (id: number): Promise<void> => {
    return client.delete(`/admin/articles/${id}`)
  },

  /**
   * Publish article
   */
  publish: (id: number, data?: ArticlePublishRequest): Promise<Article> => {
    return client.post(`/admin/articles/${id}/publish`, data || {})
  },

  /**
   * Archive article
   */
  archive: (id: number): Promise<Article> => {
    return client.post(`/admin/articles/${id}/archive`)
  },

  /**
   * Semantic search
   */
  search: (params: {
    q: string
    article_type?: ArticleType
    limit?: number
  }): Promise<ArticleSearchResponse> => {
    return client.get('/admin/articles/search', { params })
  },

  /**
   * Get similar articles
   */
  getSimilar: (id: number, limit?: number): Promise<ArticleSearchResponse> => {
    return client.get(`/admin/articles/${id}/similar`, {
      params: { limit: limit || 5 },
    })
  },
}
