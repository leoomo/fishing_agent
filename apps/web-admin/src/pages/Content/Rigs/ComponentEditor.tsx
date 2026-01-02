/**
 * Component Editor - Manage rig components with drag-and-drop
 */

import { useState } from 'react'
import {
  List,
  Button,
  Space,
  Typography,
  Input,
  Select,
  InputNumber,
  Popconfirm,
  Empty,
  message,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  HolderOutlined,
  SaveOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import type { RigComponent, RigComponentCreate, RigComponentUpdate } from '@/types/rig'
import { COMPONENT_TYPE_OPTIONS, getComponentTypeConfig } from '@/types/rig'

const { Text } = Typography

interface ComponentEditorProps {
  components: RigComponent[]
  loading?: boolean
  onAdd: (data: RigComponentCreate) => Promise<void>
  onUpdate: (componentId: number, data: RigComponentUpdate) => Promise<void>
  onDelete: (componentId: number) => Promise<void>
  onReorder?: (componentIds: number[]) => Promise<void>
}

interface EditingState {
  id: number | 'new' | null
  data: Partial<RigComponentCreate>
}

const ComponentEditor: React.FC<ComponentEditorProps> = ({
  components,
  loading,
  onAdd,
  onUpdate,
  onDelete,
}) => {
  const [editing, setEditing] = useState<EditingState>({ id: null, data: {} })
  const [saving, setSaving] = useState(false)

  const handleStartAdd = () => {
    setEditing({
      id: 'new',
      data: {
        component_name: '',
        component_type: 'hook',
        quantity: 1,
      },
    })
  }

  const handleStartEdit = (component: RigComponent) => {
    setEditing({
      id: component.component_id,
      data: {
        component_name: component.component_name,
        component_type: component.component_type,
        quantity: component.quantity,
        size: component.size,
        notes: component.notes,
      },
    })
  }

  const handleCancel = () => {
    setEditing({ id: null, data: {} })
  }

  const handleSave = async () => {
    if (!editing.data.component_name?.trim()) {
      message.warning('请输入组件名称')
      return
    }
    if (!editing.data.component_type) {
      message.warning('请选择组件类型')
      return
    }

    setSaving(true)
    try {
      if (editing.id === 'new') {
        await onAdd(editing.data as RigComponentCreate)
        message.success('组件已添加')
      } else if (typeof editing.id === 'number') {
        await onUpdate(editing.id, editing.data)
        message.success('组件已更新')
      }
      handleCancel()
    } catch {
      message.error('操作失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (componentId: number) => {
    try {
      await onDelete(componentId)
      message.success('组件已删除')
    } catch {
      message.error('删除失败')
    }
  }

  const updateEditingData = (field: string, value: unknown) => {
    setEditing(prev => ({
      ...prev,
      data: { ...prev.data, [field]: value },
    }))
  }

  // Sort by position
  const sortedComponents = [...components].sort(
    (a, b) => (a.position || 0) - (b.position || 0)
  )

  const renderEditForm = () => (
    <div
      style={{
        padding: 16,
        background: '#fafafa',
        borderRadius: 8,
        marginBottom: 12,
      }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        <Space wrap style={{ width: '100%' }}>
          <Input
            placeholder="组件名称"
            value={editing.data.component_name}
            onChange={e => updateEditingData('component_name', e.target.value)}
            style={{ width: 180 }}
          />
          <Select
            value={editing.data.component_type}
            onChange={v => updateEditingData('component_type', v)}
            style={{ width: 120 }}
            options={COMPONENT_TYPE_OPTIONS.map(opt => ({
              value: opt.value,
              label: `${opt.icon || ''} ${opt.label}`,
            }))}
          />
          <InputNumber
            min={1}
            value={editing.data.quantity}
            onChange={v => updateEditingData('quantity', v)}
            addonBefore="数量"
            style={{ width: 120 }}
          />
          <Input
            placeholder="尺寸规格"
            value={editing.data.size}
            onChange={e => updateEditingData('size', e.target.value)}
            style={{ width: 120 }}
          />
        </Space>
        <Input
          placeholder="备注说明（可选）"
          value={editing.data.notes}
          onChange={e => updateEditingData('notes', e.target.value)}
        />
        <Space>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saving}
          >
            保存
          </Button>
          <Button icon={<CloseOutlined />} onClick={handleCancel}>
            取消
          </Button>
        </Space>
      </Space>
    </div>
  )

  return (
    <div>
      {/* Add button */}
      <div style={{ marginBottom: 16 }}>
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={handleStartAdd}
          disabled={editing.id !== null}
          block
        >
          添加组件
        </Button>
      </div>

      {/* New component form */}
      {editing.id === 'new' && renderEditForm()}

      {/* Component list */}
      {sortedComponents.length === 0 && editing.id !== 'new' ? (
        <Empty
          description="暂无组件"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <List
          loading={loading}
          dataSource={sortedComponents}
          renderItem={(component, index) => {
            const isEditing = editing.id === component.component_id
            const typeConfig = getComponentTypeConfig(component.component_type)

            if (isEditing) {
              return (
                <List.Item style={{ padding: 0, border: 'none' }}>
                  {renderEditForm()}
                </List.Item>
              )
            }

            return (
              <List.Item
                style={{
                  padding: '12px 16px',
                  background: '#fff',
                  borderRadius: 8,
                  marginBottom: 8,
                  border: '1px solid #f0f0f0',
                }}
                actions={[
                  <Button
                    key="edit"
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => handleStartEdit(component)}
                    disabled={editing.id !== null}
                  />,
                  <Popconfirm
                    key="delete"
                    title="确定删除此组件？"
                    onConfirm={() => handleDelete(component.component_id)}
                    okText="删除"
                    cancelText="取消"
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      disabled={editing.id !== null}
                    />
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                      }}
                    >
                      <HolderOutlined style={{ color: '#d9d9d9', cursor: 'grab' }} />
                      <span
                        style={{
                          width: 24,
                          height: 24,
                          borderRadius: 6,
                          background: '#f5f5f5',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 12,
                          color: '#999',
                        }}
                      >
                        {index + 1}
                      </span>
                    </div>
                  }
                  title={
                    <Space>
                      <Text strong>{component.component_name}</Text>
                      <Text
                        style={{
                          fontSize: 12,
                          padding: '2px 8px',
                          background: '#f5f5f5',
                          borderRadius: 4,
                        }}
                      >
                        {typeConfig.icon} {typeConfig.label}
                      </Text>
                    </Space>
                  }
                  description={
                    <Space size={16}>
                      <Text type="secondary">×{component.quantity}</Text>
                      {component.size && (
                        <Text type="secondary">{component.size}</Text>
                      )}
                      {component.notes && (
                        <Text type="secondary" ellipsis style={{ maxWidth: 200 }}>
                          {component.notes}
                        </Text>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )
          }}
        />
      )}
    </div>
  )
}

export default ComponentEditor
