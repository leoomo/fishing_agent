/**
 * 配件详情查看弹窗
 *
 * 功能：
 * - 只读展示配件完整信息
 * - 基本信息（名称、分类、级别、描述等）
 * - 规格参数（尺寸、重量、材质等）
 * - 应用场景（目标鱼种、适用钓组等）
 * - 商业信息（品牌、价格等）
 * - 可切换到编辑模式
 */

import { useState, useEffect } from 'react'
import {
  Modal,
  Spin,
  Typography,
  Tag,
  Descriptions,
  Space,
  Empty,
  Button,
  Image,
  Divider,
} from 'antd'
import { EditOutlined } from '@ant-design/icons'
import { accessoryApi } from '@/api/services/accessory'
import type { Accessory, AccessoryCategory, UserLevel } from '@/types/accessory'
import { ACCESSORY_CATEGORY_CONFIG, USER_LEVEL_CONFIG } from '@/types/accessory'

const { Title, Text, Paragraph } = Typography

interface AccessoryDetailModalProps {
  open: boolean
  accessoryId: number | null
  onClose: () => void
  onEdit: () => void
}

// 格式化价格区间
const formatPriceRange = (min?: number, max?: number): string => {
  if (min && max) {
    return `${min} - ${max} 元`
  } else if (min) {
    return `${min} 元起`
  } else if (max) {
    return `最高 ${max} 元`
  }
  return '-'
}

