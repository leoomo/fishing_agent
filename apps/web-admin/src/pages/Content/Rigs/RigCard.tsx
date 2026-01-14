/**
 * Rig Card Component - Jobs-style minimalist design
 */

import { Card, Tag, Typography, Space } from 'antd'
import { AppstoreOutlined, SettingOutlined } from '@ant-design/icons'
import type { RigListItem } from '@/types/rig'
import { RIG_CATEGORY_CONFIG, RIG_DIFFICULTY_CONFIG } from '@/types/rig'

const { Text } = Typography

// 分类渐变背景配置
const CATEGORY_GRADIENTS: Record<string, string> = {
  bottom: 'linear-gradient(135deg, #ff9a56 0%, #ff6b35 100%)',  // 橙色-底钓
  float: 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',   // 蓝色-浮漂
  lure: 'linear-gradient(135deg, #55efc4 0%, #00b894 100%)',    // 绿色-路亚
  fly: 'linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%)',     // 紫色-飞蝇
  surf: 'linear-gradient(135deg, #81ecec 0%, #00cec9 100%)',    // 青色-海钓
}

// 解析并格式化目标鱼种
const formatTargetSpecies = (species: string | undefined): React.ReactNode => {
  if (!species) return null
  try {
    const arr = JSON.parse(species)
    if (Array.isArray(arr) && arr.length > 0) {
      return (
        <Space size={4} wrap style={{ marginTop: 8 }}>
          {arr.slice(0, 2).map((s, i) => (
            <Tag
              key={i}
              style={{
                borderRadius: 4,
                margin: 0,
                fontSize: 11,
                background: '#f5f5f5',
                border: 'none',
                color: '#666',
              }}
            >
              {s}
            </Tag>
          ))}
          {arr.length > 2 && (
            <Text type="secondary" style={{ fontSize: 11 }}>+{arr.length - 2}</Text>
          )}
        </Space>
      )
    }
  } catch {
    // 如果不是 JSON，直接显示
    return (
      <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
        {species}
      </Text>
    )
  }
  return null
}

interface RigCardProps {
  rig: RigListItem
  onClick?: (rig: RigListItem) => void
}

const RigCard: React.FC<RigCardProps> = ({ rig, onClick }) => {
  const categoryConfig = RIG_CATEGORY_CONFIG[rig.category] || {
    label: rig.category,
    icon: '📋',
    color: 'default',
  }

  const difficultyConfig = RIG_DIFFICULTY_CONFIG[rig.difficulty] || {
    label: rig.difficulty,
    color: 'default',
  }

  return (
    <Card
      hoverable
      onClick={() => onClick?.(rig)}
      styles={{
        body: { padding: 0 },
      }}
      style={{
        borderRadius: 16,
        overflow: 'hidden',
        border: 'none',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        transition: 'all 0.3s ease',
      }}
      className="rig-card"
    >
      {/* Image area with gradient background */}
      <div
        style={{
          height: 140,
          background: rig.diagram_url
            ? `linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%)`
            : CATEGORY_GRADIENTS[rig.category] || 'linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
      >
        {rig.diagram_url ? (
          <img
            src={rig.diagram_url}
            alt={rig.name}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        ) : (
          <span style={{ fontSize: 56, opacity: 0.9, filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}>
            {categoryConfig.icon}
          </span>
        )}

        {/* Category badge */}
        <Tag
          style={{
            position: 'absolute',
            top: 12,
            left: 12,
            margin: 0,
            borderRadius: 12,
            border: 'none',
            fontWeight: 500,
            background: 'rgba(255,255,255,0.95)',
            color: '#333',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          {categoryConfig.icon} {categoryConfig.label}
        </Tag>
      </div>

      {/* Content area */}
      <div style={{ padding: '14px 16px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: 4,
          }}
        >
          <Text
            strong
            style={{
              fontSize: 15,
              color: '#1a1a1a',
              lineHeight: 1.4,
            }}
          >
            {rig.name}
          </Text>
          <Tag
            color={difficultyConfig.color}
            style={{
              marginLeft: 8,
              borderRadius: 8,
              border: 'none',
              fontSize: 11,
            }}
          >
            {difficultyConfig.label}
          </Tag>
        </div>

        {/* Target species as tags */}
        {formatTargetSpecies(rig.target_species)}

        {/* Stats with icons */}
        <div
          style={{
            display: 'flex',
            gap: 16,
            marginTop: 12,
            paddingTop: 12,
            borderTop: '1px solid #f0f0f0',
          }}
        >
          <Space size={4}>
            <AppstoreOutlined style={{ color: '#1890ff', fontSize: 12 }} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {rig.component_count} 组件
            </Text>
          </Space>
          <Space size={4}>
            <SettingOutlined style={{ color: '#52c41a', fontSize: 12 }} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {rig.spec_count} 规格
            </Text>
          </Space>
        </div>
      </div>

      <style>{`
        .rig-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important;
        }
      `}</style>
    </Card>
  )
}

export default RigCard
