# 内容管理API文档

## 概述

内容管理API提供鱼百科、文章、配件、拟饵类型、钓组配置等内容的完整CRUD操作。

## 鱼百科管理API

### 鱼种管理

#### 获取鱼种列表

```http
GET /api/v1/fish-species
```

**查询参数:**
- `page`: 页码（默认: 1）
- `page_size`: 每页数量（默认: 20）
- `category`: 分类过滤（freshwater/saltwater/brackish）
- `target_species`: 目标鱼种过滤

**响应示例:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "大嘴鲈",
      "scientific_name": "Micropterus salmoides",
      "category": "freshwater",
      "description": "淡水路亚钓法最热门的目标鱼种",
      "distribution": "全国各大淡水水域",
      "habits": "喜栖息于水草丛生、结构复杂的区域"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

#### 创建鱼种

```http
POST /api/v1/fish-species
```

**请求体:**
```json
{
  "name": "大嘴鲈",
  "scientific_name": "Micropterus salmoides",
  "category": "freshwater",
  "description": "淡水路亚钓法最热门的目标鱼种",
  "distribution": "全国各大淡水水域",
  "habits": "喜栖息于水草丛生、结构复杂的区域"
}
```

#### 获取鱼种详情

```http
GET /api/v1/fish-species/{id}
```

#### 更新鱼种

```http
PUT /api/v1/fish-species/{id}
```

#### 删除鱼种

```http
DELETE /api/v1/fish-species/{id}
```

### 知识库管理

#### 获取知识库列表

```http
GET /api/v1/fish-knowledge
```

**查询参数:**
- `species_id`: 鱼种ID过滤
- `page`: 页码
- `page_size`: 每页数量

#### 创建知识

```http
POST /api/v1/fish-knowledge
```

**请求体:**
```json
{
  "species_id": 1,
  "content_type": "habits",
  "title": "生活习性",
  "content": "大嘴鲈喜栖息于...",
  "references": ["来源1", "来源2"]
}
```

### 季节活动管理

#### 获取季节活动列表

```http
GET /api/v1/fish-seasons
```

**查询参数:**
- `species_id`: 鱼种ID过滤
- `season`: 季节过滤（spring/summer/autumn/winter）

#### 创建季节活动

```http
POST /api/v1/fish-seasons
```

**请求体:**
```json
{
  "species_id": 1,
  "season": "spring",
  "activity_level": "active",
  "description": "春季活跃期",
  "best_time": "早晨6-9点",
  "best_locations": "浅水区、水草边缘",
  "recommended_lures": ["米诺", "软虫"]
}
```

### 装备推荐

#### 获取鱼种装备推荐

```http
GET /api/v1/fish-species/{id}/equipment
```

**响应示例:**
```json
{
  "species_id": 1,
  "species_name": "大嘴鲈",
  "recommended_lures": ["软虫", "米诺", "摇滚", "VIB", "铅头钩"],
  "recommended_rigs": ["德州钓组", "无铅钓组", "卡罗莱纳钓组", "倒吊钓组"],
  "recommended_rod_power": ["ML", "M", "MH"],
  "recommended_line_lb": {
    "min": 8,
    "max": 20
  },
  "lure_difficulty": "新手",
  "fight_intensity": "中等"
}
```

### 统计数据

#### 获取分类统计

```http
GET /api/v1/fish-species/stats/stats
```

**响应示例:**
```json
{
  "categories": [
    {
      "category": "freshwater",
      "count": 35,
      "label": "淡水鱼",
      "icon": "🐟",
      "color": "#1890ff"
    },
    {
      "category": "saltwater",
      "count": 12,
      "label": "海水鱼",
      "icon": "🐠",
      "color": "#13c2c2"
    }
  ],
  "total_species": 50
}
```

#### 初始化数据

```http
GET /api/v1/fish-species/init-data
```

返回系统预置的鱼种、知识库和季节活动数据。

---

## 文章管理API

### 文章CRUD

#### 创建文章（草稿）

```http
POST /api/v1/articles
```

**请求体:**
```json
{
  "title": "春季路亚技巧",
  "content": "文章内容...",
  "article_type": "technique",
  "summary": "春季路亚钓法的核心技巧",
  "tags": ["路亚", "春季", "技巧"],
  "cover_image": "https://example.com/cover.jpg"
}
```

**响应示例:**
```json
{
  "id": 1,
  "title": "春季路亚技巧",
  "status": "draft",
  "article_type": "technique",
  "author_id": 1,
  "author_name": "管理员",
  "created_at": "2025-01-02T10:00:00",
  "updated_at": "2025-01-02T10:00:00"
}
```

