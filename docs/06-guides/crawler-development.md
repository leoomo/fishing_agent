# 爬虫开发指南 v5.0.2

深入理解和开发智能钓鱼助手的数据采集系统，包括分布式爬虫、RPA自动化、任务调度和数据持久化。

## 📋 目录

- [系统架构](#系统架构)
- [核心组件](#核心组件)
- [开发流程](#开发流程)
- [实战案例](#实战案例)
- [性能优化](#性能优化)
- [监控告警](#监控告警)
- [故障排除](#故障排除)

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                       爬虫管理系统                            │
├─────────────────────────────────────────────────────────────┤
│  Master Node (Control Plane)                                │
│  ├── Task Scheduler (任务调度)                               │
│  ├── Task Queue (任务队列)                                  │
│  ├── Monitor Service (监控服务)                             │
│  └── API Gateway (API网关)                                  │
├─────────────────────────────────────────────────────────────┤
│  Worker Nodes (执行节点)                                    │
│  ├── Worker 1 (任务执行器)                                  │
│  ├── Worker 2 (任务执行器)                                  │
│  └── Worker N (任务执行器)                                  │
├─────────────────────────────────────────────────────────────┤
│  Data Layer (数据层)                                        │
│  ├── Task Database (任务数据库)                             │
│  ├── Result Database (结果数据库)                           │
│  └── Cache Layer (缓存层)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 核心特性

- **分布式架构**: 支持多节点水平扩展
- **任务调度**: 基于Cron表达式的灵活调度
- **断点续传**: 支持任务中断后从断点继续
- **失败重试**: 自动重试机制，可配置重试策略
- **实时监控**: WebSocket实时推送任务状态
- **数据持久化**: 完整的任务生命周期管理

## 🧩 核心组件

### 1. Spider (爬虫核心)

爬虫的核心抽象类，定义了爬虫的基本接口。

```python
# packages/scraper/spider/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from packages.scraper.models import CrawlItem

class BaseSpider(ABC):
    """爬虫基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None

    @abstractmethod
    async def crawl(self, keywords: List[str], **kwargs) -> List[CrawlItem]:
        """爬取数据的核心方法"""
        pass

    @abstractmethod
    async def parse(self, response: str) -> List[CrawlItem]:
        """解析响应数据"""
        pass

    async def setup(self):
        """爬虫初始化"""
        pass

    async def cleanup(self):
        """爬虫清理"""
        pass
```

### 2. Platform (平台抽象层)

针对不同电商平台的具体实现。

```python
# packages/scraper/platform/taobao_platform.py
class TaobaoPlatform(BasePlatform):
    """淘宝平台爬虫实现"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://s.taobao.com"
        self.search_url = "https://s.taobao.com/search"

    async def search(self, keyword: str, page: int = 1) -> List[CrawlItem]:
        """搜索商品"""
        params = {
            "q": keyword,
            "s": (page - 1) * 44,  # 每页44个商品
            "sort": "sale-desc"     # 按销量排序
        }

        headers = self._get_headers()
        response = await self.session.get(self.search_url, params=params, headers=headers)

        return await self.parse_search_results(response.text)

    async def get_product_detail(self, product_id: str) -> CrawlItem:
        """获取商品详情"""
        detail_url = f"https://detail.tmall.com/item.htm?id={product_id}"
        response = await self.session.get(detail_url)
        return await self.parse_product_detail(response.text)
```

### 3. RPA (机器人自动化)

对于需要JavaScript渲染的反爬虫页面，使用RPA技术。

```python
# packages/scraper/rpa/taobao_rpa.py
from playwright.async_api import async_playwright

class TaobaoRPA:
    """淘宝RPA爬虫"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()

    async def search_products(self, keyword: str, max_pages: int = 5):
        """搜索商品"""
        await self.page.goto("https://www.taobao.com")

        # 输入搜索关键词
        await self.page.fill("#q", keyword)
        await self.page.click(".btn-search")

        # 等待搜索结果加载
        await self.page.wait_for_selector(".item")

        products = []
        for page_num in range(max_pages):
            # 提取当前页商品信息
            page_products = await self._extract_products()
            products.extend(page_products)

            # 点击下一页
            next_button = await self.page.query_selector(".next")
            if next_button and page_num < max_pages - 1:
                await next_button.click()
                await self.page.wait_for_timeout(2000)
            else:
                break

        return products

    async def _extract_products(self):
        """提取商品信息"""
        products = []
        items = await self.page.query_selector_all(".item")

        for item in items:
            try:
                title = await item.query_selector(".title a")
                price = await item.query_selector(".price")

                product = {
                    "title": await title.inner_text() if title else "",
                    "price": await price.inner_text() if price else "",
                    "url": await title.get_attribute("href") if title else ""
                }
                products.append(product)
            except Exception as e:
                logger.warning(f"提取商品信息失败: {e}")

        return products
```

### 4. Task Queue (任务队列)

基于Redis的任务队列，支持任务分发和状态管理。

```python
# packages/scraper/executor/task_queue.py
import redis.asyncio as redis
import json
from typing import Optional, Dict, Any
from packages.scraper.models import CrawlerTask

class TaskQueue:
    """异步任务队列"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.task_queue = "crawler:tasks:pending"
        self.running_queue = "crawler:tasks:running"
        self.completed_queue = "crawler:tasks:completed"

    async def enqueue(self, task: CrawlerTask) -> bool:
        """将任务加入队列"""
        try:
            task_data = task.to_dict()
            await self.redis.lpush(
                self.task_queue,
                json.dumps(task_data)
            )
            return True
        except Exception as e:
            logger.error(f"任务入队失败: {e}")
            return False

    async def dequeue(self, worker_id: str) -> Optional[CrawlerTask]:
        """从队列取出任务"""
        try:
            task_data = await self.redis.brpop(self.task_queue, timeout=10)
            if task_data:
                task = CrawlerTask.from_json(task_data[1])
                task.worker_id = worker_id
                task.status = TaskStatus.RUNNING

                # 移动到运行队列
                await self.redis.hset(
                    self.running_queue,
                    task.id,
                    json.dumps(task.to_dict())
                )
                return task
        except Exception as e:
            logger.error(f"任务出队失败: {e}")
        return None

    async def complete_task(self, task: CrawlerTask):
        """标记任务完成"""
        try:
            # 从运行队列移除
            await self.redis.hdel(self.running_queue, task.id)

            # 加入完成队列
            await self.redis.lpush(
                self.completed_queue,
                json.dumps(task.to_dict())
            )
        except Exception as e:
            logger.error(f"任务完成失败: {e}")
```

### 5. Worker (任务执行器)

分布式任务执行器，负责具体任务的执行。

```python
# packages/scraper/worker/worker.py
import asyncio
from typing import Dict, Any
from packages.scraper.executor.task_queue import TaskQueue
from packages.scraper.spiders import TaobaoSpider, JDSpider

class CrawlerWorker:
    """爬虫任务执行器"""

    def __init__(self, worker_id: str, redis_url: str):
        self.worker_id = worker_id
        self.task_queue = TaskQueue(redis_url)
        self.spiders = {
            "taobao": TaobaoSpider,
            "jd": JDSpider
        }

    async def start(self):
        """启动Worker"""
        logger.info(f"Worker {self.worker_id} 启动")

        while True:
            try:
                # 获取任务
                task = await self.task_queue.dequeue(self.worker_id)
                if not task:
                    await asyncio.sleep(1)
                    continue

                # 执行任务
                await self.execute_task(task)

            except KeyboardInterrupt:
                logger.info(f"Worker {self.worker_id} 停止")
                break
            except Exception as e:
                logger.error(f"Worker执行异常: {e}")
                await asyncio.sleep(5)

    async def execute_task(self, task: CrawlerTask):
        """执行具体任务"""
        try:
            logger.info(f"执行任务: {task.name}")

            # 获取对应的爬虫
            spider_class = self.spiders.get(task.platform)
            if not spider_class:
                raise ValueError(f"不支持的平台: {task.platform}")

            spider = spider_class(task.config)

            # 执行爬取
            results = await spider.crawl(
                keywords=task.keywords,
                max_pages=task.max_pages
            )

            # 保存结果
            await self.save_results(task, results)

            # 更新任务状态
            task.status = TaskStatus.SUCCESS
            task.completed_at = datetime.utcnow()
            task.result_count = len(results)

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1

        finally:
            await self.task_queue.complete_task(task)

    async def save_results(self, task: CrawlerTask, results: List[Any]):
        """保存爬取结果"""
        # 实现数据持久化逻辑
        pass
```

## 🔄 开发流程

### 1. 添加新的爬虫平台

#### 步骤1: 创建平台实现

```python
# packages/scraper/platform/new_platform.py
class NewPlatform(BasePlatform):
    """新平台爬虫实现"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://example.com"

    async def search(self, keyword: str, page: int = 1) -> List[CrawlItem]:
        """实现搜索逻辑"""
        params = {
            "q": keyword,
            "page": page
        }

        async with self.session.get(self.base_url + "/search", params=params) as response:
            return await self.parse_search_results(await response.text())

    async def parse_search_results(self, html: str) -> List[CrawlItem]:
        """解析搜索结果"""
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html, 'html.parser')
        items = []

        for item_element in soup.select(".product-item"):
            item = CrawlItem(
                title=item_element.select_one(".title").text,
                price=item_element.select_one(".price").text,
                url=item_element.select_one("a")["href"]
            )
            items.append(item)

        return items
```

#### 步骤2: 注册平台

```python
# packages/scraper/platform/registry.py
class PlatformRegistry:
    """平台注册表"""

    PLATFORMS = {
        "taobao": TaobaoPlatform,
        "jd": JDSpider,
        "new_platform": NewPlatform  # 注册新平台
    }

    @classmethod
    def get_platform(cls, name: str) -> BasePlatform:
        """获取平台实例"""
        if name not in cls.PLATFORMS:
            raise ValueError(f"未知平台: {name}")
        return cls.PLATFORMS[name]()
```

#### 步骤3: 更新Worker

```python
# packages/scraper/worker/worker.py
class CrawlerWorker:
    def __init__(self, worker_id: str, redis_url: str):
        self.worker_id = worker_id
        self.task_queue = TaskQueue(redis_url)

        # 动态加载所有注册的平台
        from packages.scraper.platform.registry import PlatformRegistry
        self.spiders = PlatformRegistry.get_all_spiders()
```

### 2. 创建新的爬虫任务

```python
# 使用API创建任务
import requests

task_data = {
    "name": "新平台装备采集",
    "platform": "new_platform",
    "keywords": ["路亚竿", "渔轮"],
    "max_pages": 10,
    "schedule": {
        "type": "cron",
        "expression": "0 2 * * *"  # 每天凌晨2点执行
    },
    "config": {
        "timeout": 30,
        "retry_times": 3
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/admin/crawler/tasks",
    json=task_data,
    headers={"Authorization": "Bearer your_token"}
)

task = response.json()
print(f"任务创建成功，ID: {task['data']['id']}")
```

### 3. 运行Worker

```bash
# 启动Master节点
python -m packages.scraper.master.app

# 启动Worker节点
python -m packages.scraper.worker.worker --worker-id worker-1
```

## 📊 实战案例

### 案例1: 淘宝路亚装备爬取

```python
# 创建淘宝爬虫任务
task = CrawlerTask(
    name="淘宝路亚装备采集",
    platform="taobao",
    keywords=["路亚竿", "渔轮", "拟饵"],
    max_pages=5,
    config={
        "use_proxy": True,
        "delay_range": (1, 3),
        "max_retries": 3
    }
)

# 使用RPA方式爬取
rpa = TaobaoRPA(headless=False)
await rpa.start()

results = await rpa.search_products(
    keyword="路亚竿",
    max_pages=3
)

await rpa.cleanup()

print(f"成功爬取 {len(results)} 个商品")
```

### 案例2: 分布式爬取

```python
# Master节点 - 任务分发
master = CrawlerMaster()

# 创建多个任务
tasks = [
    CrawlerTask(name="任务1", platform="taobao", keywords=["路亚竿"]),
    CrawlerTask(name="任务2", platform="jd", keywords=["渔轮"]),
    CrawlerTask(name="任务3", platform="new_platform", keywords=["拟饵"])
]

# 批量提交任务
for task in tasks:
    await master.submit_task(task)

# Worker节点 - 并行执行
workers = [
    CrawlerWorker("worker-1", "redis://localhost:6379"),
    CrawlerWorker("worker-2", "redis://localhost:6379"),
    CrawlerWorker("worker-3", "redis://localhost:6379")
]

# 并行启动Worker
await asyncio.gather(*[worker.start() for worker in workers])
```

## ⚡ 性能优化

### 1. 并发控制

```python
# 使用信号量控制并发数
import asyncio

class ConcurrencyLimiter:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def crawl_page(self, url: str):
        async with self.semaphore:
            # 限制并发数的爬取逻辑
            pass
```

### 2. 请求缓存

```python
# 使用Redis缓存请求结果
class CachedRequests:
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl

    async def get(self, url: str) -> Optional[str]:
        cache_key = f"cache:{hash(url)}"
        cached = await self.redis.get(cache_key)
        return cached.decode() if cached else None

    async def set(self, url: str, content: str):
        cache_key = f"cache:{hash(url)}"
        await self.redis.setex(cache_key, self.ttl, content)
```

### 3. 智能延迟

```python
import random
import time

class SmartDelay:
    def __init__(self, base_delay: float = 1.0, jitter: float = 0.5):
        self.base_delay = base_delay
        self.jitter = jitter

    async def wait(self):
        """智能等待时间"""
        delay = self.base_delay + random.uniform(-self.jitter, self.jitter)
        await asyncio.sleep(delay)
```

## 📈 监控告警

### 1. 任务监控

```python
# packages/scraper/monitoring/monitor.py
class CrawlerMonitor:
    def __init__(self):
        self.metrics = {
            "tasks_running": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "items_crawled": 0
        }

    async def update_metrics(self, event_type: str, value: int = 1):
        """更新监控指标"""
        self.metrics[event_type] += value

        # 推送到监控系统
        await self.push_to_prometheus(event_type, value)

    async def check_alerts(self):
        """检查告警条件"""
        if self.metrics["tasks_failed"] > 10:
            await self.send_alert("任务失败率过高")

        if self.metrics["tasks_running"] == 0:
            await self.send_alert("没有运行中的任务")
```

### 2. 健康检查

```python
# packages/scraper/monitoring/health_check.py
class HealthCheck:
    async def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖服务状态"""
        status = {
            "redis": await self.check_redis(),
            "database": await self.check_database(),
            "proxy_pool": await self.check_proxy_pool()
        }
        return status

    async def check_redis(self) -> bool:
        """检查Redis连接"""
        try:
            await self.redis.ping()
            return True
        except:
            return False
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 反爬虫封禁

**问题**: 频繁请求导致IP被封禁
**解决方案**:
- 使用代理IP池
- 降低请求频率
- 轮换User-Agent
- 使用RPA模拟真实用户

```python
# 使用代理IP池
class ProxyRotator:
    def __init__(self, proxy_list: List[str]):
        self.proxies = proxy_list
        self.current_index = 0

    def get_proxy(self) -> str:
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

# 配置Session使用代理
session.proxies = {
    "http": proxy_rotator.get_proxy(),
    "https": proxy_rotator.get_proxy()
}
```

#### 2. 页面结构变化

**问题**: 网站改版导致解析失败
**解决方案**:
- 实现多版本解析器
- 使用模糊匹配
- 添加健康检查
- 实现自动降级

```python
# 多版本解析器
class AdaptiveParser:
    def __init__(self):
        self.parsers = {
            "v1": self.parse_v1,
            "v2": self.parse_v2,
            "fallback": self.parse_fallback
        }

    async def parse(self, html: str):
        """自适应解析"""
        for parser_name, parser_func in self.parsers.items():
            try:
                results = await parser_func(html)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"解析器 {parser_name} 失败: {e}")
                continue
        return []
```

#### 3. 任务队列积压

**问题**: 任务执行速度慢导致队列积压
**解决方案**:
- 增加Worker节点
- 优化任务粒度
- 实现任务优先级
- 添加自动扩缩容

```python
# 任务优先级队列
class PriorityTaskQueue:
    async def enqueue(self, task: CrawlerTask, priority: int = 0):
        """按优先级入队"""
        priority_queue = f"{self.task_queue}:{priority}"
        await self.redis.lpush(priority_queue, json.dumps(task.to_dict()))

    async def dequeue(self, worker_id: str):
        """按优先级出队"""
        # 先尝试高优先级队列
        for priority in [3, 2, 1, 0]:  # 从高到低
            queue = f"{self.task_queue}:{priority}"
            task_data = await self.redis.brpop(queue, timeout=1)
            if task_data:
                return CrawlerTask.from_json(task_data[1])
        return None
```

## 📚 最佳实践

### 1. 代码规范

- 使用类型注解
- 编写单元测试
- 添加日志记录
- 实现优雅降级

### 2. 安全考虑

- 不要在代码中硬编码敏感信息
- 使用环境变量管理配置
- 实现访问频率限制
- 定期更新依赖库

### 3. 运维建议

- 设置监控告警
- 定期备份数据
- 实现灰度发布
- 建立回滚机制

## 🔗 相关资源

- [API文档](../05-api-reference/endpoints/admin-api.md) - 爬虫管理API
- [架构设计](../03-architecture/system-design.md) - 系统架构详情
- [代码结构](../02-developer-guide/codebase-structure.md) - 项目代码组织
- [测试指南](../02-developer-guide/testing.md) - 测试策略和方法

---

**指南版本**: v5.0.2
**适用系统版本**: v5.0.2+
**最后更新**: 2024-12-20