# Phase 6-8: 前端开发详细方案

**目标**: 构建完整的 Web 管理后台前端
**周期**: 第 8-10 周（15 个工作日）
**优先级**: P1（核心功能）

---

## 目标概述

使用 React + TypeScript + Ant Design Pro 构建生产级管理后台，涵盖所有 7 大功能模块。

**技术栈**:
- React 18 + TypeScript
- Ant Design Pro 组件库
- Redux Toolkit 状态管理
- React Router v6 路由
- Axios HTTP 客户端
- ECharts 数据可视化
- Vite 构建工具

---

## Week 8: 基础架构 + 装备管理（Day 1-5）

### Step 1: 项目初始化（Day 1）

#### 1.1 创建项目

```bash
# 进入项目根目录
cd /Users/zen/projects/fishing_agent

# 创建前端应用目录
mkdir -p apps/web-admin
cd apps/web-admin

# 使用 Vite 创建 React + TypeScript 项目
npm create vite@latest . -- --template react-ts

# 安装依赖
npm install

# 安装 Ant Design Pro 及相关依赖
npm install antd @ant-design/pro-components
npm install axios @reduxjs/toolkit react-redux react-router-dom
npm install echarts echarts-for-react
npm install @monaco-editor/react  # 代码编辑器（配置管理用）
npm install dayjs  # 日期处理

# 安装开发依赖
npm install -D @types/node
npm install -D tailwindcss postcss autoprefixer  # 可选：TailwindCSS
```

#### 1.2 配置项目

**文件**: `apps/web-admin/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**文件**: `apps/web-admin/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### 1.3 创建项目结构

```bash
cd src
mkdir -p api components pages store utils types

# 创建目录结构
mkdir -p pages/{Login,Equipment,Users,Content,Crawler,Monitor,Analytics,Settings}
mkdir -p components/{Layout,Equipment,Common}
mkdir -p store/slices
mkdir -p api/{client,services}
```

**目录结构**:
```
src/
├── api/                    # API 客户端
│   ├── client.ts          # Axios 实例 + 拦截器
│   └── services/          # API 服务封装
│       ├── auth.ts
│       ├── equipment.ts
│       ├── users.ts
│       └── ...
├── components/            # 通用组件
│   ├── Layout/           # 布局组件
│   ├── Equipment/        # 装备相关组件
│   └── Common/           # 通用组件
├── pages/                # 页面组件
│   ├── Login/
│   ├── Equipment/
│   └── ...
├── store/                # Redux 状态管理
│   ├── store.ts
│   └── slices/
├── utils/                # 工具函数
│   ├── auth.ts           # Token 管理
│   └── request.ts        # 请求封装
├── types/                # TypeScript 类型定义
│   ├── equipment.ts
│   └── api.ts
├── App.tsx
└── main.tsx
```

---

### Step 2: API 客户端封装（Day 1）

#### 2.1 创建 Axios 客户端

**文件**: `src/api/client.ts`

```typescript
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import { getToken, clearToken } from '@/utils/auth'

// 创建 axios 实例
const client: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：添加 token
client.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
client.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    // 401: token 过期或无效
    if (error.response?.status === 401) {
      message.error('登录已过期，请重新登录')
      clearToken()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // 403: 权限不足
    if (error.response?.status === 403) {
      message.error('权限不足')
      return Promise.reject(error)
    }

    // 500: 服务器错误
    if (error.response?.status >= 500) {
      message.error('服务器错误，请稍后重试')
      return Promise.reject(error)
    }

    // 其他错误
    const errorMessage = error.response?.data?.detail || error.message
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

export default client
```

#### 2.2 创建认证 API

**文件**: `src/api/services/auth.ts`

```typescript
import client from '../client'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user_info: {
    user_id: number
    username: string
    role: string
    email?: string
  }
}

export const authApi = {
  // 登录
  login: (data: LoginRequest): Promise<LoginResponse> => {
    return client.post('/auth/login', data)
  },

  // 刷新 token（可选）
  refreshToken: (): Promise<LoginResponse> => {
    return client.post('/auth/refresh')
  },
}
```

#### 2.3 创建装备 API

**文件**: `src/api/services/equipment.ts`

