import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider } from 'react-redux'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { Suspense, lazy } from 'react'
import { store } from '@/store/store'
import { getToken } from '@/utils/auth'
import MainLayout from '@/components/Layout/MainLayout'

// 懒加载页面组件（代码分割优化）
const Login = lazy(() => import('@/pages/Login'))
const EquipmentList = lazy(() => import('@/pages/Equipment/List'))
const EquipmentForm = lazy(() => import('@/pages/Equipment/Form'))
const UserList = lazy(() => import('@/pages/Users/List'))
const UserDetail = lazy(() => import('@/pages/Users/Detail'))
const Analytics = lazy(() => import('@/pages/Analytics'))
const Settings = lazy(() => import('@/pages/Settings'))
const Crawler = lazy(() => import('@/pages/Crawler'))
const Monitor = lazy(() => import('@/pages/Monitor'))
const Workflow = lazy(() => import('@/pages/Workflow'))

// 加载中组件
const PageLoading = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    minHeight: '200px'
  }}>
    <Spin size="large" tip="Loading..." />
  </div>
)

// 路由守卫组件
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = getToken()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

// 内容管理占位页面（Phase 6-8 后续扩展）
const ContentPlaceholder = ({ title }: { title: string }) => (
  <div style={{ textAlign: 'center', padding: '50px' }}>
    <h2>{title}</h2>
    <p style={{ color: '#999' }}>Developing...</p>
  </div>
)

const App = () => {
  return (
    <Provider store={store}>
      <ConfigProvider locale={zhCN}>
        <BrowserRouter>
          <Suspense fallback={<PageLoading />}>
            <Routes>
              {/* Login page */}
              <Route path="/login" element={<Login />} />

              {/* Protected routes */}
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <MainLayout />
                  </PrivateRoute>
                }
              >
                {/* Default redirect to equipment */}
                <Route index element={<Navigate to="/equipment" replace />} />

                {/* Equipment Management */}
                <Route path="equipment" element={<EquipmentList />} />
                <Route path="equipment/create" element={<EquipmentForm />} />
                <Route path="equipment/edit/:id" element={<EquipmentForm />} />

                {/* User Management */}
                <Route path="users" element={<UserList />} />
                <Route path="users/:id" element={<UserDetail />} />

                {/* Content Management - Placeholders */}
                <Route path="content/fish" element={<ContentPlaceholder title="Fish Management" />} />
                <Route path="content/rigs" element={<ContentPlaceholder title="Rig Management" />} />
                <Route path="content/lures" element={<ContentPlaceholder title="Lure Management" />} />

                {/* Crawler Management */}
                <Route path="crawler" element={<Crawler />} />

                {/* Workflow Management */}
                <Route path="workflow/*" element={<Workflow />} />

                {/* System Monitor */}
                <Route path="monitor" element={<Monitor />} />

                {/* Analytics */}
                <Route path="analytics" element={<Analytics />} />

                {/* Settings */}
                <Route path="settings" element={<Settings />} />
              </Route>

              {/* 404 redirect */}
              <Route path="*" element={<Navigate to="/equipment" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ConfigProvider>
    </Provider>
  )
}

export default App
