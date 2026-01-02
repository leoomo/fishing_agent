/**
 * Rig configuration types
 */

// Rig category classification
export type RigCategory = 'bottom' | 'float' | 'lure' | 'fly' | 'surf'

// Rig difficulty levels
export type RigDifficulty = 'easy' | 'medium' | 'hard'

// Component types
export type ComponentType =
  | 'hook'      // 钓钩
  | 'sinker'    // 铅坠
  | 'swivel'    // 转环
  | 'leader'    // 前导线
  | 'float'     // 浮漂
  | 'bead'      // 珠子
  | 'stopper'   // 太空豆
  | 'snap'      // 别针
  | 'ring'      // 连接环
  | 'tube'      // 套管
  | 'other'     // 其他

// Rig specification
export interface RigSpec {
  spec_id: number
  rig_id: number
  spec_name: string
  spec_value: string
  unit?: string
  notes?: string
}

// Rig component
export interface RigComponent {
  component_id: number
  rig_id: number
  component_name: string
  component_type: string
  quantity: number
  size?: string
  position?: number
  notes?: string
}

// Full rig detail
export interface Rig {
  rig_id: number
  name: string
  category: RigCategory
  description?: string
  diagram_url?: string
  difficulty: RigDifficulty
  target_species?: string
  best_conditions?: string
  created_at?: string
  updated_at?: string
  specs: RigSpec[]
  components: RigComponent[]
}

// Rig list item (without nested details)
export interface RigListItem {
  rig_id: number
  name: string
  category: RigCategory
  difficulty: RigDifficulty
  target_species?: string
  diagram_url?: string
  component_count: number
  spec_count: number
  created_at?: string
  updated_at?: string
}

// Paginated list response
export interface RigListResponse {
  total: number
  page: number
  page_size: number
  items: RigListItem[]
}

// Create rig request
export interface RigCreateRequest {
  name: string
  category: RigCategory
  description?: string
  diagram_url?: string
  difficulty?: RigDifficulty
  target_species?: string
  best_conditions?: string
  specs?: RigSpecCreate[]
  components?: RigComponentCreate[]
}

// Update rig request
export interface RigUpdateRequest {
  name?: string
  category?: RigCategory
  description?: string
  diagram_url?: string
  difficulty?: RigDifficulty
  target_species?: string
  best_conditions?: string
}

// Create spec request
export interface RigSpecCreate {
  spec_name: string
  spec_value: string
  unit?: string
  notes?: string
}

// Update spec request
export interface RigSpecUpdate {
  spec_name?: string
  spec_value?: string
  unit?: string
  notes?: string
}

// Create component request
export interface RigComponentCreate {
  component_name: string
  component_type: string
  quantity?: number
  size?: string
  position?: number
  notes?: string
}

// Update component request
export interface RigComponentUpdate {
  component_name?: string
  component_type?: string
  quantity?: number
  size?: string
  position?: number
  notes?: string
}

// Simplified lure type for associations
export interface LureTypeSimple {
  lure_type_id: number
  name: string
  category?: string
}

// Lure type association request
export interface RigLureAssociationRequest {
  lure_type_ids: number[]
}

// Option item for dropdowns
export interface OptionItem {
  value: string
  label: string
  description?: string
  color?: string
  icon?: string
}

// Rig form options response
export interface RigOptionsResponse {
  categories: OptionItem[]
  difficulties: OptionItem[]
  component_types: OptionItem[]
}

// ========== Configuration Constants ==========

// Rig category configuration
export const RIG_CATEGORY_CONFIG: Record<RigCategory, {
  label: string
  icon: string
  color: string
  description: string
}> = {
  bottom: {
    label: '底钓钓组',
    icon: '⚓',
    color: 'volcano',
    description: '适合底层鱼类，如鲤鱼、鲫鱼',
  },
  float: {
    label: '浮漂钓组',
    icon: '🎈',
    color: 'blue',
    description: '适合中上层鱼类，如草鱼、鲢鱼',
  },
  lure: {
    label: '路亚钓组',
    icon: '🎣',
    color: 'green',
    description: '适合掠食性鱼类，如黑鲈、鳜鱼',
  },
  fly: {
    label: '飞蝇钓组',
    icon: '🦋',
    color: 'purple',
    description: '适合溪流鱼类，如虹鳟、马口',
  },
  surf: {
    label: '海钓钓组',
    icon: '🌊',
    color: 'cyan',
    description: '适合海水鱼类，如海鲈、真鲷',
  },
}

// Rig difficulty configuration
export const RIG_DIFFICULTY_CONFIG: Record<RigDifficulty, {
  label: string
  color: string
  description: string
}> = {
  easy: {
    label: '简单',
    color: 'success',
    description: '新手友好，组装简单',
  },
  medium: {
    label: '中等',
    color: 'warning',
    description: '需要一定经验',
  },
  hard: {
    label: '困难',
    color: 'error',
    description: '需要丰富经验和技巧',
  },
}

// Component type options
export const COMPONENT_TYPE_OPTIONS: OptionItem[] = [
  { value: 'hook', label: '钓钩', icon: '🪝', color: 'red' },
  { value: 'sinker', label: '铅坠', icon: '⚫', color: 'default' },
  { value: 'swivel', label: '转环', icon: '🔄', color: 'blue' },
  { value: 'leader', label: '前导线', icon: '〰️', color: 'green' },
  { value: 'float', label: '浮漂', icon: '🎈', color: 'orange' },
  { value: 'bead', label: '珠子', icon: '⚪', color: 'purple' },
  { value: 'stopper', label: '太空豆', icon: '⏹️', color: 'cyan' },
  { value: 'snap', label: '别针', icon: '📎', color: 'gold' },
  { value: 'ring', label: '连接环', icon: '⭕', color: 'lime' },
  { value: 'tube', label: '套管', icon: '🔲', color: 'magenta' },
  { value: 'other', label: '其他', icon: '📦', color: 'default' },
]

// Helper function to get component type config
export const getComponentTypeConfig = (type: string): OptionItem => {
  return COMPONENT_TYPE_OPTIONS.find(opt => opt.value === type)
    || { value: type, label: type, color: 'default' }
}