```typescript
import client from '../client'
import { Equipment, EquipmentListResponse, Brand } from '@/types/equipment'

export interface EquipmentCreateRequest {
  name: string
  category: string
  brand_id: number
  model?: string
  price_min?: number
  price_max?: number
  description?: string
  features?: string
  user_level: string
  specs?: any
}

export const equipmentApi = {
  // 查询装备列表
  list: (params: {
    page: number
    page_size: number
    category?: string
    brand_id?: number
    keyword?: string
  }): Promise<EquipmentListResponse> => {
    return client.get('/admin/equipment', { params })
  },

  // 获取装备详情
  get: (id: number): Promise<Equipment> => {
    return client.get(`/admin/equipment/${id}`)
  },

  // 创建装备
  create: (data: EquipmentCreateRequest): Promise<Equipment> => {
    return client.post('/admin/equipment', data)
  },

  // 更新装备
  update: (id: number, data: Partial<EquipmentCreateRequest>): Promise<Equipment> => {
    return client.put(`/admin/equipment/${id}`, data)
  },

  // 删除装备
  delete: (id: number): Promise<void> => {
    return client.delete(`/admin/equipment/${id}`)
  },

  // 查询品牌列表
  listBrands: (): Promise<Brand[]> => {
    return client.get('/admin/brands')
  },

  // 创建品牌
  createBrand: (data: { name_cn: string; name_en?: string }): Promise<Brand> => {
    return client.post('/admin/brands', data)
  },

  // 导出 CSV
  exportCSV: (params: { category?: string }): Promise<Blob> => {
    return client.get('/admin/import-export/export/csv', {
      params,
      responseType: 'blob',
    })
  },

  // 导入 CSV
  importCSV: (file: File): Promise<any> => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/admin/import-export/import/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
```

#### 2.4 创建 Token 管理工具

**文件**: `src/utils/auth.ts`

```typescript
const TOKEN_KEY = 'fishing_admin_token'
const USER_KEY = 'fishing_admin_user'

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const getUserInfo = (): any => {
  const userStr = localStorage.getItem(USER_KEY)
  return userStr ? JSON.parse(userStr) : null
}

export const setUserInfo = (user: any): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export const isAuthenticated = (): boolean => {
  return !!getToken()
}
```

---

### Step 3: Redux 状态管理（Day 2）

#### 3.1 创建 Store

**文件**: `src/store/store.ts`

```typescript
import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import equipmentReducer from './slices/equipmentSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    equipment: equipmentReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
```

#### 3.2 创建认证 Slice

**文件**: `src/store/slices/authSlice.ts`

```typescript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { authApi, LoginRequest } from '@/api/services/auth'
import { setToken, setUserInfo, clearToken } from '@/utils/auth'

interface AuthState {
  isAuthenticated: boolean
  user: any | null
  loading: boolean
  error: string | null
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  loading: false,
  error: null,
}

// 异步登录
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await authApi.login(credentials)
      setToken(response.access_token)
      setUserInfo(response.user_info)
      return response
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || '登录失败')
    }
  }
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      clearToken()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user_info
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { logout } = authSlice.actions
export default authSlice.reducer
```

#### 3.3 创建装备 Slice

**文件**: `src/store/slices/equipmentSlice.ts`

```typescript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { equipmentApi } from '@/api/services/equipment'
import { Equipment, Brand } from '@/types/equipment'

interface EquipmentState {
  list: Equipment[]
  total: number
  loading: boolean
  brands: Brand[]
  currentEquipment: Equipment | null
}

const initialState: EquipmentState = {
  list: [],
  total: 0,
  loading: false,
  brands: [],
  currentEquipment: null,
}

// 异步获取装备列表
export const fetchEquipmentList = createAsyncThunk(
  'equipment/fetchList',
  async (params: { page: number; page_size: number; category?: string }) => {
    const response = await equipmentApi.list(params)
    return response
  }
)

// 异步获取品牌列表
export const fetchBrandList = createAsyncThunk(
  'equipment/fetchBrands',
  async () => {
    const response = await equipmentApi.listBrands()
    return response
  }
)

const equipmentSlice = createSlice({
  name: 'equipment',
  initialState,
  reducers: {
    setCurrentEquipment: (state, action) => {
      state.currentEquipment = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchEquipmentList.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchEquipmentList.fulfilled, (state, action) => {
        state.loading = false
        state.list = action.payload.items
        state.total = action.payload.total
      })
      .addCase(fetchEquipmentList.rejected, (state) => {
        state.loading = false
      })
      .addCase(fetchBrandList.fulfilled, (state, action) => {
        state.brands = action.payload
      })
  },
})

export const { setCurrentEquipment } = equipmentSlice.actions
export default equipmentSlice.reducer
```

