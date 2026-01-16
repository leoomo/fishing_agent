/**
 * 配件导入弹窗
 *
 * 功能：
 * - 上传 Excel 文件
 * - 预览导入数据
 * - 显示验证结果
 * - 执行导入
 */

import { useState } from 'react'
import {
  Modal,
  Upload,
  Button,
  Table,
  Tag,
  Space,
  Typography,
  Alert,
  message,
  Progress,
} from 'antd'
import { InboxOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload'
import { accessoryApi } from '@/api/services/accessory'
import type { AccessoryImportPreviewItem, AccessoryImportPreviewResponse } from '@/types/accessory'

const { Dragger } = Upload
const { Text, Title } = Typography

interface AccessoryImportModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

type ImportStep = 'upload' | 'preview' | 'importing' | 'done'

const AccessoryImportModal: React.FC<AccessoryImportModalProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [step, setStep] = useState<ImportStep>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [previewData, setPreviewData] = useState<AccessoryImportPreviewResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [importProgress, setImportProgress] = useState(0)
  const [importResult, setImportResult] = useState<{
    success: boolean
    message: string
    imported: number
    failed: number
  } | null>(null)

  const handleReset = () => {
    setStep('upload')
    setFile(null)
    setFileList([])
    setPreviewData(null)
    setLoading(false)
    setImportProgress(0)
    setImportResult(null)
  }

  const handleClose = () => {
    handleReset()
    onClose()
  }

  const handleFileChange = (info: { file: UploadFile; fileList: UploadFile[] }) => {
    setFileList(info.fileList.slice(-1)) // 只保留最后一个文件

    if (info.file.originFileObj) {
      setFile(info.file.originFileObj)
    }
  }

  const handlePreview = async () => {
    if (!file) {
      message.error('请先选择文件')
      return
    }

    setLoading(true)
    try {
      const result = await accessoryApi.importPreview(file)
      setPreviewData(result)
      setStep('preview')
    } catch {
      message.error('预览失败，请检查文件格式')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    if (!file) {
      message.error('请先选择文件')
      return
    }

    setStep('importing')
    setLoading(true)
    setImportProgress(0)

    // 模拟进度
    const progressInterval = setInterval(() => {
      setImportProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return prev
        }
        return prev + 10
      })
    }, 200)

    try {
      const result = await accessoryApi.importExecute(file)
      clearInterval(progressInterval)
      setImportProgress(100)

      setImportResult({
        success: result.success,
        message: result.message,
        imported: result.imported_count,
        failed: result.failed_count,
      })
      setStep('done')

      if (result.success) {
        onSuccess()
      }
    } catch {
      clearInterval(progressInterval)
      message.error('导入失败')
      setStep('preview')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadTemplate = async () => {
    try {
      await accessoryApi.downloadTemplate()
      message.success('模板下载成功')
    } catch {
      message.error('模板下载失败')
    }
  }

  // 预览表格列
  const previewColumns = [
    {
      title: '行号',
      dataIndex: 'row_number',
      key: 'row_number',
      width: 60,
    },
    {
      title: '配件名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'is_valid',
      key: 'is_valid',
      width: 80,
      render: (isValid: boolean) =>
        isValid ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            有效
          </Tag>
        ) : (
          <Tag color="error" icon={<CloseCircleOutlined />}>
            无效
          </Tag>
        ),
    },
    {
      title: '错误信息',
      dataIndex: 'errors',
      key: 'errors',
      render: (errors: string[]) =>
        errors && errors.length > 0 ? (
          <Text type="danger">{errors.join(', ')}</Text>
        ) : (
          '-'
        ),
    },
  ]

  const renderContent = () => {
    switch (step) {
      case 'upload':
        return (
          <div>
            <Dragger
              accept=".xlsx,.xls"
              fileList={fileList}
              beforeUpload={() => false}
              onChange={handleFileChange}
              maxCount={1}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
              <p className="ant-upload-hint">支持 .xlsx, .xls 格式</p>
            </Dragger>

            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Button type="link" onClick={handleDownloadTemplate}>
                下载导入模板
              </Button>
            </div>
          </div>
        )

      case 'preview':
        return (
          <div>
            {previewData && (
              <>
                <Alert
                  style={{ marginBottom: 16 }}
                  type={previewData.invalid_rows > 0 ? 'warning' : 'success'}
                  message={
                    <Space>
                      <span>总计 {previewData.total_rows} 行</span>
                      <Tag color="success">有效 {previewData.valid_rows} 行</Tag>
                      {previewData.invalid_rows > 0 && (
                        <Tag color="error">无效 {previewData.invalid_rows} 行</Tag>
                      )}
                    </Space>
                  }
                />

                <Table<AccessoryImportPreviewItem>
                  columns={previewColumns}
                  dataSource={previewData.items}
                  rowKey="row_number"
                  size="small"
                  pagination={{ pageSize: 5 }}
                  scroll={{ y: 300 }}
                />
              </>
            )}
          </div>
        )

      case 'importing':
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Title level={4}>正在导入...</Title>
            <Progress percent={importProgress} status="active" />
            <Text type="secondary">请勿关闭窗口</Text>
          </div>
        )

      case 'done':
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            {importResult?.success ? (
              <>
                <CheckCircleOutlined
                  style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }}
                />
                <Title level={4}>导入完成</Title>
                <Space direction="vertical">
                  <Text>成功导入 {importResult.imported} 条数据</Text>
                  {importResult.failed > 0 && (
                    <Text type="danger">失败 {importResult.failed} 条</Text>
                  )}
                </Space>
              </>
            ) : (
              <>
                <CloseCircleOutlined
                  style={{ fontSize: 48, color: '#ff4d4f', marginBottom: 16 }}
                />
                <Title level={4}>导入失败</Title>
                <Text type="danger">{importResult?.message}</Text>
              </>
            )}
          </div>
        )
    }
  }

  const renderFooter = () => {
    switch (step) {
      case 'upload':
        return [
          <Button key="cancel" onClick={handleClose}>
            取消
          </Button>,
          <Button
            key="preview"
            type="primary"
            onClick={handlePreview}
            loading={loading}
            disabled={!file}
          >
            预览数据
          </Button>,
        ]

      case 'preview':
        return [
          <Button key="back" onClick={() => setStep('upload')}>
            重新选择
          </Button>,
          <Button
            key="import"
            type="primary"
            onClick={handleImport}
            loading={loading}
            disabled={!previewData || previewData.valid_rows === 0}
          >
            开始导入 ({previewData?.valid_rows || 0} 条)
          </Button>,
        ]

      case 'importing':
        return null

      case 'done':
        return [
          <Button key="close" type="primary" onClick={handleClose}>
            完成
          </Button>,
        ]
    }
  }

  return (
    <Modal
      title="导入配件"
      open={open}
      onCancel={handleClose}
      width={700}
      footer={renderFooter()}
      destroyOnClose
    >
      {renderContent()}
    </Modal>
  )
}

export default AccessoryImportModal
