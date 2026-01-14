/**
 * 鱼种详情查看弹窗
 *
 * 功能：
 * - 只读展示鱼种完整信息
 * - 基本信息（名称、分类、体型等）
 * - 季节活动（折叠面板）
 * - 知识库（折叠面板）
 * - 装备推荐（复用 EquipmentPanel）
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
import { fishApi } from '@/api/services/fish'
import type { FishSpecies, FishSeasonActivity, FishKnowledge } from '@/types/fish'
import { FISH_CATEGORY_CONFIG, SEASON_CONFIG, ACTIVITY_LEVEL_CONFIG } from '@/types/fish'
import EquipmentPanel from './EquipmentPanel'

const { Title, Text, Paragraph } = Typography

interface FishDetailModalProps {
  open: boolean
  speciesId: number | null
  onClose: () => void
  onEdit: () => void
}

const FishDetailModal: React.FC<FishDetailModalProps> = ({
  open,
  speciesId,
  onClose,
  onEdit,
}) => {
  const [loading, setLoading] = useState(false)
  const [fish, setFish] = useState<FishSpecies | null>(null)

  useEffect(() => {
    if (open && speciesId) {
      loadFishDetail(speciesId)
    }
    if (!open) {
      setFish(null)
    }
  }, [open, speciesId])

  const loadFishDetail = async (id: number) => {
    setLoading(true)
    try {
      const data = await fishApi.get(id)
      setFish(data)
    } catch {
      setFish(null)
    } finally {
      setLoading(false)
    }
  }

  // 格式化体型范围
  const formatRange = (min?: number, max?: number, unit?: string) => {
    if (min && max) {
      return `${min} - ${max} ${unit || ''}`
    } else if (min) {
      return `${min}+ ${unit || ''}`
    } else if (max) {
      return `${max} ${unit || ''} 以下`
    }
    return '-'
  }

  // 渲染季节活动项
  const renderSeasonActivity = (activity: FishSeasonActivity) => {
    const seasonConfig = SEASON_CONFIG[activity.season]
    const activityConfig = ACTIVITY_LEVEL_CONFIG[activity.activity_level]

    return (
      <div key={activity.id} style={{ marginBottom: 12 }}>
        <Space size={8} style={{ marginBottom: 8 }}>
          <Tag
            style={{
              borderRadius: 8,
              border: 'none',
              background: `${seasonConfig?.color || '#8c8c8c'}15`,
              color: seasonConfig?.color || '#8c8c8c',
            }}
          >
            {seasonConfig?.icon} {seasonConfig?.label}
          </Tag>
          <Tag
            style={{
              borderRadius: 8,
              border: 'none',
              background: `${activityConfig?.color || '#8c8c8c'}15`,
              color: activityConfig?.color || '#8c8c8c',
            }}
          >
            活跃度: {activity.activity_level}
          </Tag>
        </Space>
        <Descriptions size="small" column={2} style={{ marginTop: 8 }}>
          {activity.best_time && (
            <Descriptions.Item label="最佳时间">{activity.best_time}</Descriptions.Item>
          )}
          {activity.recommended_lures && (
            <Descriptions.Item label="推荐拟饵">{activity.recommended_lures}</Descriptions.Item>
          )}
          {activity.fishing_tips && (
            <Descriptions.Item label="钓鱼技巧" span={2}>
              {activity.fishing_tips}
            </Descriptions.Item>
          )}
        </Descriptions>
      </div>
    )
  }

  // 渲染知识条目
  const renderKnowledge = (knowledge: FishKnowledge) => {
    return (
      <div key={knowledge.id} style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <Text strong>{knowledge.topic}</Text>
          {knowledge.source && (
            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
              来源: {knowledge.source}
            </Text>
          )}
        </div>
        <Paragraph
          style={{
            margin: 0,
            padding: '8px 12px',
            background: '#fafafa',
            borderRadius: 8,
            fontSize: 14,
          }}
        >
          {knowledge.content}
        </Paragraph>
        {knowledge.tags && (
          <Space size={4} style={{ marginTop: 8 }}>
            {knowledge.tags.split(',').map((tag, index) => (
              <Tag
                key={index}
                style={{
                  borderRadius: 8,
                  border: 'none',
                  background: '#f0f0f0',
                  color: '#666',
                  fontSize: 12,
                }}
              >
                {tag.trim()}
              </Tag>
            ))}
          </Space>
        )}
      </div>
    )
  }

  // 构建折叠面板项
  const collapseItems = []

  if (fish?.season_activity && fish.season_activity.length > 0) {
    collapseItems.push({
      key: 'seasons',
      label: (
        <Space>
          <span>季节活动</span>
          <Tag style={{ borderRadius: 8, background: '#e6f7ff', color: '#1890ff', border: 'none' }}>
            {fish.season_activity.length}/4
          </Tag>
        </Space>
      ),
      children: fish.season_activity.map(renderSeasonActivity),
    })
  }

  if (fish?.knowledge && fish.knowledge.length > 0) {
    collapseItems.push({
      key: 'knowledge',
      label: (
        <Space>
          <span>知识库</span>
          <Tag style={{ borderRadius: 8, background: '#f6ffed', color: '#52c41a', border: 'none' }}>
            {fish.knowledge.length} 条
          </Tag>
        </Space>
      ),
      children: fish.knowledge.map(renderKnowledge),
    })
  }

  if (fish) {
    collapseItems.push({
      key: 'equipment',
      label: '装备推荐',
      children: <EquipmentPanel speciesId={fish.species_id} />,
    })
  }

  const categoryConfig = fish ? FISH_CATEGORY_CONFIG[fish.category] : null

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
      ) : fish ? (
        <>
          {/* 头部：图片 + 基本信息 */}
          <div style={{ display: 'flex', gap: 24, marginBottom: 24 }}>
            <Image
              src={fish.image_url}
              alt={fish.name_cn}
              width={160}
              height={120}
              style={{ borderRadius: 12, objectFit: 'cover' }}
              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTYwIiBoZWlnaHQ9IjEyMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjgwIiB5PSI2MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSIjYmZiZmJmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7wn5CFPC90ZXh0Pjwvc3ZnPg=="
              preview={!!fish.image_url}
            />
            <div style={{ flex: 1 }}>
              <Title level={3} style={{ margin: 0 }}>
                {fish.name_cn}
              </Title>
              {(fish.name_en || fish.scientific_name) && (
                <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 14 }}>
                  {[fish.name_en, fish.scientific_name].filter(Boolean).join(' · ')}
                </Text>
              )}
              {categoryConfig && (
                <Tag
                  style={{
                    marginTop: 12,
                    borderRadius: 8,
                    border: 'none',
                    background: `${categoryConfig.color}15`,
                    color: categoryConfig.color,
                  }}
                >
                  {categoryConfig.icon} {categoryConfig.label}
                </Tag>
              )}
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
              <Descriptions.Item label="栖息环境">{fish.habitat || '-'}</Descriptions.Item>
              <Descriptions.Item label="体长">
                {formatRange(fish.min_length, fish.max_length, 'cm')}
              </Descriptions.Item>
              <Descriptions.Item label="体重">
                {formatRange(fish.min_weight, fish.max_weight, 'kg')}
              </Descriptions.Item>
            </Descriptions>
            {fish.description && (
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
                {fish.description}
              </Paragraph>
            )}
          </div>

          {/* 折叠面板：季节活动、知识库、装备推荐 */}
          {collapseItems.length > 0 && (
            <Collapse
              items={collapseItems}
              defaultActiveKey={['seasons']}
              bordered={false}
              style={{ background: 'transparent' }}
              expandIconPosition="end"
            />
          )}

          {/* 空状态 */}
          {!fish.season_activity?.length && !fish.knowledge?.length && (
            <Empty
              description="暂无更多信息"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 24 }}
            />
          )}
        </>
      ) : (
        <Empty description="未找到鱼种信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Modal>
  )
}

export default FishDetailModal
