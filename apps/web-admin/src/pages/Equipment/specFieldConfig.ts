/**
 * 装备规格字段配置
 * 定义每种类别的字段配置（名称、类型、验证规则、分组）
 *
 * 注意：select 类型字段使用 dynamicOptionKey 指定动态加载的选项，
 * options 作为静态 fallback。
 */

import type { DynamicOptionsMap } from './SpecFormFields'

// 字段定义接口
export interface SpecFieldDef {
  name: string
  label: string
  type: 'input' | 'number' | 'select' | 'textarea'
  required?: boolean
  options?: { label: string; value: string }[]
  dynamicOptionKey?: keyof DynamicOptionsMap // 动态选项键
  min?: number
  max?: number
  step?: number
  addonAfter?: string
  placeholder?: string
  group: 'basic' | 'range' | 'advanced'
}

// 鱼竿规格字段
export const ROD_SPEC_FIELDS: SpecFieldDef[] = [
  // 基本规格
  {
    name: 'length',
    label: '竿长',
    type: 'number',
    required: true,
    min: 0.5,
    max: 10,
    step: 0.01,
    addonAfter: '米',
    group: 'basic',
  },
  {
    name: 'power',
    label: '调性',
    type: 'select',
    required: true,
    dynamicOptionKey: 'power',
    options: [
      { label: 'UL', value: 'UL' },
      { label: 'L', value: 'L' },
      { label: 'ML', value: 'ML' },
      { label: 'M', value: 'M' },
      { label: 'MH', value: 'MH' },
      { label: 'H', value: 'H' },
      { label: 'XH', value: 'XH' },
    ],
    group: 'basic',
  },
  {
    name: 'action',
    label: '动作',
    type: 'select',
    required: true,
    dynamicOptionKey: 'action',
    options: [
      { label: 'Fast(快调)', value: 'Fast' },
      { label: 'Medium(中调)', value: 'Medium' },
      { label: 'Slow(慢调)', value: 'Slow' },
    ],
    group: 'basic',
  },
  {
    name: 'sections',
    label: '节数',
    type: 'number',
    min: 1,
    max: 10,
    step: 1,
    addonAfter: '节',
    group: 'basic',
  },
  {
    name: 'weight',
    label: '自重',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '克',
    group: 'basic',
  },
  {
    name: 'closed_length',
    label: '收缩长度',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '厘米',
    group: 'basic',
  },
  // 重量范围
  {
    name: 'lure_weight_min',
    label: '饵重(最小)',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '克',
    group: 'range',
  },
  {
    name: 'lure_weight_max',
    label: '饵重(最大)',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '克',
    group: 'range',
  },
  {
    name: 'line_weight_min',
    label: '线重(最小)',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'lb',
    group: 'range',
  },
  {
    name: 'line_weight_max',
    label: '线重(最大)',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'lb',
    group: 'range',
  },
  // 高级参数
  {
    name: 'guide_type',
    label: '导环类型',
    type: 'input',
    placeholder: '如: 富士SIC',
    group: 'advanced',
  },
  {
    name: 'handle_type',
    label: '握把类型',
    type: 'input',
    placeholder: '如: EVA、软木',
    group: 'advanced',
  },
  {
    name: 'tip_diameter',
    label: '竿稍直径',
    type: 'number',
    min: 0,
    step: 0.01,
    addonAfter: 'mm',
    group: 'advanced',
  },
  {
    name: 'butt_diameter',
    label: '竿柄直径',
    type: 'number',
    min: 0,
    step: 0.01,
    addonAfter: 'mm',
    group: 'advanced',
  },
  {
    name: 'carbon_content',
    label: '含碳量',
    type: 'number',
    min: 0,
    max: 100,
    step: 1,
    addonAfter: '%',
    group: 'advanced',
  },
  {
    name: 'handle_length',
    label: '握把长度',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'cm',
    group: 'advanced',
  },
  {
    name: 'craft_description',
    label: '工艺描述',
    type: 'textarea',
    placeholder: '工艺说明...',
    group: 'advanced',
  },
]

