/**
 * 列配置管理 Hook
 * 从后端 API 加载和保存列配置
 */

import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import { configApi } from '@/api/services/config'
import {
  COLUMN_CONFIG_KEY,
  getDefaultVisibleColumns,
  validateColumns,
} from '../columnConfig'

interface UseColumnSettingsReturn {
  visibleColumns: string[] // 当前显示的列
  loading: boolean // 加载状态
  saving: boolean // 保存状态
  setVisibleColumns: (columns: string[]) => void // 设置显示列（本地）
  saveColumns: (columns: string[]) => Promise<boolean> // 保存到后端
  resetToDefault: () => void // 重置为默认
}

export const useColumnSettings = (): UseColumnSettingsReturn => {
  const [visibleColumns, setVisibleColumnsState] = useState<string[]>(getDefaultVisibleColumns())
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [configId, setConfigId] = useState<number | null>(null)

  // 加载列配置
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config = await configApi.get(COLUMN_CONFIG_KEY)
        if (config && config.config_value) {
          // config_value 可能是数组（后端已解析）或字符串（需要解析）
          const columns = Array.isArray(config.config_value)
            ? config.config_value
            : JSON.parse(config.config_value)
          setVisibleColumnsState(validateColumns(columns as string[]))
          setConfigId(config.id)
        }
      } catch {
        // 配置不存在，使用默认值
        setVisibleColumnsState(getDefaultVisibleColumns())
      } finally {
        setLoading(false)
      }
    }
    loadConfig()
  }, [])

  // 设置显示列（本地状态）
  const setVisibleColumns = useCallback((columns: string[]) => {
    setVisibleColumnsState(validateColumns(columns))
  }, [])

  // 保存列配置到后端
  const saveColumns = useCallback(
    async (columns: string[]): Promise<boolean> => {
      setSaving(true)
      try {
        const validColumns = validateColumns(columns)
        const configValue = JSON.stringify(validColumns)

        if (configId) {
          // 更新现有配置（使用 config key）
          await configApi.update(COLUMN_CONFIG_KEY, {
            config_value: configValue,
          })
        } else {
          // 创建新配置
          const newConfig = await configApi.create({
            config_key: COLUMN_CONFIG_KEY,
            config_value: configValue,
            config_type: 'system',
            description: '装备列表显示列配置',
          })
          setConfigId(newConfig.id)
        }

        setVisibleColumnsState(validColumns)
        message.success('列设置已保存')
        return true
      } catch {
        message.error('保存列设置失败')
        return false
      } finally {
        setSaving(false)
      }
    },
    [configId]
  )

  // 重置为默认配置
  const resetToDefault = useCallback(() => {
    setVisibleColumnsState(getDefaultVisibleColumns())
  }, [])

  return {
    visibleColumns,
    loading,
    saving,
    setVisibleColumns,
    saveColumns,
    resetToDefault,
  }
}
