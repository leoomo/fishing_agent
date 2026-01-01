import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom'
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
const EquipmentBatchCreate = lazy(() => import('@/pages/Equipment/BatchCreate'))
const UserList = lazy(() => import('@/pages/Users/List'))
const UserDetail = lazy(() => import('@/pages/Users/Detail'))
const Analytics = lazy(() => import('@/pages/Analytics'))
const Settings = lazy(() => import('@/pages/Settings'))
const EquipmentOptions = lazy(() => import('@/pages/Settings/EquipmentOptions'))
const Monitor = lazy(() => import('@/pages/Monitor'))
const DataWorkflow = lazy(() => import('@/pages/DataWorkflow'))

// Content Management - Articles
const ArticleList = lazy(() => import('@/pages/Content/Articles/List'))
const ArticleEditor = lazy(() => import('@/pages/Content/Articles/Editor'))

// Content Management - Rigs
const RigList = lazy(() => import('@/pages/Content/Rigs'))

// Content Management - Lure Types
const LureTypeList = lazy(() => import('@/pages/Content/LureTypes'))

// 加载中组件
const PageLoading = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    minHeight: '200px'
  }}>
    <Spin size="large" />
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

// 创建路由配置
const router = createBrowserRouter(
  [
    {
      path: '/login',
      element: (
        <Suspense fallback={<PageLoading />}>
          <Login />
        </Suspense>
      ),
    },
    {
      path: '/',
      element: (
        <PrivateRoute>
          <MainLayout />
        </PrivateRoute>
      ),
      children: [
        { index: true, element: <Navigate to="/equipment" replace /> },
        // Equipment Management
        {
          path: 'equipment',
          element: (
            <Suspense fallback={<PageLoading />}>
              <EquipmentList />
            </Suspense>
          ),
        },
        {
          path: 'equipment/create',
          element: (
            <Suspense fallback={<PageLoading />}>
              <EquipmentForm />
            </Suspense>
          ),
        },
        {
          path: 'equipment/batch-create',
          element: (
            <Suspense fallback={<PageLoading />}>
              <EquipmentBatchCreate />
            </Suspense>
          ),
        },
        {
          path: 'equipment/edit/:id',
          element: (
            <Suspense fallback={<PageLoading />}>
              <EquipmentForm />
            </Suspense>
          ),
        },
        // User Management
        {
          path: 'users',
          element: (
            <Suspense fallback={<PageLoading />}>
              <UserList />
            </Suspense>
          ),
        },
        {
          path: 'users/:id',
          element: (
            <Suspense fallback={<PageLoading />}>
              <UserDetail />
            </Suspense>
          ),
        },
        // Content Management - Articles
        {
          path: 'content/articles',
          element: (
            <Suspense fallback={<PageLoading />}>
              <ArticleList />
            </Suspense>
          ),
        },
        {
          path: 'content/articles/create',
          element: (
            <Suspense fallback={<PageLoading />}>
              <ArticleEditor />
            </Suspense>
          ),
        },
        {
          path: 'content/articles/edit/:id',
          element: (
            <Suspense fallback={<PageLoading />}>
              <ArticleEditor />
            </Suspense>
          ),
        },
        // Content Management - Rigs
        {
          path: 'content/rigs',
          element: (
            <Suspense fallback={<PageLoading />}>
              <RigList />
            </Suspense>
          ),
        },
        // Content Management - Lure Types
        {
          path: 'content/lure-types',
          element: (
            <Suspense fallback={<PageLoading />}>
              <LureTypeList />
            </Suspense>
          ),
        },
        // Content Management - Placeholders
        { path: 'content/fish', element: <ContentPlaceholder title="鱼类百科" /> },
        { path: 'content/accessories', element: <ContentPlaceholder title="钓鱼配件" /> },
        // Data Workflow
        {
          path: 'data-workflow',
          element: (
            <Suspense fallback={<PageLoading />}>
              <DataWorkflow />
            </Suspense>
          ),
        },
        // System Monitor
        {
          path: 'monitor',
          element: (
            <Suspense fallback={<PageLoading />}>
              <Monitor />
            </Suspense>
          ),
        },
        // Analytics
        {
          path: 'analytics',
          element: (
            <Suspense fallback={<PageLoading />}>
              <Analytics />
            </Suspense>
          ),
        },
        // Settings
        {
          path: 'settings',
          element: (
            <Suspense fallback={<PageLoading />}>
              <Settings />
            </Suspense>
          ),
        },
        {
          path: 'settings/equipment-options',
          element: (
            <Suspense fallback={<PageLoading />}>
              <EquipmentOptions />
            </Suspense>
          ),
        },
      ],
    },
    // 404 redirect
    { path: '*', element: <Navigate to="/equipment" replace /> },
  ],
  {
    future: {
      v7_relativeSplatPath: true,
      v7_startTransition: true,
      v7_fetcherPersist: true,
      v7_normalizeFormMethod: true,
      v7_partialHydration: true,
      v7_skipActionErrorRevalidation: true,
    },
  }
)

const App = () => {
  return (
    <Provider store={store}>
      <ConfigProvider locale={zhCN}>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </ConfigProvider>
    </Provider>
  )
}

export default App
