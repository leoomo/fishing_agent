import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { EquipmentSearchFilters } from '@/types/equipment'

interface UseEquipmentSearchOptions {
  defaultPageSize?: number
  debounceMs?: number
}

interface UseEquipmentSearchReturn {
  filters: EquipmentSearchFilters
  page: number
  pageSize: number
  setFilters: (filters: EquipmentSearchFilters) => void
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void
  resetFilters: () => void
  // 用于 API 请求的参数
  searchParams: EquipmentSearchFilters & { page: number; page_size: number }
}

// URL 参数键映射
const URL_PARAM_KEYS: (keyof EquipmentSearchFilters)[] = [
  'category',
  'brand_id',
  'keyword',
  'price_min',
  'price_max',
  'user_level',
  'is_active',
  'power',
  'action',
  'length_min',
  'length_max',
]

export function useEquipmentSearch(
  options: UseEquipmentSearchOptions = {}
): UseEquipmentSearchReturn {
  const { defaultPageSize = 20, debounceMs = 300 } = options
  const [searchParams, setSearchParams] = useSearchParams()
  const debounceTimerRef = useRef<number | null>(null)

  // 从 URL 解析初始筛选条件
  const parseFiltersFromURL = useCallback((): EquipmentSearchFilters => {
    const filters: EquipmentSearchFilters = {}

    URL_PARAM_KEYS.forEach((key) => {
      const value = searchParams.get(key)
      if (value !== null && value !== '') {
        if (key === 'brand_id') {
          filters[key] = parseInt(value, 10)
        } else if (key === 'price_min' || key === 'price_max' || key === 'length_min' || key === 'length_max') {
          filters[key] = parseFloat(value)
        } else if (key === 'is_active') {
          filters[key] = value === 'true'
        } else {
          filters[key] = value
        }
      }
    })

    return filters
  }, [searchParams])

  // 状态
  const [filters, setFiltersState] = useState<EquipmentSearchFilters>(parseFiltersFromURL)
  const [page, setPageState] = useState(() => {
    const pageParam = searchParams.get('page')
    return pageParam ? parseInt(pageParam, 10) : 1
  })
  const [pageSize, setPageSizeState] = useState(() => {
    const pageSizeParam = searchParams.get('page_size')
    return pageSizeParam ? parseInt(pageSizeParam, 10) : defaultPageSize
  })

  // 同步筛选条件到 URL（防抖）
  const syncToURL = useCallback(
    (newFilters: EquipmentSearchFilters, newPage: number, newPageSize: number) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }

      debounceTimerRef.current = window.setTimeout(() => {
        const params = new URLSearchParams()

        // 添加筛选参数
        Object.entries(newFilters).forEach(([key, value]) => {
          if (value !== undefined && value !== '' && value !== null) {
            params.set(key, String(value))
          }
        })

        // 添加分页参数
        if (newPage !== 1) {
          params.set('page', String(newPage))
        }
        if (newPageSize !== defaultPageSize) {
          params.set('page_size', String(newPageSize))
        }

        setSearchParams(params, { replace: true })
      }, debounceMs)
    },
    [setSearchParams, defaultPageSize, debounceMs]
  )

  // 设置筛选条件
  const setFilters = useCallback(
    (newFilters: EquipmentSearchFilters) => {
      setFiltersState(newFilters)
      setPageState(1) // 筛选条件变更时重置页码
      syncToURL(newFilters, 1, pageSize)
    },
    [pageSize, syncToURL]
  )

  // 设置页码
  const setPage = useCallback(
    (newPage: number) => {
      setPageState(newPage)
      syncToURL(filters, newPage, pageSize)
    },
    [filters, pageSize, syncToURL]
  )

  // 设置每页数量
  const setPageSize = useCallback(
    (newPageSize: number) => {
      setPageSizeState(newPageSize)
      setPageState(1) // 每页数量变更时重置页码
      syncToURL(filters, 1, newPageSize)
    },
    [filters, syncToURL]
  )

  // 重置筛选条件
  const resetFilters = useCallback(() => {
    setFiltersState({})
    setPageState(1)
    setSearchParams({}, { replace: true })
  }, [setSearchParams])

  // 清理定时器
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  // 构建 API 请求参数（使用 useMemo 稳定化引用）
  const apiParams = useMemo(
    () => ({
      ...filters,
      page,
      page_size: pageSize,
    }),
    [filters, page, pageSize]
  )

  return {
    filters,
    page,
    pageSize,
    setFilters,
    setPage,
    setPageSize,
    resetFilters,
    searchParams: apiParams,
  }
}
