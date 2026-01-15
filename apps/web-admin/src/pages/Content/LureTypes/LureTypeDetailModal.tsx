/**
 * 拟饵类型详情查看弹窗
 *
 * 功能：
 * - 只读展示拟饵类型完整信息
 * - 基本信息（名称、分类、描述等）
 * - 扩展信息（使用技巧、优缺点、收线技巧等）
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
} from 'antd'
import { EditOutlined } from '@ant-design/icons'
import { lureTypeApi } from '@/api/services/lureType'
import type { LureType, LureTypeExtendedInfo } from '@/types/lureType'
import { LURE_CATEGORY_CONFIG } from '@/types/lureType'

const { Title, Text, Paragraph } = Typography

interface LureTypeDetailModalProps {
  open: boolean
  lureTypeId: number | null
  onClose: () => void
  onEdit: () => void
}

// 解析扩展信息 JSON
const parseExtendedInfo = (bestConditions: string | undefined): LureTypeExtendedInfo | null => {
  if (!bestConditions) return null
  try {
    const parsed = JSON.parse(bestConditions)
    if (typeof parsed === 'object' && parsed !== null) {
      return parsed as LureTypeExtendedInfo
    }
  } catch {
    // 不是 JSON，返回 null
  }
  return null
}

const LureTypeDetailModal: React.FC<LureTypeDetailModalProps> = ({
  open,
  lureTypeId,
  onClose,
  onEdit,
}) => {
  const [loading, setLoading] = useState(false)
  const [lureType, setLureType] = useState<LureType | null>(null)

  useEffect(() => {
    if (open && lureTypeId) {
      loadLureTypeDetail(lureTypeId)
    }
    if (!open) {
      setLureType(null)
    }
  }, [open, lureTypeId])

  const loadLureTypeDetail = async (id: number) => {
    setLoading(true)
    try {
      const data = await lureTypeApi.get(id)
      setLureType(data)
    } catch {
      setLureType(null)
    } finally {
      setLoading(false)
    }
  }

  // 解析扩展信息
  const extendedInfo = parseExtendedInfo(lureType?.best_conditions)

  // 构建折叠面板项
  const collapseItems = []

  // 使用技巧
  if (extendedInfo?.usage_tips && extendedInfo.usage_tips.length > 0) {
    collapseItems.push({
      key: 'usage_tips',
      label: (
        <Space>
          <span>使用技巧</span>
          <Tag
            style={{
              borderRadius: 8,
              background: '#e6f7ff',
              color: '#1890ff',
              border: 'none',
            }}
          >
            {extendedInfo.usage_tips.length} 条
          </Tag>
        </Space>
      ),
      children: (
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          {extendedInfo.usage_tips.map((tip, i) => (
            <li key={i} style={{ marginBottom: 8, color: '#333' }}>{tip}</li>
          ))}
        </ul>
      ),
    })
  }

  // 收线技巧
  if (extendedInfo?.retrieve_techniques && extendedInfo.retrieve_techniques.length > 0) {
    collapseItems.push({
      key: 'retrieve',
      label: (
        <Space>
          <span>收线技巧</span>
          <Tag
            style={{
              borderRadius: 8,
              background: '#fff7e6',
              color: '#fa8c16',
              border: 'none',
            }}
          >
            {extendedInfo.retrieve_techniques.length} 种
          </Tag>
        </Space>
      ),
      children: (
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          {extendedInfo.retrieve_techniques.map((tech, i) => (
            <li key={i} style={{ marginBottom: 8, color: '#333' }}>{tech}</li>
          ))}
        </ul>
      ),
    })
  }

  // 优缺点
  if ((extendedInfo?.pros && extendedInfo.pros.length > 0) ||
      (extendedInfo?.cons && extendedInfo.cons.length > 0)) {
    collapseItems.push({
      key: 'pros_cons',
      label: '优缺点',
      children: (
        <div style={{ display: 'flex', gap: 24 }}>
          {extendedInfo?.pros && extendedInfo.pros.length > 0 && (
            <div style={{ flex: 1 }}>
              <Text strong style={{ color: '#52c41a', display: 'block', marginBottom: 8 }}>优点</Text>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {extendedInfo.pros.map((pro, i) => (
                  <li key={i} style={{ marginBottom: 4, color: '#333' }}>{pro}</li>
                ))}
              </ul>
            </div>
          )}
          {extendedInfo?.cons && extendedInfo.cons.length > 0 && (
            <div style={{ flex: 1 }}>
              <Text strong style={{ color: '#ff4d4f', display: 'block', marginBottom: 8 }}>缺点</Text>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {extendedInfo.cons.map((con, i) => (
                  <li key={i} style={{ marginBottom: 4, color: '#333' }}>{con}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ),
    })
  }

  // 装备推荐
  if (extendedInfo?.recommended_rod_power || extendedInfo?.recommended_line) {
    collapseItems.push({
      key: 'equipment',
      label: '装备推荐',
      children: (
        <Descriptions size="small" column={1} labelStyle={{ color: '#666', width: 100 }}>
          {extendedInfo.recommended_rod_power && extendedInfo.recommended_rod_power.length > 0 && (
            <Descriptions.Item label="推荐竿子调性">
              <Space size={4} wrap>
                {extendedInfo.recommended_rod_power.map((power, i) => (
                  <Tag key={i} style={{ borderRadius: 4, margin: 0 }}>{power}</Tag>
                ))}
              </Space>
            </Descriptions.Item>
          )}
          {extendedInfo.recommended_line && (
            <Descriptions.Item label="推荐线组">
              {extendedInfo.recommended_line}
            </Descriptions.Item>
          )}
        </Descriptions>
      ),
    })
  }

  // 使用条件
  if (extendedInfo?.best_seasons || extendedInfo?.best_water_conditions || extendedInfo?.color_selection) {
    collapseItems.push({
      key: 'conditions',
      label: '使用条件',
      children: (
        <Descriptions size="small" column={1} labelStyle={{ color: '#666', width: 100 }}>
          {extendedInfo.best_seasons && extendedInfo.best_seasons.length > 0 && (
            <Descriptions.Item label="最佳季节">
              <Space size={4} wrap>
                {extendedInfo.best_seasons.map((season, i) => (
                  <Tag key={i} style={{ borderRadius: 4, margin: 0 }}>{season}</Tag>
                ))}
              </Space>
            </Descriptions.Item>
          )}
          {extendedInfo.best_water_conditions && (
            <Descriptions.Item label="水域条件">
              {extendedInfo.best_water_conditions}
            </Descriptions.Item>
          )}
          {extendedInfo.color_selection && (
            <Descriptions.Item label="颜色选择">
              {extendedInfo.color_selection}
            </Descriptions.Item>
          )}
        </Descriptions>
      ),
    })
  }

  const categoryConfig = lureType ? LURE_CATEGORY_CONFIG[lureType.category] : null

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
      ) : lureType ? (
        <>
          {/* 头部：图片 + 基本信息 */}
          <div style={{ display: 'flex', gap: 24, marginBottom: 24 }}>
            <Image
              src={lureType.image_url}
              alt={lureType.name}
              width={160}
              height={120}
              style={{ borderRadius: 12, objectFit: 'cover', background: '#f5f7fa' }}
              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTYwIiBoZWlnaHQ9IjEyMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjgwIiB5PSI2MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSIjYmZiZmJmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7wn46jPC90ZXh0Pjwvc3ZnPg=="
              preview={!!lureType.image_url}
            />
            <div style={{ flex: 1 }}>
              <Title level={3} style={{ margin: 0 }}>
                {lureType.name}
              </Title>
              {lureType.name_en && (
                <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 14 }}>
                  {lureType.name_en}
                </Text>
              )}
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
                {(lureType.typical_weight_min || lureType.typical_weight_max) && (
                  <Tag
                    style={{
                      borderRadius: 8,
                      border: 'none',
                      background: '#f5f5f5',
                      color: '#666',
                    }}
                  >
                    {lureType.typical_weight_min && lureType.typical_weight_max
                      ? `${lureType.typical_weight_min}-${lureType.typical_weight_max}g`
                      : lureType.typical_weight_min
                        ? `≥${lureType.typical_weight_min}g`
                        : `≤${lureType.typical_weight_max}g`
                    }
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
              column={1}
              labelStyle={{ color: '#666', width: 80 }}
              contentStyle={{ fontWeight: 500 }}
            >
              {lureType.target_species && (
                <Descriptions.Item label="目标鱼种">
                  {lureType.target_species}
                </Descriptions.Item>
              )}
              {lureType.action_description && (
                <Descriptions.Item label="动作特点">
                  {lureType.action_description}
                </Descriptions.Item>
              )}
            </Descriptions>
            {lureType.description && (
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
                {lureType.description}
              </Paragraph>
            )}
          </div>

          {/* 折叠面板：扩展信息 */}
          {collapseItems.length > 0 && (
            <Collapse
              items={collapseItems}
              defaultActiveKey={['usage_tips']}
              bordered={false}
              style={{ background: 'transparent' }}
              expandIconPosition="end"
            />
          )}

          {/* 空状态 */}
          {!lureType.description && !lureType.action_description && collapseItems.length === 0 && (
            <Empty
              description="暂无更多信息"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 24 }}
            />
          )}
        </>
      ) : (
        <Empty description="未找到拟饵类型信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Modal>
  )
}

export default LureTypeDetailModal
