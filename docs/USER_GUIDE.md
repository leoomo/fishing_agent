# 用户指南

本指南将帮助您深入了解和使用智能钓鱼助手的各种功能。

## 目录

- [快速开始](#快速开始)
- [基础使用](#基础使用)
- [钓鱼推荐功能](#钓鱼推荐功能)
- [路亚装备管理](#路亚装备管理)
- [API 使用示例](#api-使用示例)
- [高级功能](#高级功能)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

## 快速开始

### 第一个钓鱼推荐

```python
from packages.agent_fishing import create_agent

# 创建智能体
agent = create_agent(model_provider="zhipu")

# 获取钓鱼推荐
response = agent.run("明天北京天气怎么样？适合钓鱼吗？")
print(response)
```

### API 方式调用

```bash
# 获取 JWT Token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 使用 Token 调用聊天接口
curl -X POST "http://localhost:8000/api/v1/fishing/chat" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "明天上海哪里适合钓鱼？",
    "model_provider": "zhipu",
    "user_id": 1
  }'
```

## 基础使用

### 1. 时间查询

支持多种时间表达方式：

```python
# 相对时间
agent.run("今天钓鱼怎么样？")
agent.run("明天杭州钓鱼条件如何？")
agent.run("这个周末适合钓鱼吗？")

# 绝对时间
agent.run("2024年12月25日钓鱼怎么样？")

# 时间段
agent.run("明天上午适合钓鱼吗？")
agent.run("后天晚上去钓鱼可以吗？")
```

### 2. 地点查询

支持全国所有城市和地区：

```python
# 城市级别
agent.run("北京哪里适合钓鱼？")
agent.run("武汉东湖钓鱼条件怎么样？")

# 具体地点
agent.run("杭州西湖现在天气如何？能钓鱼吗？")

# 坐标查询（高级功能）
from packages.agent_fishing.utils import get_coordinates
coords = get_coordinates("北京")
print(f"北京坐标: {coords}")
```

### 3. 天气查询

获取详细的天气信息：

```python
from packages.agent_fishing.tools import get_weather

# 获取当前天气
weather = get_weather("北京", "今天")
print(f"温度: {weather.temperature}°C")
print(f"风速: {weather.wind_speed} m/s")
print(f"气压: {weather.pressure} hPa")
```

## 钓鱼推荐功能

### 7因子科学评分体系

系统使用科学的7因子评分体系：

| 因子 | 权重 | 说明 |
|------|------|------|
| 温度 | 25% | 影响鱼类活跃度 |
| 天气 | 20% | 晴雨情况影响 |
| 风力 | 15% | 影响水面状况 |
| 气压 | 15% | 快速下降触发黄金期 |
| 湿度 | 10% | 影响体感舒适度 |
| 季节 | 5% | 季节性鱼类习性 |
| 月相 | 5% | 影响夜间活动 |

### 评分解读

- **90-100分**: 极佳条件，钓鱼黄金期
- **80-89分**: 很好条件，适合出钓
- **70-79分**: 一般条件，可选择性出钓
- **60-69分**: 较差条件，不建议出钓
- **60分以下**: 极差条件，避免出钓

### 动态趋势分析

```python
# 系统会自动识别气压快速下降
response = agent.run("上海明天钓鱼怎么样？")
# 可能触发"钓鱼黄金期"提示，评分+20%
```

### 时间段推荐

系统支持6个时间段的专门分析：

```python
# 不同时间段的推荐
agent.run("明天上午北京哪里钓鱼好？")    # 6:00-12:00
agent.run("明天晚上杭州钓鱼条件如何？")  # 18:00-24:00
agent.run("后天深夜能钓鱼吗？")         # 0:00-6:00
```

## 路亚装备管理

### 创建用户档案

```bash
curl -X POST "http://localhost:8000/api/v1/user-equipment/users" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "nickname": "钓鱼爱好者",
    "user_level": "进阶",
    "fishing_experience_years": 3,
    "preferred_fish": "鲈鱼,翘嘴,鳜鱼"
  }'
```

### 添加装备记录

```bash
curl -X POST "http://localhost:8000/api/v1/user-equipment/users/1/equipment" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": 123,
    "purchase_price": 599.99,
    "purchase_date": "2024-01-15",
    "notes": "我的第一支路亚竿",
    "tags": ["入门", "鲈鱼专用"]
  }'
```

### 智能装备推荐

```python
# 通过智能体获取装备推荐
response = agent.run("""
我是新手，预算1000元，想买一套鲈鱼路亚装备，有什么推荐吗？
""")

# 或通过API获取推荐
curl -X POST "http://localhost:8000/api/v1/user-equipment/users/1/recommend" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_type": "upgrade",
    "budget": 1000,
    "target_fish": "鲈鱼"
  }'
```

### 装备对比分析

```python
# 对比多款装备
response = agent.run("""
对比一下禧玛诺和达亿瓦的入门级纺车轮，哪个更适合新手？
预算500元左右。
""")
```

### 获取装备统计

```bash
curl -X GET "http://localhost:8000/api/v1/user-equipment/users/1/statistics" \
  -H "Authorization: Bearer <token>"
```

## API 使用示例

### Python SDK 示例

```python
import requests

class FishingClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        """用户登录获取Token"""
        response = requests.post(f"{self.base_url}/api/v1/auth/login", json={
            "username": username,
            "password": password
        })
        data = response.json()
        self.token = data["access_token"]
        return data["user"]

    def chat(self, query, model_provider="zhipu", user_id=1):
        """智能对话"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/api/v1/fishing/chat",
                               headers=headers, json={
            "query": query,
            "model_provider": model_provider,
            "user_id": user_id
        })
        return response.json()

    def get_equipment_list(self, user_id, category=None, page=1):
        """获取用户装备列表"""
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"page": page, "page_size": 20}
        if category:
            params["category"] = category

        response = requests.get(
            f"{self.base_url}/api/v1/user-equipment/users/{user_id}/equipment",
            headers=headers, params=params
        )
        return response.json()

# 使用示例
client = FishingClient()
user = client.login("admin", "admin123")
print(f"登录成功: {user['username']}")

response = client.chat("明天北京钓鱼怎么样？")
print(f"推荐: {response['response']}")
```

### JavaScript SDK 示例

```javascript
class FishingAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.token = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await response.json();
        this.token = data.access_token;
        return data.user;
    }

    async chat(query, modelProvider = 'zhipu', userId = 1) {
        const response = await fetch(`${this.baseURL}/api/v1/fishing/chat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query,
                model_provider: modelProvider,
                user_id: userId
            })
        });
        return response.json();
    }

    async getTools() {
        const response = await fetch(`${this.baseURL}/api/v1/fishing/tools`);
        return response.json();
    }
}