---

### Step 4: 登录页面（Day 2）

**文件**: `src/pages/Login/index.tsx`

```typescript
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { login } from '@/store/slices/authSlice'
import { AppDispatch } from '@/store/store'
import './index.css'

const Login: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      await dispatch(login(values)).unwrap()
      message.success('登录成功')
      navigate('/equipment')
    } catch (error: any) {
      message.error(error || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <Card className="login-card" title="智能钓鱼助手 - 管理后台">
        <Form
          name="login"
          initialValues={{ username: '', password: '' }}
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
      </Card>
    </div>
  )
}

export default Login
```

**文件**: `src/pages/Login/index.css`

```css
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.login-card .ant-card-head-title {
  text-align: center;
  font-size: 20px;
  font-weight: 600;
}
```

---

### Step 5: 布局组件（Day 3）

#### 5.1 创建主布局

**文件**: `src/components/Layout/MainLayout.tsx`

```typescript
import React, { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, message } from 'antd'
import {
  DashboardOutlined,
  DatabaseOutlined,
  UserOutlined,
  FileTextOutlined,
  RobotOutlined,
  MonitorOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { useDispatch } from 'react-redux'
import { logout } from '@/store/slices/authSlice'
import { getUserInfo } from '@/utils/auth'

const { Header, Sider, Content } = Layout

const MainLayout: React.FC = () => {
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
      key: '/crawler',
      icon: <RobotOutlined />,
      label: '爬虫管理',
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
      key: '/settings',
      icon: <SettingOutlined />,
      label: '配置管理',
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
        <div style={{ height: 32, margin: 16, textAlign: 'center', color: '#fff' }}>
          {collapsed ? '钓鱼' : '智能钓鱼助手'}
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
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>管理后台</h2>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span style={{ marginLeft: 8 }}>{userInfo?.username || 'Admin'}</span>
            </div>
          </Dropdown>
        </Header>

        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
```

---

### Step 6: 装备管理页面（Day 3-4）

#### 6.1 装备列表页

**文件**: `src/pages/Equipment/List.tsx`

```typescript
import React, { useEffect, useState } from 'react'
import { Table, Button, Input, Select, Space, Modal, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ExportOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import { Equipment } from '@/types/equipment'

const { Search } = Input

const EquipmentList: React.FC = () => {
  const navigate = useNavigate()
  const [data, setData] = useState<Equipment[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [category, setCategory] = useState<string>()
  const [keyword, setKeyword] = useState<string>()

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await equipmentApi.list({
        page,
        page_size: pageSize,
        category,
        keyword,
      })
      setData(response.items)
      setTotal(response.total)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [page, pageSize, category])

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个装备吗？',
      onOk: async () => {
        try {
          await equipmentApi.delete(id)
          message.success('删除成功')
          fetchData()
        } catch (error) {
          message.error('删除失败')
        }
      },
    })
  }

  const handleExport = async () => {
    try {
      const blob = await equipmentApi.exportCSV({ category })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'equipment_export.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch (error) {
      message.error('导出失败')
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'equipment_id',
      width: 80,
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 200,
    },
    {
      title: '类别',
      dataIndex: 'category',
      width: 100,
    },
    {
      title: '品牌',
      dataIndex: 'brand_name',
      width: 120,
    },
    {
      title: '型号',
      dataIndex: 'model',
      width: 120,
    },
    {
      title: '价格范围',
      width: 150,
      render: (record: Equipment) =>
        record.price_min && record.price_max
          ? `¥${record.price_min} - ¥${record.price_max}`
          : '-',
    },
    {
      title: '适用水平',
      dataIndex: 'user_level',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (active: boolean) => (active ? '启用' : '禁用'),
    },
    {
      title: '操作',
      width: 150,
      fixed: 'right' as const,
      render: (record: Equipment) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/equipment/edit/${record.equipment_id}`)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.equipment_id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Select
            placeholder="选择类别"
            style={{ width: 120 }}
            allowClear
            onChange={setCategory}
          >
            <Select.Option value="鱼竿">鱼竿</Select.Option>
            <Select.Option value="渔轮">渔轮</Select.Option>
            <Select.Option value="鱼线">鱼线</Select.Option>
            <Select.Option value="拟饵">拟饵</Select.Option>
            <Select.Option value="套装">套装</Select.Option>
          </Select>

          <Search
            placeholder="搜索装备名称"
            style={{ width: 200 }}
            onSearch={setKeyword}
          />
        </Space>

        <Space>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            导出
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/equipment/create')}
          >
            新增装备
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="equipment_id"
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (page, pageSize) => {
            setPage(page)
            setPageSize(pageSize)
          },
        }}
        scroll={{ x: 1200 }}
      />
    </div>
  )
}

