/**
 * 装备推荐面板组件
 *
 * 功能：
 * - 只读展示
 * - 推荐拟饵（Tag 列表）
 * - 推荐钓组（Tag 列表）
 * - 推荐竿力（ML/M/MH）
 * - 推荐鱼线（8-20lb）
 * - 路亚难度
 * - 搏斗强度
 */

import React, { useEffect, useState } from 'react'
import { Tag, Space, Spin, Empty, Typography, Descriptions } from 'antd'
import { fishApi } from '@/api/services/fish'
import type { EquipmentRecommendation } from '@/types/fish'

const { Text } = Typography

interface EquipmentPanelProps {
  speciesId: number
}

const EquipmentPanel: React.FC<EquipmentPanelProps> = ({ speciesId }) => {
  const [loading, setLoading] = useState(false)
  const [equipment, setEquipment] = useState<EquipmentRecommendation | null>(null)

  useEffect(() => {
    const loadEquipment = async () => {
      setLoading(true)
      try {
        const data = await fishApi.getEquipmentRecommendation(speciesId)
        setEquipment(data)
      } catch {
        setEquipment(null)
      } finally {
        setLoading(false)
      }
    }

    loadEquipment()
  }, [speciesId])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Spin />
      </div>
    )
  }

  if (!equipment) {
    return (
      <Empty
        description={
          <span style={{ color: '#999' }}>
            暂无装备推荐数据
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              装备推荐数据由系统预设，无法手动编辑
            </Text>
          </span>
        }
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    )
  }

  // 检查是否有任何数据
  const hasData =
    (equipment.recommended_lures && equipment.recommended_lures.length > 0) ||
    (equipment.recommended_rigs && equipment.recommended_rigs.length > 0) ||
    (equipment.recommended_rod_power && equipment.recommended_rod_power.length > 0) ||
    equipment.recommended_line_lb_min ||
    equipment.recommended_line_lb_max ||
    equipment.lure_difficulty ||
    equipment.fight_intensity

  if (!hasData) {
    return (
      <Empty
        description={
          <span style={{ color: '#999' }}>
            暂无装备推荐数据
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              装备推荐数据由系统预设，无法手动编辑
            </Text>
          </span>
        }
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 16, color: '#666', fontSize: 14 }}>
        以下为系统预设的装备推荐，仅供参考
      </div>

      <Descriptions
        column={1}
        size="small"
        labelStyle={{ width: 120, color: '#666' }}
        contentStyle={{ fontWeight: 500 }}
      >
        {/* 推荐拟饵 */}
        {equipment.recommended_lures && equipment.recommended_lures.length > 0 && (
          <Descriptions.Item label="推荐拟饵">
            <Space size={4} wrap>
              {equipment.recommended_lures.map((lure, index) => (
                <Tag
                  key={index}
                  style={{
                    borderRadius: 8,
                    border: 'none',
                    background: '#e6f7ff',
                    color: '#1890ff',
                  }}
                >
                  {lure}
                </Tag>
              ))}
            </Space>
          </Descriptions.Item>
        )}

        {/* 推荐钓组 */}
        {equipment.recommended_rigs && equipment.recommended_rigs.length > 0 && (
          <Descriptions.Item label="推荐钓组">
            <Space size={4} wrap>
              {equipment.recommended_rigs.map((rig, index) => (
                <Tag
                  key={index}
                  style={{
                    borderRadius: 8,
                    border: 'none',
                    background: '#f6ffed',
                    color: '#52c41a',
                  }}
                >
                  {rig}
                </Tag>
              ))}
            </Space>
          </Descriptions.Item>
        )}

        {/* 推荐竿力 */}
        {equipment.recommended_rod_power && equipment.recommended_rod_power.length > 0 && (
          <Descriptions.Item label="推荐竿力">
            <Space size={4} wrap>
              {equipment.recommended_rod_power.map((power, index) => (
                <Tag
                  key={index}
                  style={{
                    borderRadius: 8,
                    border: 'none',
                    background: '#fff7e6',
                    color: '#fa8c16',
                  }}
                >
                  {power}
                </Tag>
              ))}
            </Space>
          </Descriptions.Item>
        )}

        {/* 推荐鱼线 */}
        {(equipment.recommended_line_lb_min || equipment.recommended_line_lb_max) && (
          <Descriptions.Item label="推荐鱼线">
            <Tag
              style={{
                borderRadius: 8,
                border: 'none',
                background: '#f9f0ff',
                color: '#722ed1',
              }}
            >
              {equipment.recommended_line_lb_min && equipment.recommended_line_lb_max
                ? `${equipment.recommended_line_lb_min} - ${equipment.recommended_line_lb_max} lb`
                : equipment.recommended_line_lb_min
                  ? `${equipment.recommended_line_lb_min}+ lb`
                  : `${equipment.recommended_line_lb_max} lb 以下`}
            </Tag>
          </Descriptions.Item>
        )}

        {/* 路亚难度 */}
        {equipment.lure_difficulty && (
          <Descriptions.Item label="路亚难度">
            <Tag
              style={{
                borderRadius: 8,
                border: 'none',
                background:
                  equipment.lure_difficulty === '高'
                    ? '#fff1f0'
                    : equipment.lure_difficulty === '中'
                      ? '#fff7e6'
                      : '#f6ffed',
                color:
                  equipment.lure_difficulty === '高'
                    ? '#ff4d4f'
                    : equipment.lure_difficulty === '中'
                      ? '#faad14'
                      : '#52c41a',
              }}
            >
              {equipment.lure_difficulty}
            </Tag>
          </Descriptions.Item>
        )}

        {/* 搏斗强度 */}
        {equipment.fight_intensity && (
          <Descriptions.Item label="搏斗强度">
            <Tag
              style={{
                borderRadius: 8,
                border: 'none',
                background:
                  equipment.fight_intensity === '高'
                    ? '#fff1f0'
                    : equipment.fight_intensity === '中'
                      ? '#fff7e6'
                      : '#f6ffed',
                color:
                  equipment.fight_intensity === '高'
                    ? '#ff4d4f'
                    : equipment.fight_intensity === '中'
                      ? '#faad14'
                      : '#52c41a',
              }}
            >
              {equipment.fight_intensity}
            </Tag>
          </Descriptions.Item>
        )}
      </Descriptions>
    </div>
  )
}

export default EquipmentPanel
