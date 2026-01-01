/**
 * 配件分类统计卡片组件
 *
 * 乔布斯简洁风格：
 * - 无边框设计
 * - 微阴影效果
 * - hover 抬升动画
 * - 分类图标配色
 */

import React from 'react'
import type { AccessoryCategoryStats } from '@/types/accessory'

interface AccessoryCardProps {
  stats: AccessoryCategoryStats
  selected?: boolean
  onClick?: () => void
}

const AccessoryCard: React.FC<AccessoryCardProps> = ({
  stats,
  selected = false,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '20px 24px',
        background: selected ? `${stats.color}10` : '#fff',
        borderRadius: 12,
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        boxShadow: selected
          ? `0 4px 12px ${stats.color}30`
          : '0 2px 8px rgba(0, 0, 0, 0.06)',
        border: selected ? `2px solid ${stats.color}` : '2px solid transparent',
        minWidth: 120,
        textAlign: 'center',
      }}
      onMouseEnter={(e) => {
        if (!selected) {
          e.currentTarget.style.transform = 'translateY(-4px)'
          e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.12)'
        }
      }}
      onMouseLeave={(e) => {
        if (!selected) {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.06)'
        }
      }}
    >
      {/* 图标 */}
      <div
        style={{
          fontSize: 28,
          marginBottom: 8,
        }}
      >
        {stats.icon}
      </div>

      {/* 分类名称 */}
      <div
        style={{
          fontSize: 14,
          fontWeight: 600,
          color: stats.color,
          marginBottom: 4,
        }}
      >
        {stats.label}
      </div>

      {/* 数量 */}
      <div
        style={{
          fontSize: 22,
          fontWeight: 700,
          color: '#333',
        }}
      >
        {stats.count}
      </div>

      {/* 单位 */}
      <div
        style={{
          fontSize: 12,
          color: '#999',
        }}
      >
        种配件
      </div>
    </div>
  )
}

export default AccessoryCard
