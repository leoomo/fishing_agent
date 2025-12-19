# 装备爬虫使用指南

**版本**: v3.1.1
**最后更新**: 2024-12-03

## 概述

装备爬虫模块用于自动从电商网站和论坛爬取路亚装备信息，并自动入库到装备数据库。支持淘宝、京东和路亚论坛三个数据源。

### 核心功能

- **多源爬取**: 支持淘宝、京东、路亚论坛
- **反爬虫策略**: UA轮换、请求延迟、错误重试
- **智能去重**: 3级去重策略（精确匹配/模糊匹配/规格匹配）
- **数据持久化**: 自动保存装备信息、规格、图片
- **增量更新**: 支持定期同步更新价格和库存

---

## 快速开始

### 安装依赖

爬虫模块的依赖已包含在项目中：

```bash
uv sync
```

主要依赖：
- `beautifulsoup4>=4.12.0` - HTML解析
- `lxml>=5.0.0` - 高性能解析器
- `fake-useragent>=1.4.0` - UA轮换
- `requests` - HTTP客户端

### 基础使用

```python
from packages.agent_fishing.tools.crawler import (
    JDSpider,
    TaobaoSpider,
    ForumSpider,
    DataPersister
)
from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.lure.image_manager import ImageManager

# 初始化
db = get_db()
image_manager = ImageManager()
persister = DataPersister(db, image_manager)

# 使用京东爬虫
jd_spider = JDSpider()
equipment_list = jd_spider.search_equipment(
    keyword="路亚竿",
    category="鱼竿",
    max_results=20
)

# 保存数据
for equipment in equipment_list:
    equipment_id = persister.save_equipment(equipment)
    print(f"保存装备: {equipment.name} (ID:{equipment_id})")

# 查看统计
stats = persister.get_stats()
print(f"总处理: {stats['total_processed']}")
print(f"插入: {stats['inserted']}")
print(f"更新: {stats['updated']}")
print(f"跳过: {stats['duplicates_skipped']}")
```

---

## 爬虫详解

### 1. 京东爬虫 (JDSpider)

**特点**:
- API结构清晰，稳定性高
- 数据完整度最好
- 反爬虫强度中等

**使用示例**:

```python
from packages.agent_fishing.tools.crawler import JDSpider

spider = JDSpider()

# 搜索装备
results = spider.search_equipment(
    keyword="达亿瓦渔轮",
    category="渔轮",
    max_results=50
)

print(f"找到 {len(results)} 件装备")

# 获取详情
for equipment in results[:3]:
    print(f"\n装备: {equipment.name}")
    print(f"品牌: {equipment.brand_name}")
    print(f"价格: ¥{equipment.price_min}")
    print(f"规格: {equipment.specs}")
    print(f"图片: {len(equipment.images)}张")
```

**支持的类别**:
- 鱼竿 (rod, 路亚竿, 鱼竿)
- 渔轮 (reel, 渔轮, 纺车轮)
- 鱼线 (line, 鱼线, PE线)
- 拟饵 (lure, 拟饵, 路亚饵)

### 2. 淘宝爬虫 (TaobaoSpider)

**特点**:
- 商品数量最多
- 反爬虫最严格
- 使用移动端API（简化版）

**使用示例**:

```python
from packages.agent_fishing.tools.crawler import TaobaoSpider

spider = TaobaoSpider()

# 搜索装备
results = spider.search_equipment(
    keyword="禧玛诺鱼竿",
    category="鱼竿",
    max_results=30
)

# 获取单个商品详情
if results:
    detail = spider.get_product_detail(results[0].source_url)
    print(f"详情: {detail.description}")
```

**注意事项**:
- 请求频率不要太高（建议2-5秒间隔）
- 可能需要定期更换IP
- 移动端接口数据较简化

### 3. 论坛爬虫 (ForumSpider)

**特点**:
- 真实用户评测和测评
- 数据质量高但数量少
- 适合补充装备详细信息

**使用示例**:

```python
from packages.agent_fishing.tools.crawler import ForumSpider

spider = ForumSpider()

# 搜索装备评测帖
results = spider.search_equipment(
    keyword="毒牙评测",
    category="鱼竿",
    max_results=10
)

# 论坛爬虫侧重评测内容
for equipment in results:
    print(f"\n标题: {equipment.name}")
    print(f"评测内容: {equipment.description[:200]}...")
    print(f"来源: {equipment.source_url}")
```