// 使用示例
const api = new FishingAPI();
await api.login('admin', 'admin123');

const response = await api.chat('明天杭州适合钓鱼吗？');
console.log(response.response);
```

## 高级功能

### 1. 实时天气监控

```python
from packages.agent_fishing.tools import get_weather

# 监控天气变化
def monitor_weather(location, hours=24):
    """监控指定地点的天气变化"""
    import time

    for i in range(hours):
        weather = get_weather(location, "现在")
        print(f"[{i}] 温度: {weather.temperature}°C, "
              f"天气: {weather.condition}")

        # 检查气压变化
        if hasattr(weather, 'pressure_trend'):
            if weather.pressure_trend == 'falling_fast':
                print("⚠️  气压快速下降，即将进入钓鱼黄金期！")

        time.sleep(3600)  # 每小时检查一次
```

### 2. 批量地点分析

```python
# 分析多个地点的钓鱼条件
locations = ["北京", "上海", "广州", "成都", "杭州"]

for location in locations:
    response = agent.run(f"明天{location}钓鱼怎么样？")
    print(f"\n=== {location} ===")
    print(response)
```

### 3. 自定义Prompt

```python
from packages.agent_fishing import FishingAgent
from packages.agent_fishing.core.prompts import FISHING_PROMPT

# 创建自定义Agent
agent = FishingAgent(
    model_provider="zhipu",
    system_prompt="你是一个专业的路亚钓鱼教练，请提供详细的作钓建议。"
)

