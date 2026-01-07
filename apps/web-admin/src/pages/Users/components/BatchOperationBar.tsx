import { useState } from 'react'
import { Space, Button, Select, Modal, App, Alert } from 'antd'
import {
  ExportOutlined,
  EditOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { USER_LEVELS } from '@/types/user'
import { usersApi } from '@/api/services/users'

interface BatchOperationBarProps {
  selectedIds: number[]
  onClear: () => void
  onSuccess: () => void
}

const BatchOperationBar: React.FC<BatchOperationBarProps> = ({
  selectedIds,
  onClear,
  onSuccess,
}) => {
  const { message } = App.useApp()
  const [batchModalOpen, setBatchModalOpen] = useState(false)
  const [selectedLevel, setSelectedLevel] = useState<string>()
  const [updating, setUpdating] = useState(false)

  const handleBatchUpdateLevel = async () => {
    if (!selectedLevel) {
      message.warning('请选择要修改的用户水平')
      return
    }

    setUpdating(true)
    try {
      const result = await usersApi.batchUpdate({
        user_ids: selectedIds,
        user_level: selectedLevel,
      })

      if (result.success) {
        message.success(result.message)
        setBatchModalOpen(false)
        setSelectedLevel(undefined)
        onClear()
        onSuccess()
      } else {
        message.error(result.message)
      }
    } catch {
      message.error('批量更新失败')
    } finally {
      setUpdating(false)
    }
  }

  const handleExportSelected = async () => {
    try {
      const blob = await usersApi.exportCSV({
        user_ids: selectedIds.join(','),
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `users_export_${selectedIds.length}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      message.success(`成功导出 ${selectedIds.length} 个用户`)
    } catch {
      message.error('导出失败')
    }
  }

  if (selectedIds.length === 0) return null

  return (
    <>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message={
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <span>已选择 {selectedIds.length} 个用户</span>
            <Space>
              <Button
                size="small"
                icon={<EditOutlined />}
                onClick={() => setBatchModalOpen(true)}
              >
                批量修改水平
              </Button>
              <Button
                size="small"
                icon={<ExportOutlined />}
                onClick={handleExportSelected}
              >
                导出选中
              </Button>
              <Button
                size="small"
                icon={<CloseOutlined />}
                onClick={onClear}
              >
                清空选择
              </Button>
            </Space>
          </Space>
        }
      />

      <Modal
        title="批量修改用户水平"
        open={batchModalOpen}
        onCancel={() => {
          setBatchModalOpen(false)
          setSelectedLevel(undefined)
        }}
        onOk={handleBatchUpdateLevel}
        confirmLoading={updating}
        okText="确认修改"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          将选中的 {selectedIds.length} 个用户的水平修改为：
        </div>
        <Select
          placeholder="选择用户水平"
          style={{ width: '100%' }}
          value={selectedLevel}
          onChange={setSelectedLevel}
          options={USER_LEVELS.map((level) => ({
            label: level,
            value: level,
          }))}
        />
      </Modal>
    </>
  )
}

export default BatchOperationBar
