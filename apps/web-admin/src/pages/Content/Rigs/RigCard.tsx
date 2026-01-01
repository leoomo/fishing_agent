/**
 * Rig Card Component - Jobs-style minimalist design
 */

import { Card, Tag, Typography } from 'antd'
import type { RigListItem } from '@/types/rig'
import { RIG_CATEGORY_CONFIG, RIG_DIFFICULTY_CONFIG } from '@/types/rig'

const { Text, Paragraph } = Typography

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
      {/* Image area */}
      <div
        style={{
          height: 160,
          background: `linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%)`,
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
          <span style={{ fontSize: 48, opacity: 0.6 }}>{categoryConfig.icon}</span>
        )}

        {/* Category badge */}
        <Tag
          color={categoryConfig.color}
          style={{
            position: 'absolute',
            top: 12,
            left: 12,
            margin: 0,
            borderRadius: 12,
            border: 'none',
            fontWeight: 500,
          }}
        >
          {categoryConfig.icon} {categoryConfig.label}
        </Tag>
      </div>

      {/* Content area */}
      <div style={{ padding: '16px 20px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: 8,
          }}
        >
          <Text
            strong
            style={{
              fontSize: 16,
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
            }}
          >
            {difficultyConfig.label}
          </Tag>
        </div>

        {rig.target_species && (
          <Paragraph
            type="secondary"
            style={{
              margin: 0,
              fontSize: 13,
              lineHeight: 1.5,
            }}
            ellipsis={{ rows: 1 }}
          >
            目标鱼种: {rig.target_species}
          </Paragraph>
        )}

        {/* Stats */}
        <div
          style={{
            display: 'flex',
            gap: 16,
            marginTop: 12,
            paddingTop: 12,
            borderTop: '1px solid #f0f0f0',
          }}
        >
          <Text type="secondary" style={{ fontSize: 12 }}>
            {rig.component_count} 个组件
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {rig.spec_count} 项规格
          </Text>
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