export default EquipmentList
```

#### 6.2 装备表单页

**文件**: `src/pages/Equipment/Form.tsx`

```typescript
import React, { useEffect, useState } from 'react'
import { Form, Input, Select, InputNumber, Button, Card, message } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { equipmentApi } from '@/api/services/equipment'
import { Brand } from '@/types/equipment'

const { TextArea } = Input

const EquipmentForm: React.FC = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [brands, setBrands] = useState<Brand[]>([])
  const [category, setCategory] = useState<string>('鱼竿')

  useEffect(() => {
    // 加载品牌列表
    equipmentApi.listBrands().then(setBrands)

    // 编辑模式：加载装备详情
    if (id) {
      equipmentApi.get(Number(id)).then((data) => {
        form.setFieldsValue(data)
        setCategory(data.category)
      })
    }
  }, [id])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      if (id) {
        await equipmentApi.update(Number(id), values)
        message.success('更新成功')
      } else {
        await equipmentApi.create(values)
        message.success('创建成功')
      }
      navigate('/equipment')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  // 根据类别渲染不同的规格表单
  const renderSpecsForm = () => {
    switch (category) {
      case '鱼竿':
        return (
          <>
            <Form.Item label="长度（米）" name={['specs', 'length']}>
              <InputNumber min={0.5} max={10} step={0.1} />
            </Form.Item>
            <Form.Item label="调性" name={['specs', 'power']}>
              <Select>
                <Select.Option value="UL">UL</Select.Option>
                <Select.Option value="L">L</Select.Option>
                <Select.Option value="ML">ML</Select.Option>
                <Select.Option value="M">M</Select.Option>
                <Select.Option value="MH">MH</Select.Option>
                <Select.Option value="H">H</Select.Option>
                <Select.Option value="XH">XH</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item label="动作" name={['specs', 'action']}>
              <Select>
                <Select.Option value="Fast">Fast</Select.Option>
                <Select.Option value="Medium">Medium</Select.Option>
                <Select.Option value="Slow">Slow</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item label="适用饵重（克）">
              <Input.Group compact>
                <Form.Item name={['specs', 'lure_weight_min']} noStyle>
                  <InputNumber placeholder="最小" min={0} style={{ width: '50%' }} />
                </Form.Item>
                <Form.Item name={['specs', 'lure_weight_max']} noStyle>
                  <InputNumber placeholder="最大" min={0} style={{ width: '50%' }} />
                </Form.Item>
              </Input.Group>
            </Form.Item>
          </>
        )
      // 其他类别类似...
      default:
        return null
    }
  }

  return (
    <Card title={id ? '编辑装备' : '新增装备'}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{ user_level: '新手', is_active: true }}
      >
        <Form.Item
          label="装备名称"
          name="name"
          rules={[{ required: true, message: '请输入装备名称' }]}
        >
          <Input placeholder="请输入装备名称" />
        </Form.Item>

        <Form.Item
          label="类别"
          name="category"
          rules={[{ required: true, message: '请选择类别' }]}
        >
          <Select onChange={setCategory}>
            <Select.Option value="鱼竿">鱼竿</Select.Option>
            <Select.Option value="渔轮">渔轮</Select.Option>
            <Select.Option value="鱼线">鱼线</Select.Option>
            <Select.Option value="拟饵">拟饵</Select.Option>
            <Select.Option value="套装">套装</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="品牌"
          name="brand_id"
          rules={[{ required: true, message: '请选择品牌' }]}
        >
          <Select placeholder="请选择品牌">
            {brands.map((brand) => (
              <Select.Option key={brand.brand_id} value={brand.brand_id}>
                {brand.name_cn}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item label="型号" name="model">
          <Input placeholder="请输入型号" />
        </Form.Item>

        <Form.Item label="价格范围（元）">
          <Input.Group compact>
            <Form.Item name="price_min" noStyle>
              <InputNumber placeholder="最低价" min={0} style={{ width: '50%' }} />
            </Form.Item>
            <Form.Item name="price_max" noStyle>
              <InputNumber placeholder="最高价" min={0} style={{ width: '50%' }} />
            </Form.Item>
          </Input.Group>
        </Form.Item>

        <Form.Item label="描述" name="description">
          <TextArea rows={4} placeholder="请输入装备描述" />
        </Form.Item>

        <Form.Item label="特点" name="features">
          <TextArea rows={3} placeholder="请输入装备特点" />
        </Form.Item>

        <Form.Item label="适用水平" name="user_level">
          <Select>
            <Select.Option value="新手">新手</Select.Option>
            <Select.Option value="进阶">进阶</Select.Option>
            <Select.Option value="高手">高手</Select.Option>
          </Select>
        </Form.Item>

        {/* 规格表单（动态） */}
        <Card title="规格信息" style={{ marginBottom: 16 }}>
          {renderSpecsForm()}
        </Card>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={() => navigate('/equipment')}>
            取消
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default EquipmentForm
```

---

### Step 7: 路由配置（Day 5）

**文件**: `src/App.tsx`

```typescript
import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider } from 'react-redux'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { store } from './store/store'
import { isAuthenticated } from './utils/auth'

// 页面组件
import Login from './pages/Login'
import MainLayout from './components/Layout/MainLayout'
import EquipmentList from './pages/Equipment/List'
import EquipmentForm from './pages/Equipment/Form'

// 权限路由
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" />
}

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ConfigProvider locale={zhCN}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route
              path="/"
              element={
                <PrivateRoute>
                  <MainLayout />
                </PrivateRoute>
              }
            >
              <Route index element={<Navigate to="/equipment" />} />
              <Route path="equipment" element={<EquipmentList />} />
              <Route path="equipment/create" element={<EquipmentForm />} />
              <Route path="equipment/edit/:id" element={<EquipmentForm />} />

              {/* 其他模块路由将在后续添加 */}
            </Route>
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </Provider>
  )
}

