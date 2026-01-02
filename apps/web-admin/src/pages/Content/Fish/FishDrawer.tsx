/**
 * 鱼种编辑抽屉组件
 *
 * 功能：
 * - 多标签页设计（基本信息/季节活动/知识库/装备推荐）
 * - 创建时只显示基本信息标签
 * - 编辑时显示全部4个标签
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Drawer,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  Tabs,
  message,
  Spin,
  Row,
  Col,
  Typography,
} from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { fishApi } from '@/api/services/fish'
import type {
  FishSpecies,
  FishSpeciesCreateRequest,
  FishSpeciesUpdateRequest,
  FishKnowledgeCreate,
  FishKnowledgeUpdate,
  FishSeasonActivityCreate,
  FishSeasonActivityUpdate,
} from '@/types/fish'
import { FISH_CATEGORY_OPTIONS } from '@/types/fish'
import SeasonActivityEditor from './SeasonActivityEditor'
import KnowledgeEditor from './KnowledgeEditor'
import EquipmentPanel from './EquipmentPanel'

const { TextArea } = Input
const { Text } = Typography

interface FishDrawerProps {
  open: boolean
  speciesId?: number | null
  onClose: () => void
  onSuccess: () => void
}

const FishDrawer: React.FC<FishDrawerProps> = ({ open, speciesId, onClose, onSuccess }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [fish, setFish] = useState<FishSpecies | null>(null)
  const [activeTab, setActiveTab] = useState('basic')

  const isEditing = speciesId !== null && speciesId !== undefined

  // 加载鱼种数据
  const loadFish = useCallback(async () => {
    if (!speciesId) return

    setLoading(true)
    try {
      const data = await fishApi.get(speciesId)
      setFish(data)
      form.setFieldsValue({
        name_cn: data.name_cn,
        name_en: data.name_en,
        scientific_name: data.scientific_name,
        category: data.category,
        habitat: data.habitat,
        description: data.description,
        image_url: data.image_url,
        min_weight: data.min_weight,
        max_weight: data.max_weight,
        min_length: data.min_length,
        max_length: data.max_length,
      })
    } catch {
      message.error('加载鱼种数据失败')
    } finally {
      setLoading(false)
    }
  }, [speciesId, form])

  useEffect(() => {
    if (open) {
      if (isEditing) {
        loadFish()
      } else {
        setFish(null)
        form.resetFields()
        form.setFieldsValue({
          category: 'freshwater',
        })
      }
      setActiveTab('basic')
    }
  }, [open, isEditing, loadFish, form])

  // 保存基本信息
  const handleSaveBasic = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)

      if (isEditing && speciesId) {
        const updated = await fishApi.update(speciesId, values as FishSpeciesUpdateRequest)
        setFish(updated)
        message.success('保存成功')
      } else {
        const created = await fishApi.create(values as FishSpeciesCreateRequest)
        setFish(created)
        message.success('创建成功')
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

  // 知识库操作
  const handleAddKnowledge = async (data: FishKnowledgeCreate) => {
    if (!fish) return
    await fishApi.addKnowledge(fish.species_id, data)
    await loadFish()
  }

  const handleUpdateKnowledge = async (knowledgeId: number, data: FishKnowledgeUpdate) => {
    if (!fish) return
    await fishApi.updateKnowledge(fish.species_id, knowledgeId, data)
    await loadFish()
  }

  const handleDeleteKnowledge = async (knowledgeId: number) => {
    if (!fish) return
    await fishApi.deleteKnowledge(fish.species_id, knowledgeId)
    await loadFish()
  }

  // 季节活动操作
  const handleAddSeasonActivity = async (data: FishSeasonActivityCreate) => {
    if (!fish) return
    await fishApi.addSeasonActivity(fish.species_id, data)
    await loadFish()
  }

  const handleUpdateSeasonActivity = async (seasonId: number, data: FishSeasonActivityUpdate) => {
    if (!fish) return
    await fishApi.updateSeasonActivity(fish.species_id, seasonId, data)
    await loadFish()
  }

  const handleDeleteSeasonActivity = async (seasonId: number) => {
    if (!fish) return
    await fishApi.deleteSeasonActivity(fish.species_id, seasonId)
    await loadFish()
  }

  // 分类选项
  const categoryOptions = FISH_CATEGORY_OPTIONS.map((opt) => ({
    value: opt.value,
    label: `${opt.icon} ${opt.label}`,
  }))

  // 标签页配置
  const tabItems = [
    {
      key: 'basic',
      label: '基本信息',
      children: (
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="name_cn"
            label="中文名"
            rules={[
              { required: true, message: '请输入中文名' },
              { max: 100, message: '中文名不能超过100个字符' },
            ]}
          >
            <Input placeholder="如：大嘴鲈、翘嘴鲌、鳜鱼" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name_en" label="英文名">
                <Input placeholder="如：Largemouth Bass" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="scientific_name" label="学名">
                <Input placeholder="如：Micropterus salmoides" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="category"
                label="分类"
                rules={[{ required: true, message: '请选择分类' }]}
              >
                <Select placeholder="选择分类" options={categoryOptions} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="habitat" label="栖息环境">
                <Input placeholder="如：湖泊、水库、河流" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="物种描述">
            <TextArea rows={3} placeholder="描述该鱼种的特点、习性等" />
          </Form.Item>

          <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>体型参数</div>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="min_weight" label="最小体重(kg)">
                <InputNumber min={0} step={0.1} precision={1} style={{ width: '100%' }} placeholder="0.5" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="max_weight" label="最大体重(kg)">
                <InputNumber min={0} step={0.1} precision={1} style={{ width: '100%' }} placeholder="10" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="min_length" label="最小体长(cm)">
                <InputNumber min={0} step={1} precision={0} style={{ width: '100%' }} placeholder="20" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="max_length" label="最大体长(cm)">
                <InputNumber min={0} step={1} precision={0} style={{ width: '100%' }} placeholder="80" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="image_url" label="图片URL">
            <Input placeholder="https://..." />
          </Form.Item>

          <div style={{ marginTop: 24 }}>
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveBasic} loading={saving}>
              {isEditing ? '保存修改' : '创建鱼种'}
            </Button>
          </div>
        </Form>
      ),
    },
    {
      key: 'seasons',
      label: '季节活动',
      disabled: !fish,
      children: fish ? (
        <SeasonActivityEditor
          activities={fish.season_activity}
          loading={loading}
          onAdd={handleAddSeasonActivity}
          onUpdate={handleUpdateSeasonActivity}
          onDelete={handleDeleteSeasonActivity}
        />
      ) : (
        <Text type="secondary">请先保存基本信息</Text>
      ),
    },
    {
      key: 'knowledge',
      label: '知识库',
      disabled: !fish,
      children: fish ? (
        <KnowledgeEditor
          knowledge={fish.knowledge}
          loading={loading}
          onAdd={handleAddKnowledge}
          onUpdate={handleUpdateKnowledge}
          onDelete={handleDeleteKnowledge}
        />
      ) : (
        <Text type="secondary">请先保存基本信息</Text>
      ),
    },
    {
      key: 'equipment',
      label: '装备推荐',
      disabled: !fish,
      children: fish ? (
        <EquipmentPanel speciesId={fish.species_id} />
      ) : (
        <Text type="secondary">请先保存基本信息</Text>
      ),
    },
  ]

  return (
    <Drawer
      title={isEditing ? '编辑鱼种' : '新建鱼种'}
      open={open}
      onClose={onClose}
      width={640}
      destroyOnClose
    >
      <Spin spinning={loading}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Spin>
    </Drawer>
  )
}

export default FishDrawer