// 渔轮规格字段
export const REEL_SPEC_FIELDS: SpecFieldDef[] = [
  // 基本规格
  {
    name: 'reel_type',
    label: '轮类型',
    type: 'select',
    dynamicOptionKey: 'reel_type',
    options: [
      { label: 'spinning(纺车轮)', value: 'spinning' },
      { label: 'baitcasting(水滴轮)', value: 'baitcasting' },
      { label: 'fly(飞蝇轮)', value: 'fly' },
    ],
    group: 'basic',
  },
  {
    name: 'gear_ratio',
    label: '速比',
    type: 'input',
    placeholder: '如: 6.2:1',
    group: 'basic',
  },
  {
    name: 'bearings',
    label: '轴承',
    type: 'input',
    placeholder: '如: 10+1BB',
    group: 'basic',
  },
  {
    name: 'weight',
    label: '自重',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '克',
    group: 'basic',
  },
  // 性能参数
  {
    name: 'line_capacity',
    label: '线容量',
    type: 'input',
    placeholder: '如: 0.2mm/200m',
    group: 'range',
  },
  {
    name: 'max_drag',
    label: '最大拽力',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'kg',
    group: 'range',
  },
  {
    name: 'retrieve_per_turn',
    label: '每转收线',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'cm',
    group: 'range',
  },
  // 尺寸参数
  {
    name: 'spool_width',
    label: '线杯宽度',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'mm',
    group: 'advanced',
  },
  {
    name: 'frame_height',
    label: '框架高度',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'mm',
    group: 'advanced',
  },
]

// 鱼线规格字段
export const LINE_SPEC_FIELDS: SpecFieldDef[] = [
  // 基本规格
  {
    name: 'line_type',
    label: '线型',
    type: 'select',
    required: true,
    dynamicOptionKey: 'line_type',
    options: [
      { label: 'PE(编织线)', value: 'PE' },
      { label: '尼龙(尼龙线)', value: '尼龙' },
      { label: '碳线(碳素线)', value: '碳线' },
      { label: '钢丝(钢丝线)', value: '钢丝' },
    ],
    group: 'basic',
  },
  {
    name: 'diameter',
    label: '线径',
    type: 'number',
    min: 0,
    step: 0.01,
    addonAfter: 'mm',
    group: 'basic',
  },
  {
    name: 'length_m',
    label: '长度',
    type: 'number',
    min: 0,
    step: 1,
    addonAfter: '米',
    group: 'basic',
  },
  // 强度参数
  {
    name: 'strength_lb',
    label: '拉力',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'lb',
    group: 'range',
  },
  {
    name: 'knot_strength',
    label: '节结拉力',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'lb',
    group: 'range',
  },
  // 其他
  {
    name: 'color',
    label: '颜色',
    type: 'input',
    placeholder: '如: 黄绿色',
    group: 'advanced',
  },
  {
    name: 'material',
    label: '材质',
    type: 'input',
    placeholder: '如: 日本原丝',
    group: 'advanced',
  },
]

// 拟饵规格字段
export const LURE_SPEC_FIELDS: SpecFieldDef[] = [
  // 基本规格
  {
    name: 'lure_type',
    label: '类型',
    type: 'input',
    required: true,
    placeholder: '如: 米诺、摇滚、VIB',
    group: 'basic',
  },
  {
    name: 'lure_category',
    label: '分类',
    type: 'input',
    placeholder: '如: 硬饵、软饵',
    group: 'basic',
  },
  {
    name: 'weight',
    label: '重量',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '克',
    group: 'basic',
  },
  {
    name: 'length',
    label: '长度',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: 'cm',
    group: 'basic',
  },
  // 潜深范围
  {
    name: 'diving_depth_min',
    label: '潜深(最小)',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '米',
    group: 'range',
  },
  {
    name: 'diving_depth_max',
    label: '潜深(最大)',
    type: 'number',
    min: 0,
    step: 0.1,
    addonAfter: '米',
    group: 'range',
  },
  // 其他
  {
    name: 'color',
    label: '颜色',
    type: 'input',
    placeholder: '如: 银白、红头',
    group: 'advanced',
  },
  {
    name: 'action_type',
    label: '动作类型',
    type: 'input',
    placeholder: '如: 悬停、快沉',
    group: 'advanced',
  },
]

// 根据类别获取规格字段配置
export function getSpecFields(category: string): SpecFieldDef[] {
  switch (category) {
    case '鱼竿':
      return ROD_SPEC_FIELDS
    case '渔轮':
      return REEL_SPEC_FIELDS
    case '鱼线':
      return LINE_SPEC_FIELDS
    case '拟饵':
      return LURE_SPEC_FIELDS
    default:
      return []
  }
}

// 分组标题（简洁，不需要过多装饰）
export const GROUP_LABELS: Record<string, string> = {
  basic: '规格',
  range: '范围',
  advanced: '更多',
}
