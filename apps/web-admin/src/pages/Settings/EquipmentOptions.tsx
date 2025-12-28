import { useState, useEffect, useRef } from 'react'
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
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  CloseOutlined,
  HolderOutlined,
} from '@ant-design/icons'
import { configApi } from '@/api/services/config'
import type { Config } from '@/types/config'

const { Title, Text } = Typography

/**
 * 预定义的装备选项组配置
 */
const OPTION_GROUPS = [
  {
    key: 'equipment.rod.power_options',
    name: '鱼竿调性 (Power)',
    description: '鱼竿硬度等级，从超软到超硬',
    defaultValue: ['UL', 'L', 'ML', 'M', 'MH', 'H', 'XH'],
    color: 'blue',
  },
  {
    key: 'equipment.rod.action_options',
    name: '鱼竿动作 (Action)',
    description: '鱼竿弯曲恢复速度',
    defaultValue: ['Fast', 'Medium', 'Slow'],
    color: 'green',
  },
  {
    key: 'equipment.rod.action_options_cn',
    name: '鱼竿动作 (中文)',
    description: '鱼竿调性的中文表述',
    defaultValue: ['慢调', '中调', '快调', '超快调'],
    color: 'cyan',
  },
  {
    key: 'equipment.user_level_options',
    name: '用户级别',
    description: '装备适合的用户水平',
    defaultValue: ['新手', '进阶', '高手'],
    color: 'purple',
  },
  {
    key: 'equipment.category_options',
    name: '装备类别',
    description: '装备的分类',
    defaultValue: ['鱼竿', '渔轮', '鱼线', '拟饵'],
    color: 'orange',
  },
]

interface OptionGroupState {
  options: string[]
  loading: boolean
  editing: boolean
  editingIndex: number | null
  editingValue: string
  newValue: string
  saving: boolean
}

const EquipmentOptions = () => {
  const [groupStates, setGroupStates] = useState<Record<string, OptionGroupState>>({})
  const [initializing, setInitializing] = useState(true)
  const inputRef = useRef<any>(null)

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
          const options = JSON.parse(config.config_value)
          newStates[group.key] = {
            options: Array.isArray(options) ? options : group.defaultValue,
            loading: false,
            editing: false,
            editingIndex: null,
            editingValue: '',
            newValue: '',
            saving: false,
          }
        } catch {
          // 配置不存在，使用默认值
          newStates[group.key] = {
            options: group.defaultValue,
            loading: false,
            editing: false,
            editingIndex: null,
            editingValue: '',
            newValue: '',
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

  const saveOptions = async (groupKey: string, newOptions: string[]) => {
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
        editing: false,
        editingIndex: null,
        editingValue: '',
        newValue: '',
      })
      message.success('保存成功')
    } catch {
      updateGroupState(groupKey, { saving: false })
      message.error('保存失败')
    }
  }

  const handleAddOption = (groupKey: string) => {
    const state = groupStates[groupKey]
    if (!state || !state.newValue.trim()) return

    const newValue = state.newValue.trim()
    if (state.options.includes(newValue)) {
      message.warning('该选项已存在')
      return
    }

    const newOptions = [...state.options, newValue]
    saveOptions(groupKey, newOptions)
  }

  const handleEditOption = (groupKey: string, index: number) => {
    const state = groupStates[groupKey]
    if (!state) return

    updateGroupState(groupKey, {
      editing: true,
      editingIndex: index,
      editingValue: state.options[index],
    })

    // 自动聚焦输入框
    setTimeout(() => {
      inputRef.current?.focus()
    }, 100)
  }

  const handleSaveEdit = (groupKey: string) => {
    const state = groupStates[groupKey]
    if (!state || state.editingIndex === null) return

    const newValue = state.editingValue.trim()
    if (!newValue) {
      message.warning('选项值不能为空')
      return
    }

    // 检查是否与其他选项重复
    const otherOptions = state.options.filter((_, i) => i !== state.editingIndex)
    if (otherOptions.includes(newValue)) {
      message.warning('该选项已存在')
      return
    }

    const newOptions = [...state.options]
    newOptions[state.editingIndex] = newValue
    saveOptions(groupKey, newOptions)
  }

  const handleCancelEdit = (groupKey: string) => {
    updateGroupState(groupKey, {
      editing: false,
      editingIndex: null,
      editingValue: '',
    })
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
        <div style={{ marginBottom: 24 }}>
          <Title level={4} style={{ marginBottom: 8 }}>装备属性选项管理</Title>
          <Text type="secondary">
            管理装备相关的属性选项，如调性、动作、用户级别等。修改后即时生效。
          </Text>
        </div>

        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {OPTION_GROUPS.map((group) => {
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
                      <div key={index} style={{ display: 'inline-flex', alignItems: 'center' }}>
                        {state.editing && state.editingIndex === index ? (
                          <Space.Compact>
                            <Input
                              ref={inputRef}
                              size="small"
                              value={state.editingValue}
                              onChange={(e) =>
                                updateGroupState(group.key, { editingValue: e.target.value })
                              }
                              onPressEnter={() => handleSaveEdit(group.key)}
                              style={{ width: 100 }}
                            />
                            <Button
                              size="small"
                              type="primary"
                              icon={<SaveOutlined />}
                              onClick={() => handleSaveEdit(group.key)}
                              loading={state.saving}
                            />
                            <Button
                              size="small"
                              icon={<CloseOutlined />}
                              onClick={() => handleCancelEdit(group.key)}
                            />
                          </Space.Compact>
                        ) : (
                          <Tag
                            color={group.color}
                            style={{ cursor: 'pointer', userSelect: 'none' }}
                          >
                            <Space size={4}>
                              <HolderOutlined style={{ cursor: 'grab', opacity: 0.5 }} />
                              <span>{option}</span>
                              <Tooltip title="编辑">
                                <EditOutlined
                                  style={{ fontSize: 10, opacity: 0.6 }}
                                  onClick={() => handleEditOption(group.key, index)}
                                />
                              </Tooltip>
                              <Popconfirm
                                title="确定删除此选项？"
                                onConfirm={() => handleDeleteOption(group.key, index)}
                                okText="确定"
                                cancelText="取消"
                              >
                                <Tooltip title="删除">
                                  <DeleteOutlined
                                    style={{ fontSize: 10, opacity: 0.6, color: '#ff4d4f' }}
                                  />
                                </Tooltip>
                              </Popconfirm>
                            </Space>
                          </Tag>
                        )}
                      </div>
                    ))
                  )}

                  {/* 添加新选项 */}
                  <Space.Compact>
                    <Input
                      size="small"
                      placeholder="新选项..."
                      value={state.newValue}
                      onChange={(e) => updateGroupState(group.key, { newValue: e.target.value })}
                      onPressEnter={() => handleAddOption(group.key)}
                      style={{ width: 100 }}
                    />
                    <Button
                      size="small"
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => handleAddOption(group.key)}
                      loading={state.saving}
                      disabled={!state.newValue.trim()}
                    >
                      添加
                    </Button>
                  </Space.Compact>
                </div>
              </Card>
            )
          })}
        </Space>
      </Card>
    </div>
  )
}

export default EquipmentOptions
