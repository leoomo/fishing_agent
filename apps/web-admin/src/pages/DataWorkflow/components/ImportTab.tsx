/**
 * 数据导入 Tab 组件
 *
 * 支持 Excel 文件上传、预览和导入到审核队列
 */

import React, { useState, useCallback } from 'react'
import {
  Card,
  Upload,
  Button,
  Space,
  Table,
  Tag,
  Alert,
  message,
  Select,
  Typography,
  Result,
  Descriptions,
  Tooltip,
  Spin,
} from 'antd'
import {
  DownloadOutlined,
  InboxOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileExcelOutlined,
  SendOutlined,
} from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd/es/upload'
import type { ColumnsType } from 'antd/es/table'

import { dataWorkflowApi } from '@/api/services/dataWorkflow'
import type {
  ImportPreviewRow,
  ImportPreviewResponse,
  ImportResponse,
} from '@/types/dataWorkflow'
import { IMPORT_EQUIPMENT_TYPES } from '@/types/dataWorkflow'

const { Dragger } = Upload
const { Text } = Typography

interface ImportTabProps {
  onSuccess?: () => void
}

type ImportStep = 'upload' | 'preview' | 'result'

const ImportTab: React.FC<ImportTabProps> = ({ onSuccess }) => {
  // 状态管理
  const [step, setStep] = useState<ImportStep>('upload')
  const [equipmentType, setEquipmentType] = useState<string>('rod')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null)
  const [importResult, setImportResult] = useState<ImportResponse | null>(null)
  const [loading, setLoading] = useState(false)

  // 下载模板
  const handleDownloadTemplate = useCallback((type: string) => {
    const url = dataWorkflowApi.getTemplateDownloadUrl(type)
    window.open(url, '_blank')
  }, [])

  // 文件选择（不自动上传）
  const handleFileSelect: UploadProps['beforeUpload'] = (file) => {
    // 验证文件类型
    const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
    if (!isExcel) {
      message.error('只支持 .xlsx 或 .xls 格式的 Excel 文件')
      return Upload.LIST_IGNORE
    }

    setSelectedFile(file)
    return false // 阻止自动上传
  }

  // 预览导入数据
  const handlePreview = useCallback(async () => {
    if (!selectedFile) {
      message.warning('请先选择文件')
      return
    }

    setLoading(true)
    try {
      const result = await dataWorkflowApi.previewImport(selectedFile, equipmentType)
      setPreviewData(result)

      if (result.success) {
        setStep('preview')
      } else {
        message.error(result.message)
      }
    } catch (error: unknown) {
      const err = error as Error
      message.error(`预览失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }, [selectedFile, equipmentType])

  // 执行导入
  const handleImport = useCallback(async () => {
    if (!selectedFile) {
      message.warning('请先选择文件')
      return
    }

    setLoading(true)
    try {
      const result = await dataWorkflowApi.executeImport(selectedFile, equipmentType)
      setImportResult(result)
      setStep('result')

      if (result.success) {
        message.success(result.message)
        onSuccess?.()
      } else {
        message.error(result.message)
      }
    } catch (error: unknown) {
      const err = error as Error
      message.error(`导入失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }, [selectedFile, equipmentType, onSuccess])

  // 重置状态
  const handleReset = useCallback(() => {
    setStep('upload')
    setSelectedFile(null)
    setPreviewData(null)
    setImportResult(null)
  }, [])

  // 预览表格列
  const previewColumns: ColumnsType<ImportPreviewRow> = [
    {
      title: '行号',
      dataIndex: 'row_number',
      key: 'row_number',
      width: 60,
    },
    {
      title: '状态',
      key: 'status',
      width: 80,
      render: (_, record) => (
        record.is_valid ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>有效</Tag>
        ) : (
          <Tooltip title={record.errors.join('; ')}>
            <Tag color="error" icon={<CloseCircleOutlined />}>无效</Tag>
          </Tooltip>
        )
      ),
    },
    {
      title: '品牌',
      dataIndex: ['data', 'brand_name'],
      key: 'brand_name',
      width: 100,
      ellipsis: true,
    },
    {
      title: '产品名称',
      dataIndex: ['data', 'name'],
      key: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '型号',
      dataIndex: ['data', 'model'],
      key: 'model',
      width: 120,
      ellipsis: true,
    },
    {
      title: '价格区间',
      key: 'price',
      width: 120,
      render: (_, record) => {
        const min = record.data.price_min
        const max = record.data.price_max
        if (min || max) {
          return `¥${min || '-'} ~ ¥${max || '-'}`
        }
        return '-'
      },
    },
    {
      title: '错误信息',
      key: 'errors',
      render: (_, record) => (
        record.errors.length > 0 ? (
          <Text type="danger">{record.errors.join('; ')}</Text>
        ) : null
      ),
    },
  ]

  // 渲染上传步骤
  const renderUploadStep = () => (
    <>
      {/* 模板下载区 */}
      <Card size="small" title="第一步：下载导入模板" style={{ marginBottom: 16 }}>
        <Space wrap>
          {IMPORT_EQUIPMENT_TYPES.map((type) => (
            <Button
              key={type.key}
              icon={<DownloadOutlined />}
              onClick={() => handleDownloadTemplate(type.key)}
            >
              {type.label}模板
            </Button>
          ))}
        </Space>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">
            请先下载对应装备类型的模板，按照模板格式填写数据后上传
          </Text>
        </div>
      </Card>

      {/* 文件上传区 */}
      <Card size="small" title="第二步：选择装备类型并上传文件" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <Text strong style={{ marginRight: 8 }}>装备类型：</Text>
            <Select
              value={equipmentType}
              onChange={setEquipmentType}
              style={{ width: 200 }}
              options={IMPORT_EQUIPMENT_TYPES.map((t) => ({
                value: t.key,
                label: t.label,
              }))}
            />
          </div>

          <Dragger
            accept=".xlsx,.xls"
            maxCount={1}
            fileList={selectedFile ? [{
              uid: '-1',
              name: selectedFile.name,
              status: 'done',
            } as UploadFile] : []}
            beforeUpload={handleFileSelect}
            onRemove={() => setSelectedFile(null)}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽 Excel 文件到此区域</p>
            <p className="ant-upload-hint">
              支持 .xlsx 或 .xls 格式
            </p>
          </Dragger>
        </Space>
      </Card>

      {/* 操作按钮 */}
      <div style={{ textAlign: 'center' }}>
        <Button
          type="primary"
          icon={<FileExcelOutlined />}
          size="large"
          loading={loading}
          disabled={!selectedFile}
          onClick={handlePreview}
        >
          预览数据
        </Button>
      </div>
    </>
  )

  // 渲染预览步骤
  const renderPreviewStep = () => (
    <>
      {/* 统计信息 */}
      <Alert
        type={previewData?.invalid_rows === 0 ? 'success' : 'warning'}
        showIcon
        style={{ marginBottom: 16 }}
        message={
          <Space split={<span style={{ color: '#d9d9d9' }}>|</span>}>
            <span>总计: <Text strong>{previewData?.total_rows}</Text> 条</span>
            <span>有效: <Text strong type="success">{previewData?.valid_rows}</Text> 条</span>
            <span>无效: <Text strong type="danger">{previewData?.invalid_rows}</Text> 条</span>
          </Space>
        }
        description={
          previewData?.invalid_rows ? '请修正无效数据后重新上传，或直接导入有效数据' : '所有数据验证通过，可以直接导入'
        }
      />

      {/* 预览表格 */}
      <Card size="small" title="数据预览" style={{ marginBottom: 16 }}>
        <Table
          dataSource={previewData?.preview_data || []}
          columns={previewColumns}
          rowKey="row_number"
          size="small"
          scroll={{ x: 800, y: 400 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 条`,
          }}
          rowClassName={(record) => record.is_valid ? '' : 'ant-table-row-warning'}
        />
      </Card>

      {/* 操作按钮 */}
      <div style={{ textAlign: 'center' }}>
        <Space>
          <Button onClick={handleReset}>
            返回重选
          </Button>
          <Button
            type="primary"
            icon={<SendOutlined />}
            size="large"
            loading={loading}
            disabled={previewData?.valid_rows === 0}
            onClick={handleImport}
          >
            确认导入 {previewData?.valid_rows} 条数据
          </Button>
        </Space>
      </div>
    </>
  )

  // 渲染结果步骤
  const renderResultStep = () => (
    <Result
      status={importResult?.success ? 'success' : 'warning'}
      title={importResult?.success ? '导入完成' : '部分导入成功'}
      subTitle={importResult?.message}
      extra={[
        <Button key="reset" onClick={handleReset}>
          继续导入
        </Button>,
        <Button key="review" type="primary" onClick={() => onSuccess?.()}>
          查看审核列表
        </Button>,
      ]}
    >
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="总行数">{importResult?.total_rows}</Descriptions.Item>
        <Descriptions.Item label="成功导入">
          <Text type="success" strong>{importResult?.imported_count}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="失败数量">
          <Text type="danger">{importResult?.failed_count}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="创建记录 ID">
          {importResult?.pending_ids?.slice(0, 10).join(', ')}
          {(importResult?.pending_ids?.length || 0) > 10 && '...'}
        </Descriptions.Item>
      </Descriptions>

      {/* 错误列表 */}
      {importResult?.errors && importResult.errors.length > 0 && (
        <Card
          size="small"
          title={`失败详情 (${importResult.errors.length} 条)`}
          style={{ marginTop: 16 }}
        >
          <Table
            dataSource={importResult.errors}
            rowKey="row"
            size="small"
            pagination={false}
            columns={[
              { title: '行号', dataIndex: 'row', width: 60 },
              {
                title: '错误信息',
                dataIndex: 'errors',
                render: (errors: string[]) => errors.join('; '),
              },
            ]}
          />
        </Card>
      )}
    </Result>
  )

  return (
    <Spin spinning={loading}>
      {/* 步骤提示 */}
      {step === 'upload' && renderUploadStep()}
      {step === 'preview' && renderPreviewStep()}
      {step === 'result' && renderResultStep()}
    </Spin>
  )
}

export default ImportTab
