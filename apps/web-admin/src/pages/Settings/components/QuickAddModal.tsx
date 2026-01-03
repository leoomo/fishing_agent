import { Modal, Form, Input, Alert, Typography } from 'antd'
import { useState, useEffect } from 'react'
import type { APIProvider } from '../constants'

const { Text, Link } = Typography

interface QuickAddModalProps {
  visible: boolean
  provider: APIProvider | null
  currentValue?: string
  onCancel: () => void
  onSave: (key: string, value: string) => Promise<void>
}

const QuickAddModal: React.FC<QuickAddModalProps> = ({
  visible,
  provider,
  currentValue,
  onCancel,
  onSave,
}) => {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (visible && provider) {
      form.setFieldsValue({
        apiKey: currentValue || '',
      })
    }
  }, [visible, provider, currentValue, form])

  const handleOk = async () => {
    if (!provider) return

    try {
      const values = await form.validateFields()
      setSaving(true)
      await onSave(provider.configKey, values.apiKey)
      form.resetFields()
      onCancel()
    } catch {
      // Validation failed
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onCancel()
  }

  if (!provider) return null

  const isEdit = !!currentValue

  return (
    <Modal
      title={
        <span>
          <span style={{ fontSize: 20, marginRight: 8 }}>{provider.icon}</span>
          {isEdit ? '编辑' : '配置'} {provider.name}
        </span>
      }
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={saving}
      okText={isEdit ? '保存' : '添加'}
      cancelText="取消"
      width={500}
      destroyOnClose
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message={provider.description}
        description={
          <Text type="secondary">
            获取密钥：
            <Link href={provider.docUrl} target="_blank">
              查看官方文档
            </Link>
          </Text>
        }
      />

      <Form form={form} layout="vertical">
        <Form.Item
          name="apiKey"
          label="API 密钥"
          rules={[
            { required: true, message: '请输入 API 密钥' },
            {
              min: 10,
              message: 'API 密钥长度不能少于 10 个字符',
            },
          ]}
          extra={
            provider.placeholder && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                格式示例：{provider.placeholder}
              </Text>
            )
          }
        >
          <Input.Password
            placeholder={provider.placeholder || '请输入 API 密钥'}
            autoComplete="off"
          />
        </Form.Item>
      </Form>

      {isEdit && (
        <Alert
          type="warning"
          showIcon
          message="修改密钥后建议重新测试连接"
          style={{ marginTop: 16 }}
        />
      )}
    </Modal>
  )
}

export default QuickAddModal
