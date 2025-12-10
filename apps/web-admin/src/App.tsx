import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider } from 'react-redux'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { store } from '@/store/store'
import { getToken } from '@/utils/auth'
import MainLayout from '@/components/Layout/MainLayout'
import Login from '@/pages/Login'
import EquipmentList from '@/pages/Equipment/List'
import EquipmentForm from '@/pages/Equipment/Form'

// 路由守卫组件
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = getToken()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

// 占位页面组件
const PlaceholderPage = ({ title }: { title: string }) => (
  <div style={{ textAlign: 'center', padding: '50px' }}>
    <h2>{title}</h2>
    <p style={{ color: '#999' }}>功能开发中...</p>
  </div>
)

const App = () => {
  return (
    <Provider store={store}>
      <ConfigProvider locale={zhCN}>
        <BrowserRouter>
          <Routes>
            {/* 登录页面 */}
            <Route path="/login" element={<Login />} />

            {/* 需要登录的页面 */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <MainLayout />
                </PrivateRoute>
              }
            >
              {/* 默认重定向到装备管理 */}
              <Route index element={<Navigate to="/equipment" replace />} />

              {/* 装备管理 */}
              <Route path="equipment" element={<EquipmentList />} />
              <Route path="equipment/create" element={<EquipmentForm />} />
              <Route path="equipment/edit/:id" element={<EquipmentForm />} />

              {/* 用户管理 - 占位 */}
              <Route path="users" element={<PlaceholderPage title="用户管理" />} />

              {/* 爬虫管理 - 占位 */}
              <Route path="crawler" element={<PlaceholderPage title="爬虫管理" />} />

              {/* 系统监控 - 占位 */}
              <Route path="monitor" element={<PlaceholderPage title="系统监控" />} />

              {/* 数据分析 - 占位 */}
              <Route path="analytics" element={<PlaceholderPage title="数据分析" />} />

              {/* 配置管理 - 占位 */}
              <Route path="settings" element={<PlaceholderPage title="配置管理" />} />
            </Route>

            {/* 404 重定向 */}
            <Route path="*" element={<Navigate to="/equipment" replace />} />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </Provider>
  )
}

export default App
