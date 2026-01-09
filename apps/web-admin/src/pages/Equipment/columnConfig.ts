/**
 * 装备列表列配置
 * 定义所有可用列及其属性
 */

// 列配置接口
export interface ColumnConfig {
  key: string // 列标识
  title: string // 列标题
  required?: boolean // 是否必选（不可隐藏）
  defaultVisible: boolean // 默认是否显示
}

// 配置存储键
export const COLUMN_CONFIG_KEY = 'ui.equipment_list.columns'

// 所有可用列定义
export const COLUMN_DEFINITIONS: ColumnConfig[] = [
  { key: 'name', title: '名称', required: true, defaultVisible: true },
  { key: 'category', title: '类别', defaultVisible: true },
  { key: 'brand_name', title: '品牌', defaultVisible: true },
  { key: 'model', title: '型号', defaultVisible: true },
  { key: 'price', title: '价格范围', defaultVisible: true },
  { key: 'length', title: '竿长', defaultVisible: false },
  { key: 'action', title: '动作', defaultVisible: false },
  { key: 'power', title: '调性', defaultVisible: false },
  { key: 'sections', title: '节数', defaultVisible: false },
  { key: 'weight', title: '自重', defaultVisible: false },
  { key: 'lure_weight', title: '饵重范围', defaultVisible: false },
  { key: 'user_level', title: '适用水平', defaultVisible: true },
  { key: 'is_active', title: '状态', defaultVisible: true },
  { key: 'actions', title: '操作', required: true, defaultVisible: true },
]

// 获取默认显示的列
export const getDefaultVisibleColumns = (): string[] => {
  return COLUMN_DEFINITIONS.filter((col) => col.defaultVisible).map((col) => col.key)
}

// 获取必选列
export const getRequiredColumns = (): string[] => {
  return COLUMN_DEFINITIONS.filter((col) => col.required).map((col) => col.key)
}

// 验证列配置（确保必选列存在）
export const validateColumns = (columns: string[]): string[] => {
  const required = getRequiredColumns()
  const validColumns = [...new Set([...required, ...columns])]
  // 只保留有效的列
  return validColumns.filter((key) => COLUMN_DEFINITIONS.some((col) => col.key === key))
}
