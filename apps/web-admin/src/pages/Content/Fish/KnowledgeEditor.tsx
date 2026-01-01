/**
 * 知识库编辑器组件
 *
 * 功能：
 * - 主题列表表格
 * - 每行: 主题、内容预览、来源、标签
 * - 添加/编辑/删除模态框
 */

import React, { useState } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Space,
  Popconfirm,
  Tag,
  Tooltip,
  message,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, LinkOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { FishKnowledge, FishKnowledgeCreate, FishKnowledgeUpdate } from '@/types/fish'

interface KnowledgeEditorProps {
  knowledge: FishKnowledge[]
  loading?: boolean
  onAdd: (data: FishKnowledgeCreate) => Promise<void>
  onUpdate: (id: number, data: FishKnowledgeUpdate) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

const KnowledgeEditor: React.FC<KnowledgeEditorProps> = ({
  knowledge,
  loading = false,
  onAdd,
  onUpdate,
  onDelete,
}) => {
  const [modalOpen, setModalOpen] = useState(false)
  const [editingKnowledge, setEditingKnowledge] = useState<FishKnowledge | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  // 打开新增弹窗
  const handleAdd = () => {
    setEditingKnowledge(null)
    form.resetFields()
    setModalOpen(true)
  }

  // 打开编辑弹窗
  const handleEdit = (item: FishKnowledge) => {
    setEditingKnowledge(item)
    form.setFieldsValue({
      topic: item.topic,
      content: item.content,
      source: item.source,
      tags: item.tags,
    })
    setModalOpen(true)
  }

  // 删除
  const handleDelete = async (id: number) => {
    try {
      await onDelete(id)
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  // 保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)

      if (editingKnowledge) {
        await onUpdate(editingKnowledge.id, values as FishKnowledgeUpdate)
        message.success('更新成功')
      } else {
        await onAdd(values as FishKnowledgeCreate)
        message.success('添加成功')
      }

      setModalOpen(false)
    } catch (error) {
      if (error && typeof error === 'object' && 'errorFields' in error) {
        return
      }
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<FishKnowledge> = [
    {
      title: '主题',
      dataIndex: 'topic',
      key: 'topic',
      width: 150,
      render: (topic) => (
        <span style={{ fontWeight: 500 }}>{topic}</span>
      ),
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (content) => (
        <Tooltip title={content} placement="topLeft">
          <span style={{ color: '#666' }}>{content}</span>
        </Tooltip>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 120,
      render: (source) =>
        source ? (
          <Tooltip title={source}>
            <Tag icon={<LinkOutlined />} style={{ borderRadius: 8, border: 'none', background: '#f0f0f0' }}>
              {source.length > 10 ? source.slice(0, 10) + '...' : source}
            </Tag>
          </Tooltip>
        ) : (
          '-'
        ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 150,
      render: (tags: string | undefined) => {
        if (!tags) return '-'
        const tagList = tags.split(',').filter(Boolean)
        return (
          <Space size={4} wrap>
            {tagList.slice(0, 3).map((tag, index) => (
              <Tag
                key={index}
                style={{
                  borderRadius: 6,
                  border: 'none',
                  background: '#e6f7ff',
                  color: '#1890ff',
                  fontSize: 12,
                }}
              >
                {tag.trim()}
              </Tag>
            ))}
            {tagList.length > 3 && (
              <Tag style={{ borderRadius: 6, border: 'none', background: '#f0f0f0', fontSize: 12 }}>
                +{tagList.length - 3}
              </Tag>
            )}
          </Space>
        )
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size={0}>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="确定删除此知识条目？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#666', fontSize: 14 }}>
          管理鱼种相关的知识条目，如习性、分布、繁殖等
        </span>
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleAdd}>
          添加知识
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={knowledge}
        rowKey="id"
        loading={loading}
        pagination={knowledge.length > 5 ? { pageSize: 5 } : false}
        size="small"
        style={{ marginBottom: 16 }}
      />

      {/* 编辑弹窗 */}
      <Modal
        title={editingKnowledge ? '编辑知识条目' : '添加知识条目'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        confirmLoading={saving}
        destroyOnClose
        width={600}
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="topic"
            label="主题"
            rules={[
              { required: true, message: '请输入主题' },
              { max: 100, message: '主题不能超过100个字符' },
            ]}
          >
            <Input placeholder="如：生活习性、繁殖特点、分布区域" />
          </Form.Item>

          <Form.Item
            name="content"
            label="内容"
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <Input.TextArea rows={4} placeholder="详细描述该主题的相关知识" />
          </Form.Item>

          <Form.Item name="source" label="来源">
            <Input placeholder="如：百度百科、《中国淡水鱼图鉴》" />
          </Form.Item>

          <Form.Item name="tags" label="标签">
            <Input placeholder="标签，用逗号分隔，如：习性,生态,繁殖" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KnowledgeEditor
