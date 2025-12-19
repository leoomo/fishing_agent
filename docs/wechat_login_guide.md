# 微信登录功能使用指南

## 功能概述

本功能为智能钓鱼助手小程序集成了微信登录能力，用户可以使用微信账号快速登录系统。

## 功能特性

- ✅ 微信小程序快速登录
- ✅ 自动创建用户账号（可配置）
- ✅ 微信账号绑定功能
- ✅ JWT Token认证
- ✅ 用户信息同步（昵称、头像等）
- ✅ 安全的会话管理

## 后端配置

### 1. 环境变量配置

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# ========== 微信小程序配置 ==========
# 微信小程序 AppID (必需，从微信公众平台获取)
WECHAT_APPID=your-wechat-appid-here

# 微信小程序 AppSecret (必需，从微信公众平台获取)
WECHAT_SECRET=your-wechat-secret-here

# 微信API服务器地址 (可选，默认为官方地址)
WECHAT_API_URL=https://api.weixin.qq.com

# 是否自动创建新用户 (可选，默认为 true)
WECHAT_AUTO_CREATE_USER=true

# 微信用户默认角色 (可选，默认为 readonly)
WECHAT_DEFAULT_ROLE=readonly
```

### 2. 获取微信小程序凭证

1. 登录[微信公众平台](https://mp.weixin.qq.com/)
2. 选择你的小程序
3. 在"开发"->"开发管理"->"开发设置"中获取：
   - AppID（小程序ID）
   - AppSecret（小程序密钥）

### 3. 数据库迁移

运行微信登录相关的数据库迁移：

```bash
# 运行测试脚本（包含迁移）
uv run python scripts/test_wechat_login.py

# 或者手动运行迁移
uv run python -c "
from packages.agent_fishing.tools.lure.migrations_wechat import run_wechat_migrations
from packages.agent_fishing.tools.lure.database import get_db
import sqlite3

conn = sqlite3.connect(get_db().get_database_path())
run_wechat_migrations(conn)
conn.commit()
"
```

### 4. 启动后端服务

```bash
# 启动API服务器
uv run uvicorn apps.api.main:app --reload
```

## 前端配置

### 1. 配置小程序AppID

编辑 `fishing_agent_app/fishing_agent/manifest.json`：

```json
{
  "mp-weixin" : {
    "appid" : "你的微信小程序AppID",
    "setting" : {
      "urlCheck" : false,
      "es6" : true,
      "minified" : true
    },
    "usingComponents" : true,
    "permission" : {
      "scope.userInfo" : {
        "desc" : "用于获取用户昵称、头像进行登录"
      }
    }
  }
}
```

### 2. 前端代码说明

前端登录页面已经实现了微信登录功能，位于 `fishing_agent_app/fishing_agent/pages/login/login.vue`。

主要功能包括：
- 微信小程序环境自动检测
- 获取微信用户信息（昵称、头像）
- 调用后端微信登录API
- Token管理和状态保持

## API接口

### 1. 微信登录

```http
POST /api/v1/auth/wechat/login
Content-Type: application/json

{
  "code": "031Kc1002CqHL31hR0002VvLTK3Kc10g",
  "nickname": "微信用户昵称",
  "avatar_url": "https://thirdwx.qlogo.cn/...",
  "gender": 1,
  "city": "深圳",
  "province": "广东",
  "country": "中国",
  "language": "zh_CN"
}
```

**响应示例：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "wx_abc12345",
    "email": "wx_abc12345@wechat.local",
    "role": "readonly",
    "full_name": "微信用户昵称",
    "is_active": true,
    "login_type": "wechat"
  },
  "wechat_info": {
    "openid": "ox1234567890abcdef",
    "nickname": "微信用户昵称",
    "avatar_url": "https://thirdwx.qlogo.cn/..."
  }
}
```

### 2. 绑定微信账号

```http
POST /api/v1/auth/wechat/bind
Authorization: Bearer {token}
Content-Type: application/json

{
  "admin_user_id": 1,
  "code": "031Kc1002CqHL31hR0002VvLTK3Kc10g",
  "nickname": "微信用户昵称",
  "avatar_url": "https://thirdwx.qlogo.cn/..."
}
```

### 3. 获取微信配置

```http
GET /api/v1/auth/wechat/config
```

**响应示例：**

```json
{
  "app_id": "wx1234567890abcdef",
  "api_url": "https://api.weixin.qq.com",
  "auto_create_user": true
}
```

## 测试

### 1. 运行测试脚本

```bash
# 运行微信登录测试
uv run python scripts/test_wechat_login.py
```

测试脚本会：
- 检查环境配置
- 运行数据库迁移
- 测试API接口
- 提供错误诊断

### 2. 小程序测试

1. 使用微信开发者工具打开小程序项目
2. 配置正确的AppID
3. 在小程序中测试登录功能
4. 检查网络请求是否正常

## 数据库结构

### 微信用户表 (wechat_users)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键 |
| openid | STRING | 微信OpenID（唯一） |
| unionid | STRING | 微信UnionID |
| nickname | STRING | 微信昵称 |
| avatar_url | STRING | 头像URL |
| admin_user_id | INTEGER | 绑定的管理员用户ID |
| session_key | STRING | 微信会话密钥 |
| session_expires_at | TIMESTAMP | 会话过期时间 |
| is_active | BOOLEAN | 是否激活 |
| last_login_at | TIMESTAMP | 最后登录时间 |
| login_count | INTEGER | 登录次数 |

### 管理员用户表扩展 (admin_users)

新增字段：
- `wechat_unionid`: 微信UnionID（唯一）

## 安全注意事项

1. **AppSecret保护**：AppSecret只能在后端服务器使用，切勿暴露在小程序代码中
2. **会话管理**：微信session_key有24小时有效期，需要定期刷新
3. **数据验证**：所有用户输入都需要进行验证和清理
4. **HTTPS**：生产环境必须使用HTTPS
5. **域名白名单**：在微信公众平台配置服务器域名

## 常见问题

### Q1: 微信登录返回"配置缺失"错误
**A:** 检查 `.env` 文件中的 `WECHAT_APPID` 和 `WECHAT_SECRET` 是否正确配置

### Q2: 微信登录返回"code无效"错误
**A:** 微信code只能使用一次，且5分钟内有效。需要从微信小程序重新获取code

### Q3: 如何禁止自动创建用户？
**A:** 设置环境变量 `WECHAT_AUTO_CREATE_USER=false`

### Q4: 如何修改微信用户的默认角色？
**A:** 设置环境变量 `WECHAT_DEFAULT_ROLE=admin` 或 `editor`

### Q5: 如何测试微信登录？
**A:** 使用微信开发者工具的小程序模拟器，或使用真实手机微信扫码测试

## 更新日志

### v1.0.0 (2025-12-19)
- ✅ 实现微信小程序登录功能
- ✅ 支持自动创建用户
- ✅ 支持微信账号绑定
- ✅ 实现JWT认证
- ✅ 添加数据库迁移
- ✅ 完善测试工具