/**
 * 装备批量添加页面
 *
 * 支持两种添加方式：
 * 1. 手动批量输入 - 模板+变体表格
 * 2. 文本导入 - 从粘贴的规格表解析
 */

import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Tabs,
  Steps,
  Button,
  Space,
  Typography,
  message,
  Result,
  Spin,
  Alert,
} from 'antd'
import {
  ArrowLeftOutlined,
  FormOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { equipmentApi, type Brand } from '@/api/services/equipment'
import type { BatchEquipmentCreateResponse } from '@/api/services/equipment'
import ManualBatchForm from './ManualBatch'
import TextImportForm from './TextImport'

const { Title, Text } = Typography

type TabKey = 'manual' | 'text'

const BatchCreatePage: React.FC = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabKey>('manual')
  const [brands, setBrands] = useState<Brand[]>([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BatchEquipmentCreateResponse | null>(null)

  // 加载品牌列表
  useEffect(() => {
    const loadBrands = async () => {
      try {
        const data = await equipmentApi.listBrands()
        setBrands(data)
      } catch (error) {
        console.error('加载品牌列表失败:', error)
        message.error('加载品牌列表失败')
      }
    }
    loadBrands()
  }, [])

  // 处理批量创建
  const handleBatchCreate = async (
    category: string,
    template: Record<string, unknown>,
    variants: Record<string, unknown>[],
    skipDuplicates: boolean
  ) => {
    setLoading(true)
    try {
      const response = await equipmentApi.batchCreate({
        category,
        template,
        variants,
        skip_duplicates: skipDuplicates,
      })
      setResult(response)

      if (response.success_count > 0) {
        message.success(`成功创建 ${response.success_count} 个装备`)
      }
      if (response.skip_count > 0) {
        message.warning(`跳过 ${response.skip_count} 个重复装备`)
      }
      if (response.error_count > 0) {
        message.error(`${response.error_count} 个装备创建失败`)
      }
    } catch (error) {
      console.error('批量创建失败:', error)
      message.error('批量创建失败')
    } finally {
      setLoading(false)
    }
  }

  // 重置结果，返回表单
  const handleReset = () => {
    setResult(null)
  }

  // 返回装备列表
  const handleBackToList = () => {
    navigate('/equipment')
  }

  // 渲染结果页面
  const renderResult = () => {
    if (!result) return null

    const isSuccess = result.success_count > 0 && result.error_count === 0

    return (
      <Result
        status={isSuccess ? 'success' : 'warning'}
        title={isSuccess ? '批量创建完成' : '批量创建完成（有部分失败）'}
        subTitle={
          <Space direction="vertical" size="small">
            <Text>成功创建: {result.success_count} 个装备</Text>
            {result.skip_count > 0 && (
              <Text type="warning">跳过重复: {result.skip_count} 个</Text>
            )}
            {result.error_count > 0 && (
              <Text type="danger">创建失败: {result.error_count} 个</Text>
            )}
          </Space>
        }
        extra={[
          <Button key="back" onClick={handleBackToList}>
            返回装备列表
          </Button>,
          <Button key="continue" type="primary" onClick={handleReset}>
            继续添加
          </Button>,
        ]}
      >
        {result.skipped_models.length > 0 && (
          <Alert
            type="warning"
            message="跳过的型号"
            description={result.skipped_models.join(', ')}
            style={{ marginBottom: 16, textAlign: 'left' }}
          />
        )}
        {result.errors.length > 0 && (
          <Alert
            type="error"
            message="失败详情"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {result.errors.map((err, idx) => (
                  <li key={idx}>
                    {err.model}: {err.error}
                  </li>
                ))}
              </ul>
            }
            style={{ textAlign: 'left' }}
          />
        )}
      </Result>
    )
  }

  // Tab 配置
  const tabItems = [
    {
      key: 'manual',
      label: (
        <span>
          <FormOutlined />
          手动批量输入
        </span>
      ),
      children: (
        <ManualBatchForm
          brands={brands}
          onSubmit={handleBatchCreate}
          loading={loading}
        />
      ),
    },
    {
      key: 'text',
      label: (
        <span>
          <FileTextOutlined />
          从文本导入
        </span>
      ),
      children: (
        <TextImportForm
          brands={brands}
          onSubmit={handleBatchCreate}
          loading={loading}
        />
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={handleBackToList}
          >
            返回
          </Button>
          <Title level={4} style={{ margin: 0 }}>
            批量添加装备
          </Title>
        </Space>
        <div style={{ marginTop: 8, color: '#666' }}>
          快速添加同一品牌同一产品线的多个型号装备
        </div>
      </div>

      {/* 主内容区 */}
      <Spin spinning={loading}>
        {result ? (
          <Card>{renderResult()}</Card>
        ) : (
          <Card>
            <Tabs
              activeKey={activeTab}
              onChange={(key) => setActiveTab(key as TabKey)}
              items={tabItems}
            />
          </Card>
        )}
      </Spin>
    </div>
  )
}

export default BatchCreatePage
