/**
 * 列设置弹窗组件
 * 允许用户选择显示/隐藏哪些列
 */

import React, { useState, useEffect } from 'react'
import { Modal, Checkbox, Button, Space } from 'antd'
import { COLUMN_DEFINITIONS, getDefaultVisibleColumns, getRequiredColumns } from '../columnConfig'

interface ColumnSettingsModalProps {
  open: boolean
  visibleColumns: string[]
  saving: boolean
  onOk: (columns: string[]) => void
  onCancel: () => void
}

const ColumnSettingsModal: React.FC<ColumnSettingsModalProps> = ({
  open,
  visibleColumns,
  saving,
  onOk,
  onCancel,
}) => {
  const [selected, setSelected] = useState<string[]>(visibleColumns)
  const requiredColumns = getRequiredColumns()

  // 当弹窗打开时，同步外部状态
  useEffect(() => {
    if (open) {
      setSelected(visibleColumns)
    }
  }, [open, visibleColumns])

  // 切换列选中状态
  const handleToggle = (key: string, checked: boolean) => {
    if (checked) {
      setSelected([...selected, key])
    } else {
      setSelected(selected.filter((k) => k !== key))
    }
  }

  // 恢复默认
  const handleReset = () => {
    setSelected(getDefaultVisibleColumns())
  }

  // 确认保存
  const handleOk = () => {
    onOk(selected)
  }

  return (
    <Modal
      title="列设置"
      open={open}
      onCancel={onCancel}
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button onClick={handleReset}>恢复默认</Button>
          <Space>
            <Button onClick={onCancel}>取消</Button>
            <Button type="primary" onClick={handleOk} loading={saving}>
              确定
            </Button>
          </Space>
        </div>
      }
      width={320}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '8px 0' }}>
        {COLUMN_DEFINITIONS.map((col) => {
          const isRequired = requiredColumns.includes(col.key)
          const isChecked = selected.includes(col.key)

          return (
            <Checkbox
              key={col.key}
              checked={isChecked || isRequired}
              disabled={isRequired}
              onChange={(e) => handleToggle(col.key, e.target.checked)}
            >
              {col.title}
              {isRequired && (
                <span style={{ color: '#999', fontSize: 12, marginLeft: 4 }}>(必选)</span>
              )}
            </Checkbox>
          )
        })}
      </div>
    </Modal>
  )
}

export default ColumnSettingsModal
