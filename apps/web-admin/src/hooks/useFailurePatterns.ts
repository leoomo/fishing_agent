import { useState, useEffect, useCallback } from 'react'
import client from '@/api/client'

export interface FailurePattern {
  pattern_id: string
  pattern_type: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  frequency: number
  affected_services: string[]
  confidence: number
  detected_at: string
  metadata: Record<string, any>
}

export interface ErrorChain {
  correlation_id: string
  errors: Array<{
    timestamp: string
    service: string
    endpoint?: string
    agent_type?: string
    error_category?: string
    severity?: string
    failure_stage?: string
    error_message?: string
    status_code?: number
    success?: boolean
    failed_tool_name?: string
  }>
  root_cause: string
  impact_score: number
  total_errors: number
}

export interface RootCause {
  cause_id: string
  cause_type: string
  description: string
  confidence: number
  evidence: string[]
  suggested_action: string
  generated_at: string
}

interface FailureMetrics {
  api_error_rate_24h: number
  agent_success_rate_24h: number
  error_categories_24h: Array<{ category: string; count: number }>
  top_error_messages_7d: Array<{ message: string; count: number }>
  mttr_minutes?: number
}

interface UseFailurePatternsReturn {
  patterns: FailurePattern[]
  errorChains: Record<string, ErrorChain>
  rootCauses: RootCause[]
  metrics: FailureMetrics | null
  loading: {
    patterns: boolean
    correlation: boolean
    rootCauses: boolean
    metrics: boolean
  }
  error: string | null
  fetchPatterns: (timeRange: string) => Promise<void>
  fetchErrorCorrelation: (correlationId: string) => Promise<ErrorChain | null>
  fetchRootCauses: (timeRange: string) => Promise<void>
  fetchMetrics: () => Promise<void>
  clearError: () => void
}

export const useFailurePatterns = (): UseFailurePatternsReturn => {
  const [patterns, setPatterns] = useState<FailurePattern[]>([])
  const [errorChains, setErrorChains] = useState<Record<string, ErrorChain>>({})
  const [rootCauses, setRootCauses] = useState<RootCause[]>([])
  const [metrics, setMetrics] = useState<FailureMetrics | null>(null)
  const [loading, setLoading] = useState({
    patterns: false,
    correlation: false,
    rootCauses: false,
    metrics: false,
  })
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const fetchPatterns = useCallback(async (timeRange: string = '1h') => {
    setLoading(prev => ({ ...prev, patterns: true }))
    setError(null)

    try {
      const response = await client.get(`/admin/monitor/failure-patterns`, {
        params: { time_range: timeRange }
      })
      setPatterns(response.data?.patterns || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch failure patterns')
      console.error('Error fetching failure patterns:', err)
    } finally {
      setLoading(prev => ({ ...prev, patterns: false }))
    }
  }, [])

  const fetchErrorCorrelation = useCallback(async (correlationId: string): Promise<ErrorChain | null> => {
    setLoading(prev => ({ ...prev, correlation: true }))
    setError(null)

    try {
      const response = await client.get(`/admin/monitor/error-correlation/${correlationId}`)
      const data = response.data
      const errorChain: ErrorChain = {
        correlation_id: data.correlation_id,
        errors: data.errors,
        root_cause: data.root_cause,
        impact_score: data.impact_score,
        total_errors: data.total_errors,
      }

      setErrorChains(prev => ({
        ...prev,
        [correlationId]: errorChain
      }))

      return errorChain
    } catch (err: any) {
      if (err.response?.status === 404) {
        return null
      }
      setError(err instanceof Error ? err.message : 'Failed to fetch error correlation')
      console.error('Error fetching error correlation:', err)
      return null
    } finally {
      setLoading(prev => ({ ...prev, correlation: false }))
    }
  }, [])

  const fetchRootCauses = useCallback(async (timeRange: string = '24h') => {
    setLoading(prev => ({ ...prev, rootCauses: true }))
    setError(null)

    try {
      const response = await client.get(`/admin/monitor/root-cause-analysis`, {
        params: { time_range: timeRange }
      })
      setRootCauses(response.data?.root_causes || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch root causes')
      console.error('Error fetching root causes:', err)
    } finally {
      setLoading(prev => ({ ...prev, rootCauses: false }))
    }
  }, [])

  const fetchMetrics = useCallback(async () => {
    setLoading(prev => ({ ...prev, metrics: true }))
    setError(null)

    try {
      const response = await client.get('/admin/monitor/failure-metrics')
      setMetrics(response.data?.metrics)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch failure metrics')
      console.error('Error fetching failure metrics:', err)
    } finally {
      setLoading(prev => ({ ...prev, metrics: false }))
    }
  }, [])

  // Auto-refresh patterns and metrics every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchPatterns()
      fetchMetrics()
    }, 30000)

    // Initial fetch
    fetchPatterns()
    fetchMetrics()

    return () => clearInterval(interval)
  }, [fetchPatterns, fetchMetrics])

  return {
    patterns,
    errorChains,
    rootCauses,
    metrics,
    loading,
    error,
    fetchPatterns,
    fetchErrorCorrelation,
    fetchRootCauses,
    fetchMetrics,
    clearError,
  }
}