/**
 * 装备添加/编辑表单
 *
 * 设计原则：乔布斯式简洁
 * - 无分割线，用留白代替
 * - 无冗余标题
 * - 渐进式展示
 * - 视觉层次清晰
 */

import { useEffect, useState } from 'react'
import { Form, Input, Select, InputNumber, Button, Card, message, Row, Col } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import type { Brand, Equipment } from '@/types/equipment'
import { EQUIPMENT_CATEGORIES, USER_LEVELS } from '@/types/equipment'
import SpecFormFields from './SpecFormFields'

const { TextArea } = Input

const EquipmentForm = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [brands, setBrands] = useState<Brand[]>([])
  const [category, setCategory] = useState<string>('')

  useEffect(() => {
    // 加载品牌列表
    equipmentApi
      .listBrands()
      .then(setBrands)
      .catch(() => {
        message.error('加载品牌列表失败')
      })

    // 编辑模式：加载装备详情
    if (id) {
      equipmentApi
        .get(Number(id))
        .then((data: Equipment) => {
          setCategory(data.category)
          form.setFieldsValue(data)
        })
        .catch(() => {
          message.error('加载装备详情失败')
        })
    }
  }, [id, form])

  const handleCategoryChange = (value: string) => {
    setCategory(value)
    // 清空规格字段
    form.setFieldsValue({ specs: {} })
  }

  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true)
    try {
      if (id) {
        await equipmentApi.update(Number(id), values)
        message.success('更新成功')
      } else {
        await equipmentApi.create(values as unknown as Parameters<typeof equipmentApi.create>[0])
        message.success('创建成功')
      }
      navigate('/equipment')
    } catch {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card
      title={id ? '编辑装备' : '新增装备'}
      bordered={false}
      style={{ maxWidth: 900, margin: '0 auto' }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{ user_level: '新手', is_active: true }}
        requiredMark={false}
      >
        {/* 第一行：名称、类别、品牌 */}
        <Row gutter={16}>
          <Col span={10}>
            <Form.Item
              label="装备名称"
              name="name"
              rules={[{ required: true, message: '请输入装备名称' }]}
            >
              <Input placeholder="装备名称" />
            </Form.Item>
          </Col>
          <Col span={7}>
            <Form.Item
              label="类别"
              name="category"
              rules={[{ required: true, message: '请选择类别' }]}
            >
              <Select
                placeholder="选择类别"
                onChange={handleCategoryChange}
                options={EQUIPMENT_CATEGORIES.filter((c) => c !== '套装').map((c) => ({
                  label: c,
                  value: c,
                }))}
              />
            </Form.Item>
          </Col>
          <Col span={7}>
            <Form.Item
              label="品牌"
              name="brand_id"
              rules={[{ required: true, message: '请选择品牌' }]}
            >
              <Select
                placeholder="选择品牌"
                showSearch
                optionFilterProp="label"
                options={brands.map((brand) => ({
                  label: brand.name_cn,
                  value: brand.brand_id,
                }))}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 第二行：型号、价格范围、适用水平 */}
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item label="型号" name="model">
              <Input placeholder="型号" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="价格范围">
              <Input.Group compact>
                <Form.Item name="price_min" noStyle>
                  <InputNumber
                    placeholder="最低"
                    min={0}
                    style={{ width: '45%' }}
                    addonBefore="¥"
                  />
                </Form.Item>
                <Input
                  style={{
                    width: '10%',
                    textAlign: 'center',
                    borderLeft: 0,
                    borderRight: 0,
                    pointerEvents: 'none',
                    backgroundColor: '#fafafa',
                  }}
                  placeholder="~"
                  disabled
                />
                <Form.Item name="price_max" noStyle>
                  <InputNumber placeholder="最高" min={0} style={{ width: '45%' }} />
                </Form.Item>
              </Input.Group>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="适用水平" name="user_level">
              <Select
                options={USER_LEVELS.map((level) => ({
                  label: level,
                  value: level,
                }))}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 规格参数（根据类别动态显示） */}
        {category && <SpecFormFields category={category} />}

        {/* 描述信息 */}
        <div style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="描述" name="description">
                <TextArea rows={3} placeholder="装备描述..." />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="特点" name="features">
                <TextArea rows={3} placeholder="装备特点（每行一条）..." />
              </Form.Item>
            </Col>
          </Row>
        </div>

        {/* 操作按钮 */}
        <div style={{ marginTop: 32, textAlign: 'right' }}>
          <Button onClick={() => navigate('/equipment')} style={{ marginRight: 12 }}>
            取消
          </Button>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存
          </Button>
        </div>
      </Form>
    </Card>
  )
}

export default EquipmentForm
