// 鱼竿规格接口
export interface RodSpecs {
  spec_id?: number
  equipment_id?: number
  // 基本规格
  length?: number           // 长度（米）
  power?: string            // 调性 (UL|L|ML|M|MH|H|XH)
  action?: string           // 动作 (Fast|Moderate|Slow)
  sections?: number         // 节数
  weight?: number           // 自重（克）
  closed_length?: number    // 收缩长度（厘米）
  // 重量范围
  lure_weight_min?: number  // 适用饵重最小值（克）
  lure_weight_max?: number  // 适用饵重最大值（克）
  line_weight_min?: number  // 适用线重最小值（lb）
  line_weight_max?: number  // 适用线重最大值（lb）
  // 高级参数
  guide_type?: string       // 导环类型
  handle_type?: string      // 握把类型
  tip_diameter?: number     // 竿稍直径（mm）
  butt_diameter?: number    // 竿柄直径（mm）
  handle_length?: number    // 握把长度（cm）
  craft_description?: string // 工艺描述
}

// 渔轮规格接口
export interface ReelSpecs {
  spec_id?: number
  equipment_id?: number
  // 基本规格
  reel_type?: string        // 轮类型 (spinning|baitcasting|fly)
  gear_ratio?: string       // 速比（如 5.2:1）
  bearings?: string         // 轴承数
  weight?: number           // 自重（克）
  // 性能参数
  line_capacity?: string    // 线容量（如 0.2mm/100m）
  max_drag?: number         // 最大拽力（kg）
  retrieve_per_turn?: number // 每转收线（cm）
  // 尺寸参数
  spool_width?: number      // 线杯宽度（mm）
  frame_height?: number     // 框架高度（mm）
}

// 鱼线规格接口
export interface LineSpecs {
  spec_id?: number
  equipment_id?: number
  // 基本规格
  line_type?: string        // 线型 (PE|尼龙|碳线|钢丝)
  diameter?: number         // 线径（mm）
  length_m?: number         // 长度（米）
  // 强度参数
  strength_lb?: number      // 拉力（lb）
  knot_strength?: number    // 节结拉力（lb）
  // 其他
  color?: string            // 颜色
  material?: string         // 材质
}

// 拟饵规格接口
export interface LureSpecs {
  spec_id?: number
  equipment_id?: number
  // 基本规格
  lure_type?: string        // 拟饵类型
  lure_category?: string    // 拟饵分类
  weight?: number           // 重量（克）
  length?: number           // 长度（cm）
  // 潜深范围
  diving_depth_min?: number // 最小潜深（米）
  diving_depth_max?: number // 最大潜深（米）
  // 其他
  color?: string            // 颜色/花纹
  action_type?: string      // 动作类型
}

// 规格联合类型
export type EquipmentSpecs = RodSpecs | ReelSpecs | LineSpecs | LureSpecs

// 装备接口
export interface Equipment {
  equipment_id: number
  name: string
  category: string
  brand_id: number
  brand_name?: string
  model?: string
  price_min?: number
  price_max?: number
  price_currency?: string
  description?: string
  features?: string
  user_level?: string
  specs?: EquipmentSpecs | Record<string, unknown>
  is_active: boolean
  source?: string
  source_url?: string
  created_at: string
  updated_at: string
}

// 品牌接口
export interface Brand {
  brand_id: number
  name_cn: string
  name_en?: string
  logo_url?: string
  website?: string
  country?: string
  description?: string
  equipment_count?: number
  created_at?: string
  updated_at?: string
}

// 装备列表响应
export interface EquipmentListResponse {
  items: Equipment[]
  total: number
  page: number
  page_size: number
}

// 装备创建请求
export interface EquipmentCreate {
  name: string
  category: string
  brand_id: number
  model?: string
  price_min?: number
  price_max?: number
  price_currency?: string
  description?: string
  features?: string
  user_level?: string
  is_active?: boolean
  source?: string
  source_url?: string
  specs?: EquipmentSpecs
}

// 装备更新请求
export interface EquipmentUpdate {
  name?: string
  category?: string
  brand_id?: number
  model?: string
  price_min?: number
  price_max?: number
  description?: string
  features?: string
  user_level?: string
  is_active?: boolean
  specs?: EquipmentSpecs
}

// 装备类别选项
export const EQUIPMENT_CATEGORIES = ['鱼竿', '渔轮', '鱼线', '拟饵', '套装'] as const
export type EquipmentCategory = (typeof EQUIPMENT_CATEGORIES)[number]

// 用户级别选项
export const USER_LEVELS = ['新手', '进阶', '高手'] as const
export type UserLevel = (typeof USER_LEVELS)[number]

// 鱼竿调性选项
export const ROD_POWERS = ['UL', 'L', 'ML', 'M', 'MH', 'H', 'XH'] as const
export type RodPower = (typeof ROD_POWERS)[number]

// 鱼竿动作选项
export const ROD_ACTIONS = ['Fast', 'Moderate', 'Slow'] as const
export type RodAction = (typeof ROD_ACTIONS)[number]

// 渔轮类型选项
export const REEL_TYPES = ['spinning', 'baitcasting', 'fly'] as const
export type ReelType = (typeof REEL_TYPES)[number]

// 鱼线类型选项
export const LINE_TYPES = ['PE', '尼龙', '碳线', '钢丝'] as const
export type LineType = (typeof LINE_TYPES)[number]

// 装备搜索筛选接口
export interface EquipmentSearchFilters {
  category?: string
  brand_id?: number
  keyword?: string
  price_min?: number
  price_max?: number
  user_level?: string
  is_active?: boolean
  // 鱼竿专属
  power?: string
  action?: string
  length_min?: number
  length_max?: number
}