---

## 反爬虫策略

### UA 轮换

```python
from packages.agent_fishing.tools.crawler import UserAgentRotator

ua_rotator = UserAgentRotator()

# 获取随机UA
headers = ua_rotator.get_headers(referer="https://www.jd.com")
print(headers["User-Agent"])

# 内置12个真实浏览器UA
```

### 请求延迟

```python
from packages.agent_fishing.tools.crawler import RequestThrottler

throttler = RequestThrottler(min_delay=2.0, max_delay=5.0)

# 每次请求前等待
throttler.wait()  # 随机等待2-5秒
```

### 错误重试

BaseSpider 内置指数退避重试：

```python
# 自动重试配置
max_retries = 3  # 最多重试3次
initial_delay = 1  # 初始延迟1秒
exponential_base = 2  # 指数基数

# 重试间隔: 1秒, 2秒, 4秒
```

### 代理轮换 (可选)

```python
from packages.agent_fishing.tools.crawler import ProxyRotator

# 配置代理池
proxy_rotator = ProxyRotator([
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://proxy3:8080"
])

# 获取随机代理
proxies = proxy_rotator.get_proxy()
response = requests.get(url, proxies=proxies)
```

---

## 数据去重

### 去重策略

爬虫使用3级去重策略，按优先级依次检查：

#### 优先级1: 精确匹配

```python
# 品牌 + 型号完全匹配
if brand_name == existing_brand and model == existing_model:
    return existing_id
```

**示例**:
- 禧玛诺 + ZODIAS 264ML
- 达亿瓦 + BASS X 662ML

#### 优先级2: 模糊匹配

```python
# 品牌 + 名称相似度 > 80%
from difflib import SequenceMatcher

similarity = SequenceMatcher(None, name1, name2).ratio()
if brand_name == existing_brand and similarity > 0.8:
    return existing_id
```

**示例**:
- "禧玛诺毒牙鱼竿ML" vs "禧玛诺 毒牙 ML调路亚竿" (相似度: 85%)

#### 优先级3: 规格匹配

```python
# 类别 + 关键规格匹配
if category == "鱼竿":
    if length == existing_length and power == existing_power:
        return existing_id
```

**关键规格**:
- 鱼竿: 长度 + 硬度
- 渔轮: 轮型 + 速比
- 鱼线: 线型 + 线径 + 拉力
- 拟饵: 饵型 + 长度 + 重量

### 使用去重器

```python
from packages.agent_fishing.tools.crawler import EquipmentDeduplicator, EquipmentData

db = get_db()
deduplicator = EquipmentDeduplicator(db)

# 检查是否重复
equipment = EquipmentData(
    name="禧玛诺ZODIAS 264ML",
    brand_name="禧玛诺",
    model="264ML",
    category="鱼竿",
    # ...
)

existing_id = deduplicator.find_duplicates(equipment)
if existing_id:
    print(f"装备已存在: ID={existing_id}")
else:
    print("装备不重复，可以添加")
```

---

## 数据持久化

### 完整流程

DataPersister 自动处理完整的数据保存流程：

```python
from packages.agent_fishing.tools.crawler import DataPersister

persister = DataPersister(db, image_manager)

# 保存装备（自动处理所有步骤）
equipment_id = persister.save_equipment(equipment, update_if_exists=True)

# 流程包括：
# 1. 检查去重
# 2. 确保品牌存在（不存在则自动创建）
# 3. 插入装备主表
# 4. 插入规格表（rod_specs/reel_specs/line_specs/lure_specs）
# 5. 下载并保存图片
```

### 增量更新策略

```python
# update_if_exists=True: 更新动态字段
equipment_id = persister.save_equipment(equipment, update_if_exists=True)

# 更新的字段：
# - price_min, price_max (价格)
# - description (描述)
# - last_synced_at (同步时间)

# 不更新的字段：
# - equipment_name, brand_id, model (基础信息)
# - 规格表数据
```

### 图片下载