// 解析并格式化目标鱼种（支持JSON数组或逗号分隔）
const formatTargetSpecies = (species?: string): React.ReactNode => {
  if (!species) return null

  let speciesArray: string[] = []
  try {
    const parsed = JSON.parse(species)
    if (Array.isArray(parsed)) {
      speciesArray = parsed
    }
  } catch {
    // 不是JSON，尝试按逗号分隔
    speciesArray = species.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  }

  if (speciesArray.length > 0) {
    return (
      <Space size={4} wrap>
        {speciesArray.map((s, i) => (
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

  return <Text>{species}</Text>
}

// 格式化适用钓组
const formatApplicableRigs = (rigs?: string): React.ReactNode => {
  if (!rigs) return null

  const rigsArray = rigs.split(/[,，]/).map(s => s.trim()).filter(Boolean)

  if (rigsArray.length > 0) {
    return (
      <Space size={4} wrap>
        {rigsArray.map((r, i) => (
          <Tag
            key={i}
            style={{
              borderRadius: 4,
              margin: 0,
              fontSize: 12,
              background: '#e6f7ff',
              border: 'none',
              color: '#1890ff',
            }}
          >
            {r}
          </Tag>
        ))}
      </Space>
    )
  }

  return <Text>{rigs}</Text>
}

const AccessoryDetailModal: React.FC<AccessoryDetailModalProps> = ({
  open,
  accessoryId,
  onClose,
  onEdit,
}) => {
  const [loading, setLoading] = useState(false)
  const [accessory, setAccessory] = useState<Accessory | null>(null)

  useEffect(() => {
    if (open && accessoryId) {
      loadAccessoryDetail(accessoryId)
    }
    if (!open) {
      setAccessory(null)
    }
  }, [open, accessoryId])

  const loadAccessoryDetail = async (id: number) => {
    setLoading(true)
    try {
      const data = await accessoryApi.get(id)
      setAccessory(data)
    } catch {
      setAccessory(null)
    } finally {
      setLoading(false)
    }
  }

  const categoryConfig = accessory
    ? ACCESSORY_CATEGORY_CONFIG[accessory.category as AccessoryCategory]
    : null
  const userLevelConfig = accessory?.user_level
    ? USER_LEVEL_CONFIG[accessory.user_level as UserLevel]
    : null

  // 检查是否有规格参数
  const hasSpecs = accessory && (
    accessory.size ||
    accessory.weight ||
    accessory.material ||
    accessory.color ||
    accessory.quantity_per_pack
  )

  // 检查是否有应用场景
  const hasApplication = accessory && (
    accessory.target_species ||
    accessory.applicable_rigs ||
    accessory.best_conditions
  )

  // 检查是否有商业信息
  const hasCommercial = accessory && (
    accessory.brand ||
    accessory.price_min ||
    accessory.price_max
  )

  return (
    <Modal
      title={null}
      open={open}
      onCancel={onClose}
      width={640}
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
      ) : accessory ? (
        <>
          {/* 头部：图片 + 基本信息 */}
          <div style={{ display: 'flex', gap: 24, marginBottom: 24 }}>
            <Image
              src={accessory.image_url}
              alt={accessory.name}
              width={120}
              height={120}
              style={{ borderRadius: 12, objectFit: 'cover', background: '#f5f7fa' }}
              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjYwIiB5PSI2MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSIjYmZiZmJmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7wn46jPC90ZXh0Pjwvc3ZnPg=="
              preview={!!accessory.image_url}
            />
            <div style={{ flex: 1 }}>
              <Title level={3} style={{ margin: 0 }}>
                {accessory.name}
              </Title>
              <Space style={{ marginTop: 12 }}>
                {categoryConfig && (
                  <Tag
                    style={{
                      borderRadius: 8,
                      border: 'none',
                      background: `${categoryConfig.color}15`,
                      color: categoryConfig.color,
                    }}
                  >
                    {categoryConfig.icon} {categoryConfig.label}
                  </Tag>
                )}
                {userLevelConfig && (
                  <Tag
                    style={{
                      borderRadius: 8,
                      border: 'none',
                      background: `${userLevelConfig.color}15`,
                      color: userLevelConfig.color,
                    }}
                  >
                    {userLevelConfig.label}
                  </Tag>
                )}
              </Space>
              {accessory.features && (
                <Paragraph
                  type="secondary"
                  style={{ marginTop: 12, marginBottom: 0, fontSize: 13 }}
                >
                  {accessory.features}
                </Paragraph>
              )}
            </div>
          </div>

          {/* 描述 */}
          {accessory.description && (
            <>
              <Divider style={{ margin: '16px 0' }} />
              <div style={{ marginBottom: 24 }}>
                <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }}>
                  详细描述
                </Text>
                <Paragraph
                  style={{
                    padding: '12px 16px',
                    background: '#fafafa',
                    borderRadius: 8,
                    fontSize: 14,
                    color: '#333',
                    margin: 0,
                  }}
                >
                  {accessory.description}
                </Paragraph>
              </div>
            </>
          )}

          {/* 规格参数 */}
          {hasSpecs && (
            <>
              <Divider style={{ margin: '16px 0' }} />
              <div style={{ marginBottom: 24 }}>
                <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 12 }}>
                  规格参数
                </Text>
                <Descriptions
                  size="small"
                  column={2}
                  labelStyle={{ color: '#666', width: 80 }}
                  contentStyle={{ fontWeight: 500 }}
                >
                  {accessory.size && (
                    <Descriptions.Item label="规格尺寸">{accessory.size}</Descriptions.Item>
                  )}
                  {accessory.weight && (
                    <Descriptions.Item label="重量">{accessory.weight}g</Descriptions.Item>
                  )}
                  {accessory.material && (
                    <Descriptions.Item label="材质">{accessory.material}</Descriptions.Item>
                  )}
                  {accessory.color && (
                    <Descriptions.Item label="颜色">{accessory.color}</Descriptions.Item>
                  )}
                  {accessory.quantity_per_pack && (
                    <Descriptions.Item label="每包数量">
                      {accessory.quantity_per_pack} 个
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </div>
            </>
          )}

          {/* 应用场景 */}
          {hasApplication && (
            <>
              <Divider style={{ margin: '16px 0' }} />
              <div style={{ marginBottom: 24 }}>
                <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 12 }}>
                  应用场景
                </Text>
                <Descriptions
                  size="small"
                  column={1}
                  labelStyle={{ color: '#666', width: 80 }}
                  contentStyle={{ fontWeight: 500 }}
                >
                  {accessory.target_species && (
                    <Descriptions.Item label="目标鱼种">
                      {formatTargetSpecies(accessory.target_species)}
                    </Descriptions.Item>
                  )}
                  {accessory.applicable_rigs && (
                    <Descriptions.Item label="适用钓组">
                      {formatApplicableRigs(accessory.applicable_rigs)}
                    </Descriptions.Item>
                  )}
                  {accessory.best_conditions && (
                    <Descriptions.Item label="最佳条件">
                      {accessory.best_conditions}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </div>
            </>
          )}

          {/* 商业信息 */}
          {hasCommercial && (
            <>
              <Divider style={{ margin: '16px 0' }} />
              <div>
                <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 12 }}>
                  商业信息
                </Text>
                <Descriptions
                  size="small"
                  column={2}
                  labelStyle={{ color: '#666', width: 80 }}
                  contentStyle={{ fontWeight: 500 }}
                >
                  {accessory.brand && (
                    <Descriptions.Item label="品牌">{accessory.brand}</Descriptions.Item>
                  )}
                  {(accessory.price_min || accessory.price_max) && (
                    <Descriptions.Item label="价格区间">
                      {formatPriceRange(accessory.price_min, accessory.price_max)}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </div>
            </>
          )}

          {/* 空状态 */}
          {!accessory.description && !hasSpecs && !hasApplication && !hasCommercial && (
            <Empty
              description="暂无更多信息"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 24 }}
            />
          )}
        </>
      ) : (
        <Empty description="未找到配件信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Modal>
  )
}

export default AccessoryDetailModal
