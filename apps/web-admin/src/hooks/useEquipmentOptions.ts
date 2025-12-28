import { useState, useEffect, useCallback } from 'react'
import { configApi } from '@/api/services/config'

/**
 * 选项配置键常量
 */
export const EQUIPMENT_OPTION_KEYS = {
  POWER: 'equipment.rod.power_options',
  ACTION: 'equipment.rod.action_options',
  ACTION_CN: 'equipment.rod.action_options_cn',
  USER_LEVEL: 'equipment.user_level_options',
  CATEGORY: 'equipment.category_options',
} as const

/**
 * 默认选项值 (作为 fallback)
 */
export const DEFAULT_OPTIONS = {
  [EQUIPMENT_OPTION_KEYS.POWER]: ['UL', 'L', 'ML', 'M', 'MH', 'H', 'XH'],
  [EQUIPMENT_OPTION_KEYS.ACTION]: ['Fast', 'Medium', 'Slow'],
  [EQUIPMENT_OPTION_KEYS.ACTION_CN]: ['慢调', '中调', '快调', '超快调'],
  [EQUIPMENT_OPTION_KEYS.USER_LEVEL]: ['新手', '进阶', '高手'],
  [EQUIPMENT_OPTION_KEYS.CATEGORY]: ['鱼竿', '渔轮', '鱼线', '拟饵'],
} as const

type OptionKey = typeof EQUIPMENT_OPTION_KEYS[keyof typeof EQUIPMENT_OPTION_KEYS]

interface UseEquipmentOptionsResult {
  options: string[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

/**
 * 从配置 API 加载装备选项
 *
 * @param optionKey - 选项配置键 (如 'equipment.rod.power_options')
 * @returns 选项列表、加载状态、错误信息和刷新函数
 *
 * @example
 * ```tsx
 * const { options: powerOptions, loading } = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.POWER)
 *
 * return (
 *   <Select loading={loading}>
 *     {powerOptions.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
 *   </Select>
 * )
 * ```
 */
export function useEquipmentOptions(optionKey: OptionKey): UseEquipmentOptionsResult {
  const [options, setOptions] = useState<string[]>(DEFAULT_OPTIONS[optionKey] || [])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const loadOptions = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const config = await configApi.get(optionKey)
      const parsedOptions = JSON.parse(config.config_value)

      if (Array.isArray(parsedOptions)) {
        setOptions(parsedOptions)
      } else {
        // 如果解析结果不是数组，使用默认值
        setOptions(DEFAULT_OPTIONS[optionKey] || [])
      }
    } catch (err) {
      // 配置不存在或解析失败，使用默认值
      setOptions(DEFAULT_OPTIONS[optionKey] || [])
      // 只有非 404 错误才设置 error
      if (err instanceof Error && !err.message.includes('404')) {
        setError(err)
      }
    } finally {
      setLoading(false)
    }
  }, [optionKey])

  useEffect(() => {
    loadOptions()
  }, [loadOptions])

  return {
    options,
    loading,
    error,
    refresh: loadOptions,
  }
}

/**
 * 批量加载多个选项组
 *
 * @returns 所有选项组的加载状态和数据
 *
 * @example
 * ```tsx
 * const { powerOptions, actionOptions, loading } = useAllEquipmentOptions()
 * ```
 */
export function useAllEquipmentOptions() {
  const power = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.POWER)
  const action = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.ACTION)
  const actionCn = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.ACTION_CN)
  const userLevel = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.USER_LEVEL)
  const category = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.CATEGORY)

  return {
    powerOptions: power.options,
    actionOptions: action.options,
    actionOptionsCn: actionCn.options,
    userLevelOptions: userLevel.options,
    categoryOptions: category.options,
    loading: power.loading || action.loading || actionCn.loading || userLevel.loading || category.loading,
    refresh: async () => {
      await Promise.all([
        power.refresh(),
        action.refresh(),
        actionCn.refresh(),
        userLevel.refresh(),
        category.refresh(),
      ])
    },
  }
}

export default useEquipmentOptions
