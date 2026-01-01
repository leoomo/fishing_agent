/**
 * Spec Editor - Manage rig specifications (key-value pairs)
 */

import { useState } from 'react'
import {
  Table,
  Button,
  Space,
  Input,
  Popconfirm,
  Empty,
  message,
  Form,
  Modal,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons'
import type { RigSpec, RigSpecCreate, RigSpecUpdate } from '@/types/rig'
import type { ColumnsType } from 'antd/es/table'

interface SpecEditorProps {
  specs: RigSpec[]
  loading?: boolean
  onAdd: (data: RigSpecCreate) => Promise<void>
  onUpdate: (specId: number, data: RigSpecUpdate) => Promise<void>
  onDelete: (specId: number) => Promise<void>
}

const SpecEditor: React.FC<SpecEditorProps> = ({
  specs,
  loading,
  onAdd,
  onUpdate,
  onDelete,
}) => {
  const [modalVisible, setModalVisible] = useState(false)
  const [editingSpec, setEditingSpec] = useState<RigSpec | null>(null)
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)

  const handleOpenModal = (spec?: RigSpec) => {
    if (spec) {
      setEditingSpec(spec)
      form.setFieldsValue({
        spec_name: spec.spec_name,
        spec_value: spec.spec_value,
        unit: spec.unit,
        notes: spec.notes,
      })
    } else {
      setEditingSpec(null)
      form.resetFields()
    }
    setModalVisible(true)
  }

  const handleCloseModal = () => {
    setModalVisible(false)
    setEditingSpec(null)
    form.resetFields()
  }

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)

      if (editingSpec) {
        await onUpdate(editingSpec.spec_id, values)
        message.success('规格已更新')
      } else {
        await onAdd(values)
        message.success('规格已添加')
      }
      handleCloseModal()
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) {
        // Form validation error, ignore
        return
      }
      message.error('操作失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (specId: number) => {
    try {
      await onDelete(specId)
      message.success('规格已删除')
    } catch {
      message.error('删除失败')
    }
  }

  const columns: ColumnsType<RigSpec> = [
    {
      title: '规格名称',
      dataIndex: 'spec_name',
      key: 'spec_name',
      width: 150,
    },
    {
      title: '规格值',
      dataIndex: 'spec_value',
      key: 'spec_value',
      width: 150,
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
      render: (unit) => unit || '-',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
      render: (notes) => notes || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size={0}>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          />
          <Popconfirm
            title="确定删除此规格？"
            onConfirm={() => handleDelete(record.spec_id)}
            okText="删除"
            cancelText="取消"
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* Add button */}
      <div style={{ marginBottom: 16 }}>
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={() => handleOpenModal()}
          block
        >
          添加规格
        </Button>
      </div>

      {/* Specs table */}
      {specs.length === 0 ? (
        <Empty
          description="暂无规格参数"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Table
          columns={columns}
          dataSource={specs}
          rowKey="spec_id"
          loading={loading}
          pagination={false}
          size="small"
          style={{
            borderRadius: 8,
            overflow: 'hidden',
          }}
        />
      )}

      {/* Edit Modal */}
      <Modal
        title={editingSpec ? '编辑规格' : '添加规格'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={handleCloseModal}
        confirmLoading={saving}
        okText="保存"
        cancelText="取消"
        width={480}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 24 }}
        >
          <Form.Item
            name="spec_name"
            label="规格名称"
            rules={[{ required: true, message: '请输入规格名称' }]}
          >
            <Input placeholder="如：主线线径、子线长度" />
          </Form.Item>

          <Space style={{ width: '100%' }} size={16}>
            <Form.Item
              name="spec_value"
              label="规格值"
              rules={[{ required: true, message: '请输入规格值' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="如：1.5、30-50" />
            </Form.Item>

            <Form.Item
              name="unit"
              label="单位"
              style={{ width: 100 }}
            >
              <Input placeholder="如：号、cm" />
            </Form.Item>
          </Space>

          <Form.Item
            name="notes"
            label="备注"
          >
            <Input.TextArea
              placeholder="补充说明（可选）"
              rows={2}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SpecEditor
