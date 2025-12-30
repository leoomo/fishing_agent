import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, message } from 'antd'
import {
  DatabaseOutlined,
  UserOutlined,
  FileTextOutlined,
  MonitorOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons'
import { useDispatch } from 'react-redux'
import { logout } from '@/store/slices/authSlice'
import { getUserInfo } from '@/utils/auth'

const { Header, Sider, Content } = Layout

const MainLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const [collapsed, setCollapsed] = useState(false)
  const userInfo = getUserInfo()

  const menuItems = [
    {
      key: '/equipment',
      icon: <DatabaseOutlined />,
      label: '装备管理',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/content',
      icon: <FileTextOutlined />,
      label: '内容管理',
      children: [
        { key: '/content/fish', label: '鱼类管理' },
        { key: '/content/rigs', label: '钓组管理' },
        { key: '/content/lures', label: '拟饵管理' },
      ],
    },
    {
      key: '/data-workflow',
      icon: <NodeIndexOutlined />,
      label: '数据工作流',
    },
    {
      key: '/monitor',
      icon: <MonitorOutlined />,
      label: '系统监控',
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: '数据分析',
    },
    {
      key: 'settings-menu',
      icon: <SettingOutlined />,
      label: '配置管理',
      children: [
        { key: '/settings', label: 'API 配置' },
        { key: '/settings/equipment-options', label: '装备属性选项' },
      ],
    },
  ]

  const handleLogout = () => {
    dispatch(logout())
    message.success('已退出登录')
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      label: '个人信息',
      icon: <UserOutlined />,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{
          height: 32,
          margin: 16,
          textAlign: 'center',
          color: '#fff',
          fontSize: collapsed ? 14 : 16,
          fontWeight: 600
        }}>
          {collapsed ? '🎣' : '🎣 钓鱼助手'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ margin: 0 }}>管理后台</h2>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span style={{ marginLeft: 8 }}>{userInfo?.username || 'Admin'}</span>
            </div>
          </Dropdown>
        </Header>

        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
