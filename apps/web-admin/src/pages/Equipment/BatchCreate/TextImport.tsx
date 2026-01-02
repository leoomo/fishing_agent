/**
 * 文本导入表单
 *
 * 从粘贴的规格表文本解析装备信息
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
  message,
  Card,
  Typography,
  Switch,
  Alert,
} from 'antd'
import { CopyOutlined } from '@ant-design/icons'
import { equipmentApi, type Brand, type TextParseResponse } from '@/api/services/equipment'
import type { ColumnsType } from 'antd/es/table'

const { Option } = Select
const { TextArea } = Input
const { Text, Title } = Typography

interface TextImportFormProps {
  brands: Brand[]
  onSubmit: (
    category: string,
    template: Record<string, unknown>,
    variants: Record<string, unknown>[],
    skipDuplicates: boolean
  ) => Promise<void>
  loading: boolean
}

const CATEGORIES = [
  { value: '鱼竿', label: '鱼竿' },
  { value: '渔轮', label: '渔轮' },
  { value: '鱼线', label: '鱼线' },
  { value: '拟饵', label: '拟饵' },
]

const USER_LEVEL_OPTIONS = ['新手', '进阶', '高手']

const TextImportForm: React.FC<TextImportFormProps> = ({
  brands,
  onSubmit,
  loading,
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [category, setCategory] = useState<string>('鱼竿')
  const [text, setText] = useState('')
  const [parsing, setParsing] = useState(false)
  const [parseResult, setParseResult] = useState<TextParseResponse | null>(null)
  const [templateForm] = Form.useForm()
  const [variants, setVariants] = useState<Record<string, unknown>[]>([])
  const [skipDuplicates, setSkipDuplicates] = useState(true)

  // 解析文本
  const handleParse = async () => {
    if (!text.trim()) {
      message.warning('请粘贴规格表文本')
      return
    }

    setParsing(true)
    try {
      const result = await equipmentApi.parseText({
        text,
        category,
      })
      setParseResult(result)

      if (result.success) {
        // 设置模板默认值
        if (result.template) {
          templateForm.setFieldsValue(result.template)
        }
        // 添加 key 到变体
        setVariants(
          result.variants.map((v, idx) => ({
            ...v,
            key: `row_${idx}`,
          }))
        )
        message.success(`成功解析 ${result.row_count} 行数据`)
        setCurrentStep(1)
      } else {
        message.error('解析失败: ' + (result.warnings[0] || '未知错误'))
      }
    } catch (error) {
      console.error('解析失败:', error)
      message.error('解析失败')
    } finally {
      setParsing(false)
    }
  }

  // 更新变体行
  const handleUpdateVariant = (
    index: number,
    field: string,
    value: unknown
  ) => {
    const newVariants = [...variants]
    newVariants[index] = { ...newVariants[index], [field]: value }
    setVariants(newVariants)
  }

  // 删除变体行
  const handleDeleteVariant = (index: number) => {
    setVariants(variants.filter((_, i) => i !== index))
  }

  // 下一步
  const handleNext = async () => {
    if (currentStep === 1) {
      try {
        await templateForm.validateFields()
        setCurrentStep(2)
      } catch {
        message.warning('请完成必填字段')
      }
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

  // 变体表格列定义（鱼竿）
  const rodVariantColumns: ColumnsType<Record<string, unknown>> = [
    {
      title: '型号',
      dataIndex: 'model',
      width: 100,
      render: (value, _, index) => (
        <Input
          value={value as string}
          onChange={(e) => handleUpdateVariant(index, 'model', e.target.value)}
          size="small"
        />
      ),
    },
    {
      title: '长度(米)',
      dataIndex: 'length',
      width: 80,
      render: (value, _, index) => (
        <InputNumber
          value={value as number}
          onChange={(v) => handleUpdateVariant(index, 'length', v)}
          min={0.5}
          max={10}
          size="small"
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: '调性',
      dataIndex: 'power',
      width: 70,
      render: (value, _, index) => (
        <Select
          value={value as string}
          onChange={(v) => handleUpdateVariant(index, 'power', v)}
          size="small"
          style={{ width: '100%' }}
        >
          {['UL', 'L', 'ML', 'M', 'MH', 'H', 'XH'].map((p) => (
            <Option key={p} value={p}>
              {p}
            </Option>
          ))}
        </Select>
      ),
    },
    {
      title: '自重(g)',
      dataIndex: 'weight',
      width: 80,
      render: (value, _, index) => (
        <InputNumber
          value={value as number}
          onChange={(v) => handleUpdateVariant(index, 'weight', v)}
          min={0}
          size="small"
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: '操作',
      width: 60,
      render: (_, __, index) => (
        <Button
          type="text"
          danger
          size="small"
          onClick={() => handleDeleteVariant(index)}
        >
          删除
        </Button>
      ),
    },
  ]

  // 示例文本
  const exampleText = `型号	长度	调性	自重
264MH	2.64m	MH	105g
702M	2.13m	M	95g
701MH	2.13m	MH	100g`

  // 渲染步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Text>装备类别：</Text>
                <Select
                  value={category}
                  onChange={setCategory}
                  style={{ width: '100%', marginTop: 8 }}
                >
                  {CATEGORIES.map((c) => (
                    <Option key={c.value} value={c.value}>
                      {c.label}
                    </Option>
                  ))}
                </Select>
              </Col>
            </Row>

            <Alert
              message="支持的格式"
              description={
                <div>
                  <p style={{ margin: 0 }}>
                    支持 Tab 分隔、空格分隔、逗号分隔、Markdown 表格等格式。
                    系统会自动识别表头并映射到标准字段。
                  </p>
                </div>
              }
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Card
              title="示例文本"
              size="small"
              style={{ marginBottom: 16 }}
              extra={
                <Button
                  type="link"
                  icon={<CopyOutlined />}
                  onClick={() => {
                    setText(exampleText)
                    message.success('已填入示例')
                  }}
                >
                  使用示例
                </Button>
              }
            >
              <pre style={{ margin: 0, fontSize: 12 }}>{exampleText}</pre>
            </Card>

            <Form.Item label="规格表文本">
              <TextArea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={10}
                placeholder="粘贴规格表文本..."
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <div style={{ textAlign: 'center' }}>
              <Button type="primary" onClick={handleParse} loading={parsing}>
                解析文本
              </Button>
            </div>

            {parseResult && !parseResult.success && (
              <Alert
                message="解析失败"
                description={parseResult.warnings.join('; ')}
                type="error"
                style={{ marginTop: 16 }}
              />
            )}
          </div>
        )

      case 1:
        return (
          <div>
            {parseResult?.warnings && parseResult.warnings.length > 0 && (
              <Alert
                message="提示"
                description={parseResult.warnings.join('; ')}
                type="warning"
                style={{ marginBottom: 16 }}
              />
            )}

            <Title level={5}>补充共享信息</Title>
            <Form
              form={templateForm}
              layout="vertical"
              initialValues={{
                user_level: '进阶',
              }}
            >
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="brand_id"
                    label="品牌"
                    rules={[{ required: true, message: '请选择品牌' }]}
                  >
                    <Select
                      placeholder="选择品牌"
                      showSearch
                      optionFilterProp="children"
                    >
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

              <Row gutter={16}>
                <Col span={6}>
                  <Form.Item name="price_min" label="默认最低价">
                    <InputNumber min={0} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item name="price_max" label="默认最高价">
                    <InputNumber min={0} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>

            <Divider />

            <Title level={5}>
              解析结果 ({variants.length} 个型号)
              <Text type="secondary" style={{ fontSize: 12, marginLeft: 16 }}>
                原始表头: {parseResult?.raw_headers.join(', ')}
              </Text>
            </Title>

            <Table
              columns={rodVariantColumns}
              dataSource={variants}
              pagination={false}
              size="small"
              scroll={{ x: 'max-content' }}
              rowKey={(_, index) => `row_${index}`}
            />
          </div>
        )

      case 2:
        const template = templateForm.getFieldsValue()
        const selectedBrand = brands.find((b) => b.brand_id === template.brand_id)

        return (
          <div>
            <Card title="共享信息" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Text type="secondary">品牌：</Text>
                  <Text strong>{selectedBrand?.name_cn || '-'}</Text>
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
                    render: (_, record) =>
                      `${selectedBrand?.name_cn || ''} ${template.product_line || ''} ${record.model}`,
                  },
                  {
                    title: '长度',
                    dataIndex: 'length',
                    render: (v) => (v ? `${v}m` : '-'),
                  },
                  { title: '调性', dataIndex: 'power' },
                  {
                    title: '自重',
                    dataIndex: 'weight',
                    render: (v) => (v ? `${v}g` : '-'),
                  },
                ]}
                dataSource={variants}
                pagination={false}
                size="small"
                rowKey={(_, index) => `row_${index}`}
              />
            </Card>

            <Card size="small">
              <Space>
                <Text>跳过重复装备（同品牌同型号）：</Text>
                <Switch checked={skipDuplicates} onChange={setSkipDuplicates} />
              </Space>
            </Card>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div>
      <Steps
        current={currentStep}
        items={[
          { title: '粘贴文本' },
          { title: '补充信息' },
          { title: '预览确认' },
        ]}
        style={{ marginBottom: 24 }}
      />

      <div style={{ minHeight: 300 }}>{renderStepContent()}</div>

      <Divider />

      <div style={{ textAlign: 'right' }}>
        <Space>
          {currentStep > 0 && <Button onClick={handlePrev}>上一步</Button>}
          {currentStep === 1 && (
            <Button type="primary" onClick={handleNext}>
              下一步
            </Button>
          )}
          {currentStep === 2 && (
            <Button type="primary" onClick={handleSubmit} loading={loading}>
              确认创建 ({variants.length} 个装备)
            </Button>
          )}
        </Space>
      </div>
    </div>
  )
}

export default TextImportForm
