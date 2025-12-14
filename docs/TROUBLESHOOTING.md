# 故障排除指南

本指南提供智能钓鱼助手常见问题的解决方案和调试技巧。

## 目录

- [环境配置问题](#环境配置问题)
- [API连接问题](#api连接问题)
- [认证和权限问题](#认证和权限问题)
- [工作流管理问题](#工作流管理问题)
- [爬虫任务问题](#爬虫任务问题)
- [数据库问题](#数据库问题)
- [前端连接问题](#前端连接问题)
- [性能优化建议](#性能优化建议)
- [日志和调试](#日志和调试)

## 环境配置问题

### Q: 提示"未设置API密钥"错误

**症状**:
```
ValueError: DASHSCOPE_API_KEY not set
```

**解决方案**:
1. 检查 `.env` 文件是否存在：
   ```bash
   ls -la .env
   ```

2. 如果不存在，复制模板文件：
   ```bash
   cp .env.example .env
   ```

3. 编辑 `.env` 文件，添加必需的API密钥：
   ```bash
   # 必需的API密钥
   CAIYUN_API_KEY=your-caiyun-api-key
   AMAP_API_KEY=your-amap-api-key
   DASHSCOPE_API_KEY=your-dashscope-api-key

   # JWT认证（生产环境必需）
   JWT_SECRET_KEY=your-super-secret-jwt-key-here-min-32-chars
   ```

4. 确保没有多余的空格或引号：
   ```bash
   # ✅ 正确格式
   API_KEY=your_key_here

   # ❌ 错误格式
   API_KEY= "your_key_here"
   ```

### Q: 模块导入错误

**症状**:
```
ModuleNotFoundError: No module named 'packages.agent_fishing'
```

**解决方案**:
1. 确保使用 `uv` 运行命令：
   ```bash
   # ✅ 正确方式
   uv run python main.py
   uv run uvicorn apps.api.main:app --reload

   # ❌ 错误方式
   python main.py
   uvicorn apps.api.main:app --reload
   ```

2. 检查项目结构：
   ```bash
   ls -la packages/agent_fishing/
   ```

3. 如果问题持续，重新同步依赖：
   ```bash
   uv sync
   ```

## API连接问题

### Q: 外部API调用失败

**症状**:
```
RequestException: Connection timeout
```

**解决方案**:
1. 检查网络连接：
   ```bash
   curl -I https://api.caiyunapp.com/v2.6
   ```

2. 验证API密钥有效性：
   ```bash
   # 测试彩云天气API
   curl "https://api.caiyunapp.com/v2.6/your_api_key/121.6544,31.2224/realtime"
   ```

3. 检查防火墙和代理设置。

4. 在配置中设置合理的超时时间：
   ```python
   # 在 utils/api_client.py 中
   timeout = 30  # 30秒超时
   ```

### Q: API响应格式错误

**症状**:
```
JSONDecodeError: Expecting property name enclosed in double quotes
```

**解决方案**:
1. 检查API密钥是否正确且未过期
2. 查看API文档确认请求格式
3. 使用调试模式查看原始响应：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## 认证和权限问题

### Q: JWT Token无效

**症状**:
```
HTTPError: 401 Unauthorized
```

**解决方案**:
1. 检查 `JWT_SECRET_KEY` 是否设置：
   ```bash
   grep JWT_SECRET_KEY .env
   ```

2. 确保密钥长度至少32个字符：
   ```python
   import secrets
   print(secrets.token_urlsafe(32))  # 生成新密钥
   ```

3. 检查Token是否过期：
   ```python
   import jwt
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(decoded.get("exp"))  # 查看过期时间
   ```

### Q: 权限不足

**症状**:
```
HTTPError: 403 Forbidden
```

**解决方案**:
1. 检查用户角色：
   ```bash
   # 登录后查看用户信息
   curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/api/v1/auth/me
   ```

2. 确认所需权限：
   ```python
   # 查看路由权限要求
   @router.get("/admin/...")

## 工作流管理问题

### Q: 工作流模板创建失败

**症状**:
```
ValidationError: steps must contain at least one step
```

**解决方案**:
1. 检查请求体格式：
   ```json
   {
     "name": "测试工作流",
     "description": "测试描述",
     "steps": [
       {
         "name": "步骤1",
         "task_type": "taobao",
         "config": {},
         "depends_on": []
       }
     ]
   }
   ```

2. 确保至少有一个步骤
3. 检查 `depends_on` 中的依赖步骤是否存在
4. 验证 `task_type` 是否为支持的类型

### Q: 工作流执行卡住

**症状**:
```
工作流状态一直是 "running"
```

**解决方案**:
1. 查看执行状态：
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/api/v1/admin/crawler/workflows/status/exec_id
   ```

2. 检查日志：
   ```bash
   # 查看应用日志
   uv run uvicorn apps.api.main:app --reload | grep workflow
   ```

3. 手动停止工作流：
   ```bash
   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/api/v1/admin/crawler/workflows/stop/exec_id
   ```

### Q: Cron调度不执行

**症状**:
```
调度任务未按预期执行
```

**解决方案**:
1. 验证Cron表达式：
   ```python
   from croniter import croniter
   from datetime import datetime

   # 验证表达式
   cron = croniter('0 2 * * *', datetime.now())
   print(cron.get_next(datetime))  # 下次执行时间
   ```

2. 检查时区设置：
   ```json
   {
     "cron_expression": "0 2 * * *",
     "timezone": "Asia/Shanghai"
   }
   ```

3. 预览执行时间：
   ```bash
   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"cron_expression":"0 2 * * *","timezone":"Asia/Shanghai","count":5}' \
        http://localhost:8000/api/v1/admin/crawler/schedules/preview
   ```

## 爬虫任务问题

### Q: 爬虫任务无法显示

**症状**:
```
任务列表为空或返回错误
```

**解决方案**:
1. 检查枚举值是否正确：
   ```python
   # 查看支持的TaskStatus值
   from packages.agent_fishing.tools.lure.models.system import TaskStatus
   print(TaskStatus.__members__)
   ```

2. 确保数据库连接正常：
   ```bash
   uv run python -c "
   from packages.agent_fishing.tools.lure.orm.session import get_db_session
   with get_db_session() as session:
       print('数据库连接正常')
   "
   ```

3. 检查任务状态值是否有效：
   ```json
   {
     "task_type": "taobao",
     "status": "pending",  // 或 "running", "completed", "failed"
     "progress": 0
   }
   ```

### Q: 爬虫任务删除失败

**症状**:
```
sqlite3.OperationalError: no such column: updated_at
```

**解决方案**:
1. 检查数据库schema：
   ```bash
   sqlite3 packages/agent_fishing/tools/lure/data/equipment.db \
          ".schema crawler_logs"
   ```

2. 添加缺失的列：
   ```sql
   ALTER TABLE crawler_logs ADD COLUMN updated_at TIMESTAMP;
   ```

3. 或重新初始化数据库（注意备份）：
   ```bash
   # 备份现有数据
   cp packages/agent_fishing/tools/lure/data/equipment.db \
      packages/agent_fishing/tools/lure/data/equipment.db.bak

   # 重新初始化
   uv run python -c "
   from packages.agent_fishing.tools.lure.database import init_database
   init_database()
   "
   ```

## 数据库问题

### Q: 数据库锁定

**症状**:
```
sqlite3.OperationalError: database is locked
```

**解决方案**:
1. 确保没有其他进程在使用数据库：
   ```bash
   lsof packages/agent_fishing/tools/lure/data/equipment.db
   ```

2. 使用上下文管理器确保连接关闭：
   ```python
   # 正确方式
   with get_db_session() as session:
       session.query(...)

   # 错误方式
   session = get_db_session()
   session.query(...)
   # 忘记关闭
   ```

3. 重启应用释放锁。

### Q: 数据迁移问题

**症状**:
```
列不存在或类型不匹配
```

**解决方案**:
1. 备份数据：
   ```bash
   cp equipment.db equipment_backup.db
   ```

2. 生成迁移脚本：
   ```python
   from alembic import command
   command.revision(config="alembic.ini", autogenerate=True)
   ```

3. 执行迁移：
   ```python
   command.upgrade(config="alembic.ini", "head")
   ```

## 前端连接问题

### Q: 前端无法连接后端

**症状**:
```
Network Error: Failed to fetch
```

**解决方案**:
1. 检查CORS配置：
   ```python
   # apps/api/main.py
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. 确认端口配置：
   - 后端: http://localhost:8000
   - 前端: http://localhost:5173

3. 检查API服务是否运行：
   ```bash
   curl http://localhost:8000/health
   ```

### Q: WebSocket连接失败

**症状**:
```
WebSocket connection to 'ws://localhost:8000/ws/monitor' failed
```

**解决方案**:
1. 检查WebSocket路由是否正确注册：
   ```python
   app.include_router(websocket_router)
   ```

2. 确保使用正确的协议：
   ```javascript
   // 开发环境
   const ws = new WebSocket(`ws://localhost:8000/ws/monitor`);

   // 生产环境(HTTPS)
   const ws = new WebSocket(`wss://your-domain.com/ws/monitor`);
   ```

## 性能优化建议

### 1. 数据库优化

```python
# 使用连接池
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///equipment.db",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
```

### 2. 缓存优化

```python
# 使用缓存减少API调用
from functools import lru_cache

@lru_cache(maxsize=128)
def get_weather_cached(location: str, date: str):
    return get_weather(location, date)
```

### 3. 异步优化

```python
# 对于IO密集型操作使用异步
import asyncio
import aiohttp

async def fetch_weather_async(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses
```

## 日志和调试

### 启用调试模式

1. **应用日志**:
   ```python
   import logging
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **SQL日志**:
   ```python
   import logging
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

3. **请求日志**:
   ```python
   # 在FastAPI中添加日志中间件
   @app.middleware("http")
   async def log_requests(request: Request, call_next):
       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time
       logging.info(
           f"{request.method} {request.url} - "
           f"Status: {response.status_code} - "
           f"Time: {process_time:.3f}s"
       )
       return response
   ```

### 常用调试命令

```bash
# 检查环境变量
env | grep -E "(API_KEY|JWT)"

# 测试API连接
curl -X GET http://localhost:8000/health

# 查看Python路径
uv run python -c "import sys; print('\n'.join(sys.path))"

# 测试数据库连接
uv run python -c "
from packages.agent_fishing.tools.lure.orm.session import get_db_session
with get_db_session() as session:
    result = session.execute('SELECT 1').fetchone()
    print(f'Database OK: {result}')
"
```

## 获取帮助

如果以上解决方案无法解决您的问题：

1. **查看日志文件**:
   - 应用日志: `logs/fishing_agent.log`
   - 错误日志: `logs/error.log`

2. **GitHub Issues**:
   - 搜索现有问题: [Issues页面](https://github.com/yourusername/fishing-agent/issues)
   - 创建新问题时请包含：
     - 错误信息和堆栈跟踪
     - 操作系统和Python版本
     - 复现步骤
     - 相关配置（去除敏感信息）

3. **社区支持**:
   - 查看文档: [文档中心](./)
   - 提交PR: [贡献指南](./DEVELOPMENT.md)

---

**最后更新**: 2024-12-14
**版本**: v5.0.1