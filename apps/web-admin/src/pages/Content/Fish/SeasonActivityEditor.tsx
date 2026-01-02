/**
 * 季节活动编辑器组件
 *
 * 功能：
 * - 4季节表格（春/夏/秋/冬）
 * - 每行: 活跃度、最佳时间、推荐拟饵、钓鱼技巧
 * - 添加/编辑/删除操作
 */

import React, { useState } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Space,
  Popconfirm,
  Tag,
  message,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type {
  FishSeasonActivity,
  FishSeasonActivityCreate,
  FishSeasonActivityUpdate,
  Season,
  ActivityLevel,
} from '@/types/fish'
import { SEASON_CONFIG, SEASON_OPTIONS, ACTIVITY_LEVEL_CONFIG, ACTIVITY_LEVEL_OPTIONS } from '@/types/fish'

interface SeasonActivityEditorProps {
  activities: FishSeasonActivity[]
  loading?: boolean
  onAdd: (data: FishSeasonActivityCreate) => Promise<void>
  onUpdate: (id: number, data: FishSeasonActivityUpdate) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

const SeasonActivityEditor: React.FC<SeasonActivityEditorProps> = ({
  activities,
  loading = false,
  onAdd,
  onUpdate,
  onDelete,
}) => {
  const [modalOpen, setModalOpen] = useState(false)
  const [editingActivity, setEditingActivity] = useState<FishSeasonActivity | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  // 获取已使用的季节
  const usedSeasons = activities.map((a) => a.season)

  // 打开新增弹窗
  const handleAdd = () => {
    setEditingActivity(null)
    form.resetFields()
    form.setFieldsValue({
      activity_level: '中',
    })
    setModalOpen(true)
  }

  // 打开编辑弹窗
  const handleEdit = (activity: FishSeasonActivity) => {
    setEditingActivity(activity)
    form.setFieldsValue({
      season: activity.season,
      activity_level: activity.activity_level,
      best_time: activity.best_time,
      recommended_lures: activity.recommended_lures,
      fishing_tips: activity.fishing_tips,
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

      if (editingActivity) {
        await onUpdate(editingActivity.id, values as FishSeasonActivityUpdate)
        message.success('更新成功')
      } else {
        await onAdd(values as FishSeasonActivityCreate)
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

  // 可选季节（排除已使用的，编辑时保留当前季节）
  const availableSeasons = SEASON_OPTIONS.filter(
    (opt) => !usedSeasons.includes(opt.value) || editingActivity?.season === opt.value
  )

  const columns: ColumnsType<FishSeasonActivity> = [
    {
      title: '季节',
      dataIndex: 'season',
      key: 'season',
      width: 100,
      render: (season: Season) => {
        const config = SEASON_CONFIG[season]
        return (
          <Tag
            style={{
              borderRadius: 8,
              border: 'none',
              background: `${config.color}15`,
              color: config.color,
            }}
          >
            {config.icon} {config.label}
          </Tag>
        )
      },
    },
    {
      title: '活跃度',
      dataIndex: 'activity_level',
      key: 'activity_level',
      width: 80,
      render: (level: ActivityLevel) => {
        const config = ACTIVITY_LEVEL_CONFIG[level]
        return (
          <Tag
            style={{
              borderRadius: 8,
              border: 'none',
              background: `${config.color}15`,
              color: config.color,
            }}
          >
            {config.label}
          </Tag>
        )
      },
    },
    {
      title: '最佳时间',
      dataIndex: 'best_time',
      key: 'best_time',
      width: 120,
      render: (text) => text || '-',
    },
    {
      title: '推荐拟饵',
      dataIndex: 'recommended_lures',
      key: 'recommended_lures',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '钓鱼技巧',
      dataIndex: 'fishing_tips',
      key: 'fishing_tips',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size={0}>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="确定删除此季节活动？"
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
          管理不同季节的鱼类活跃情况和钓鱼建议
        </span>
        <Button
          type="primary"
          size="small"
          icon={<PlusOutlined />}
          onClick={handleAdd}
          disabled={usedSeasons.length >= 4}
        >
          添加季节
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={activities}
        rowKey="id"
        loading={loading}
        pagination={false}
        size="small"
        style={{ marginBottom: 16 }}
      />

      {/* 编辑弹窗 */}
      <Modal
        title={editingActivity ? '编辑季节活动' : '添加季节活动'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSave}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="season"
            label="季节"
            rules={[{ required: true, message: '请选择季节' }]}
          >
            <Select placeholder="选择季节" options={availableSeasons} />
          </Form.Item>

          <Form.Item
            name="activity_level"
            label="活跃度"
            rules={[{ required: true, message: '请选择活跃度' }]}
          >
            <Select placeholder="选择活跃度" options={ACTIVITY_LEVEL_OPTIONS} />
          </Form.Item>

          <Form.Item name="best_time" label="最佳钓鱼时间">
            <Input placeholder="如：早晨6-9点、傍晚4-7点" />
          </Form.Item>

          <Form.Item name="recommended_lures" label="推荐拟饵">
            <Input placeholder="如：软虫、米诺、VIB（逗号分隔）" />
          </Form.Item>

          <Form.Item name="fishing_tips" label="钓鱼技巧">
            <Input.TextArea rows={3} placeholder="描述该季节的钓鱼技巧和注意事项" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SeasonActivityEditor
