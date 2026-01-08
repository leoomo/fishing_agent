import { useState, useEffect, useMemo } from 'react'
import {
  Card,
  Tag,
  Input,
  Button,
  Space,
  message,
  Spin,
  Typography,
  Tooltip,
  Popconfirm,
  Empty,
  Modal,
  Form,
  Collapse,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  HolderOutlined,
  InfoCircleOutlined,
  AimOutlined,
  SettingOutlined,
  DashOutlined,
  AppstoreOutlined,
  ExpandAltOutlined,
  ShrinkOutlined,
} from '@ant-design/icons'
import { configApi } from '@/api/services/config'

const { Title, Text } = Typography

/**
 * 选项数据结构（支持备注）
 */
interface OptionItem {
  value: string
  note?: string
}

/**
 * 分类定义
 */
type CategoryKey = 'rod' | 'reel' | 'line' | 'general'

const CATEGORIES: { key: CategoryKey; name: string; icon: React.ReactNode }[] = [
  { key: 'rod', name: '鱼竿设置', icon: <AimOutlined /> },
  { key: 'reel', name: '渔轮设置', icon: <SettingOutlined /> },
  { key: 'line', name: '鱼线设置', icon: <DashOutlined /> },
  { key: 'general', name: '通用设置', icon: <AppstoreOutlined /> },
]

/**
 * 预定义的装备选项组配置
 */
interface OptionGroupDef {
  key: string
  name: string
  description: string
  defaultValue: OptionItem[]
  color: string
  category: CategoryKey
}

const OPTION_GROUPS: OptionGroupDef[] = [
  {
    key: 'equipment.rod.power_options',
    name: '鱼竿调性 (Power)',
    description: '鱼竿硬度等级，从超软到超硬',
    category: 'rod',
    defaultValue: [
      { value: 'UL', note: '超轻调，适合微物钓法' },
      { value: 'L', note: '轻调，适合小型鱼类' },
      { value: 'ML', note: '中轻调，通用型' },
      { value: 'M', note: '中调，平衡性好' },
      { value: 'MH', note: '中硬调，适合中大型鱼' },
      { value: 'H', note: '硬调，适合大型鱼' },
      { value: 'XH', note: '超硬调，适合巨物' },
    ] as OptionItem[],
    color: 'blue',
  },
  {
    key: 'equipment.rod.action_options',
    name: '鱼竿动作 (Action)',
    description: '鱼竿弯曲恢复速度',
    category: 'rod',
    defaultValue: [
      { value: 'Fast', note: '快调，恢复迅速' },
      { value: 'Medium', note: '中调，平衡性好' },
      { value: 'Slow', note: '慢调，弯曲幅度大' },
    ] as OptionItem[],
    color: 'green',
  },
  {
    key: 'equipment.rod.action_options_cn',
    name: '鱼竿动作 (中文)',
    description: '鱼竿调性的中文表述',
    category: 'rod',
    defaultValue: [
      { value: '慢调', note: '弯曲幅度大，适合溜鱼' },
      { value: '中调', note: '平衡型，适用范围广' },
      { value: '快调', note: '恢复快，灵敏度高' },
      { value: '超快调', note: '极速恢复，精准度高' },
    ] as OptionItem[],
    color: 'cyan',
  },
  {
    key: 'equipment.user_level_options',
    name: '用户级别',
    description: '装备适合的用户水平',
    category: 'general',
    defaultValue: [
      { value: '新手', note: '入门级用户' },
      { value: '进阶', note: '有一定经验的用户' },
      { value: '高手', note: '经验丰富的专业用户' },
    ] as OptionItem[],
    color: 'purple',
  },
  {
    key: 'equipment.category_options',
    name: '装备类别',
    description: '装备的分类',
    category: 'general',
    defaultValue: [
      { value: '鱼竿', note: '钓鱼主要工具' },
      { value: '渔轮', note: '收放线装置' },
      { value: '鱼线', note: '连接鱼竿和鱼钩' },
      { value: '拟饵', note: '模拟饵料吸引鱼类' },
    ] as OptionItem[],
    color: 'orange',
  },
  {
    key: 'equipment.reel.type_options',
    name: '渔轮类型',
    description: '渔轮的类型分类',
    category: 'reel',
    defaultValue: [
      { value: 'spinning', note: '纺车轮，适合新手' },
      { value: 'baitcasting', note: '水滴轮，精准抛投' },
      { value: 'fly', note: '飞蝇轮，飞蝇钓专用' },
    ] as OptionItem[],
    color: 'geekblue',
  },
  {
    key: 'equipment.line.type_options',
    name: '鱼线类型',
    description: '鱼线的材质分类',
    category: 'line',
    defaultValue: [
      { value: 'PE', note: '编织线，强度高' },
      { value: '尼龙', note: '尼龙线，延展性好' },
      { value: '碳线', note: '碳素线，隐蔽性强' },
      { value: '钢丝', note: '钢丝线，防咬断' },
    ] as OptionItem[],
    color: 'magenta',
  },
]

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

