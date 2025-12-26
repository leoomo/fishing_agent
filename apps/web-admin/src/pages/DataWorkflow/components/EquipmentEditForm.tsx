/**
 * 装备编辑表单组件
 *
 * 用于显示和编辑提取的装备信息
 */

import React from 'react'
import {
  Form,
  Input,
  InputNumber,
  Select,
  Collapse,
  Button,
  Space,
  Tag,
  Divider,
  Row,
  Col,
  Tooltip,
  Empty,
} from 'antd'
import {
  DeleteOutlined,
  PlusOutlined,
  UndoOutlined,
} from '@ant-design/icons'
import type { ExtractedEquipmentItem } from '../../../types/dataWorkflow'
import {
  ROD_POWER_OPTIONS,
  ROD_ACTION_OPTIONS,
  USER_LEVEL_OPTIONS,
  EQUIPMENT_TYPE_OPTIONS,
} from '../../../types/dataWorkflow'

const { TextArea } = Input
const { Panel } = Collapse

interface EquipmentEditFormProps {
  items: ExtractedEquipmentItem[]
  onChange: (items: ExtractedEquipmentItem[]) => void
  onReset: () => void
  disabled?: boolean
}

// 创建空白装备项
const createEmptyItem = (): ExtractedEquipmentItem => ({
  equipment_type: '',
  brand_name: null,
  model: null,
  name: null,
  price_min: null,
  price_max: null,
  description: null,
  features: [],
  target_fish: [],
  user_level: null,
  specs: {},
  confidence: 0,
  extraction_notes: '',
})

