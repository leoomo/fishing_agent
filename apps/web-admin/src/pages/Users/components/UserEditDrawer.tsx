import { useEffect } from 'react'
import {
  Drawer,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Space,
  App,
} from 'antd'
import type { User, UserUpdateData } from '@/types/user'
import { USER_LEVELS, FISHING_METHODS } from '@/types/user'
import { usersApi } from '@/api/services/users'

interface UserEditDrawerProps {
  open: boolean
  user: User | null
  onClose: () => void
  onSuccess: () => void
}

const UserEditDrawer: React.FC<UserEditDrawerProps> = ({
  open,
  user,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm()
  const { message } = App.useApp()

  // 当用户变化时重置表单
  useEffect(() => {
    if (user && open) {
      form.setFieldsValue({
        email: user.email,
        phone: user.phone,
        user_level: user.user_level,
        fishing_experience_years: user.fishing_experience_years,
        preferred_fish: user.favorite_fish_species,
        preferred_scenarios: user.preferred_fishing_method,
      })
    }
  }, [user, open, form])

  const handleSubmit = async () => {
    if (!user) return

    try {
      const values = await form.validateFields()
      const updateData: UserUpdateData = {}

      // 只包含有变化的字段
      if (values.email !== user.email) updateData.email = values.email
      if (values.phone !== user.phone) updateData.phone = values.phone
      if (values.user_level !== user.user_level)
        updateData.user_level = values.user_level
      if (values.fishing_experience_years !== user.fishing_experience_years)
        updateData.fishing_experience_years = values.fishing_experience_years
      if (values.preferred_fish !== user.favorite_fish_species)
        updateData.preferred_fish = values.preferred_fish
      if (values.preferred_scenarios !== user.preferred_fishing_method)
        updateData.preferred_scenarios = values.preferred_scenarios

      if (Object.keys(updateData).length === 0) {
        message.info('没有修改任何内容')
        return
      }

      await usersApi.update(user.user_id, updateData)
      message.success('更新成功')
      onSuccess()
      onClose()
    } catch (error) {
      message.error('更新失败')
    }
  }

  return (
    <Drawer
      title={`编辑用户 - ${user?.username || ''}`}
      open={open}
      onClose={onClose}
      width={480}
      extra={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" onClick={handleSubmit}>
            保存
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical">
        <Form.Item label="用户名">
          <Input value={user?.username} disabled />
        </Form.Item>

        <Form.Item
          name="email"
          label="邮箱"
          rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
        >
          <Input placeholder="请输入邮箱" />
        </Form.Item>

        <Form.Item name="phone" label="手机">
          <Input placeholder="请输入手机号码" />
        </Form.Item>

        <Form.Item
          name="user_level"
          label="用户水平"
          rules={[{ required: true, message: '请选择用户水平' }]}
        >
          <Select
            placeholder="请选择"
            options={USER_LEVELS.map((level) => ({
              label: level,
              value: level,
            }))}
          />
        </Form.Item>

        <Form.Item name="fishing_experience_years" label="钓龄（年）">
          <InputNumber min={0} max={100} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="preferred_fish" label="喜欢鱼种">
          <Input placeholder="多个鱼种用逗号分隔，如：鲈鱼,黑鱼,翘嘴" />
        </Form.Item>

        <Form.Item name="preferred_scenarios" label="偏好钓法">
          <Select
            mode="multiple"
            placeholder="请选择"
            options={FISHING_METHODS.map((method) => ({
              label: method,
              value: method,
            }))}
            onChange={(values) => {
              form.setFieldValue('preferred_scenarios', values.join(','))
            }}
          />
        </Form.Item>
      </Form>
    </Drawer>
  )
}

export default UserEditDrawer