#### 获取文章列表

```http
GET /api/v1/articles
```

**查询参数:**
- `page`: 页码（默认: 1）
- `page_size`: 每页数量（默认: 20）
- `status`: 状态过滤（draft/published/archived）
- `article_type`: 类型过滤（technique/review/fish/spot）
- `author_id`: 作者ID过滤
- `tag`: 标签过滤

#### 获取文章详情

```http
GET /api/v1/articles/{id}
```

#### 更新文章（自动保存）

```http
PUT /api/v1/articles/{id}
```

#### 删除文章

```http
DELETE /api/v1/articles/{id}
```

### 文章发布

#### 发布文章

```http
POST /api/v1/articles/{id}/publish
```

**请求体:**
```json
{
  "publish_notes": "审核通过，准予发布"
}
```

#### 归档文章

```http
POST /api/v1/articles/{id}/archive
```

### 搜索和推荐

#### 语义搜索

```http
GET /api/v1/articles/search
```

**查询参数:**
- `q`: 搜索关键词
- `top_k`: 返回数量（默认: 5）
- `article_type`: 文章类型过滤
- `status`: 状态过滤（默认: published）

**示例:**
```bash
GET /api/v1/articles/search?q=春季路亚技巧&top_k=5
```

**响应示例:**
```json
{
  "query": "春季路亚技巧",
  "results": [
    {
      "article_id": 1,
      "title": "春季路亚技巧",
      "content": "文章内容...",
      "score": 0.95,
      "article_type": "technique",
      "status": "published"
    }
  ],
  "total": 5
}
```

#### 相似文章推荐

```http
GET /api/v1/articles/{id}/similar
```

**查询参数:**
- `top_k`: 返回数量（默认: 3）

**响应示例:**
```json
{
  "article_id": 1,
  "similar_articles": [
    {
      "id": 2,
      "title": "春季选饵指南",
      "similarity": 0.88
    },
    {
      "id": 3,
      "title": "路亚新手入门",
      "similarity": 0.75
    }
  ]
}
```

### 文章网络采集

从外部数据源（如维基百科）采集钓鱼相关文章，使用LLM翻译增强内容质量，采集的文章进入草稿状态待审核。

#### 获取可用数据源

```http
GET /api/v1/articles/fetch/sources
```

**响应示例:**
```json
[
  {
    "id": "wikipedia",
    "name": "Wikipedia (钓鱼词条)",
    "description": "从维基百科获取钓鱼相关知识文章",
    "total_items": 30,
    "enabled": true
  }
]
```

#### 获取采集进度

```http
GET /api/v1/articles/fetch/progress
```

**响应示例:**
```json
{
  "is_running": true,
  "stats": {
    "total": 30,
    "pending": 25,
    "fetching": 0,
    "enriching": 1,
    "completed": 3,
    "failed": 1,
    "skipped": 0
  },
  "items": [
    {
      "source_url": "https://en.wikipedia.org/wiki/Fishing",
      "title": "钓鱼概述",
      "source_type": "wikipedia",
      "status": "completed",
      "article_id": 4,
      "error": null,
      "updated_at": "2025-01-16T10:30:00"
    }
  ]
}
```

#### 开始采集

```http
POST /api/v1/articles/fetch/start
```

**请求体:**
```json
{
  "source_id": "wikipedia",
  "use_llm": true
}
```

**参数说明:**
- `source_id`: 数据源ID（默认: "wikipedia"）
- `use_llm`: 是否使用LLM翻译增强（默认: true）

**响应示例:**
```json
{
  "message": "采集任务已启动"
}
```

#### 暂停采集

```http
POST /api/v1/articles/fetch/pause
```

**响应示例:**
```json
{
  "message": "正在暂停采集..."
}
```

#### 重试失败项

```http
POST /api/v1/articles/fetch/retry
```

**请求体:**
```json
{
  "urls": ["https://en.wikipedia.org/wiki/Fishing"]
}
```

**参数说明:**
- `urls`: 指定重试的URL列表，为空则重试所有失败项

**响应示例:**
```json
{
  "message": "已重置失败项目"
}
```

#### 重置进度

```http
POST /api/v1/articles/fetch/reset
```

**响应示例:**
```json
{
  "message": "已重置所有进度"
}
```

