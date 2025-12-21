import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { Form, Input, Button, Card, Checkbox, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { login } from '@/store/slices/authSlice'
import type { AppDispatch } from '@/store/store'
import './index.css'

// 本地存储键名
const STORAGE_KEY = 'fishing_admin_remember'

// 存储凭据的接口
interface StoredCredentials {
  username: string
  password: string
  remember: boolean
}

// 存储凭据到本地存储
const saveCredentials = (username: string, password: string, remember: boolean): void => {
  if (remember) {
    const credentials: StoredCredentials = { username, password, remember }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(credentials))
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}

// 从本地存储加载凭据
const loadCredentials = (): Partial<StoredCredentials> => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.warn('加载存储的凭据失败:', error)
    localStorage.removeItem(STORAGE_KEY)
  }
  return {}
}

const Login = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const onFinish = async (values: { username: string; password: string; remember: boolean }) => {
    setLoading(true)
    try {
      await dispatch(login({ username: values.username, password: values.password })).unwrap()
      message.success('登录成功')

      // 保存凭据
      saveCredentials(values.username, values.password, values.remember)

      navigate('/equipment')
    } catch (error) {
      message.error((error as string) || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  // 组件加载时尝试填充保存的凭据
  useEffect(() => {
    const credentials = loadCredentials()
    if (credentials.username && credentials.password && credentials.remember) {
      form.setFieldsValue({
        username: credentials.username,
        password: credentials.password,
        remember: credentials.remember,
      })
    }
  }, [form])

  return (
    <div className="login-container">
      <Card className="login-card" title="智能钓鱼助手 - 管理后台">
        <Form
          form={form}
          name="login"
          initialValues={{ remember: false }}
          onFinish={onFinish}
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>记住密码</Checkbox>
            </Form.Item>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              size="large"
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center', color: '#999' }}>
          默认账号: admin / admin123
        </div>
      </Card>
    </div>
  )
}

export default Login
