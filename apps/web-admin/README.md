# 智能钓鱼助手 - React管理前端 v5.0.0

基于现代技术栈的钓鱼助手管理界面，提供装备管理、数据分析、系统配置等功能。

> 🎯 **当前版本**: v5.0.0
> 📱 **前端地址**: http://localhost:5174
> 🔗 **API后端**: http://localhost:8000

## 🚀 技术栈

### 核心框架
- **React 19.2.0**: 最新版本的React框架，支持并发特性
- **TypeScript ~5.9.3**: 类型安全的JavaScript超集
- **Vite 7.2.4**: 现代化的前端构建工具，提供极速的开发体验

### UI组件库
- **Ant Design 5.22.0**: 企业级UI组件库
- **Ant Design Pro**: 高级中后台前端解决方案
- **@ant-design/icons 5.4.0**: Ant Design图标库

### 状态管理和路由
- **@reduxjs/toolkit 2.2.7**: Redux状态管理工具
- **react-router-dom 6.28.0**: React路由管理

### 数据可视化
- **echarts 5.5.0**: 强大的数据可视化图表库
- **echarts-for-react**: ECharts的React封装

### 开发工具
- **ESLint**: 代码质量检查和格式化
- **@vitejs/plugin-react-swc**: 使用SWC的快速刷新

## 📦 安装和运行

### 环境要求
- Node.js 18+
- npm 或 yarn

### 安装依赖
```bash
# 进入前端目录
cd apps/web-admin

# 安装依赖
npm install
```

### 开发模式
```bash
# 启动开发服务器
npm run dev

# 访问地址
# 前端: http://localhost:5174
# 后端API: http://localhost:8000
```

### 生产构建
```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 🏗️ 项目结构

```
apps/web-admin/
├── src/                      # 源代码
│   ├── components/           # 通用组件
│   │   ├── Layout/          # 布局组件
│   │   ├── Charts/          # 图表组件
│   │   └── Common/          # 通用组件
│   ├── pages/               # 页面组件
│   │   ├── Login/           # 登录页面
│   │   ├── Dashboard/       # 仪表盘
│   │   ├── Equipment/       # 装备管理
│   │   ├── Analytics/       # 数据分析
│   │   ├── Config/          # 配置管理
│   │   ├── Crawler/         # 爬虫管理
│   │   └── Monitor/         # 系统监控
│   ├── services/            # API服务
│   │   ├── api.ts           # API基础配置
│   │   ├── auth.ts          # 认证服务
│   │   ├── equipment.ts     # 装备管理服务
│   │   ├── analytics.ts     # 数据分析服务
│   │   └── config.ts        # 配置管理服务
│   ├── store/               # Redux状态管理
│   │   ├── index.ts         # Store配置
│   │   ├── authSlice.ts     # 认证状态
│   │   └── userSlice.ts     # 用户状态
│   ├── utils/               # 工具函数
│   │   ├── auth.ts          # 认证工具
│   │   ├── request.ts       # 请求封装
│   │   └── constants.ts     # 常量定义
│   ├── types/               # TypeScript类型定义
│   │   ├── auth.ts          # 认证相关类型
│   │   ├── equipment.ts     # 装备相关类型
│   │   └── api.ts           # API通用类型
│   ├── hooks/               # 自定义Hooks
│   ├── App.tsx              # 应用根组件
│   └── main.tsx             # 应用入口
├── public/                  # 静态资源
├── package.json             # 项目配置
├── tsconfig.json            # TypeScript配置
├── vite.config.ts           # Vite构建配置
└── README.md                # 本文档
```

## 🔐 认证流程

1. 用户访问登录页面 (`/login`)
2. 输入用户名和密码
3. 调用登录API获取JWT Token
4. Token存储在localStorage中
5. 自动在请求头中添加Token (`Authorization: Bearer <token>`)
6. Token过期时自动跳转到登录页

## 📊 功能模块

### 1. 装备管理 (Equipment Management)
- **装备列表**: 展示所有装备信息（17条装备数据）
- **装备分类**: 按鱼竿、渔轮、鱼线、鱼饵等分类
- **装备搜索**: 支持按名称、品牌、价格搜索
- **装备详情**: 查看装备详细信息和参数
- **装备操作**: 添加、编辑、删除装备

### 2. 数据分析 (Analytics)
- **装备统计**: 装备总量、分类统计、价格分布
- **趋势分析**: 按月统计装备增长趋势
- **品牌排行**: Top N品牌统计和市场占有率
- **用户行为**: 用户活跃度和购买行为分析
- **报表导出**: 支持PDF和Excel格式导出

### 3. 系统配置 (Configuration)
- **API密钥管理**: 安全存储和管理各类API密钥
- **系统参数**: 配置系统运行参数
- **密钥测试**: 在线测试API密钥有效性
- **配置历史**: 查看配置更新历史

### 4. 爬虫管理 (Crawler Management)
- **任务列表**: 查看所有爬虫任务
- **任务触发**: 手动触发爬虫任务
- **进度监控**: 实时查看爬虫进度
- **数据同步**: 查看数据同步状态

### 5. 系统监控 (Monitor)
- **API统计**: 调用量、响应时间、错误率
- **LLM统计**: Token消耗、成本统计
- **数据库监控**: 查询时间、连接池状态
- **系统健康**: 服务状态检查

## 🔧 开发指南

### 环境变量配置
创建 `.env` 文件：
```bash
# API地址
VITE_API_BASE_URL=http://localhost:8000

# 应用标题
VITE_APP_TITLE=智能钓鱼助手管理后台

# 是否启用Mock数据
VITE_USE_MOCK=false
```

### API请求封装
使用 `src/utils/request.ts` 统一处理API请求：
```typescript
import { request } from '@/utils/request';

// GET请求
const data = await request.get('/api/v1/admin/equipment/list');

// POST请求
const result = await request.post('/api/v1/admin/equipment/create', {
  name: '新装备',
  category: '鱼竿'
});
```

### 状态管理
使用Redux Toolkit管理状态：
```typescript
import { useAppDispatch, useAppSelector } from '@/store';

// 派发action
const dispatch = useAppDispatch();
dispatch(updateUserInfo(userInfo));

// 获取状态
const { user } = useAppSelector(state => state.auth);
```

## 🚀 部署

### Docker部署
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx配置
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 更新日志

### v5.0.0 (2025-12-11)
- ✅ 完成React管理前端初始版本
- ✅ 实现装备管理功能（17条装备数据展示）
- ✅ 集成数据分析报表模块
- ✅ 完成系统配置管理功能
- ✅ 实现用户认证和权限控制
- ✅ 完成前后端分离架构
- ✅ 支持独立部署

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

MIT License

---

> 🎣 智能钓鱼，管理更轻松！
>
> 如有问题，请查看 [项目文档](../../../README.md) 或提交 Issue。