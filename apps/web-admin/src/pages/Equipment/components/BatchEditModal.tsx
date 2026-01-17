import { useState, useEffect } from 'react'
import { Modal, Form, Select, Switch, Space, Alert, Typography } from 'antd'
import type { Brand } from '@/types/equipment'

const { Text } = Typography

interface BatchEditModalProps {
  open: boolean
  selectedCount: number
  brands: Brand[]
  loading: boolean
  onOk: (updates: { brand_id?: number; user_level?: string; is_active?: boolean }) => void
  onCancel: () => void
}

const USER_LEVELS = [
  { value: '入门', label: '入门' },
  { value: '新手', label: '新手' },
  { value: '进阶', label: '进阶' },
  { value: '高手', label: '高手' },
]

const BatchEditModal = ({
  open,
  selectedCount,
  brands,
  loading,
  onOk,
  onCancel,
}: BatchEditModalProps) => {
  const [form] = Form.useForm()
  const [editFields, setEditFields] = useState<string[]>([])

  useEffect(() => {
    if (open) {
      form.resetFields()
      setEditFields([])
    }
  }, [open, form])

  const handleOk = () => {
    form.validateFields().then((values) => {
      const updates: { brand_id?: number; user_level?: string; is_active?: boolean } = {}

      if (editFields.includes('brand_id') && values.brand_id !== undefined) {
        updates.brand_id = values.brand_id
      }
      if (editFields.includes('user_level') && values.user_level !== undefined) {
        updates.user_level = values.user_level
      }
      if (editFields.includes('is_active') && values.is_active !== undefined) {
        updates.is_active = values.is_active
      }

      if (Object.keys(updates).length === 0) {
        return
      }

      onOk(updates)
    })
  }

  const fieldOptions = [
    { value: 'brand_id', label: '品牌' },
    { value: 'user_level', label: '适用水平' },
    { value: 'is_active', label: '启用状态' },
  ]

  return (
    <Modal
      title="批量编辑"
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      okText="确认更新"
      cancelText="取消"
      confirmLoading={loading}
      okButtonProps={{ disabled: editFields.length === 0 }}
    >
      <Alert
        message={`已选择 ${selectedCount} 个装备`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Form form={form} layout="vertical">
        <Form.Item label="选择要修改的字段" required>
          <Select
            mode="multiple"
            placeholder="请选择要修改的字段"
            options={fieldOptions}
            value={editFields}
            onChange={setEditFields}
            style={{ width: '100%' }}
          />
        </Form.Item>

        {editFields.includes('brand_id') && (
          <Form.Item
            name="brand_id"
            label="品牌"
            rules={[{ required: true, message: '请选择品牌' }]}
          >
            <Select
              placeholder="选择品牌"
              showSearch
              optionFilterProp="label"
              options={brands.map((b) => ({
                value: b.brand_id,
                label: b.name_cn,
              }))}
            />
          </Form.Item>
        )}

        {editFields.includes('user_level') && (
          <Form.Item
            name="user_level"
            label="适用水平"
            rules={[{ required: true, message: '请选择适用水平' }]}
          >
            <Select placeholder="选择适用水平" options={USER_LEVELS} />
          </Form.Item>
        )}

        {editFields.includes('is_active') && (
          <Form.Item
            name="is_active"
            label="启用状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        )}

        {editFields.length > 0 && (
          <Alert
            message="更新预览"
            description={
              <Space direction="vertical" size={4}>
                {editFields.includes('brand_id') && (
                  <Text>
                    品牌:{' '}
                    {form.getFieldValue('brand_id')
                      ? brands.find((b) => b.brand_id === form.getFieldValue('brand_id'))?.name_cn
                      : '未选择'}
                  </Text>
                )}
                {editFields.includes('user_level') && (
                  <Text>适用水平: {form.getFieldValue('user_level') || '未选择'}</Text>
                )}
                {editFields.includes('is_active') && (
                  <Text>状态: {form.getFieldValue('is_active') ? '启用' : '禁用'}</Text>
                )}
              </Space>
            }
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Form>
    </Modal>
  )
}

export default BatchEditModal
