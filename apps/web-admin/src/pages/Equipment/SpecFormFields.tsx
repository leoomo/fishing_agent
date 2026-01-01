/**
 * 动态规格表单组件
 * 根据装备类别动态渲染规格字段
 *
 * 设计原则：乔布斯式简洁
 * - 无分割线，用留白代替
 * - 渐进式展示，高级选项默认折叠
 * - 视觉层次清晰
 */

import React, { useState, useMemo } from 'react'
import { Form, Input, InputNumber, Select, Row, Col, Typography } from 'antd'
import { DownOutlined, RightOutlined } from '@ant-design/icons'
import { getSpecFields, GROUP_LABELS } from './specFieldConfig'
import type { SpecFieldDef } from './specFieldConfig'

const { TextArea } = Input
const { Text } = Typography

interface SpecFormFieldsProps {
  category: string
  formItemPrefix?: string // Form.Item name 前缀，如 ['specs']
}

/**
 * 渲染单个字段
 */
const SpecField: React.FC<{ field: SpecFieldDef; prefix?: string[] }> = ({ field, prefix = [] }) => {
  const name = prefix.length > 0 ? [...prefix, field.name] : field.name

  const rules = field.required ? [{ required: true, message: `请输入${field.label}` }] : []

  // 根据类型渲染不同的输入控件
  const renderInput = () => {
    switch (field.type) {
      case 'number':
        return (
          <InputNumber
            style={{ width: '100%' }}
            min={field.min}
            max={field.max}
            step={field.step}
            addonAfter={field.addonAfter}
            placeholder={field.placeholder}
          />
        )
      case 'select':
        return (
          <Select
            placeholder={`选择${field.label}`}
            options={field.options}
            allowClear
          />
        )
      case 'textarea':
        return (
          <TextArea
            rows={2}
            placeholder={field.placeholder}
          />
        )
      default:
        return (
          <Input
            placeholder={field.placeholder}
            addonAfter={field.addonAfter}
          />
        )
    }
  }

  return (
    <Form.Item
      name={name}
      label={field.label}
      rules={rules}
    >
      {renderInput()}
    </Form.Item>
  )
}

/**
 * 规格表单字段组件
 */
const SpecFormFields: React.FC<SpecFormFieldsProps> = ({
  category,
  formItemPrefix = 'specs',
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false)

  // 获取该类别的字段配置
  const fields = useMemo(() => getSpecFields(category), [category])

  // 按分组组织字段
  const groupedFields = useMemo(() => {
    const groups: Record<string, SpecFieldDef[]> = {
      basic: [],
      range: [],
      advanced: [],
    }
    fields.forEach((field) => {
      if (groups[field.group]) {
        groups[field.group].push(field)
      }
    })
    return groups
  }, [fields])

  const prefix = formItemPrefix ? [formItemPrefix] : []

  // 如果没有字段，不渲染
  if (fields.length === 0) {
    return null
  }

  return (
    <div style={{ marginTop: 16 }}>
      {/* 基本规格 - 始终显示 */}
      {groupedFields.basic.length > 0 && (
        <Row gutter={16}>
          {groupedFields.basic.map((field) => (
            <Col span={8} key={field.name}>
              <SpecField field={field} prefix={prefix} />
            </Col>
          ))}
        </Row>
      )}

      {/* 范围参数 - 始终显示 */}
      {groupedFields.range.length > 0 && (
        <Row gutter={16} style={{ marginTop: 8 }}>
          {groupedFields.range.map((field) => (
            <Col span={8} key={field.name}>
              <SpecField field={field} prefix={prefix} />
            </Col>
          ))}
        </Row>
      )}

      {/* 高级参数 - 可折叠 */}
      {groupedFields.advanced.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              color: '#666',
              userSelect: 'none',
              marginBottom: showAdvanced ? 12 : 0,
            }}
          >
            {showAdvanced ? <DownOutlined style={{ fontSize: 10, marginRight: 6 }} /> : <RightOutlined style={{ fontSize: 10, marginRight: 6 }} />}
            <Text type="secondary" style={{ fontSize: 13 }}>
              {GROUP_LABELS.advanced}
            </Text>
          </div>

          {showAdvanced && (
            <Row gutter={16}>
              {groupedFields.advanced.map((field) => (
                <Col span={field.type === 'textarea' ? 24 : 8} key={field.name}>
                  <SpecField field={field} prefix={prefix} />
                </Col>
              ))}
            </Row>
          )}
        </div>
      )}
    </div>
  )
}

export default SpecFormFields
