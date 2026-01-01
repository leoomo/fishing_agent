/**
 * Rig configuration API service
 */

import client from '../client'
import type {
  Rig,
  RigListItem,
  RigListResponse,
  RigCreateRequest,
  RigUpdateRequest,
  RigSpec,
  RigSpecCreate,
  RigSpecUpdate,
  RigComponent,
  RigComponentCreate,
  RigComponentUpdate,
  RigOptionsResponse,
  LureTypeSimple,
  RigCategory,
  RigDifficulty,
} from '@/types/rig'

export interface RigListParams {
  page?: number
  page_size?: number
  category?: RigCategory
  difficulty?: RigDifficulty
  keyword?: string
}

export const rigApi = {
  // ========== Rig CRUD ==========

  /**
   * List rigs with filters
   */
  list: (params: RigListParams = {}): Promise<RigListResponse> => {
    return client.get('/admin/content/rigs', { params })
  },

  /**
   * Get featured rigs for cards display
   */
  getFeatured: (limit?: number): Promise<RigListItem[]> => {
    return client.get('/admin/content/rigs/featured', {
      params: { limit: limit || 4 },
    })
  },

  /**
   * Get rig by ID
   */
  get: (id: number): Promise<Rig> => {
    return client.get(`/admin/content/rigs/${id}`)
  },

  /**
   * Create rig
   */
  create: (data: RigCreateRequest): Promise<Rig> => {
    return client.post('/admin/content/rigs', data)
  },

  /**
   * Update rig
   */
  update: (id: number, data: RigUpdateRequest): Promise<Rig> => {
    return client.put(`/admin/content/rigs/${id}`, data)
  },

  /**
   * Delete rig
   */
  delete: (id: number): Promise<void> => {
    return client.delete(`/admin/content/rigs/${id}`)
  },

  // ========== Spec Management ==========

  /**
   * Add spec to rig
   */
  addSpec: (rigId: number, data: RigSpecCreate): Promise<RigSpec> => {
    return client.post(`/admin/content/rigs/${rigId}/specs`, data)
  },

  /**
   * Update spec
   */
  updateSpec: (rigId: number, specId: number, data: RigSpecUpdate): Promise<RigSpec> => {
    return client.put(`/admin/content/rigs/${rigId}/specs/${specId}`, data)
  },

  /**
   * Delete spec
   */
  deleteSpec: (rigId: number, specId: number): Promise<void> => {
    return client.delete(`/admin/content/rigs/${rigId}/specs/${specId}`)
  },

  // ========== Component Management ==========

  /**
   * Add component to rig
   */
  addComponent: (rigId: number, data: RigComponentCreate): Promise<RigComponent> => {
    return client.post(`/admin/content/rigs/${rigId}/components`, data)
  },

  /**
   * Update component
   */
  updateComponent: (
    rigId: number,
    componentId: number,
    data: RigComponentUpdate
  ): Promise<RigComponent> => {
    return client.put(`/admin/content/rigs/${rigId}/components/${componentId}`, data)
  },

  /**
   * Delete component
   */
  deleteComponent: (rigId: number, componentId: number): Promise<void> => {
    return client.delete(`/admin/content/rigs/${rigId}/components/${componentId}`)
  },

  /**
   * Reorder components
   */
  reorderComponents: (rigId: number, componentIds: number[]): Promise<void> => {
    return client.put(`/admin/content/rigs/${rigId}/components/reorder`, {
      component_ids: componentIds,
    })
  },

  // ========== Lure Type Association ==========

  /**
   * Get lure types associated with rig
   */
  getLureTypes: (rigId: number): Promise<LureTypeSimple[]> => {
    return client.get(`/admin/content/rigs/${rigId}/lure-types`)
  },

  /**
   * Set lure types for rig
   */
  setLureTypes: (rigId: number, lureTypeIds: number[]): Promise<LureTypeSimple[]> => {
    return client.put(`/admin/content/rigs/${rigId}/lure-types`, {
      lure_type_ids: lureTypeIds,
    })
  },

  // ========== Options ==========

  /**
   * Get rig form options (categories, difficulties, component types)
   */
  getOptions: (): Promise<RigOptionsResponse> => {
    return client.get('/admin/content/rig-options')
  },

  /**
   * Get all lure types for association (simple list)
   */
  getAllLureTypes: (): Promise<LureTypeSimple[]> => {
    return client.get('/admin/content/lure-types/simple')
  },
}
