/**
 * 钓组详情查看弹窗
 *
 * 功能：
 * - 只读展示钓组完整信息
 * - 基本信息（名称、分类、难度、描述等）
 * - 组件列表（折叠面板）
 * - 规格参数（折叠面板）
 * - 可切换到编辑模式
 */

import { useState, useEffect } from 'react'
import {
  Modal,
  Spin,
  Typography,
  Tag,
  Descriptions,
  Collapse,
  Space,
  Empty,
  Button,
  Image,
  Divider,
  Table,
} from 'antd'
import { EditOutlined } from '@ant-design/icons'
import { rigApi } from '@/api/services/rig'
import type { Rig, RigComponent, RigSpec } from '@/types/rig'
import {
  RIG_CATEGORY_CONFIG,
  RIG_DIFFICULTY_CONFIG,
  getComponentTypeConfig,
} from '@/types/rig'

const { Title, Text, Paragraph } = Typography

interface RigDetailModalProps {
  open: boolean
  rigId: number | null
  onClose: () => void
  onEdit: () => void
}

// 解析并格式化目标鱼种
const formatTargetSpecies = (species: string | undefined): React.ReactNode => {
  if (!species) return null
  try {
    const arr = JSON.parse(species)
    if (Array.isArray(arr) && arr.length > 0) {
      return (
        <Space size={4} wrap>
          {arr.map((s, i) => (
            <Tag
              key={i}
              style={{
                borderRadius: 4,
                margin: 0,
                fontSize: 12,
                background: '#f5f5f5',
                border: 'none',
                color: '#666',
              }}
            >
              {s}
            </Tag>
          ))}
        </Space>
      )
    }
  } catch {
    // 如果不是 JSON，直接显示
    return <Text>{species}</Text>
  }
  return null
}

