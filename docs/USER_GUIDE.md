# 用户指南 v5.0.2

本指南将帮助您深入了解和使用智能钓鱼助手 v5.0.2 的各种功能。

## 目录

- [快速开始](#快速开始)
- [基础使用](#基础使用)
- [钓鱼推荐功能](#钓鱼推荐功能)
- [路亚装备管理](#路亚装备管理)
- [装备信息提取与导入](#装备信息提取与导入)
- [图片处理与OCR识别](#图片处理与ocr识别)
- [微信小程序使用](#微信小程序使用)
- [API 使用示例](#api-使用示例)
- [高级功能](#高级功能)
- [爬虫与工作流管理](#爬虫与工作流管理)
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

## 装备信息提取与导入

### 使用装备导入Agent

v5.0.2 新增了专门的装备导入Agent，可以从文本中智能提取装备信息：

```python
from packages.agent_equipment_import import EquipmentImportAgent

# 创建Agent（支持文本压缩）
agent = EquipmentImportAgent(
    model_provider="zhipu",
    enable_compression=True,  # 启用文本压缩中间件
    compression_min_length=2000
)

# 对话式交互
response = agent.run("帮我从这段文字提取装备信息：光威赤刃 GT602L-M 路亚竿...")

# 批量提取并保存
results = agent.batch_extract_and_save(
    text="长文本包含多个装备型号...",
    source_type="ecommerce",
    source_url="https://example.com"
)

# 查看结果
for result in results:
    if result.success:
        print(f"成功: {result.message}, 待审核ID: {result.pending_id}")
    else:
        print(f"失败: {result.message}")
```

### 文本压缩功能

对于长文本，系统会自动压缩以提取核心信息：

```python
# 文本压缩示例
compressed_result = agent.compress_text(text="""
长文本内容...
包括英文营销语、售后说明、技术原理图等冗余内容...
以及规格表、型号描述、技术特色等核心信息...
""")

print(f"压缩率: {compressed_result.compression_ratio}")
print(f"原始长度: {compressed_result.original_length}")
print(f"压缩后长度: {compressed_result.compressed_length}")
print(f"核心信息: {compressed_result.core_info}")
```

### API方式提取装备信息

```bash
# 提取单个装备信息
curl -X POST "http://localhost:8000/api/v1/equipment/import/extract" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "光威赤刃 GT602L-M 路亚竿，碳纤维材质，适合淡水路亚，价格¥299",
    "source_type": "forum",
    "source_url": "https://example.com/forum/post/123",
    "enable_compression": true
  }'

# 批量提取装备信息
curl -X POST "http://localhost:8000/api/v1/equipment/import/batch-extract" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "长文本包含多个装备型号...",
    "source_type": "ecommerce",
    "source_url": "https://example.com",
    "enable_compression": true
  }'
```

### 审核待审核装备

```bash
# 获取待审核列表
curl -X GET "http://localhost:8000/api/v1/equipment/pending?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"

# 审核通过
curl -X POST "http://localhost:8000/api/v1/equipment/pending/12345/review" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "review_notes": "信息准确，批准入库",
    "equipment_data": {
      "brand_id": 1,
      "category": "路亚竿",
      "model_name": "赤刃 GT602L-M",
      "price": 299
    }
  }'
```

## 图片处理与OCR识别

### 智能图片合并

系统可以自动检测图片下方是否有文字，并智能合并相关图片：

```python
from packages.data_processing.image import BatchMergeProcessor

# 创建批处理器
processor = BatchMergeProcessor(
    source_dir="./images",
    output_dir="./merged",
    quality=95,
    bottom_detection_ratio=0.2,
    ocr_confidence_threshold=0.5,
    parallel_detection=True,
    max_workers=4
)

# 执行批处理
result = processor.process()
if result["success"]:
    print(f"处理完成: {result['statistics']}")
```

### OCR表格识别

```bash
# 识别图片中的表格（支持多张图片自动合并）
curl -X POST "http://localhost:8000/api/v1/ocr/recognize-table" \
  -H "Authorization: Bearer <token>" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"

# 使用图片URL
curl -X POST "http://localhost:8000/api/v1/ocr/recognize-table" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/spec-table.jpg"
  }'
```

### OCR服务配置

支持两种OCR提供商：

#### 1. Ollama本地OCR（推荐）

```bash
# 环境变量配置
OCR_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-ocr
OLLAMA_TIMEOUT=120
```

#### 2. SiliconFlow云端OCR

```bash
# 环境变量配置
OCR_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-api-key
SILICONFLOW_OCR_TIMEOUT=30
```

### 检查OCR状态

```bash
curl -X GET "http://localhost:8000/api/v1/ocr/status" \
  -H "Authorization: Bearer <token>"
```

## 微信小程序使用

### 微信登录

```javascript
// 微信小程序端代码
wx.login({
  success: async (res) => {
    // 调用后端登录接口
    const response = await wx.request({
      url: 'http://your-domain.com/api/v1/auth/wechat/login',
      method: 'POST',
      data: { code: res.code }
    });
    
    // 保存token
    wx.setStorageSync('access_token', response.data.access_token);
    
    // 获取用户信息
    if (response.data.is_new_user) {
      wx.showModal({
        title: '欢迎',
        content: '欢迎来到智能钓鱼助手！',
        showCancel: false
      });
    }
  }
});
```

### 绑定已有账号

```javascript
// 绑定微信到现有账号
wx.request({
  url: 'http://your-domain.com/api/v1/auth/wechat/bind',
  method: 'POST',
  header: {
    'Authorization': `Bearer ${token}`
  },
  data: { code: wxCode }
});
```

### 小程序API调用示例

```javascript
// 获取钓鱼推荐
function getFishingRecommendation(query) {
  const token = wx.getStorageSync('access_token');
  
  wx.request({
    url: 'http://your-domain.com/api/v1/fishing/chat',
    method: 'POST',
    header: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    data: {
      query: query,
      model_provider: 'zhipu',
      user_id: wx.getStorageSync('user_id')
    },
    success: (res) => {
      console.log('推荐结果:', res.data.response);
    }
  });
}

// 使用示例
getFishingRecommendation('明天北京钓鱼怎么样？');
```

## API 使用示例

### Python SDK 示例

```python
import requests
import os

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

    def extract_equipment(self, text, source_type="forum"):
        """提取装备信息"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/api/v1/equipment/import/extract",
                               headers=headers, json={
            "text": text,
            "source_type": source_type,
            "enable_compression": True
        })
        return response.json()

    def recognize_table(self, image_path):
        """OCR识别表格"""
        headers = {"Authorization": f"Bearer {self.token}"}
        with open(image_path, 'rb') as f:
            files = {'files': f}
            response = requests.post(f"{self.base_url}/api/v1/ocr/recognize-table",
                                   headers=headers, files=files)
        return response.json()

# 使用示例
client = FishingClient()
user = client.login("admin", "admin123")
print(f"登录成功: {user['username']}")

# 钓鱼推荐
response = client.chat("明天北京钓鱼怎么样？")
print(f"推荐: {response['response']}")

# 提取装备信息
equipment = client.extract_equipment(
    "光威赤刃 GT602L-M 路亚竿，碳纤维材质，价格299元"
)
print(f"提取结果: {equipment}")

# OCR识别
ocr_result = client.recognize_table("./spec_table.jpg")
print(f"识别结果: {ocr_result['markdown']}")
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

    async extractEquipment(text, sourceType = 'forum') {
        const response = await fetch(`${this.baseURL}/api/v1/equipment/import/extract`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text,
                source_type: sourceType,
                enable_compression: true
            })
        });
        return response.json();
    }

    async recognizeTable(imageFile) {
        const formData = new FormData();
        formData.append('files', imageFile);
        
        const response = await fetch(`${this.baseURL}/api/v1/ocr/recognize-table`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        return response.json();
    }
}

// 使用示例
const api = new FishingAPI();
await api.login('admin', 'admin123');

// 钓鱼推荐
const response = await api.chat('明天杭州适合钓鱼吗？');
console.log(response.response);

// 提取装备
const equipment = await api.extractEquipment(
    '达亿瓦 1000 纺车轮，浅线杯，适合路亚'
);
console.log(equipment.results);
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

## 爬虫与工作流管理

### 创建爬虫任务

```bash
# 触发爬虫任务
curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/trigger" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "taobao",
    "keywords": ["路亚竿", "渔轮"],
    "max_pages": 5,
    "category": "鱼竿"
  }'
```

### 创建工作流

```bash
# 创建工作流模板
curl -X POST "http://localhost:8000/api/v1/admin/crawler/workflows/templates" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "装备数据同步工作流",
    "description": "定期同步电商平台装备数据",
    "steps": [
      {
        "name": "爬取淘宝数据",
        "task_type": "taobao",
        "config": {
          "keywords": ["路亚竿"],
          "max_pages": 3
        },
        "depends_on": []
      },
      {
        "name": "数据清洗",
        "task_type": "data_clean",
        "config": {},
        "depends_on": ["爬取淘宝数据"]
      }
    ]
  }'
```

### 创建定时调度

```bash
# 创建定时任务
curl -X POST "http://localhost:8000/api/v1/admin/crawler/schedules" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "每日数据同步",
    "template_id": 1,
    "cron_expression": "0 2 * * *",
    "timezone": "Asia/Shanghai",
    "is_active": true
  }'
```

### 导入导出数据

```bash
# CSV导入装备
curl -X POST "http://localhost:8000/api/v1/equipment/import/csv" \
  -H "Authorization: Bearer <token>" \
  -F "file=@equipment.csv"

# 导出装备数据
curl -X GET "http://localhost:8000/api/v1/equipment/export/csv?category=路亚竿&limit=1000" \
  -H "Authorization: Bearer <token>" \
  -o equipment_export.csv
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

### Q: OCR识别如何提高准确率？

**A**:
1. 使用Ollama本地OCR，保护隐私且免费
2. 图片清晰度越高越好
3. 表格边界清晰，无遮挡
4. 可使用智能合并功能处理多图

### Q: 如何使用装备导入功能？

**A**:
1. 文本提取：直接粘贴商品描述
2. 图片识别：使用OCR功能识别规格表
3. 批量处理：支持长文本批量提取
4. 审核机制：所有提取信息需审核后入库

### Q: API调用频率限制？

**A**:
- 未认证用户：100 请求/小时
- 只读用户：500 请求/小时
- 编辑用户：1000 请求/小时
- 管理员：无限制

### Q: 如何配置微信小程序？

**A**:
1. 在微信公众平台获取AppID和AppSecret
2. 配置服务器域名白名单
3. 设置环境变量：
   ```bash
   WECHAT_APPID=your-appid
   WECHAT_SECRET=your-secret
   WECHAT_AUTO_CREATE_USER=true
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

### 6. 图片处理优化

```python
# 并行处理提高效率
processor = BatchMergeProcessor(
    source_dir="./images",
    parallel_detection=True,
    max_workers=8  # 根据CPU核心数调整
)

# 自定义检测参数
processor = BatchMergeProcessor(
    source_dir="./images",
    bottom_detection_ratio=0.3,  # 检测底部30%区域
    ocr_confidence_threshold=0.7  # 提高置信度阈值
)
```

## 更多资源

- [API 参考](./API_REFERENCE.md) - 完整的API文档
- [快速入门](./GETTING_STARTED.md) - 安装配置指南
- [架构文档](./ARCHITECTURE.md) - 系统架构说明
- [更新日志](../CHANGELOG.md) - 版本更新记录
- [微信小程序开发指南](./MINIPROGRAM_GUIDE.md) - 小程序集成指南
- [图片处理指南](./IMAGE_PROCESSING.md) - OCR和图片处理详细说明

---

祝您钓鱼愉快！🎣