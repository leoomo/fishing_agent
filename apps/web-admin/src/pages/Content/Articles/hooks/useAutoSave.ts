/**
 * Auto-save hook for article editor
 *
 * Features:
 * - Debounced save (default 2s)
 * - Save status indicator
 * - Error handling
 */

import { useState, useEffect, useRef, useCallback } from 'react'

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

interface UseAutoSaveOptions<T> {
  /** Data to be saved */
  data: T
  /** Save function */
  onSave: (data: T) => Promise<void>
  /** Debounce delay in milliseconds */
  debounceMs?: number
  /** Whether auto-save is enabled */
  enabled?: boolean
}

interface UseAutoSaveReturn {
  /** Current save status */
  status: SaveStatus
  /** Last error message */
  error: string | null
  /** Manually trigger save */
  saveNow: () => Promise<void>
  /** Last saved timestamp */
  lastSavedAt: Date | null
}

export function useAutoSave<T>({
  data,
  onSave,
  debounceMs = 2000,
  enabled = true,
}: UseAutoSaveOptions<T>): UseAutoSaveReturn {
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)

  // Keep track of the latest data
  const dataRef = useRef(data)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isFirstRender = useRef(true)

  // Update ref when data changes
  useEffect(() => {
    dataRef.current = data
  }, [data])

  // Perform save
  const performSave = useCallback(async () => {
    setStatus('saving')
    setError(null)

    try {
      await onSave(dataRef.current)
      setStatus('saved')
      setLastSavedAt(new Date())

      // Reset to idle after 3 seconds
      setTimeout(() => {
        setStatus((current) => (current === 'saved' ? 'idle' : current))
      }, 3000)
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Save failed')
    }
  }, [onSave])

  // Manual save
  const saveNow = useCallback(async () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    await performSave()
  }, [performSave])

  // Auto-save effect
  useEffect(() => {
    // Skip first render
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }

    if (!enabled) return

    // Clear existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    // Set new timer
    timerRef.current = setTimeout(() => {
      performSave()
    }, debounceMs)

    // Cleanup
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [data, debounceMs, enabled, performSave])

  return {
    status,
    error,
    saveNow,
    lastSavedAt,
  }
}

export default useAutoSave