interface OptionGroupState {
  options: OptionItem[]
  loading: boolean
  saving: boolean
}

const EquipmentOptions = () => {
  const [groupStates, setGroupStates] = useState<Record<string, OptionGroupState>>({})
  const [initializing, setInitializing] = useState(true)

  // 编辑/添加弹窗状态
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMode, setModalMode] = useState<'add' | 'edit'>('add')
  const [currentGroupKey, setCurrentGroupKey] = useState<string>('')
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [form] = Form.useForm()

  // Collapse 展开状态
  const [activeKeys, setActiveKeys] = useState<string[]>(CATEGORIES.map((c) => c.key))
  const allKeys = CATEGORIES.map((c) => c.key)
  const isAllExpanded = activeKeys.length === allKeys.length

  // 按分类分组选项
  const groupedByCategory = useMemo(() => {
    const result: Record<CategoryKey, OptionGroupDef[]> = {
      rod: [],
      reel: [],
      line: [],
      general: [],
    }
    OPTION_GROUPS.forEach((group) => {
      result[group.category].push(group)
    })
    return result
  }, [])

  useEffect(() => {
    loadAllOptions()
  }, [])

  const loadAllOptions = async () => {
    setInitializing(true)
    const newStates: Record<string, OptionGroupState> = {}

    // 并行加载所有选项组
    await Promise.all(
      OPTION_GROUPS.map(async (group) => {
        try {
          const config = await configApi.get(group.key)
          // config_value 可能已经是对象，也可能是 JSON 字符串
          const rawValue =
            typeof config.config_value === 'string'
              ? JSON.parse(config.config_value)
              : config.config_value
          const options = normalizeOptions(rawValue)
          newStates[group.key] = {
            options: options.length > 0 ? options : group.defaultValue,
            loading: false,
            saving: false,
          }
        } catch {
          // 配置不存在，使用默认值
          newStates[group.key] = {
            options: group.defaultValue,
            loading: false,
            saving: false,
          }
        }
      })
    )

    setGroupStates(newStates)
    setInitializing(false)
  }

  const updateGroupState = (key: string, updates: Partial<OptionGroupState>) => {
    setGroupStates((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...updates },
    }))
  }

  const saveOptions = async (groupKey: string, newOptions: OptionItem[]) => {
    const group = OPTION_GROUPS.find((g) => g.key === groupKey)
    if (!group) return

    updateGroupState(groupKey, { saving: true })

    try {
      // 尝试更新，如果不存在则创建
      try {
        await configApi.update(groupKey, {
          config_value: JSON.stringify(newOptions),
        })
      } catch {
        // 配置不存在，创建新的
        await configApi.create({
          config_key: groupKey,
          config_value: JSON.stringify(newOptions),
          config_type: 'system',
          description: group.description,
          is_encrypted: false,
        })
      }

      updateGroupState(groupKey, {
        options: newOptions,
        saving: false,
      })
      message.success('保存成功')
    } catch {
      updateGroupState(groupKey, { saving: false })
      message.error('保存失败')
    }
  }

  const openAddModal = (groupKey: string) => {
    setCurrentGroupKey(groupKey)
    setModalMode('add')
    setEditingIndex(null)
    form.resetFields()
    setModalVisible(true)
  }

  const openEditModal = (groupKey: string, index: number) => {
    const state = groupStates[groupKey]
    if (!state) return

    const option = state.options[index]
    setCurrentGroupKey(groupKey)
    setModalMode('edit')
    setEditingIndex(index)
    form.setFieldsValue({
      value: option.value,
      note: option.note || '',
    })
    setModalVisible(true)
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()
      const state = groupStates[currentGroupKey]
      if (!state) return

      const newOption: OptionItem = {
        value: values.value.trim(),
        note: values.note?.trim() || '',
      }

      // 检查是否重复
      const existingValues = state.options
        .filter((_, i) => i !== editingIndex)
        .map((o) => o.value)
      if (existingValues.includes(newOption.value)) {
        message.warning('该选项值已存在')
        return
      }

      let newOptions: OptionItem[]
      if (modalMode === 'add') {
        newOptions = [...state.options, newOption]
      } else {
        newOptions = [...state.options]
        if (editingIndex !== null) {
          newOptions[editingIndex] = newOption
        }
      }

      await saveOptions(currentGroupKey, newOptions)
      setModalVisible(false)
      form.resetFields()
    } catch {
      // 表单验证失败
    }
  }

  const handleDeleteOption = (groupKey: string, index: number) => {
    const state = groupStates[groupKey]
    if (!state) return

    const newOptions = state.options.filter((_, i) => i !== index)
    saveOptions(groupKey, newOptions)
  }

  const handleResetToDefault = async (groupKey: string) => {
    const group = OPTION_GROUPS.find((g) => g.key === groupKey)
    if (!group) return

    saveOptions(groupKey, group.defaultValue)
  }

  // 全部展开/收起
  const handleToggleAll = () => {
    if (isAllExpanded) {
      setActiveKeys([])
    } else {
      setActiveKeys(allKeys)
    }
  }

  if (initializing) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载配置中..." />
      </div>
    )
  }

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={4} style={{ marginBottom: 8 }}>
              装备属性选项管理
            </Title>
            <Text type="secondary">
              管理装备相关的属性选项，如调性、动作、用户级别等。修改后即时生效。鼠标悬停在选项上可查看备注。
            </Text>
          </div>
          <Button
            icon={isAllExpanded ? <ShrinkOutlined /> : <ExpandAltOutlined />}
            onClick={handleToggleAll}
          >
            {isAllExpanded ? '全部收起' : '全部展开'}
          </Button>
        </div>

        <Collapse
          activeKey={activeKeys}
          onChange={(keys) => setActiveKeys(keys as string[])}
          style={{ backgroundColor: 'transparent', border: 'none' }}
          items={CATEGORIES.map((category) => ({
            key: category.key,
            label: (
              <Space>
                {category.icon}
                <Text strong>{category.name}</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  ({groupedByCategory[category.key].length} 项)
                </Text>
              </Space>
            ),
            children: (
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {groupedByCategory[category.key].map((group) => {
                  const state = groupStates[group.key]
                  if (!state) return null

                  return (
                    <Card
                      key={group.key}
                      size="small"
                      title={
                        <Space>
                          <Text strong>{group.name}</Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            ({group.key})
                          </Text>
                        </Space>
                      }
                      extra={
                        <Space>
                          <Button
                            size="small"
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => openAddModal(group.key)}
                          >
                            添加
                          </Button>
                          <Popconfirm
                            title="确定恢复默认值？"
                            description="当前设置将被覆盖"
                            onConfirm={() => handleResetToDefault(group.key)}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button size="small" type="link">
                              恢复默认
                            </Button>
                          </Popconfirm>
                        </Space>
                      }
                    >
                      <div style={{ marginBottom: 8 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {group.description}
                        </Text>
                      </div>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                        {state.options.length === 0 ? (
                          <Empty
                            description="暂无选项"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            style={{ margin: '8px 0' }}
                          />
                        ) : (
                          state.options.map((option, index) => (
                            <Tooltip
                              key={index}
                              title={option.note || '暂无备注'}
                              placement="top"
                            >
                              <Tag
                                color={group.color}
                                style={{ cursor: 'pointer', userSelect: 'none' }}
                              >
                                <Space size={4}>
                                  <HolderOutlined style={{ cursor: 'grab', opacity: 0.5 }} />
                                  <span>{option.value}</span>
                                  {option.note && (
                                    <InfoCircleOutlined
                                      style={{ fontSize: 10, opacity: 0.6 }}
                                    />
                                  )}
                                  <EditOutlined
                                    style={{ fontSize: 10, opacity: 0.6 }}
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      openEditModal(group.key, index)
                                    }}
                                  />
                                  <Popconfirm
                                    title="确定删除此选项？"
                                    onConfirm={() => handleDeleteOption(group.key, index)}
                                    okText="确定"
                                    cancelText="取消"
                                  >
                                    <DeleteOutlined
                                      style={{ fontSize: 10, opacity: 0.6, color: '#ff4d4f' }}
                                      onClick={(e) => e.stopPropagation()}
                                    />
                                  </Popconfirm>
                                </Space>
                              </Tag>
                            </Tooltip>
                          ))
                        )}
                      </div>
                    </Card>
                  )
                })}
              </Space>
            ),
          }))}
        />
      </Card>

      {/* 添加/编辑弹窗 */}
      <Modal
        title={modalMode === 'add' ? '添加选项' : '编辑选项'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        okText="保存"
        cancelText="取消"
        forceRender
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="value"
            label="选项值"
            rules={[{ required: true, message: '请输入选项值' }]}
          >
            <Input placeholder="例如: UL" />
          </Form.Item>
          <Form.Item
            name="note"
            label="备注说明"
            extra="可选，用于解释该选项的含义"
          >
            <Input.TextArea
              placeholder="例如: 超轻调，适合微物钓法"
              rows={2}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default EquipmentOptions
