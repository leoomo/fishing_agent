/**
 * 配件编辑抽屉组件
 *
 * 功能：
 * - 创建/编辑钓鱼配件
 * - 表单验证
 * - 乔布斯简洁风格
 */

import React, { useEffect, useState } from 'react'
import {
  Drawer,
  Form,
  Input,
  Select,
  InputNumber,
  Button,
  message,
  Space,
  Divider,
  Row,
  Col,
} from 'antd'
import { SaveOutlined, CloseOutlined } from '@ant-design/icons'
import { accessoryApi } from '@/api/services/accessory'
import {
  ACCESSORY_CATEGORY_OPTIONS,
  USER_LEVEL_OPTIONS,
  type Accessory,
  type AccessoryCreateRequest,
  type AccessoryUpdateRequest,
} from '@/types/accessory'

interface AccessoryDrawerProps {
  open: boolean
  accessoryId?: number | null
  onClose: () => void
  onSuccess: () => void
}

// 常用材质选项
const COMMON_MATERIALS = [
  '碳钢',
  '不锈钢',
  '钨合金',
  '铅',
  '尼龙',
  '碳素',
  '氟碳',
  '钛合金',
  '黄铜',
  'PE材质',
]

const AccessoryDrawer: React.FC<AccessoryDrawerProps> = ({
  open,
  accessoryId,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const isEdit = !!accessoryId

  // 加载配件数据
  useEffect(() => {
    if (open && accessoryId) {
      setLoading(true)
      accessoryApi
        .get(accessoryId)
        .then((data) => {
          form.setFieldsValue(data)
        })
        .catch((err) => {
          message.error('加载配件数据失败')
          console.error(err)
        })
        .finally(() => {
          setLoading(false)
        })
    } else if (open) {
      form.resetFields()
    }
  }, [open, accessoryId, form])

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)

      if (isEdit && accessoryId) {
        await accessoryApi.update(accessoryId, values as AccessoryUpdateRequest)
        message.success('更新成功')
      } else {
        await accessoryApi.create(values as AccessoryCreateRequest)
        message.success('创建成功')
      }

      onSuccess()
      onClose()
    } catch (err: any) {
      if (err.errorFields) {
        // 表单验证错误
        return
      }
      message.error(err.message || '保存失败')
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Drawer
      title={isEdit ? '编辑配件' : '新建配件'}
      width={600}
      open={open}
      onClose={onClose}
      destroyOnClose
      extra={
        <Space>
          <Button icon={<CloseOutlined />} onClick={onClose}>
            取消
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            onClick={handleSubmit}
          >
            {isEdit ? '保存修改' : '创建'}
          </Button>
        </Space>
      }
    >
      <Form
        form={form}
        layout="vertical"
        disabled={loading}
        initialValues={{
          category: 'hook',
          user_level: 'beginner',
        }}
      >
        {/* 基本信息 */}
        <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>
          基本信息
        </div>

        <Form.Item
          name="name"
          label="配件名称"
          rules={[
            { required: true, message: '请输入配件名称' },
            { max: 100, message: '名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="如：曲柄钩、子弹铅、八字环" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="category"
              label="分类"
              rules={[{ required: true, message: '请选择分类' }]}
            >
              <Select
                placeholder="选择分类"
                options={ACCESSORY_CATEGORY_OPTIONS}
                optionFilterProp="label"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="user_level" label="适用级别">
              <Select
                placeholder="选择用户等级"
                options={USER_LEVEL_OPTIONS}
                optionFilterProp="label"
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="description" label="详细描述">
          <Input.TextArea rows={2} placeholder="描述配件的用途和特点" />
        </Form.Item>

        <Form.Item name="features" label="主要特点">
          <Input placeholder="如：防挂底、软饵专用、多种号数" />
        </Form.Item>

        <Divider style={{ margin: '16px 0' }} />

        {/* 规格参数 */}
        <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>
          规格参数
        </div>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="size" label="规格尺寸">
              <Input placeholder="如：#1/0 - #5/0" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="weight" label="重量 (克)">
              <InputNumber
                min={0}
                max={1000}
                step={0.1}
                precision={1}
                style={{ width: '100%' }}
                placeholder="如：7.0"
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="material" label="材质">
              <Select
                placeholder="选择材质"
                allowClear
                showSearch
                options={COMMON_MATERIALS.map((m) => ({ value: m, label: m }))}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="color" label="颜色/花纹">
              <Input placeholder="如：金色、银色、磨砂黑" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="quantity_per_pack" label="每包数量">
          <InputNumber min={1} max={1000} style={{ width: '100%' }} placeholder="如：10" />
        </Form.Item>

        <Divider style={{ margin: '16px 0' }} />

        {/* 应用场景 */}
        <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>
          应用场景
        </div>

        <Form.Item name="target_species" label="目标鱼种">
          <Input placeholder="如：黑鲈、鳜鱼、翘嘴" />
        </Form.Item>

        <Form.Item name="applicable_rigs" label="适用钓组">
          <Input placeholder="如：Texas钓组、Carolina钓组、Drop Shot" />
        </Form.Item>

        <Form.Item name="best_conditions" label="最佳使用条件">
          <Input.TextArea rows={2} placeholder="描述最适合使用此配件的场景" />
        </Form.Item>

        <Divider style={{ margin: '16px 0' }} />

        {/* 商业信息 */}
        <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>
          商业信息
        </div>

        <Form.Item name="brand" label="品牌">
          <Input placeholder="如：Gamakatsu、Owner" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="price_min" label="最低价格 (元)">
              <InputNumber
                min={0}
                max={10000}
                step={1}
                precision={0}
                style={{ width: '100%' }}
                placeholder="如：10"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="price_max" label="最高价格 (元)">
              <InputNumber
                min={0}
                max={10000}
                step={1}
                precision={0}
                style={{ width: '100%' }}
                placeholder="如：50"
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="image_url" label="图片URL">
          <Input placeholder="https://..." />
        </Form.Item>
      </Form>
    </Drawer>
  )
}

export default AccessoryDrawer
