/**
 * Rig Drawer - Create/Edit rig with multi-tab interface
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Drawer,
  Form,
  Input,
  Select,
  Button,
  Tabs,
  message,
  Spin,
  Space,
  Typography,
} from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { rigApi } from '@/api/services/rig'
import type {
  Rig,
  RigCreateRequest,
  RigUpdateRequest,
  RigComponentCreate,
  RigComponentUpdate,
  RigSpecCreate,
  RigSpecUpdate,
  LureTypeSimple,
} from '@/types/rig'
import {
  RIG_CATEGORY_CONFIG,
  RIG_DIFFICULTY_CONFIG,
} from '@/types/rig'
import ComponentEditor from './ComponentEditor'
import SpecEditor from './SpecEditor'

const { TextArea } = Input
const { Text } = Typography

interface RigDrawerProps {
  open: boolean
  rigId?: number | null
  onClose: () => void
  onSuccess: () => void
}

const RigDrawer: React.FC<RigDrawerProps> = ({
  open,
  rigId,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [rig, setRig] = useState<Rig | null>(null)
  const [activeTab, setActiveTab] = useState('basic')
  const [lureTypes, setLureTypes] = useState<LureTypeSimple[]>([])
  const [selectedLureTypes, setSelectedLureTypes] = useState<number[]>([])

  const isEditing = rigId !== null && rigId !== undefined

  // Load rig data
  const loadRig = useCallback(async () => {
    if (!rigId) return

    setLoading(true)
    try {
      const data = await rigApi.get(rigId)
      setRig(data)
      form.setFieldsValue({
        name: data.name,
        category: data.category,
        difficulty: data.difficulty,
        description: data.description,
        diagram_url: data.diagram_url,
        target_species: data.target_species,
        best_conditions: data.best_conditions,
      })

      // Load associated lure types
      const associatedLures = await rigApi.getLureTypes(rigId)
      setSelectedLureTypes(associatedLures.map(l => l.lure_type_id))
    } catch {
      message.error('加载钓组失败')
    } finally {
      setLoading(false)
    }
  }, [rigId, form])

  // Load all lure types for selection
  const loadLureTypes = useCallback(async () => {
    try {
      const data = await rigApi.getAllLureTypes()
      setLureTypes(data)
    } catch {
      // Ignore error, lure types may not be available
    }
  }, [])

  useEffect(() => {
    if (open) {
      loadLureTypes()
      if (isEditing) {
        loadRig()
      } else {
        setRig(null)
        form.resetFields()
        form.setFieldsValue({
          difficulty: 'medium',
        })
        setSelectedLureTypes([])
      }
      setActiveTab('basic')
    }
  }, [open, isEditing, loadRig, loadLureTypes, form])

  // Save basic info
  const handleSaveBasic = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)

      if (isEditing && rigId) {
        const updated = await rigApi.update(rigId, values as RigUpdateRequest)
        setRig(updated)
        message.success('保存成功')
      } else {
        const created = await rigApi.create(values as RigCreateRequest)
        setRig(created)
        message.success('创建成功')
        // After creating, continue editing
      }
      onSuccess()
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) {
        return
      }
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  // Component handlers
  const handleAddComponent = async (data: RigComponentCreate) => {
    if (!rig) return
    await rigApi.addComponent(rig.rig_id, data)
    await loadRig()
  }

  const handleUpdateComponent = async (componentId: number, data: RigComponentUpdate) => {
    if (!rig) return
    await rigApi.updateComponent(rig.rig_id, componentId, data)
    await loadRig()
  }

  const handleDeleteComponent = async (componentId: number) => {
    if (!rig) return
    await rigApi.deleteComponent(rig.rig_id, componentId)
    await loadRig()
  }

  // Spec handlers
  const handleAddSpec = async (data: RigSpecCreate) => {
    if (!rig) return
    await rigApi.addSpec(rig.rig_id, data)
    await loadRig()
  }

  const handleUpdateSpec = async (specId: number, data: RigSpecUpdate) => {
    if (!rig) return
    await rigApi.updateSpec(rig.rig_id, specId, data)
    await loadRig()
  }

  const handleDeleteSpec = async (specId: number) => {
    if (!rig) return
    await rigApi.deleteSpec(rig.rig_id, specId)
    await loadRig()
  }

  // Lure type association
  const handleLureTypesChange = async (values: number[]) => {
    if (!rig) return
    try {
      await rigApi.setLureTypes(rig.rig_id, values)
      setSelectedLureTypes(values)
      message.success('关联已更新')
    } catch {
      message.error('更新关联失败')
    }
  }

  // Build category options
  const categoryOptions = Object.entries(RIG_CATEGORY_CONFIG).map(([value, config]) => ({
    value,
    label: `${config.icon} ${config.label}`,
  }))

  // Build difficulty options
  const difficultyOptions = Object.entries(RIG_DIFFICULTY_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }))

  const tabItems = [
    {
      key: 'basic',
      label: '基本信息',
      children: (
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
        >
          <Form.Item
            name="name"
            label="钓组名称"
            rules={[{ required: true, message: '请输入钓组名称' }]}
          >
            <Input placeholder="如：台钓调漂钓组、德州钓组" />
          </Form.Item>

          <Space style={{ width: '100%' }} size={16}>
            <Form.Item
              name="category"
              label="分类"
              rules={[{ required: true, message: '请选择分类' }]}
              style={{ flex: 1 }}
            >
              <Select
                placeholder="选择分类"
                options={categoryOptions}
              />
            </Form.Item>

            <Form.Item
              name="difficulty"
              label="难度"
              style={{ width: 120 }}
            >
              <Select
                options={difficultyOptions}
              />
            </Form.Item>
          </Space>

          <Form.Item
            name="target_species"
            label="目标鱼种"
          >
            <Input placeholder="如：鲫鱼、鲤鱼、黑鲈" />
          </Form.Item>

          <Form.Item
            name="diagram_url"
            label="示意图URL"
          >
            <Input placeholder="https://..." />
          </Form.Item>

          <Form.Item
            name="description"
            label="详细描述"
          >
            <TextArea
              rows={3}
              placeholder="钓组特点和适用场景"
            />
          </Form.Item>

          <Form.Item
            name="best_conditions"
            label="最佳钓鱼条件"
          >
            <TextArea
              rows={2}
              placeholder="描述最适合使用此钓组的天气、水域、季节等"
            />
          </Form.Item>

          <div style={{ marginTop: 24 }}>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSaveBasic}
              loading={saving}
            >
              {isEditing ? '保存修改' : '创建钓组'}
            </Button>
          </div>
        </Form>
      ),
    },
    {
      key: 'components',
      label: '组件配件',
      disabled: !rig,
      children: rig ? (
        <ComponentEditor
          components={rig.components}
          loading={loading}
          onAdd={handleAddComponent}
          onUpdate={handleUpdateComponent}
          onDelete={handleDeleteComponent}
        />
      ) : (
        <Text type="secondary">请先保存基本信息</Text>
      ),
    },
    {
      key: 'specs',
      label: '规格参数',
      disabled: !rig,
      children: rig ? (
        <SpecEditor
          specs={rig.specs}
          loading={loading}
          onAdd={handleAddSpec}
          onUpdate={handleUpdateSpec}
          onDelete={handleDeleteSpec}
        />
      ) : (
        <Text type="secondary">请先保存基本信息</Text>
      ),
    },
    {
      key: 'lures',
      label: '关联拟饵',
      disabled: !rig,
      children: rig ? (
        <div>
          <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
            选择适用于此钓组的拟饵类型
          </Text>
          <Select
            mode="multiple"
            placeholder="选择拟饵类型"
            value={selectedLureTypes}
            onChange={handleLureTypesChange}
            style={{ width: '100%' }}
            options={lureTypes.map(lt => ({
              value: lt.lure_type_id,
              label: lt.name,
            }))}
            optionFilterProp="label"
            showSearch
          />
        </div>
      ) : (
        <Text type="secondary">请先保存基本信息</Text>
      ),
    },
  ]

  return (
    <Drawer
      title={isEditing ? '编辑钓组' : '新建钓组'}
      open={open}
      onClose={onClose}
      width={560}
      destroyOnClose
    >
      <Spin spinning={loading}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Spin>
    </Drawer>
  )
}

export default RigDrawer
