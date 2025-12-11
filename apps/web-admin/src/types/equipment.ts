// 鱼竿规格接口
export interface RodSpecs {
  length?: number         // 长度（米）
  power?: string         // 调性 (UL|L|ML|M|MH|H|XH)
  action?: string        // 动作 (Fast|Moderate|Slow)
  sections?: number      // 节数
  weight?: number        // 重量（克）
  lure_weight_min?: number  // 最小饵重（克）
  lure_weight_max?: number  // 最大饵重（克）
  line_weight_min?: number  // 最小线重（磅）
  line_weight_max?: number  // 最大线重（磅）
  tip_diameter?: number     // 竿稍直径（毫米）
  butt_diameter?: number    // 竿把直径（毫米）
  handle_length?: number    // 握把长度（厘米）
  guide_type?: string       // 导环类型
  handle_type?: string      // 握把类型
  craft_description?: string // 工艺描述
}

// 渔轮规格接口
export interface ReelSpecs {
  gear_ratio?: number      // 齿比
  bearings?: number        // 轴承数
  weight?: number          // 重量（克）
  line_capacity?: string   // 线容量
  drag_max?: number        // 最大拖力（公斤）
  spool_material?: string  // 线杯材质
}

// 鱼线规格接口
export interface LineSpecs {
  diameter?: number        // 直径（毫米）
  length?: number          // 长度（米）
  strength?: number        // 强力（公斤）
  material?: string        // 材质
  type?: string            // 类型（尼龙/PE/碳素）
  color?: string           // 颜色
}

// 拟饵规格接口
export interface LureSpecs {
  weight?: number          // 重量（克）
  length?: number          // 长度（毫米）
  type?: string            // 类型（米诺/摇滚/胖子/铅笔等）
  diving_depth?: number    // 潜行深度（米）
  hooks?: number           // 钩数
  material?: string        // 材质
  color?: string           // 颜色
}

// 装备接口，使用联合类型表示不同规格
export interface Equipment {
  equipment_id: number
  name: string
  category: string
  brand_id: number
  brand_name?: string
  model?: string
  price_min?: number
  price_max?: number
  description?: string
  features?: string
  user_level: string
  specs?: RodSpecs | ReelSpecs | LineSpecs | LureSpecs | Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Brand {
  brand_id: number
  name_cn: string
  name_en?: string
  logo_url?: string
  website?: string
  country?: string
}

export interface EquipmentListResponse {
  items: Equipment[]
  total: number
  page: number
  page_size: number
}