const EquipmentEditForm: React.FC<EquipmentEditFormProps> = ({
  items,
  onChange,
  onReset,
  disabled,
}) => {
  // 更新单个装备项
  const updateItem = (index: number, field: keyof ExtractedEquipmentItem, value: unknown) => {
    const newItems = [...items]
    newItems[index] = { ...newItems[index], [field]: value }
    onChange(newItems)
  }

  // 更新 specs 中的字段
  const updateSpecs = (index: number, specField: string, value: unknown) => {
    const newItems = [...items]
    newItems[index] = {
      ...newItems[index],
      specs: { ...newItems[index].specs, [specField]: value },
    }
    onChange(newItems)
  }

  // 删除装备项
  const deleteItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index)
    onChange(newItems)
  }

  // 添加新装备项
  const addItem = () => {
    onChange([...items, createEmptyItem()])
  }

  // 渲染鱼竿规格字段
  const renderRodSpecs = (index: number, specs: Record<string, unknown>) => (
    <Row gutter={[16, 8]}>
      <Col span={8}>
        <Form.Item label="长度 (m)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.length as number}
            onChange={(v) => updateSpecs(index, 'length', v)}
            placeholder="如 1.98"
            step={0.01}
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="调性" style={{ marginBottom: 8 }}>
          <Select
            value={specs.power as string}
            onChange={(v) => updateSpecs(index, 'power', v)}
            placeholder="选择调性"
            allowClear
            disabled={disabled}
          >
            {ROD_POWER_OPTIONS.map((opt) => (
              <Select.Option key={opt} value={opt}>
                {opt}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="动作" style={{ marginBottom: 8 }}>
          <Select
            value={specs.action as string}
            onChange={(v) => updateSpecs(index, 'action', v)}
            placeholder="选择动作"
            allowClear
            disabled={disabled}
          >
            {ROD_ACTION_OPTIONS.map((opt) => (
              <Select.Option key={opt} value={opt}>
                {opt}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
      <Col span={6}>
        <Form.Item label="节数" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.sections as number}
            onChange={(v) => updateSpecs(index, 'sections', v)}
            placeholder="如 2"
            min={1}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={9}>
        <Form.Item label="饵重范围 (g)" style={{ marginBottom: 8 }}>
          <Input.Group compact>
            <InputNumber
              value={specs.lure_weight_min as number}
              onChange={(v) => updateSpecs(index, 'lure_weight_min', v)}
              placeholder="最小"
              style={{ width: '50%' }}
              disabled={disabled}
            />
            <InputNumber
              value={specs.lure_weight_max as number}
              onChange={(v) => updateSpecs(index, 'lure_weight_max', v)}
              placeholder="最大"
              style={{ width: '50%' }}
              disabled={disabled}
            />
          </Input.Group>
        </Form.Item>
      </Col>
      <Col span={9}>
        <Form.Item label="线重范围 (lb)" style={{ marginBottom: 8 }}>
          <Input.Group compact>
            <InputNumber
              value={specs.line_weight_min as number}
              onChange={(v) => updateSpecs(index, 'line_weight_min', v)}
              placeholder="最小"
              style={{ width: '50%' }}
              disabled={disabled}
            />
            <InputNumber
              value={specs.line_weight_max as number}
              onChange={(v) => updateSpecs(index, 'line_weight_max', v)}
              placeholder="最大"
              style={{ width: '50%' }}
              disabled={disabled}
            />
          </Input.Group>
        </Form.Item>
      </Col>
    </Row>
  )

  // 渲染渔轮规格字段
  const renderReelSpecs = (index: number, specs: Record<string, unknown>) => (
    <Row gutter={[16, 8]}>
      <Col span={8}>
        <Form.Item label="速比" style={{ marginBottom: 8 }}>
          <Input
            value={specs.gear_ratio as string}
            onChange={(e) => updateSpecs(index, 'gear_ratio', e.target.value)}
            placeholder="如 6.2:1"
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="轴承" style={{ marginBottom: 8 }}>
          <Input
            value={specs.bearings as string}
            onChange={(e) => updateSpecs(index, 'bearings', e.target.value)}
            placeholder="如 10+1BB"
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="最大拽力 (kg)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.max_drag as number}
            onChange={(v) => updateSpecs(index, 'max_drag', v)}
            placeholder="如 8"
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="重量 (g)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.weight as number}
            onChange={(v) => updateSpecs(index, 'weight', v)}
            placeholder="如 200"
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={16}>
        <Form.Item label="线容量" style={{ marginBottom: 8 }}>
          <Input
            value={specs.line_capacity as string}
            onChange={(e) => updateSpecs(index, 'line_capacity', e.target.value)}
            placeholder="如 0.23mm/150m"
            disabled={disabled}
          />
        </Form.Item>
      </Col>
    </Row>
  )

  // 渲染鱼线规格字段
  const renderLineSpecs = (index: number, specs: Record<string, unknown>) => (
    <Row gutter={[16, 8]}>
      <Col span={8}>
        <Form.Item label="线型" style={{ marginBottom: 8 }}>
          <Input
            value={specs.line_type as string}
            onChange={(e) => updateSpecs(index, 'line_type', e.target.value)}
            placeholder="如 PE线/碳线"
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="线径 (mm)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.diameter as number}
            onChange={(v) => updateSpecs(index, 'diameter', v)}
            placeholder="如 0.23"
            step={0.01}
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="拉力 (lb)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.strength_lb as number}
            onChange={(v) => updateSpecs(index, 'strength_lb', v)}
            placeholder="如 15"
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="长度 (m)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.length_m as number}
            onChange={(v) => updateSpecs(index, 'length_m', v)}
            placeholder="如 150"
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="颜色" style={{ marginBottom: 8 }}>
          <Input
            value={specs.color as string}
            onChange={(e) => updateSpecs(index, 'color', e.target.value)}
            placeholder="如 绿色"
            disabled={disabled}
          />
        </Form.Item>
      </Col>
    </Row>
  )

  // 渲染拟饵规格字段
  const renderLureSpecs = (index: number, specs: Record<string, unknown>) => (
    <Row gutter={[16, 8]}>
      <Col span={8}>
        <Form.Item label="拟饵类型" style={{ marginBottom: 8 }}>
          <Input
            value={specs.lure_type as string}
            onChange={(e) => updateSpecs(index, 'lure_type', e.target.value)}
            placeholder="如 米诺/VIB"
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="长度 (mm)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.length as number}
            onChange={(v) => updateSpecs(index, 'length', v)}
            placeholder="如 70"
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="重量 (g)" style={{ marginBottom: 8 }}>
          <InputNumber
            value={specs.weight as number}
            onChange={(v) => updateSpecs(index, 'weight', v)}
            placeholder="如 10"
            min={0}
            style={{ width: '100%' }}
            disabled={disabled}
          />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item label="潜深范围 (m)" style={{ marginBottom: 8 }}>
          <Input.Group compact>
            <InputNumber
              value={specs.diving_depth_min as number}
              onChange={(v) => updateSpecs(index, 'diving_depth_min', v)}
              placeholder="最小"
              style={{ width: '50%' }}
              disabled={disabled}
            />
            <InputNumber
              value={specs.diving_depth_max as number}
              onChange={(v) => updateSpecs(index, 'diving_depth_max', v)}
              placeholder="最大"
              style={{ width: '50%' }}
              disabled={disabled}
            />
          </Input.Group>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item label="动作类型" style={{ marginBottom: 8 }}>
          <Input
            value={specs.action_type as string}
            onChange={(e) => updateSpecs(index, 'action_type', e.target.value)}
            placeholder="如 摇摆/颤动"
            disabled={disabled}
          />
        </Form.Item>
      </Col>
    </Row>
  )

  // 根据装备类型渲染不同的规格字段
  const renderSpecsFields = (index: number, item: ExtractedEquipmentItem) => {
    const specs = item.specs || {}

    switch (item.equipment_type) {
      case '鱼竿':
        return renderRodSpecs(index, specs)
      case '渔轮':
        return renderReelSpecs(index, specs)
      case '鱼线':
        return renderLineSpecs(index, specs)
      case '拟饵':
        return renderLureSpecs(index, specs)
      default:
        return (
          <Form.Item label="其他规格 (JSON)" style={{ marginBottom: 8 }}>
            <TextArea
              value={JSON.stringify(specs, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value)
                  const newItems = [...items]
                  newItems[index] = { ...newItems[index], specs: parsed }
                  onChange(newItems)
                } catch {
                  // JSON 解析失败，忽略
                }
              }}
              rows={4}
              disabled={disabled}
            />
          </Form.Item>
        )
    }
  }

  // 渲染单个装备项表单
  const renderItemForm = (item: ExtractedEquipmentItem, index: number) => (
    <div style={{ padding: '8px 0' }}>
      {/* 基础信息 */}
      <Row gutter={[16, 8]}>
        <Col span={8}>
          <Form.Item label="装备类型" style={{ marginBottom: 8 }}>
            <Select
              value={item.equipment_type}
              onChange={(v) => updateItem(index, 'equipment_type', v)}
              placeholder="选择类型"
              disabled={disabled}
            >
              {EQUIPMENT_TYPE_OPTIONS.map((opt) => (
                <Select.Option key={opt.value} value={opt.value}>
                  {opt.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="品牌" style={{ marginBottom: 8 }}>
            <Input
              value={item.brand_name || ''}
              onChange={(e) => updateItem(index, 'brand_name', e.target.value || null)}
              placeholder="品牌名称"
              disabled={disabled}
            />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="型号" style={{ marginBottom: 8 }}>
            <Input
              value={item.model || ''}
              onChange={(e) => updateItem(index, 'model', e.target.value || null)}
              placeholder="型号"
              disabled={disabled}
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 8]}>
        <Col span={16}>
          <Form.Item label="名称" style={{ marginBottom: 8 }}>
            <Input
              value={item.name || ''}
              onChange={(e) => updateItem(index, 'name', e.target.value || null)}
              placeholder="产品名称"
              disabled={disabled}
            />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="用户级别" style={{ marginBottom: 8 }}>
            <Select
              value={item.user_level}
              onChange={(v) => updateItem(index, 'user_level', v)}
              placeholder="选择级别"
              allowClear
              disabled={disabled}
            >
              {USER_LEVEL_OPTIONS.map((opt) => (
                <Select.Option key={opt} value={opt}>
                  {opt}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 8]}>
        <Col span={12}>
          <Form.Item label="价格范围 (元)" style={{ marginBottom: 8 }}>
            <Input.Group compact>
              <InputNumber
                value={item.price_min}
                onChange={(v) => updateItem(index, 'price_min', v)}
                placeholder="最低价"
                style={{ width: '50%' }}
                min={0}
                disabled={disabled}
              />
              <InputNumber
                value={item.price_max}
                onChange={(v) => updateItem(index, 'price_max', v)}
                placeholder="最高价"
                style={{ width: '50%' }}
                min={0}
                disabled={disabled}
              />
            </Input.Group>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="目标鱼种" style={{ marginBottom: 8 }}>
            <Select
              mode="tags"
              value={item.target_fish}
              onChange={(v) => updateItem(index, 'target_fish', v)}
              placeholder="输入目标鱼种"
              disabled={disabled}
            />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item label="产品描述" style={{ marginBottom: 8 }}>
        <TextArea
          value={item.description || ''}
          onChange={(e) => updateItem(index, 'description', e.target.value || null)}
          placeholder="产品描述"
          rows={2}
          disabled={disabled}
        />
      </Form.Item>

      <Form.Item label="特点" style={{ marginBottom: 8 }}>
        <Select
          mode="tags"
          value={item.features}
          onChange={(v) => updateItem(index, 'features', v)}
          placeholder="输入产品特点"
          disabled={disabled}
        />
      </Form.Item>

      <Divider style={{ margin: '12px 0' }}>规格参数</Divider>
      {renderSpecsFields(index, item)}

      {/* 删除按钮 */}
      {!disabled && items.length > 1 && (
        <div style={{ marginTop: 12, textAlign: 'right' }}>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteItem(index)}
          >
            删除此型号
          </Button>
        </div>
      )}
    </div>
  )

  // 生成折叠面板标题
  const getPanelHeader = (item: ExtractedEquipmentItem, index: number) => (
    <Space>
      <span>
        型号 {index + 1}: {item.model || item.name || '未命名'}
      </span>
      {item.confidence > 0 && (
        <Tag color={item.confidence >= 0.8 ? 'green' : item.confidence >= 0.5 ? 'orange' : 'red'}>
          置信度 {Math.round(item.confidence * 100)}%
        </Tag>
      )}
    </Space>
  )

  if (items.length === 0) {
    return (
      <Empty
        description="暂无提取数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        {!disabled && (
          <Button type="primary" icon={<PlusOutlined />} onClick={addItem}>
            手动添加装备
          </Button>
        )}
      </Empty>
    )
  }

  return (
    <div>
      {/* 操作按钮 */}
      <div style={{ marginBottom: 12 }}>
        <Space>
          {!disabled && (
            <>
              <Tooltip title="重置为原始提取数据">
                <Button icon={<UndoOutlined />} onClick={onReset}>
                  重置
                </Button>
              </Tooltip>
              <Button type="dashed" icon={<PlusOutlined />} onClick={addItem}>
                添加型号
              </Button>
            </>
          )}
          <span style={{ color: '#999' }}>共 {items.length} 个型号</span>
        </Space>
      </div>

      {/* 折叠面板 */}
      <Collapse defaultActiveKey={['0']}>
        {items.map((item, index) => (
          <Panel header={getPanelHeader(item, index)} key={String(index)}>
            {renderItemForm(item, index)}
          </Panel>
        ))}
      </Collapse>
    </div>
  )
}

export default EquipmentEditForm
