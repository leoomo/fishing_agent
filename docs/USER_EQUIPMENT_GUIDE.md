# 用户装备管理使用指南

**版本**: v3.1.1
**最后更新**: 2024-12-03

## 概述

用户装备管理模块允许用户创建个人装备库，记录已购买的路亚装备，并获得基于已有装备的智能推荐。

### 核心功能

- **装备库管理**: 添加、查询、删除装备记录
- **统计分析**: 装备数量、花费、类别分布统计
- **智能推荐**: 基于用户已有装备推荐升级、完善配置或搭配建议
- **Agent集成**: 通过自然语言与Agent对话管理装备

---

## 快速开始

### 1. 创建用户

使用 API 创建用户账户：

```bash
curl -X POST http://localhost:8000/api/v1/user-equipment/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "fishing_lover_001",
    "nickname": "路亚小白",
    "user_level": "新手",
    "fishing_experience_years": 1,
    "preferred_fish": "鲈鱼"
  }'
```

响应：
```json
{
  "success": true,
  "message": "用户创建成功",
  "data": {
    "user_id": 1,
    "username": "fishing_lover_001"
  }
}
```

### 2. 添加装备到装备库

```bash
curl -X POST http://localhost:8000/api/v1/user-equipment/users/1/equipment \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": 1,
    "purchase_price": 680.0,
    "purchase_date": "2024-01-15",
    "notes": "第一把路亚竿"
  }'
```

### 3. 查询装备列表

```bash
curl http://localhost:8000/api/v1/user-equipment/users/1/equipment
```

响应：
```json
{
  "total": 3,
  "equipment_list": [
    {
      "id": 1,
      "equipment_name": "禧玛诺ZODIAS 264ML",
      "category": "鱼竿",
      "brand_name": "禧玛诺",
      "purchase_price": 680.0,
      "purchase_date": "2024-01-15",
      "is_favorite": false
    }
  ]
}
```

---

## Agent 对话使用

### 查看装备库

用户可以通过自然语言与 Agent 对话：

```
用户: 查看我的装备库
Agent: [调用 list_my_equipment 工具]

# 我的装备库

## 鱼竿 (2件)

### ⭐ 禧玛诺ZODIAS 264ML
- **品牌型号**: 禧玛诺 264ML
- **购买价格**: ¥680.00
- **购买日期**: 2024-01-15

### 达亿瓦BASS X 662ML
- **品牌型号**: 达亿瓦 662ML
- **购买价格**: ¥450.00

---

**装备总数**: 2件
**收藏数**: 1件
**总花费**: ¥1130.00
```

### 添加装备

```
用户: 我刚买了一个禧玛诺毒牙鱼竿，价格680元，帮我记录一下
Agent: [调用 add_equipment_to_profile 工具]

✅ 成功添加装备到装备库

**装备**: 禧玛诺ZODIAS 264ML
**价格**: ¥680.00

您可以使用 `list_my_equipment` 查看完整装备库。
```

### 获取推荐

```
用户: 我的装备还缺什么？
Agent: [调用 recommend_based_on_my_equipment 工具，类型：complete]

# 装备配置完善建议

## ⚠️ 基础装备缺失

路亚钓鱼的基础三件套（鱼竿、渔轮、鱼线）缺少以下装备：

### 渔轮
**推荐装备** (根据您的水平：新手):

1. **达亿瓦 REVROS LT2000S**
   - 品牌: 达亿瓦
   - 价格: ¥299.00 - ¥349.00
   - 说明: 性价比极高的入门纺车轮...
```

---

## API 参考

### 用户管理

#### 创建用户

```
POST /api/v1/user-equipment/users
```

**请求体**:
```json
{
  "username": "string (必填，3-50字符)",
  "nickname": "string (可选)",
  "email": "string (可选)",
  "user_level": "新手|进阶|高手 (默认：新手)",
  "fishing_experience_years": "integer (可选)",
  "preferred_fish": "string (可选)"
}
```

**响应**: `201 Created`
```json
{
  "success": true,
  "message": "用户创建成功",
  "data": {
    "user_id": 1,
    "username": "fishing_lover_001"
  }
}
```

#### 获取用户信息

```
GET /api/v1/user-equipment/users/{user_id}
```

