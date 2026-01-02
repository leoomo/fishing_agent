/**
 * 拟饵类型编辑抽屉组件
 *
 * 功能：
 * - 创建/编辑拟饵类型
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
} from 'antd'
import { SaveOutlined, CloseOutlined } from '@ant-design/icons'
import { lureTypeApi } from '@/api/services/lureType'
import {
  LURE_CATEGORY_OPTIONS,
  type LureType,
  type LureTypeCreateRequest,
  type LureTypeUpdateRequest,
} from '@/types/lureType'

interface LureTypeDrawerProps {
  open: boolean
  lureTypeId?: number | null
  onClose: () => void
  onSuccess: () => void
}

const LureTypeDrawer: React.FC<LureTypeDrawerProps> = ({
  open,
  lureTypeId,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const isEdit = !!lureTypeId

  // 加载拟饵类型数据
  useEffect(() => {
    if (open && lureTypeId) {
      setLoading(true)
      lureTypeApi
        .get(lureTypeId)
        .then((data) => {
          form.setFieldsValue(data)
        })
        .catch((err) => {
          message.error('加载拟饵类型失败')
          console.error(err)
        })
        .finally(() => {
          setLoading(false)
        })
    } else if (open) {
      form.resetFields()
    }
  }, [open, lureTypeId, form])

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)

      if (isEdit && lureTypeId) {
        await lureTypeApi.update(lureTypeId, values as LureTypeUpdateRequest)
        message.success('更新成功')
      } else {
        await lureTypeApi.create(values as LureTypeCreateRequest)
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
      title={isEdit ? '编辑拟饵类型' : '新建拟饵类型'}
      width={520}
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
          category: 'hard',
        }}
      >
        {/* 基本信息 */}
        <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>
          基本信息
        </div>

        <Form.Item
          name="name"
          label="拟饵名称"
          rules={[
            { required: true, message: '请输入拟饵名称' },
            { max: 100, message: '名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="如：米诺、卷尾蛆、亮片" />
        </Form.Item>

        <Space style={{ display: 'flex' }} size={16}>
          <Form.Item
            name="category"
            label="分类"
            rules={[{ required: true, message: '请选择分类' }]}
            style={{ flex: 1 }}
          >
            <Select
              placeholder="选择分类"
              options={LURE_CATEGORY_OPTIONS}
              optionFilterProp="label"
            />
          </Form.Item>

          <Form.Item
            name="target_species"
            label="目标鱼种"
            style={{ flex: 1 }}
          >
            <Input placeholder="如：黑鲈、鳜鱼、翘嘴" />
          </Form.Item>
        </Space>

        <Divider style={{ margin: '16px 0' }} />

        {/* 详细描述 */}
        <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>
          详细描述
        </div>

        <Form.Item name="description" label="拟饵描述">
          <Input.TextArea
            rows={3}
            placeholder="描述拟饵的特点和用途"
          />
        </Form.Item>

        <Form.Item name="action_description" label="动作描述">
          <Input.TextArea
            rows={2}
            placeholder="描述拟饵在水中的动作特点"
          />
        </Form.Item>

        <Form.Item name="best_conditions" label="最佳使用条件">
          <Input.TextArea
            rows={2}
            placeholder="描述最适合使用此拟饵的天气、水域、季节等"
          />
        </Form.Item>

        <Divider style={{ margin: '16px 0' }} />

        {/* 规格参数 */}
        <div style={{ marginBottom: 8, fontWeight: 600, color: '#666' }}>
          规格参数
        </div>

        <Space style={{ display: 'flex' }} size={16}>
          <Form.Item
            name="typical_weight_min"
            label="最小重量 (克)"
            style={{ flex: 1 }}
          >
            <InputNumber
              min={0}
              max={1000}
              step={0.1}
              precision={1}
              style={{ width: '100%' }}
              placeholder="如：5"
            />
          </Form.Item>

          <Form.Item
            name="typical_weight_max"
            label="最大重量 (克)"
            style={{ flex: 1 }}
          >
            <InputNumber
              min={0}
              max={1000}
              step={0.1}
              precision={1}
              style={{ width: '100%' }}
              placeholder="如：20"
            />
          </Form.Item>
        </Space>

        <Form.Item name="image_url" label="图片URL">
          <Input placeholder="https://..." />
        </Form.Item>
      </Form>
    </Drawer>
  )
}

export default LureTypeDrawer
