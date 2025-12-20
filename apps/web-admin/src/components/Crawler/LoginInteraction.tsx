import React, { useState, useEffect } from 'react'
import {
  Card,
  Steps,
  Button,
  Typography,
  Space,
  Alert,
  Progress,
  Row,
  Col,
  Tag,
  Spin,
  message,
} from 'antd'
import {
  MobileOutlined,
  QrcodeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import QRCodeDisplay from './QRCodeDisplay'
import { useWebSocket } from '../../hooks/useWebSocket'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

// 登录状态类型
export type LoginStatus =
  | 'idle'
  | 'generating_qr'
  | 'qr_ready'
  | 'waiting_scan'
  | 'scan_detected'
  | 'verifying'
  | 'login_success'
  | 'login_failed'
  | 'qr_expired'

export interface LoginState {
  taskId: number
  platform: 'taobao' | 'jd' | 'pdd' | 'other'
  status: LoginStatus
  qrCode?: string | null
  expiresAt?: number | null
  userInfo?: any | null
  errorMessage?: string | null
  platformName?: string
}

interface LoginInteractionProps {
  taskId: number
  platform: string
  platformName?: string
  onComplete?: (userInfo: any) => void
  onError?: (error: string) => void
  onCancel?: () => void
}

// 状态配置映射
const statusConfig: Record<LoginStatus, {
  title: string
  description: string
  icon: React.ReactNode
  color?: string
  showProgress?: boolean
  progressPercent?: number
}> = {
  idle: {
    title: '准备登录',
    description: '点击开始登录按钮生成二维码',
    icon: <UserOutlined />,
  },
  generating_qr: {
    title: '生成二维码中',
    description: '正在获取登录二维码，请稍候...',
    icon: <LoadingOutlined />,
    showProgress: true,
    progressPercent: 25,
  },
  qr_ready: {
    title: '二维码已生成',
    description: '请使用手机APP扫描二维码登录',
    icon: <QrcodeOutlined />,
    color: 'processing',
    showProgress: true,
    progressPercent: 40,
  },
  waiting_scan: {
    title: '等待扫码',
    description: '请打开手机APP扫描二维码',
    icon: <MobileOutlined />,
    color: 'processing',
    showProgress: true,
    progressPercent: 50,
  },
  scan_detected: {
    title: '扫码成功',
    description: '检测到扫码，请在手机确认登录',
    icon: <CheckCircleOutlined />,
    color: 'processing',
    showProgress: true,
    progressPercent: 75,
  },
  verifying: {
    title: '验证中',
    description: '正在验证登录信息，请稍候...',
    icon: <LoadingOutlined />,
    color: 'processing',
    showProgress: true,
    progressPercent: 90,
  },
  login_success: {
    title: '登录成功',
    description: '恭喜！您已成功登录',
    icon: <CheckCircleOutlined />,
    color: 'success',
    showProgress: true,
    progressPercent: 100,
  },
  login_failed: {
    title: '登录失败',
    description: '登录过程中出现错误，请重试',
    icon: <ExclamationCircleOutlined />,
    color: 'error',
  },
  qr_expired: {
    title: '二维码已过期',
    description: '二维码已过期，请刷新后重新扫码',
    icon: <ExclamationCircleOutlined />,
    color: 'warning',
  },
}

const LoginInteraction: React.FC<LoginInteractionProps> = ({
  taskId,
  platform,
  platformName,
  onComplete,
  onError,
  onCancel,
}) => {
  const [loginState, setLoginState] = useState<LoginState>({
    taskId,
    platform: platform as any,
    status: 'idle',
  })

  const [loading, setLoading] = useState(false)

  // WebSocket连接管理
  const { isConnected, lastMessage, error: wsError } = useWebSocket(
    `/api/v1/admin/crawler/login/${taskId}`,
    {
      onMessage: (data) => {
        const event = JSON.parse(data)
        handleLoginEvent(event)
      },
      onConnect: () => {
        console.log('登录WebSocket连接已建立')
      },
      onDisconnect: () => {
        console.log('登录WebSocket连接已断开')
      },
      onError: (error) => {
        console.error('登录WebSocket连接错误:', error)
        message.error('连接失败，请刷新页面重试')
      },
    }
  )

  // 处理登录事件
  const handleLoginEvent = (event: any) => {
    const { type, data } = event

    switch (type) {
      case 'qr_code_ready':
        setLoginState(prev => ({
          ...prev,
          status: 'qr_ready',
          qrCode: data.qrCode,
          expiresAt: data.expiresAt,
        }))
        break

      case 'scan_detected':
        setLoginState(prev => ({
          ...prev,
          status: 'scan_detected',
        }))
        break

      case 'verifying':
        setLoginState(prev => ({
          ...prev,
          status: 'verifying',
        }))
        break

      case 'login_success':
        setLoginState(prev => ({
          ...prev,
          status: 'login_success',
          userInfo: data.userInfo,
        }))
        onComplete?.(data.userInfo)
        message.success('登录成功！')
        break

      case 'login_failed':
        setLoginState(prev => ({
          ...prev,
          status: 'login_failed',
          errorMessage: data.reason,
        }))
        onError?.(data.reason)
        message.error(`登录失败: ${data.reason}`)
        break

      case 'qr_code_expired':
        setLoginState(prev => ({
          ...prev,
          status: 'qr_expired',
        }))
        message.warning('二维码已过期，请刷新后重新扫码')
        break

      default:
        console.log('未知登录事件:', event)
    }
  }

  // 开始登录
  const handleStartLogin = async () => {
    setLoading(true)
    setLoginState(prev => ({ ...prev, status: 'generating_qr' }))

    try {
      // 这里应该调用API开始登录流程
      // const response = await crawlerApi.startLogin(taskId)
      // 模拟API调用
      setTimeout(() => {
        setLoginState(prev => ({
          ...prev,
          status: 'qr_ready',
          qrCode: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', // 占位符
          expiresAt: Date.now() + 5 * 60 * 1000, // 5分钟后过期
        }))
        setLoading(false)
      }, 2000)
    } catch (error) {
      setLoginState(prev => ({
        ...prev,
        status: 'login_failed',
        errorMessage: '启动登录失败',
      }))
      setLoading(false)
      message.error('启动登录失败')
    }
  }

  // 刷新二维码
  const handleRefreshQRCode = async () => {
    setLoading(true)
    try {
      // 调用刷新API
      // await crawlerApi.refreshQRCode(taskId)
      // 模拟刷新
      setTimeout(() => {
        setLoginState(prev => ({
          ...prev,
          status: 'qr_ready',
          qrCode: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', // 新的占位符
          expiresAt: Date.now() + 5 * 60 * 1000,
        }))
        setLoading(false)
      }, 1500)
    } catch (error) {
      setLoading(false)
      message.error('刷新二维码失败')
    }
  }

  // 重试登录
  const handleRetry = () => {
    setLoginState({
      taskId,
      platform: platform as any,
      status: 'idle',
    })
  }

  const currentConfig = statusConfig[loginState.status]
  const isSuccess = loginState.status === 'login_success'
  const isFailed = ['login_failed', 'qr_expired'].includes(loginState.status)

  return (
    <Card
      title={
        <Space>
          <MobileOutlined />
          {platformName || platform.toUpperCase()} 登录
          {isConnected ? (
            <Tag color="green">连接正常</Tag>
          ) : (
            <Tag color="red">连接断开</Tag>
          )}
        </Space>
      }
      extra={
        onCancel && (
          <Button onClick={onCancel} disabled={loading}>
            取消
          </Button>
        )
      }
      style={{ maxWidth: 800 }}
    >
      <Row gutter={24}>
        {/* 左侧：登录步骤 */}
        <Col span={12}>
          <Steps
            direction="vertical"
            size="small"
            current={Object.keys(statusConfig).indexOf(loginState.status)}
            items={[
              {
                title: '准备登录',
                description: '开始登录流程',
                icon: <UserOutlined />,
              },
              {
                title: '生成二维码',
                description: '获取登录二维码',
                icon: <QrcodeOutlined />,
              },
              {
                title: '扫码确认',
                description: '手机扫码并确认',
                icon: <MobileOutlined />,
              },
              {
                title: '登录完成',
                description: '成功登录平台',
                icon: <CheckCircleOutlined />,
              },
            ]}
          />

          <div style={{ marginTop: 24 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Title level={5}>
                  {currentConfig.icon} {currentConfig.title}
                </Title>
                <Paragraph type="secondary">
                  {currentConfig.description}
                </Paragraph>
              </div>

              {currentConfig.showProgress && (
                <Progress
                  percent={currentConfig.progressPercent}
                  status={isSuccess ? 'success' : isFailed ? 'exception' : 'active'}
                  showInfo={false}
                />
              )}

              {loginState.errorMessage && (
                <Alert
                  message={loginState.errorMessage}
                  type="error"
                  showIcon
                  style={{ marginTop: 8 }}
                />
              )}

              {wsError && (
                <Alert
                  message="连接异常"
                  description="无法实时获取登录状态，请刷新页面重试"
                  type="warning"
                  showIcon
                  style={{ marginTop: 8 }}
                />
              )}

              <Space>
                {loginState.status === 'idle' && (
                  <Button
                    type="primary"
                    icon={<MobileOutlined />}
                    onClick={handleStartLogin}
                    loading={loading}
                  >
                    开始登录
                  </Button>
                )}

                {(isFailed || loginState.status === 'qr_expired') && (
                  <Button onClick={handleRetry}>
                    重新开始
                  </Button>
                )}
              </Space>
            </Space>
          </div>
        </Col>

        {/* 右侧：二维码显示 */}
        <Col span={12}>
          <QRCodeDisplay
            taskId={taskId}
            qrCode={loginState.qrCode}
            expiresAt={loginState.expiresAt}
            onRefresh={handleRefreshQRCode}
            loading={loading}
            error={loginState.errorMessage}
          />

          {/* 平台特定说明 */}
          <div style={{ marginTop: 16 }}>
            <Alert
              message="扫码登录说明"
              description={
                <div>
                  <p>1. 打开{platformName || platform}手机APP</p>
                  <p>2. 点击"扫一扫"功能</p>
                  <p>3. 扫描左侧二维码</p>
                  <p>4. 在手机上确认登录</p>
                </div>
              }
              type="info"
              showIcon
            />
          </div>
        </Col>
      </Row>
    </Card>
  )
}

export default LoginInteraction