**响应**: `200 OK`
```json
{
  "user_id": 1,
  "username": "fishing_lover_001",
  "nickname": "路亚小白",
  "user_level": "新手",
  "fishing_experience_years": 1,
  "preferred_fish": "鲈鱼",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

### 装备管理

#### 添加装备

```
POST /api/v1/user-equipment/users/{user_id}/equipment
```

**请求体**:
```json
{
  "equipment_id": 1,
  "purchase_price": 680.0,
  "purchase_date": "2024-01-15",
  "purchase_source": "淘宝",
  "notes": "第一把路亚竿",
  "tags": ["入门", "ML调"]
}
```

**响应**: `201 Created`

#### 查询装备列表

```
GET /api/v1/user-equipment/users/{user_id}/equipment?category=鱼竿&only_favorites=false
```

**查询参数**:
- `category` (可选): 装备类别过滤（鱼竿/渔轮/鱼线/拟饵）
- `only_favorites` (可选): 仅显示收藏装备（默认 false）

**响应**: `200 OK`
```json
{
  "total": 3,
  "equipment_list": [...]
}
```

#### 删除装备

```
DELETE /api/v1/user-equipment/users/{user_id}/equipment/{equipment_id}
```

**响应**: `200 OK`
```json
{
  "success": true,
  "message": "装备删除成功",
  "data": {
    "equipment_id": 1
  }
}
```

---

### 推荐功能

#### 基于用户装备推荐

```
POST /api/v1/user-equipment/users/{user_id}/recommend
```

**请求体**:
```json
{
  "need_type": "upgrade|complete|match"
}
```

**推荐类型说明**:
- `upgrade`: 升级推荐 - 推荐更高级的同类装备
- `complete`: 完善推荐 - 推荐缺失的装备类型
- `match`: 搭配推荐 - 分析装备是否匹配并给出建议

**响应**: `200 OK`
```json
{
  "recommendation": "# 装备升级推荐\n\n...",
  "need_type": "upgrade"
}
```

---

### 统计功能

#### 获取装备统计

```
GET /api/v1/user-equipment/users/{user_id}/statistics
```

**响应**: `200 OK`
```json
{
  "user_id": 1,
  "total_count": 5,
  "total_spent": 2150.0,
  "favorite_count": 2,
  "by_category": [
    {
      "category": "鱼竿",
      "count": 2,
      "avg_price": 565.0,
      "total_price": 1130.0
    },
    {
      "category": "渔轮",
      "count": 2,
      "avg_price": 350.0,
      "total_price": 700.0
    }
  ]
}
```

---

## LangChain 工具说明

### 1. list_my_equipment

查看用户的装备库。

**参数**:
- `user_id` (int, 必填): 用户ID
- `category` (str, 可选): 装备类别过滤
- `only_favorites` (bool, 可选): 仅显示收藏装备

**触发关键词**: 我的装备、我有哪些、查看装备库、装备清单

**示例**:
```python
from packages.agent_fishing.tools.user_equipment.tools import list_my_equipment

result = list_my_equipment.invoke({
    "user_id": 1,
    "category": "鱼竿",
    "only_favorites": False
})
print(result)
```

### 2. add_equipment_to_profile

添加装备到用户装备库。

**参数**:
- `user_id` (int, 必填): 用户ID
- `equipment_id` (int, 必填): 装备ID
- `purchase_price` (float, 可选): 购买价格
- `purchase_date` (str, 可选): 购买日期 (格式: YYYY-MM-DD)
- `notes` (str, 可选): 备注

**触发关键词**: 添加装备、我买了、记录一下、加入装备库

### 3. remove_equipment_from_profile

从装备库删除装备。

**参数**:
- `user_id` (int, 必填): 用户ID
- `equipment_id` (int, 必填): 装备ID

**触发关键词**: 删除装备、移除装备、卖了、不要了

### 4. recommend_based_on_my_equipment

基于用户已有装备推荐新装备。

**参数**:
- `user_id` (int, 必填): 用户ID
- `need_type` (str, 必填): 推荐类型 (upgrade/complete/match)

**触发关键词**: 升级、搭配、配什么、买什么好、装备推荐

---

## 推荐算法详解

### 升级推荐 (upgrade)

**策略**:
1. 分析用户装备的平均水平（入门/中端/高端/旗舰）
2. 识别薄弱环节（低于平均水平的装备）
3. 推荐同类更高一级的装备

**适用场景**:
- 用户想要升级现有装备
- 预算充足，追求更好性能
- 已有基础装备，想提升整体配置

**示例输出**:
```markdown
# 装备升级推荐

分析您的 3 件装备后，发现以下升级建议：

## 1. 鱼竿 - 光威 路亚竿M调

**当前装备**: 光威 LY-M-2.1
**购买价格**: ¥299.99

**升级建议** (共2个选项):

1. **禧玛诺ZODIAS 264ML**
   - 品牌: 禧玛诺
   - 价格区间: ¥680.00 - ¥680.00
   - 特点: 经典入门级路亚竿...
