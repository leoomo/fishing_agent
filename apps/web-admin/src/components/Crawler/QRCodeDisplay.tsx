import React, { useState, useEffect } from 'react'
import {
  Card,
  Image,
  Button,
  Typography,
  Space,
  Alert,
  Spin,
  Tooltip,
} from 'antd'
import {
  ReloadOutlined,
  QrcodeOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { message } from 'antd'

const { Text } = Typography

interface QRCodeDisplayProps {
  taskId: number
  qrCode?: string | null
  expiresAt?: number | null
  onRefresh?: () => void
  loading?: boolean
  error?: string | null
}

const QRCodeDisplay: React.FC<QRCodeDisplayProps> = ({
  qrCode,
  expiresAt,
  onRefresh,
  loading = false,
  error = null,
}) => {
  const [countdown, setCountdown] = useState<number>(0)
  const [isExpired, setIsExpired] = useState<boolean>(false)

  // 倒计时效果
  useEffect(() => {
    if (!expiresAt) return

    const calculateCountdown = () => {
      const now = Date.now()
      const remaining = Math.max(0, expiresAt - now)
      setCountdown(remaining)
      setIsExpired(remaining === 0)
    }

    calculateCountdown()
    const interval = setInterval(calculateCountdown, 1000)

    return () => clearInterval(interval)
  }, [expiresAt])

  const formatCountdown = (ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh()
      message.success('二维码已刷新')
    }
  }

  const handleCopyImage = async () => {
    if (qrCode) {
      try {
        // 如果qrCode是base64数据
        if (qrCode.startsWith('data:image')) {
          // 创建blob并复制到剪贴板
          const response = await fetch(qrCode)
          const blob = await response.blob()
          await navigator.clipboard.write([
            new ClipboardItem({ [blob.type]: blob })
          ])
          message.success('二维码已复制到剪贴板')
        } else {
          // 如果是URL，复制URL
          await navigator.clipboard.writeText(qrCode)
          message.success('二维码链接已复制到剪贴板')
        }
      } catch (error) {
        message.error('复制失败，请重试')
      }
    }
  }

  if (error) {
    return (
      <Card title="登录二维码" className="qr-code-card">
        <Alert
          message="二维码获取失败"
          description={error}
          type="error"
          showIcon
          icon={<ExclamationCircleOutlined />}
          action={
            <Button size="small" onClick={handleRefresh}>
              重试
            </Button>
          }
        />
      </Card>
    )
  }

  return (
    <Card
      title={
        <Space>
          <QrcodeOutlined />
          登录二维码
          {loading && <Spin size="small" />}
        </Space>
      }
      className="qr-code-card"
      extra={
        <Tooltip title="刷新二维码">
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
            disabled={loading}
          />
        </Tooltip>
      }
    >
      <div style={{ textAlign: 'center' }}>
        {qrCode ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <Image
                src={qrCode}
                alt="登录二维码"
                width={200}
                height={200}
                preview={false}
                style={{
                  border: isExpired ? '2px dashed #ff4d4f' : '1px solid #d9d9d9',
                  borderRadius: 8,
                  opacity: isExpired ? 0.5 : 1,
                }}
              />
              {isExpired && (
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    padding: '8px 16px',
                    borderRadius: 4,
                    border: '1px solid #ff4d4f',
                  }}
                >
                  <Text type="danger" strong>
                    二维码已过期
                  </Text>
                </div>
              )}
            </div>

            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {expiresAt && (
                <div>
                  <Text type={isExpired ? 'danger' : 'secondary'}>
                    {isExpired ? '二维码已过期' : `有效时间: ${formatCountdown(countdown)}`}
                  </Text>
                </div>
              )}

              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  请使用手机APP扫描二维码登录
                </Text>
              </div>

              <Space>
                <Button size="small" onClick={handleRefresh} loading={loading}>
                  刷新二维码
                </Button>
                <Button size="small" onClick={handleCopyImage}>
                  复制二维码
                </Button>
              </Space>
            </Space>
          </>
        ) : (
          <div style={{ padding: '40px 20px' }}>
            {loading ? (
              <Space direction="vertical" align="center">
                <Spin size="large" />
                <Text type="secondary">正在生成二维码...</Text>
              </Space>
            ) : (
              <Space direction="vertical" align="center">
                <QrcodeOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                <Text type="secondary">暂无二维码</Text>
                <Button type="primary" onClick={handleRefresh}>
                  生成二维码
                </Button>
              </Space>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

export default QRCodeDisplay