const RigDetailModal: React.FC<RigDetailModalProps> = ({
  open,
  rigId,
  onClose,
  onEdit,
}) => {
  const [loading, setLoading] = useState(false)
  const [rig, setRig] = useState<Rig | null>(null)

  useEffect(() => {
    if (open && rigId) {
      loadRigDetail(rigId)
    }
    if (!open) {
      setRig(null)
    }
  }, [open, rigId])

  const loadRigDetail = async (id: number) => {
    setLoading(true)
    try {
      const data = await rigApi.get(id)
      setRig(data)
    } catch {
      setRig(null)
    } finally {
      setLoading(false)
    }
  }

  // 组件列表列配置
  const componentColumns = [
    {
      title: '组件名称',
      dataIndex: 'component_name',
      key: 'component_name',
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: '类型',
      dataIndex: 'component_type',
      key: 'component_type',
      width: 100,
      render: (type: string) => {
        const config = getComponentTypeConfig(type)
        return (
          <Tag
            style={{
              borderRadius: 8,
              border: 'none',
              background: '#f5f5f5',
            }}
          >
            {config.icon} {config.label}
          </Tag>
        )
      },
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 60,
      align: 'center' as const,
    },
    {
      title: '尺寸',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size: string) => size || '-',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
      render: (notes: string) => notes || '-',
    },
  ]

  // 规格列表列配置
  const specColumns = [
    {
      title: '规格名称',
      dataIndex: 'spec_name',
      key: 'spec_name',
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: '规格值',
      dataIndex: 'spec_value',
      key: 'spec_value',
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
      render: (unit: string) => unit || '-',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
      render: (notes: string) => notes || '-',
    },
  ]

  // 构建折叠面板项
  const collapseItems = []

  if (rig?.components && rig.components.length > 0) {
    collapseItems.push({
      key: 'components',
      label: (
        <Space>
          <span>组件列表</span>
          <Tag
            style={{
              borderRadius: 8,
              background: '#e6f7ff',
              color: '#1890ff',
              border: 'none',
            }}
          >
            {rig.components.length} 个
          </Tag>
        </Space>
      ),
      children: (
        <Table<RigComponent>
          columns={componentColumns}
          dataSource={rig.components}
          rowKey="component_id"
          size="small"
          pagination={false}
        />
      ),
    })
  }

  if (rig?.specs && rig.specs.length > 0) {
    collapseItems.push({
      key: 'specs',
      label: (
        <Space>
          <span>规格参数</span>
          <Tag
            style={{
              borderRadius: 8,
              background: '#f6ffed',
              color: '#52c41a',
              border: 'none',
            }}
          >
            {rig.specs.length} 项
          </Tag>
        </Space>
      ),
      children: (
        <Table<RigSpec>
          columns={specColumns}
          dataSource={rig.specs}
          rowKey="spec_id"
          size="small"
          pagination={false}
        />
      ),
    })
  }

  const categoryConfig = rig ? RIG_CATEGORY_CONFIG[rig.category] : null
  const difficultyConfig = rig ? RIG_DIFFICULTY_CONFIG[rig.difficulty] : null

  return (
    <Modal
      title={null}
      open={open}
      onCancel={onClose}
      width={720}
      footer={[
        <Button key="edit" type="primary" icon={<EditOutlined />} onClick={onEdit}>
          编辑
        </Button>,
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
      styles={{
        body: { padding: '24px', maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' },
      }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin size="large" />
        </div>
      ) : rig ? (
        <>
          {/* 头部：图片 + 基本信息 */}
          <div style={{ display: 'flex', gap: 24, marginBottom: 24 }}>
            <Image
              src={rig.diagram_url}
              alt={rig.name}
              width={160}
              height={120}
              style={{ borderRadius: 12, objectFit: 'cover', background: '#f5f7fa' }}
              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTYwIiBoZWlnaHQ9IjEyMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjgwIiB5PSI2MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSIjYmZiZmJmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7wn46jPC90ZXh0Pjwvc3ZnPg=="
              preview={!!rig.diagram_url}
            />
            <div style={{ flex: 1 }}>
              <Title level={3} style={{ margin: 0 }}>
                {rig.name}
              </Title>
              <Space style={{ marginTop: 12 }}>
                {categoryConfig && (
                  <Tag
                    color={categoryConfig.color}
                    style={{
                      borderRadius: 8,
                      border: 'none',
                    }}
                  >
                    {categoryConfig.icon} {categoryConfig.label}
                  </Tag>
                )}
                {difficultyConfig && (
                  <Tag
                    color={difficultyConfig.color}
                    style={{
                      borderRadius: 8,
                      border: 'none',
                    }}
                  >
                    {difficultyConfig.label}
                  </Tag>
                )}
              </Space>
            </div>
          </div>

          <Divider style={{ margin: '16px 0' }} />

          {/* 基本信息 */}
          <div style={{ marginBottom: 24 }}>
            <Text strong style={{ fontSize: 16, display: 'block', marginBottom: 12 }}>
              基本信息
            </Text>
            <Descriptions
              size="small"
              column={2}
              labelStyle={{ color: '#666', width: 80 }}
              contentStyle={{ fontWeight: 500 }}
            >
              <Descriptions.Item label="目标鱼种">
                {formatTargetSpecies(rig.target_species) || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="最佳条件">
                {rig.best_conditions || '-'}
              </Descriptions.Item>
            </Descriptions>
            {rig.description && (
              <Paragraph
                style={{
                  marginTop: 12,
                  padding: '12px 16px',
                  background: '#fafafa',
                  borderRadius: 8,
                  fontSize: 14,
                  color: '#333',
                }}
              >
                {rig.description}
              </Paragraph>
            )}
          </div>

          {/* 折叠面板：组件列表、规格参数 */}
          {collapseItems.length > 0 && (
            <Collapse
              items={collapseItems}
              defaultActiveKey={['components']}
              bordered={false}
              style={{ background: 'transparent' }}
              expandIconPosition="end"
            />
          )}

          {/* 空状态 */}
          {!rig.components?.length && !rig.specs?.length && !rig.description && (
            <Empty
              description="暂无更多信息"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 24 }}
            />
          )}
        </>
      ) : (
        <Empty description="未找到钓组信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Modal>
  )
}

export default RigDetailModal