```python
from packages.agent_fishing.tools.crawler import ImageDownloader

downloader = ImageDownloader(image_manager)

# 下载单张图片
local_path = downloader.download_and_save(
    image_url="https://example.com/image.jpg",
    equipment_name="禧玛诺ZODIAS",
    image_type="main"
)

# 批量下载
image_urls = [
    {"url": "https://...", "type": "main"},
    {"url": "https://...", "type": "detail"},
]
local_images = downloader.download_multiple(image_urls, "禧玛诺ZODIAS")
```

**图片存储格式**:
```
shared/data/images/equipment/
└── crawler/
    ├── jd_shimano_zodias_main_a1b2c3.jpg
    ├── jd_shimano_zodias_detail_d4e5f6.jpg
    └── taobao_daiwa_bassx_main_g7h8i9.jpg
```

---

## 批量爬取

### 方案1: 多关键词爬取

```python
from packages.agent_fishing.tools.crawler import JDSpider, DataPersister

spider = JDSpider()
persister = DataPersister(db, image_manager)

# 定义关键词列表
keywords = [
    ("禧玛诺", "鱼竿"),
    ("达亿瓦", "鱼竿"),
    ("光威", "鱼竿"),
    ("禧玛诺", "渔轮"),
    ("达亿瓦", "渔轮"),
]

# 批量爬取
for keyword, category in keywords:
    print(f"\n爬取: {keyword} - {category}")

    results = spider.search_equipment(
        keyword=keyword,
        category=category,
        max_results=50
    )

    # 保存数据
    for equipment in results:
        try:
            equipment_id = persister.save_equipment(equipment)
            print(f"✅ {equipment.name} (ID:{equipment_id})")
        except Exception as e:
            print(f"❌ 保存失败: {e}")

    # 请求延迟
    import time
    time.sleep(5)  # 每个关键词间隔5秒

# 查看统计
stats = persister.get_stats()
print(f"\n统计:")
print(f"总处理: {stats['total_processed']}")
print(f"插入: {stats['inserted']}")
print(f"更新: {stats['updated']}")
print(f"跳过: {stats['duplicates_skipped']}")
print(f"错误: {stats['errors']}")
```

### 方案2: 多源爬取

```python
from packages.agent_fishing.tools.crawler import JDSpider, TaobaoSpider, DataPersister

persister = DataPersister(db, image_manager)

# 从京东爬取
jd_spider = JDSpider()
jd_results = jd_spider.search_equipment("路亚竿", "鱼竿", max_results=30)
for eq in jd_results:
    persister.save_equipment(eq)

# 从淘宝爬取
taobao_spider = TaobaoSpider()
taobao_results = taobao_spider.search_equipment("路亚竿", "鱼竿", max_results=30)
for eq in taobao_results:
    persister.save_equipment(eq)

# 去重器会自动处理重复数据
```

---

## 定时任务

### 使用 cron 定时爬取

```bash
# 编辑 crontab
crontab -e

# 每天凌晨2点爬取装备数据
0 2 * * * cd /path/to/fishing_agent && uv run python scripts/crawl_equipment.py >> logs/crawler.log 2>&1

# 每周日凌晨3点增量更新价格
0 3 * * 0 cd /path/to/fishing_agent && uv run python scripts/update_prices.py >> logs/update.log 2>&1
```

### 爬取脚本示例

创建 `scripts/crawl_equipment.py`:

```python
#!/usr/bin/env python3
"""
定时爬取装备数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from packages.agent_fishing.tools.crawler import JDSpider, DataPersister
from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.lure.image_manager import ImageManager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    db = get_db()
    image_manager = ImageManager()
    persister = DataPersister(db, image_manager)
    spider = JDSpider()

    # 定义爬取任务
    tasks = [
        ("禧玛诺路亚竿", "鱼竿", 50),
        ("达亿瓦路亚竿", "鱼竿", 50),
        ("光威路亚竿", "鱼竿", 30),
        ("禧玛诺渔轮", "渔轮", 50),
        ("达亿瓦渔轮", "渔轮", 50),
    ]

    for keyword, category, max_results in tasks:
        logging.info(f"开始爬取: {keyword} - {category}")

        try:
            results = spider.search_equipment(keyword, category, max_results)

            for equipment in results:
                try:
                    equipment_id = persister.save_equipment(equipment)
                    logging.info(f"保存成功: {equipment.name} (ID:{equipment_id})")
                except Exception as e:
                    logging.error(f"保存失败: {e}")

            import time
            time.sleep(10)  # 任务间隔10秒

        except Exception as e:
            logging.error(f"爬取失败: {e}")

    # 输出统计
    stats = persister.get_stats()
    logging.info(f"爬取完成: 总处理={stats['total_processed']}, "
                f"插入={stats['inserted']}, 更新={stats['updated']}, "
                f"跳过={stats['duplicates_skipped']}, 错误={stats['errors']}")

if __name__ == "__main__":
    main()
```