export default App
```

**文件**: `src/main.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

---

## Week 9-10: 其他模块（Day 6-15）

由于篇幅限制，其他模块（用户管理、内容管理、爬虫管理、监控、分析、配置）的实现类似装备管理，遵循以下模式：

1. **创建 API 服务** (`src/api/services/xxx.ts`)
2. **创建 Redux Slice**（如需要）
3. **创建列表页** (`src/pages/Xxx/List.tsx`)
4. **创建表单页** (`src/pages/Xxx/Form.tsx`)
5. **添加路由** (`src/App.tsx`)

关键实现：
- **WebSocket 集成**（爬虫进度、实时监控）
- **ECharts 图表**（数据分析可视化）
- **Monaco Editor**（配置编辑）

---

## 测试用例

```bash
# 启动开发服务器
cd apps/web-admin
npm run dev

# 访问
open http://localhost:5173

# 测试流程:
# 1. 登录（admin/admin123）
# 2. 装备列表查看
# 3. 创建装备
# 4. 编辑装备
# 5. 删除装备
# 6. 导出 CSV
```

---

## 注意事项

### 1. 权限控制

```typescript
// 根据用户角色显示/隐藏按钮
const userInfo = getUserInfo()

{userInfo?.role === 'admin' && (
  <Button danger onClick={handleDelete}>删除</Button>
)}
```

### 2. 错误处理

```typescript
// 统一错误处理在 axios 拦截器中
// 页面只需 try-catch 显示提示
```

### 3. 性能优化

```typescript
// 列表分页加载
// 图表按需加载（React.lazy）
// 防抖搜索
```

---

## 验收标准

### 必须完成

- ✅ 登录页和认证流程
- ✅ 装备管理完整功能
- ✅ 用户管理页面
- ✅ 内容管理页面
- ✅ 爬虫管理 + WebSocket
- ✅ 监控仪表板 + 图表
- ✅ 数据分析页面
- ✅ 配置管理页面
- ✅ 响应式布局

---

## 下一步

完成 Phase 6-8 后，进入 **Phase 9: 测试与优化**