```

### 完善推荐 (complete)

**策略**:
1. 检查基础三件套是否齐全（鱼竿、渔轮、鱼线）
2. 推荐缺失的装备类型
3. 推荐拟饵组合（如果没有拟饵）

**适用场景**:
- 新手刚入门，装备不全
- 缺少关键装备类型
- 想了解还需要购买什么

**示例输出**:
```markdown
# 装备配置完善建议

## ⚠️ 基础装备缺失

路亚钓鱼的基础三件套缺少以下装备：

### 渔轮

**推荐装备** (根据您的水平：新手):

1. **达亿瓦 REVROS LT2000S**
   - 品牌: 达亿瓦
   - 价格: ¥299.00
```

### 搭配推荐 (match)

**策略**:
1. 检查鱼竿和渔轮是否匹配（长度、硬度、轮型）
2. 检查鱼线拉力是否适配鱼竿
3. 给出装备搭配建议和优化方案

**适用场景**:
- 验证现有装备是否合理搭配
- 购买新装备前确认兼容性
- 优化装备组合性能

**示例输出**:
```markdown
# 装备搭配分析

## 装备完整性检查

✅ 鱼竿: 2件 | ✅ 渔轮: 1件 | ✅ 鱼线: 1件

## 鱼竿 - 渔轮 搭配分析

### 禧玛诺ZODIAS 264ML

**规格**: 长度 2.64m | 硬度 ML

**匹配的渔轮**:
- ✅ 达亿瓦 REVROS LT2000S
```

---

## 最佳实践

### 1. 定期更新装备库

建议在购买新装备后及时添加到装备库，便于：
- 追踪装备投资
- 获得准确的推荐
- 分析装备使用情况

### 2. 使用标签分类

为装备添加标签，便于管理：
```json
{
  "tags": ["ML调", "岸钓", "常用"]
}
```

### 3. 记录购买信息

完整记录购买信息有助于：
- 计算装备总投资
- 评估性价比
- 保修和售后

### 4. 利用推荐功能

定期使用推荐功能：
- **新手**: 使用 `complete` 推荐完善配置
- **进阶**: 使用 `upgrade` 推荐升级装备
- **购买前**: 使用 `match` 检查搭配

---

## 常见问题

### Q1: equipment_id 从哪里获取？

A: 使用装备推荐工具或直接查询装备数据库：

```bash
# 方式1: 使用 Agent 推荐工具
用户: "推荐一款入门级路亚竿"
Agent: [返回推荐结果，包含 equipment_id]

# 方式2: 直接查询数据库
curl http://localhost:8000/api/v1/fishing/equipment?category=鱼竿
```

### Q2: 如何批量添加装备？

A: 循环调用添加接口：

```python
from packages.agent_fishing.tools.user_equipment import UserEquipmentManager
from packages.agent_fishing.tools.lure.database import get_db

db = get_db()
manager = UserEquipmentManager(db)

equipment_list = [
    {"equipment_id": 1, "purchase_price": 680.0},
    {"equipment_id": 2, "purchase_price": 350.0},
    {"equipment_id": 3, "purchase_price": 89.0},
]

for equipment in equipment_list:
    manager.add_equipment(
        user_id=1,
        equipment_id=equipment["equipment_id"],
        purchase_price=equipment["purchase_price"]
    )
```

### Q3: 推荐结果为空？

A: 可能原因：
1. 数据库中该类别装备数据较少
2. 没有符合条件的装备（用户水平、价格范围）
3. 用户装备库为空（upgrade 推荐需要已有装备）

解决方案：
- 使用爬虫补充装备数据
- 手动录入常见装备
- 调整推荐策略参数

### Q4: 如何导出装备库数据？

A: 使用统计接口获取数据后导出：

```python
import requests
import json

response = requests.get("http://localhost:8000/api/v1/user-equipment/users/1/equipment")
equipment_list = response.json()["equipment_list"]

# 导出为 JSON
with open("my_equipment.json", "w", encoding="utf-8") as f:
    json.dump(equipment_list, f, ensure_ascii=False, indent=2)

# 或导出为 CSV
import csv
with open("my_equipment.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=equipment_list[0].keys())
    writer.writeheader()
    writer.writerows(equipment_list)
```

---

## 下一步

- 查看 [爬虫使用指南](./CRAWLER_GUIDE.md) 了解如何补充装备数据
- 查看 [API 完整参考](./API_REFERENCE.md) 了解所有接口
- 查看主 [README](../README.md) 了解项目整体架构