---

## 常见问题

### Q1: 爬取速度太慢？

A: 可以适当减少延迟，但需要注意反爬虫：

```python
# 调整延迟（谨慎使用）
throttler = RequestThrottler(min_delay=1.0, max_delay=2.0)

# 或并发爬取（高级）
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(spider.search_equipment, kw, cat)
               for kw, cat in keywords]
    results = [f.result() for f in futures]
```

### Q2: 遇到验证码或封IP？

A: 解决方案：
1. 增加请求延迟（3-10秒）
2. 使用代理池轮换IP
3. 降低爬取频率
4. 使用多个数据源

```python
# 配置代理
proxies = {
    "http": "http://proxy:8080",
    "https": "http://proxy:8080"
}

spider = JDSpider(proxies=proxies)
```

### Q3: 图片下载失败？

A: 常见原因：
1. 图片URL失效
2. 防盗链限制
3. 网络超时

解决方案：
```python
# 增加超时时间
downloader = ImageDownloader(
    image_manager,
    timeout=30  # 30秒超时
)

# 添加referer绕过防盗链
headers = {
    "Referer": "https://www.jd.com"
}
```

### Q4: 数据重复？

A: 检查去重器配置：

```python
# 调整相似度阈值
deduplicator = EquipmentDeduplicator(db)
deduplicator.similarity_threshold = 0.85  # 提高到85%

# 检查去重日志
import logging
logging.getLogger("packages.agent_fishing.tools.crawler").setLevel(logging.DEBUG)
```

### Q5: 如何清理失效数据？

A: 清理脚本：

```python
from packages.agent_fishing.tools.lure.database import get_db
from datetime import datetime, timedelta

db = get_db()

# 删除90天未同步的爬虫数据
cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
db.execute_write("""
    DELETE FROM equipment
    WHERE source = 'crawler'
    AND (last_synced_at IS NULL OR last_synced_at < ?)
""", (cutoff_date,))

print("清理完成")
```

---

## 最佳实践

### 1. 分阶段爬取

**阶段1: 初始化数据**
- 爬取主流品牌（禧玛诺、达亿瓦、光威等）
- 每个品牌爬取50-100件装备
- 优先爬取评价高、销量好的商品

**阶段2: 补充数据**
- 爬取中端和高端品牌
- 补充冷门但口碑好的装备
- 关注新品发布

**阶段3: 定期更新**
- 每周增量更新价格
- 每月全量更新热门商品
- 清理失效数据

### 2. 数据质量控制

```python
# 过滤低质量数据
def is_valid_equipment(equipment):
    # 价格合理性
    if equipment.price_min < 10 or equipment.price_min > 10000:
        return False

    # 描述完整性
    if not equipment.description or len(equipment.description) < 20:
        return False

    # 品牌有效性
    if equipment.brand_name in ["不详", "未知", "其他"]:
        return False

    return True

# 应用过滤
results = spider.search_equipment(keyword, category, max_results=100)
valid_results = [eq for eq in results if is_valid_equipment(eq)]
```

### 3. 监控和告警

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/crawler.log'),
        logging.StreamHandler()
    ]
)

# 监控关键指标
stats = persister.get_stats()
success_rate = stats['inserted'] / stats['total_processed'] if stats['total_processed'] > 0 else 0

if success_rate < 0.5:
    logging.warning(f"⚠️ 成功率过低: {success_rate:.1%}")
    # 发送告警通知

if stats['errors'] > 10:
    logging.error(f"❌ 错误数过多: {stats['errors']}")
    # 发送告警通知
```

---

## 下一步

- 查看 [用户装备管理指南](./USER_EQUIPMENT_GUIDE.md) 了解如何使用爬取的数据
- 查看 [API 参考](./API_REFERENCE.md) 了解完整接口
- 查看主 [README](../README.md) 了解项目架构
