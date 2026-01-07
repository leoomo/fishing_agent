import { useState, useEffect, useCallback } from 'react'
import { configApi } from '@/api/services/config'

/**
 * 选项数据结构（支持备注）
 */
export interface OptionItem {
  value: string
  note?: string
}

/**
 * 选项配置键常量
 */
export const EQUIPMENT_OPTION_KEYS = {
  POWER: 'equipment.rod.power_options',
  ACTION: 'equipment.rod.action_options',
  ACTION_CN: 'equipment.rod.action_options_cn',
  USER_LEVEL: 'equipment.user_level_options',
  CATEGORY: 'equipment.category_options',
  REEL_TYPE: 'equipment.reel.type_options',
  LINE_TYPE: 'equipment.line.type_options',
} as const

/**
 * 默认选项值 (作为 fallback，带备注)
 */
export const DEFAULT_OPTIONS: Record<string, OptionItem[]> = {
  [EQUIPMENT_OPTION_KEYS.POWER]: [
    { value: 'UL', note: '超轻调，适合微物钓法' },
    { value: 'L', note: '轻调，适合小型鱼类' },
    { value: 'ML', note: '中轻调，通用型' },
    { value: 'M', note: '中调，平衡性好' },
    { value: 'MH', note: '中硬调，适合中大型鱼' },
    { value: 'H', note: '硬调，适合大型鱼' },
    { value: 'XH', note: '超硬调，适合巨物' },
  ],
  [EQUIPMENT_OPTION_KEYS.ACTION]: [
    { value: 'Fast', note: '快调，恢复迅速' },
    { value: 'Medium', note: '中调，平衡性好' },
    { value: 'Slow', note: '慢调，弯曲幅度大' },
  ],
  [EQUIPMENT_OPTION_KEYS.ACTION_CN]: [
    { value: '慢调', note: '弯曲幅度大，适合溜鱼' },
    { value: '中调', note: '平衡型，适用范围广' },
    { value: '快调', note: '恢复快，灵敏度高' },
    { value: '超快调', note: '极速恢复，精准度高' },
  ],
  [EQUIPMENT_OPTION_KEYS.USER_LEVEL]: [
    { value: '新手', note: '入门级用户' },
    { value: '进阶', note: '有一定经验的用户' },
    { value: '高手', note: '经验丰富的专业用户' },
  ],
  [EQUIPMENT_OPTION_KEYS.CATEGORY]: [
    { value: '鱼竿', note: '钓鱼主要工具' },
    { value: '渔轮', note: '收放线装置' },
    { value: '鱼线', note: '连接鱼竿和鱼钩' },
    { value: '拟饵', note: '模拟饵料吸引鱼类' },
  ],
  [EQUIPMENT_OPTION_KEYS.REEL_TYPE]: [
    { value: 'spinning', note: '纺车轮，适合新手' },
    { value: 'baitcasting', note: '水滴轮，精准抛投' },
    { value: 'fly', note: '飞蝇轮，飞蝇钓专用' },
  ],
  [EQUIPMENT_OPTION_KEYS.LINE_TYPE]: [
    { value: 'PE', note: '编织线，强度高' },
    { value: '尼龙', note: '尼龙线，延展性好' },
    { value: '碳线', note: '碳素线，隐蔽性强' },
    { value: '钢丝', note: '钢丝线，防咬断' },
  ],
}

type OptionKey = typeof EQUIPMENT_OPTION_KEYS[keyof typeof EQUIPMENT_OPTION_KEYS]

/**
 * 将旧格式（字符串数组）转换为新格式（带备注的对象数组）
 */
function normalizeOptions(data: unknown): OptionItem[] {
  if (!Array.isArray(data)) return []

  return data.map((item) => {
    if (typeof item === 'string') {
      return { value: item, note: '' }
    }
    if (typeof item === 'object' && item !== null && 'value' in item) {
      return {
        value: String((item as Record<string, unknown>).value || ''),
        note: String((item as Record<string, unknown>).note || ''),
      }
    }
    return { value: String(item), note: '' }
  })
}

interface UseEquipmentOptionsResult {
  /** 完整选项列表（带备注） */
  options: OptionItem[]
  /** 纯值列表（用于 Select 等组件） */
  values: string[]
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
 * // 使用完整选项（带备注）
 * const { options, loading } = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.POWER)
 * return options.map(opt => (
 *   <Tooltip key={opt.value} title={opt.note}>
 *     <Tag>{opt.value}</Tag>
 *   </Tooltip>
 * ))
 *
 * // 使用纯值列表（用于 Select）
 * const { values, loading } = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.POWER)
 * return (
 *   <Select loading={loading}>
 *     {values.map(v => <Option key={v} value={v}>{v}</Option>)}
 *   </Select>
 * )
 * ```
 */
export function useEquipmentOptions(optionKey: OptionKey): UseEquipmentOptionsResult {
  const [options, setOptions] = useState<OptionItem[]>(DEFAULT_OPTIONS[optionKey] || [])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const loadOptions = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const config = await configApi.get(optionKey)
      // config_value 可能已经是对象，也可能是 JSON 字符串
      const rawValue =
        typeof config.config_value === 'string'
          ? JSON.parse(config.config_value)
          : config.config_value
      const normalized = normalizeOptions(rawValue)

      if (normalized.length > 0) {
        setOptions(normalized)
      } else {
        // 如果解析结果为空，使用默认值
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
    values: options.map((opt) => opt.value),
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
 * // 使用完整选项（带备注）
 * const { powerOptions, loading } = useAllEquipmentOptions()
 * powerOptions.forEach(opt => console.log(opt.value, opt.note))
 *
 * // 使用纯值列表
 * const { powerValues, loading } = useAllEquipmentOptions()
 * ```
 */
export function useAllEquipmentOptions() {
  const power = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.POWER)
  const action = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.ACTION)
  const actionCn = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.ACTION_CN)
  const userLevel = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.USER_LEVEL)
  const category = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.CATEGORY)
  const reelType = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.REEL_TYPE)
  const lineType = useEquipmentOptions(EQUIPMENT_OPTION_KEYS.LINE_TYPE)

  return {
    // 完整选项（带备注）
    powerOptions: power.options,
    actionOptions: action.options,
    actionOptionsCn: actionCn.options,
    userLevelOptions: userLevel.options,
    categoryOptions: category.options,
    reelTypeOptions: reelType.options,
    lineTypeOptions: lineType.options,
    // 纯值列表（用于 Select 等组件）
    powerValues: power.values,
    actionValues: action.values,
    actionValuesCn: actionCn.values,
    userLevelValues: userLevel.values,
    categoryValues: category.values,
    reelTypeValues: reelType.values,
    lineTypeValues: lineType.values,
    loading: power.loading || action.loading || actionCn.loading || userLevel.loading || category.loading || reelType.loading || lineType.loading,
    refresh: async () => {
      await Promise.all([
        power.refresh(),
        action.refresh(),
        actionCn.refresh(),
        userLevel.refresh(),
        category.refresh(),
        reelType.refresh(),
        lineType.refresh(),
      ])
    },
  }
}

export default useEquipmentOptions