**采集流程说明:**
1. 系统从维基百科获取预设的30条钓鱼相关词条
2. 使用Qwen Plus模型将英文内容翻译为中文
3. LLM自动生成文章标题、摘要和标签
4. 采集的文章以草稿状态保存，需人工审核后发布
5. 原文链接保存在文章扩展信息中

---

## 配件管理API

### 配件CRUD

#### 获取配件列表

```http
GET /api/v1/accessory
```

**查询参数:**
- `page`: 页码
- `page_size`: 每页数量
- `category`: 分类过滤（hook/sinker/swivel/leader/float/snap/other）
- `user_level`: 用户等级过滤（beginner/intermediate/advanced）

#### 创建配件

```http
POST /api/v1/accessory
```

**请求体:**
```json
{
  "name": "曲柄钩",
  "category": "hook",
  "description": "路亚软饵专用钩",
  "features": "防挂底、软饵专用",
  "size": "#1/0 - #5/0",
  "material": "碳钢",
  "target_species": "黑鲈、鳜鱼",
  "applicable_rigs": "Texas钓组、Carolina钓组",
  "user_level": "beginner",
  "price_range": "10-50元"
}
```

#### 获取配件详情

```http
GET /api/v1/accessory/{id}
```

#### 更新配件

```http
PUT /api/v1/accessory/{id}
```

#### 删除配件

```http
DELETE /api/v1/accessory/{id}
```

### 配件选项

#### 获取配件选项数据

```http
GET /api/v1/accessory/options
```

**响应示例:**
```json
{
  "categories": [
    {"value": "hook", "label": "钩子", "icon": "🪝", "color": "#1890ff"},
    {"value": "sinker", "label": "铅坠", "icon": "⚓", "color": "#722ed1"}
  ],
  "user_levels": [
    {"value": "beginner", "label": "新手", "color": "#52c41a"},
    {"value": "intermediate", "label": "进阶", "color": "#1890ff"}
  ],
  "common_materials": ["碳钢", "不锈钢", "钨合金", "铅"]
}
```

#### 初始化数据

```http
GET /api/v1/accessory/init-data
```

---

## 拟饵类型管理API

### 拟饵类型CRUD

#### 获取拟饵类型列表

```http
GET /api/v1/lure-types
```

**查询参数:**
- `page`: 页码
- `page_size`: 每页数量
- `category`: 分类过滤（hard/soft/metal/fly/other）

#### 创建拟饵类型

```http
POST /api/v1/lure-types
```

**请求体:**
```json
{
  "name": "米诺",
  "category": "hard",
  "description": "模仿小鱼的经典硬饵",
  "action_description": "摇摆游动，模拟受伤小鱼",
  "target_species": "黑鲈、鳜鱼、翘嘴",
  "typical_weight_min": 5,
  "typical_weight_max": 20
}
```

#### 获取拟饵类型详情

```http
GET /api/v1/lure-types/{id}
```

#### 更新拟饵类型

```http
PUT /api/v1/lure-types/{id}
```

#### 删除拟饵类型

```http
DELETE /api/v1/lure-types/{id}
```

#### 初始化数据

```http
GET /api/v1/lure-types/init-data
```

---

## 钓组配置管理API

### 钓组CRUD

#### 获取钓组列表

```http
GET /api/v1/rigs
```

**查询参数:**
- `page`: 页码
- `page_size`: 每页数量
- `category`: 分类过滤（bottom/float/lure/fly/surf）
- `difficulty`: 难度过滤（easy/medium/hard）

#### 创建钓组

```http
POST /api/v1/rigs
```

**请求体:**
```json
{
  "name": "德州钓组",
  "category": "lure",
  "description": "最经典的路亚钓组之一",
  "difficulty": "medium",
  "target_species": "黑鲈、鳜鱼",
  "best_conditions": "水草区、障碍区",
  "specs": [
    {
      "spec_name": "适用竿长",
      "spec_value": "2.1-2.4m",
      "unit": "m"
    }
  ],
  "components": [
    {
      "component_name": "子弹铅",
      "component_type": "sinker",
      "quantity": 1,
      "position": 1
    },
    {
      "component_name": "珠子",
      "component_type": "bead",
      "quantity": 1,
      "position": 2
    },
    {
      "component_name": "曲柄钩",
      "component_type": "hook",
      "quantity": 1,
      "position": 3
    }
  ],
  "lure_types": [1, 2, 3]
}
```

#### 获取钓组详情

```http
GET /api/v1/rigs/{id}
```

#### 更新钓组

```http
PUT /api/v1/rigs/{id}
```

#### 删除钓组

