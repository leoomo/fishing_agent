/**
 * 手动批量输入表单
 *
 * 步骤式表单：
 * 1. 选择类别
 * 2. 填写共享模板
 * 3. 添加型号变体
 * 4. 预览确认
 */

import React, { useState } from 'react'
import {
  Steps,
  Button,
  Space,
  Form,
  Select,
  Input,
  InputNumber,
  Row,
  Col,
  Divider,
  Table,
  Popconfirm,
  message,
  Card,
  Typography,
  Switch,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import type { Brand } from '@/api/services/equipment'
import type { ColumnsType } from 'antd/es/table'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography

interface ManualBatchFormProps {
  brands: Brand[]
  onSubmit: (
    category: string,
    template: Record<string, unknown>,
    variants: Record<string, unknown>[],
    skipDuplicates: boolean
  ) => Promise<void>
  loading: boolean
}

interface VariantRow {
  key: string
  model: string
  length: number | null
  power: string
  action?: string
  weight?: number | null
  lure_weight_min?: number | null
  lure_weight_max?: number | null
  price_min?: number | null
  price_max?: number | null
}

const CATEGORIES = [
  { value: '鱼竿', label: '鱼竿' },
  { value: '渔轮', label: '渔轮' },
  { value: '鱼线', label: '鱼线' },
  { value: '拟饵', label: '拟饵' },
]

const POWER_OPTIONS = ['UL', 'L', 'ML', 'M', 'MH', 'H', 'XH']
const ACTION_OPTIONS = ['Fast', 'Medium', 'Slow']
const USER_LEVEL_OPTIONS = ['新手', '进阶', '高手']

const ManualBatchForm: React.FC<ManualBatchFormProps> = ({
  brands,
  onSubmit,
  loading,
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [category, setCategory] = useState<string>('鱼竿')
  const [templateForm] = Form.useForm()
  const [variants, setVariants] = useState<VariantRow[]>([])
  const [skipDuplicates, setSkipDuplicates] = useState(true)

  // 生成唯一 key
  const generateKey = () => `row_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  // 添加变体行
  const handleAddVariant = () => {
    setVariants([
      ...variants,
      {
        key: generateKey(),
        model: '',
        length: null,
        power: 'M',
        action: 'Fast',
        weight: null,
        lure_weight_min: null,
        lure_weight_max: null,
        price_min: null,
        price_max: null,
      },
    ])
  }

  // 复制变体行
  const handleCopyVariant = (record: VariantRow) => {
    setVariants([
      ...variants,
      { ...record, key: generateKey(), model: `${record.model}_copy` },
    ])
  }

  // 删除变体行
  const handleDeleteVariant = (key: string) => {
    setVariants(variants.filter((v) => v.key !== key))
  }

  // 更新变体行
  const handleUpdateVariant = (key: string, field: string, value: unknown) => {
    setVariants(
      variants.map((v) =>
        v.key === key ? { ...v, [field]: value } : v
      )
    )
  }

  // 下一步
  const handleNext = async () => {
    if (currentStep === 1) {
      // 验证模板表单
      try {
        await templateForm.validateFields()
        setCurrentStep(currentStep + 1)
      } catch {
        message.warning('请完成必填字段')
      }
    } else if (currentStep === 2) {
      // 验证变体列表
      if (variants.length === 0) {
        message.warning('请至少添加一个型号')
        return
      }
      const invalidVariants = variants.filter(
        (v) => !v.model || !v.length || !v.power
      )
      if (invalidVariants.length > 0) {
        message.warning('请完成所有型号的必填字段（型号、长度、调性）')
        return
      }
      setCurrentStep(currentStep + 1)
    } else {
      setCurrentStep(currentStep + 1)
    }
  }

  // 上一步
  const handlePrev = () => {
    setCurrentStep(currentStep - 1)
  }

  // 提交
  const handleSubmit = async () => {
    const template = templateForm.getFieldsValue()
    const variantData = variants.map(({ key, ...rest }) => rest)

    await onSubmit(category, template, variantData, skipDuplicates)
  }

  // 变体表格列定义
  const variantColumns: ColumnsType<VariantRow> = [
    {
      title: '型号 *',
      dataIndex: 'model',
      width: 120,
      render: (_, record) => (
        <Input
          value={record.model}
          onChange={(e) =>
            handleUpdateVariant(record.key, 'model', e.target.value)
          }
          placeholder="如 264MH"
        />
      ),
    },
    {
      title: '长度(米) *',
      dataIndex: 'length',
      width: 100,
      render: (_, record) => (
        <InputNumber
          value={record.length}
          onChange={(value) =>
            handleUpdateVariant(record.key, 'length', value)
          }
          min={0.5}
          max={10}
          step={0.01}
          style={{ width: '100%' }}
          placeholder="2.64"
        />
      ),
    },
    {
      title: '调性 *',
      dataIndex: 'power',
      width: 80,
      render: (_, record) => (
        <Select
          value={record.power}
          onChange={(value) =>
            handleUpdateVariant(record.key, 'power', value)
          }
          style={{ width: '100%' }}
        >
          {POWER_OPTIONS.map((p) => (
            <Option key={p} value={p}>
              {p}
            </Option>
          ))}
        </Select>
      ),
    },
    {
      title: '动作',
      dataIndex: 'action',
      width: 90,
      render: (_, record) => (
        <Select
          value={record.action}
          onChange={(value) =>
            handleUpdateVariant(record.key, 'action', value)
          }
          style={{ width: '100%' }}
          allowClear
        >
          {ACTION_OPTIONS.map((a) => (
            <Option key={a} value={a}>
              {a}
            </Option>
          ))}
        </Select>
      ),
    },
    {
      title: '自重(g)',
      dataIndex: 'weight',
      width: 80,
      render: (_, record) => (
        <InputNumber
          value={record.weight}
          onChange={(value) =>
            handleUpdateVariant(record.key, 'weight', value)
          }
          min={0}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: '饵重范围(g)',
      dataIndex: 'lure_weight',
      width: 140,
      render: (_, record) => (
        <Space size={4}>
          <InputNumber
            value={record.lure_weight_min}
            onChange={(value) =>
              handleUpdateVariant(record.key, 'lure_weight_min', value)
            }
            min={0}
            style={{ width: 60 }}
            placeholder="最小"
          />
          <span>-</span>
          <InputNumber
            value={record.lure_weight_max}
            onChange={(value) =>
              handleUpdateVariant(record.key, 'lure_weight_max', value)
            }
            min={0}
            style={{ width: 60 }}
            placeholder="最大"
          />
        </Space>
      ),
    },
    {
      title: '操作',
      width: 80,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<CopyOutlined />}
            onClick={() => handleCopyVariant(record)}
            title="复制"
          />
          <Popconfirm
            title="确定删除这一行？"
            onConfirm={() => handleDeleteVariant(record.key)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} title="删除" />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 渲染步骤 0: 选择类别
  const renderStep0 = () => (
    <div style={{ textAlign: 'center', padding: '40px 0', display: currentStep === 0 ? 'block' : 'none' }}>
      <Text style={{ fontSize: 16, marginBottom: 24, display: 'block' }}>
        选择要批量添加的装备类别
      </Text>
      <Select
        value={category}
        onChange={setCategory}
        style={{ width: 200 }}
        size="large"
      >
        {CATEGORIES.map((c) => (
          <Option key={c.value} value={c.value}>
            {c.label}
          </Option>
        ))}
      </Select>
    </div>
  )

  // 渲染步骤 1: 填写模板（始终挂载，用 display 控制显示）
  const renderStep1 = () => (
    <Form
      form={templateForm}
      layout="vertical"
      initialValues={{
        user_level: '进阶',
      }}
      style={{ display: currentStep === 1 ? 'block' : 'none' }}
      preserve={true}
    >
      <Row gutter={16}>
        <Col span={8}>
          <Form.Item
            name="brand_id"
            label="品牌"
            rules={[{ required: true, message: '请选择品牌' }]}
          >
            <Select placeholder="选择品牌" showSearch optionFilterProp="children">
              {brands.map((b) => (
                <Option key={b.brand_id} value={b.brand_id}>
                  {b.name_cn}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item
            name="product_line"
            label="产品线"
            rules={[{ required: true, message: '请输入产品线名称' }]}
          >
            <Input placeholder="如：POISON 21代" />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="user_level" label="适用水平">
            <Select>
              {USER_LEVEL_OPTIONS.map((l) => (
                <Option key={l} value={l}>
                  {l}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Divider>规格参数（可选）</Divider>

      <Row gutter={16}>
        <Col span={6}>
          <Form.Item name="sections" label="节数">
            <InputNumber min={1} max={10} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item name="guide_type" label="导环类型">
            <Input placeholder="如：富士K导环" />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item name="handle_type" label="握把类型">
            <Input placeholder="如：EVA分体式" />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item name="material" label="材质">
            <Input placeholder="如：高碳素" />
          </Form.Item>
        </Col>
      </Row>

      <Divider>价格与描述（可选）</Divider>

      <Row gutter={16}>
        <Col span={6}>
          <Form.Item name="price_min" label="默认最低价">
            <InputNumber
              min={0}
              style={{ width: '100%' }}
              formatter={(value) => `¥ ${value}`}
            />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item name="price_max" label="默认最高价">
            <InputNumber
              min={0}
              style={{ width: '100%' }}
              formatter={(value) => `¥ ${value}`}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="features" label="特点">
            <Input placeholder="输入装备特点" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="输入装备描述" />
          </Form.Item>
        </Col>
      </Row>
    </Form>
  )

  // 渲染步骤 2: 添加型号
  const renderStep2 = () => (
    <div style={{ display: currentStep === 2 ? 'block' : 'none' }}>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="dashed"
          onClick={handleAddVariant}
          icon={<PlusOutlined />}
        >
          添加型号
        </Button>
        <Text type="secondary" style={{ marginLeft: 16 }}>
          每行代表一个型号，必填：型号、长度、调性
        </Text>
      </div>

      <Table
        columns={variantColumns}
        dataSource={variants}
        pagination={false}
        size="small"
        scroll={{ x: 'max-content' }}
        locale={{ emptyText: '暂无数据，请点击"添加型号"按钮添加' }}
      />
    </div>
  )

  // 渲染步骤 3: 预览确认
  const renderStep3 = () => {
    const template = templateForm.getFieldsValue()
    const previewBrand = brands.find((b) => b.brand_id === template.brand_id)

    return (
      <div style={{ display: currentStep === 3 ? 'block' : 'none' }}>
        <Card title="共享信息" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Text type="secondary">品牌：</Text>
              <Text strong>{previewBrand?.name_cn || '-'}</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">产品线：</Text>
              <Text strong>{template.product_line || '-'}</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">适用水平：</Text>
              <Text strong>{template.user_level || '-'}</Text>
            </Col>
          </Row>
          {(template.price_min || template.price_max) && (
            <Row gutter={16} style={{ marginTop: 8 }}>
              <Col span={24}>
                <Text type="secondary">默认价格：</Text>
                <Text strong>
                  ¥{template.price_min || 0} - ¥{template.price_max || 0}
                </Text>
              </Col>
            </Row>
          )}
        </Card>

        <Card
          title={`型号列表 (${variants.length} 个)`}
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Table
            columns={[
              { title: '型号', dataIndex: 'model', width: 100 },
              {
                title: '预览名称',
                render: (_, record: VariantRow) =>
                  `${previewBrand?.name_cn || ''} ${template.product_line || ''} ${record.model}`,
              },
              { title: '长度', dataIndex: 'length', render: (v: number | null) => v ? `${v}m` : '-' },
              { title: '调性', dataIndex: 'power' },
              { title: '自重', dataIndex: 'weight', render: (v: number | null) => v ? `${v}g` : '-' },
            ]}
            dataSource={variants}
            pagination={false}
            size="small"
          />
        </Card>

        <Card size="small">
          <Space>
            <Text>跳过重复装备（同品牌同型号）：</Text>
            <Switch
              checked={skipDuplicates}
              onChange={setSkipDuplicates}
            />
          </Space>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Steps
        current={currentStep}
        items={[
          { title: '选择类别' },
          { title: '填写模板' },
          { title: '添加型号' },
          { title: '预览确认' },
        ]}
        style={{ marginBottom: 24 }}
      />

      <div style={{ minHeight: 300 }}>
        {/* 所有步骤内容同时渲染，用 display 控制显示，避免表单数据丢失 */}
        {renderStep0()}
        {renderStep1()}
        {renderStep2()}
        {renderStep3()}
      </div>

      <Divider />

      <div style={{ textAlign: 'right' }}>
        <Space>
          {currentStep > 0 && (
            <Button onClick={handlePrev}>上一步</Button>
          )}
          {currentStep < 3 && (
            <Button type="primary" onClick={handleNext}>
              下一步
            </Button>
          )}
          {currentStep === 3 && (
            <Button type="primary" onClick={handleSubmit} loading={loading}>
              确认创建 ({variants.length} 个装备)
            </Button>
          )}
        </Space>
      </div>
    </div>
  )
}

export default ManualBatchForm