# 使用自定义Prompt
response = agent.run("新手学路亚应该注意什么？")
print(response)
```

### 4. 数据分析

```bash
# 获取装备统计数据
curl -X GET "http://localhost:8000/api/v1/admin/analytics/equipment/stats" \
  -H "Authorization: Bearer <token>"

# 生成业务报表
curl -X POST "http://localhost:8000/api/v1/admin/analytics/reports/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "equipment",
    "format": "pdf",
    "filters": {
      "category": "鱼竿",
      "date_range": "2024-01-01,2024-12-31"
    },
    "include_charts": true
  }'
```

## 常见问题

### Q: 如何提高推荐准确度？

**A**:
1. 提供具体的时间（"明天上午8点"比"明天"更准确）
2. 明确地点（"北京朝阳区"比"北京"更精确）
3. 说明目标鱼种（不同鱼种偏好不同条件）
4. 提供钓鱼方式（路亚、台钓、海钓等）

### Q: 评分60分以下还能钓鱼吗？

**A**:
虽然系统不建议60分以下出钓，但实际还取决于：
- 个人经验（老手可能在较差条件下也有收获）
- 钓鱼地点（室内/室外、静水/流水）
- 目标鱼种（某些鱼耐低气压）
- 个人时间安排

### Q: 如何选择合适的装备？

**A**:
1. **新手入门**: 选择套装，性价比高
2. **目标鱼种**:
   - 鲈鱼: M(中等)调性竿
   - 翘嘴: ML(中轻)调性竿
   - 鳜鱼: MH(中重)调性竿
3. **预算**: 杆+轮+线≈1:1:0.2
4. **品牌**: 禧玛诺、达亿瓦、阿布等

### Q: API调用频率限制？

**A**:
- 未认证用户：100 请求/小时
- 普通用户：1000 请求/小时
- 管理员：无限制

### Q: 如何获取最新的装备数据？

**A**:
系统会自动从电商平台同步数据，也可以手动触发：

```bash
# 触发爬虫任务
curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/trigger" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "taobao",
    "keywords": ["路亚竿"],
    "max_pages": 3
  }'
```

## 最佳实践

### 1. 查询优化

```python
# ❌ 模糊查询
agent.run("钓鱼怎么样？")

# ✅ 具体查询
agent.run("明天上午8点，北京朝阳区，鲈鱼路亚，天气条件如何？")
```

### 2. 批量处理

```python
# 使用工具函数批量查询
from packages.agent_fishing.tools import query_fishing_recommendation

queries = [
    "北京明天钓鱼怎么样",
    "上海后天钓鱼条件",
    "广州周末钓鱼建议"
]

for query in queries:
    result = query_fishing_recommendation(query)
    print(result)
```

### 3. 缓存利用

系统自动缓存天气数据，避免重复调用：

```python
# 第一次调用会获取最新数据
weather1 = get_weather("北京", "今天")

# 第二次调用使用缓存（1小时内）
weather2 = get_weather("北京", "今天")
```

### 4. 错误处理

```python
try:
    response = agent.run("明天钓鱼怎么样")
except Exception as e:
    print(f"获取推荐失败: {e}")
    # 使用备用方案
    response = get_weather("北京", "明天")
```

### 5. Token管理

```python
# 及时刷新Token
if token_expired():
    client.login(username, password)

# 使用环境变量存储敏感信息
import os
API_KEY = os.getenv('DASHSCOPE_API_KEY')
```

## 更多资源

- [API 参考](./API_REFERENCE.md) - 完整的API文档
- [快速入门](./GETTING_STARTED.md) - 安装配置指南
- [架构文档](./ARCHITECTURE.md) - 系统架构说明
- [更新日志](../CHANGELOG.md) - 版本更新记录

---

祝您钓鱼愉快！🎣