```http
DELETE /api/v1/rigs/{id}
```

### 钓组选项

#### 获取钓组选项数据

```http
GET /api/v1/rigs/options
```

**响应示例:**
```json
{
  "categories": [
    {"value": "bottom", "label": "底钓钓组", "icon": "🎣"},
    {"value": "lure", "label": "路亚钓组", "icon": "🐟"}
  ],
  "difficulties": [
    {"value": "easy", "label": "简单", "color": "success"},
    {"value": "medium", "label": "中等", "color": "warning"}
  ],
  "component_types": [
    {"value": "hook", "label": "鱼钩"},
    {"value": "sinker", "label": "铅坠"},
    {"value": "swivel", "label": "转环"}
  ]
}
```

---

## 数据导入API

### Excel导入

#### 生成导入模板

```http
POST /api/v1/admin/workflow/import/templates
```

**请求体:**
```json
{
  "equipment_type": "rod",
  "format": "xlsx"
}
```

**响应:**
- Excel文件下载，包含完整的字段定义和示例数据

#### 预览导入

```http
POST /api/v1/admin/workflow/import/preview
```

**请求体:**
```multipart/form-data
file: Excel文件
equipment_type: rod
```

**响应示例:**
```json
{
  "success": true,
  "total_rows": 100,
  "valid_rows": 95,
  "error_rows": 5,
  "data": [
    {
      "row": 2,
      "brand_name": "达亿瓦",
      "name": "黑纹鲤",
      "model": "C3000MHG",
      "price_min": 500,
      "price_max": 800,
      "errors": []
    }
  ],
  "errors": [
    {
      "row": 15,
      "field": "price_min",
      "message": "价格必须是数字"
    }
  ]
}
```

#### 执行导入

```http
POST /api/v1/admin/workflow/import/execute
```

**请求体:**
```json
{
  "equipment_type": "rod",
  "source_type": "excel",
  "data": [
    {
      "brand_name": "达亿瓦",
      "name": "黑纹鲤",
      "model": "C3000MHG",
      "price_min": 500,
      "price_max": 800
    }
  ]
}
```

**响应示例:**
```json
{
  "success": true,
  "imported_count": 95,
  "failed_count": 5,
  "pending_ids": [1, 2, 3, ...],
  "message": "导入完成，95条成功，5条失败"
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

**错误响应示例:**
```json
{
  "detail": "鱼种名称已存在",
  "error_code": "DUPLICATE_NAME",
  "field": "name"
}
```

---

## 权限要求

所有内容管理API都需要以下权限之一：

- `CONTENT_VIEW`: 查看内容
- `CONTENT_CREATE`: 创建内容
- `CONTENT_UPDATE`: 更新内容
- `CONTENT_DELETE`: 删除内容

使用JWT Token进行认证：
```http
Authorization: Bearer <token>
```

---

## 使用示例

### Python示例

```python
import requests

# 设置API地址
BASE_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

# 设置请求头
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建鱼种
response = requests.post(
    f"{BASE_URL}/api/v1/fish-species",
    json={
        "name": "大嘴鲈",
        "category": "freshwater",
        "description": "淡水路亚热门鱼种"
    },
    headers=headers
)
print(response.json())

# 搜索文章
response = requests.get(
    f"{BASE_URL}/api/v1/articles/search",
    params={"q": "春季路亚", "top_k": 5},
    headers=headers
)
print(response.json())

# 获取配件列表
response = requests.get(
    f"{BASE_URL}/api/v1/accessory",
    params={"category": "hook", "page": 1, "page_size": 20},
    headers=headers
)
print(response.json())
```

### JavaScript示例

```javascript
const BASE_URL = 'http://localhost:8000';
const TOKEN = 'your-jwt-token';

// 设置请求头
const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// 创建钓组
async function createRig() {
  const response = await fetch(`${BASE_URL}/api/v1/rigs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      name: '德州钓组',
      category: 'lure',
      description: '最经典的路亚钓组',
      difficulty: 'medium'
    })
  });
  const data = await response.json();
  console.log(data);
}

// 搜索文章
async function searchArticles() {
  const response = await fetch(
    `${BASE_URL}/api/v1/articles/search?q=春季路亚&top_k=5`,
    { headers }
  );
  const data = await response.json();
  console.log(data);
}
```

---

## 相关文档

- [系统架构](../../03-architecture/system-design.md)
- [数据库模型](../../03-architecture/database-models.md)
- [开发流程](../../02-developer-guide/development-workflows.md)
- [API认证](./authentication.md)
