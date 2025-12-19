# 工作流系统开发方案 - 阶段1：核心引擎

**目标**: 实现工作流执行引擎、任务队列、平台抽象层

**预估工作量**: 5-6天

**前置条件**:
- 现有爬虫系统正常运行
- 数据库可访问
- 测试环境就绪

---

## 一、数据库设计与迁移

### 1.1 扩展CrawlerTask表

**文件**: `packages/agent_fishing/tools/lure/models/system.py`

**新增字段**:
```python
class CrawlerTask(Base):
    __tablename__ = "crawler_tasks"

    # === 现有字段保留 ===
    id = Column(Integer, primary_key=True)
    task_type = Column(String(50), index=True)
    task_name = Column(String(200))
    status = Column(Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILED'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    total_items = Column(Integer, default=0)
    success_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    config = Column(Text)
    result_summary = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # === 工作流相关字段（新增）===
    workflow_id = Column(String(36), index=True, nullable=True, comment='工作流分组ID（UUID）')
    workflow_name = Column(String(200), nullable=True, comment='工作流名称（冗余字段，便于查询）')
    parent_task_id = Column(Integer, ForeignKey('crawler_tasks.id'), nullable=True, comment='父任务ID（DAG依赖）')
    step_order = Column(Integer, default=0, comment='工作流中的步骤顺序')
    step_config = Column(Text, nullable=True, comment='步骤配置JSON（含depends_on）')

    # === 执行控制字段（新增）===
    platform = Column(String(50), index=True, nullable=True, comment='平台标识（taobao/jd/tmall）')
    shop_url = Column(String(500), nullable=True, comment='店铺URL（用于店铺级工作流）')
    retry_count = Column(Integer, default=0, comment='已重试次数')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    timeout_seconds = Column(Integer, default=3600, comment='超时时间（秒）')
    requires_intervention = Column(Boolean, default=False, comment='是否需要人工干预')

    # === 数据质量字段（新增）===
    duplicate_items = Column(Integer, default=0, comment='去重数量')
    invalid_items = Column(Integer, default=0, comment='无效数据量')

    # === 关系定义 ===
    children = relationship('CrawlerTask', backref=backref('parent', remote_side=[id]))
```

**索引优化**:
```python
Index('idx_crawler_task_workflow', 'workflow_id')
Index('idx_crawler_task_platform', 'platform')
Index('idx_crawler_task_parent', 'parent_task_id')
```

### 1.2 新建工作流模板表

```python
class CrawlerWorkflowTemplate(Base):
    """工作流模板表"""
    __tablename__ = "crawler_workflow_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True, comment='模板名称')
    description = Column(Text, comment='模板描述')
    template_json = Column(Text, nullable=False, comment='工作流定义JSON')
    category = Column(String(50), comment='模板分类（shop/keyword/sync）')
    is_system = Column(Boolean, default=False, comment='是否系统内置模板')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0, comment='使用次数统计')

    # 关系
    creator = relationship('User', backref='created_workflow_templates')
```

**模板JSON格式定义**:
```json
{
  "name": "淘宝店铺商品抓取",
  "description": "从店铺URL抓取所有商品",
  "version": "1.0",
  "steps": [
    {
      "id": "step_1",
      "order": 1,
      "task_type": "taobao",
      "name": "分析店铺分类",
      "config": {
        "shop_url": "{{shop_url}}",
        "action": "analyze_shop"
      },
      "max_retries": 3,
      "timeout": 600,
      "depends_on": []
    },
    {
      "id": "step_2",
      "order": 2,
      "task_type": "taobao",
      "name": "抓取店铺商品",
      "config": {
        "shop_url": "{{shop_url}}",
        "categories": "{{step_1.result.categories}}",
        "max_pages": "{{max_pages}}"
      },
      "max_retries": 3,
      "timeout": 3600,
      "depends_on": ["step_1"]
    }
  ],
  "params": {
    "shop_url": {
      "type": "string",
      "required": true,
      "description": "店铺URL"
    },
    "max_pages": {
      "type": "integer",
      "default": 5,
      "description": "每个分类最大抓取页数"
    }
  }
}
```

### 1.3 新建定时调度表

```python
class CrawlerSchedule(Base):
    """定时调度表"""
    __tablename__ = "crawler_schedules"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, comment='调度名称')
    template_id = Column(Integer, ForeignKey('crawler_workflow_templates.id'), nullable=False)
    cron_expression = Column(String(100), nullable=False, comment='Cron表达式')
    timezone = Column(String(50), default='Asia/Shanghai', comment='时区')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    config = Column(Text, comment='调度配置JSON（执行参数）')
    next_run_time = Column(DateTime, comment='下次执行时间')
    last_run_time = Column(DateTime, comment='最后执行时间')
    last_task_id = Column(Integer, ForeignKey('crawler_tasks.id'), comment='最后一次执行的任务ID')
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    template = relationship('CrawlerWorkflowTemplate', backref='schedules')
    creator = relationship('User', backref='created_schedules')
    last_task = relationship('CrawlerTask')
```

### 1.4 数据库迁移

**创建迁移脚本**:
```bash
cd /Users/zen/projects/fishing_agent
uv run alembic revision --autogenerate -m "add_workflow_support"
```

**迁移脚本内容**（自动生成后检查）:
```python
def upgrade():
    # 扩展crawler_tasks表
    op.add_column('crawler_tasks', sa.Column('workflow_id', sa.String(36), nullable=True))
    op.add_column('crawler_tasks', sa.Column('workflow_name', sa.String(200), nullable=True))
    op.add_column('crawler_tasks', sa.Column('parent_task_id', sa.Integer(), nullable=True))
    op.add_column('crawler_tasks', sa.Column('step_order', sa.Integer(), server_default='0'))
    op.add_column('crawler_tasks', sa.Column('step_config', sa.Text(), nullable=True))
    op.add_column('crawler_tasks', sa.Column('platform', sa.String(50), nullable=True))
    op.add_column('crawler_tasks', sa.Column('shop_url', sa.String(500), nullable=True))
    op.add_column('crawler_tasks', sa.Column('retry_count', sa.Integer(), server_default='0'))
    op.add_column('crawler_tasks', sa.Column('max_retries', sa.Integer(), server_default='3'))
    op.add_column('crawler_tasks', sa.Column('timeout_seconds', sa.Integer(), server_default='3600'))
    op.add_column('crawler_tasks', sa.Column('requires_intervention', sa.Boolean(), server_default='false'))
    op.add_column('crawler_tasks', sa.Column('duplicate_items', sa.Integer(), server_default='0'))
    op.add_column('crawler_tasks', sa.Column('invalid_items', sa.Integer(), server_default='0'))

    # 创建外键
    op.create_foreign_key('fk_crawler_task_parent', 'crawler_tasks', 'crawler_tasks',
                          ['parent_task_id'], ['id'], ondelete='CASCADE')

    # 创建索引
    op.create_index('idx_crawler_task_workflow', 'crawler_tasks', ['workflow_id'])
    op.create_index('idx_crawler_task_platform', 'crawler_tasks', ['platform'])

    # 创建crawler_workflow_templates表
    op.create_table('crawler_workflow_templates', ...)

    # 创建crawler_schedules表
    op.create_table('crawler_schedules', ...)

def downgrade():
    # 回滚逻辑
    op.drop_table('crawler_schedules')
    op.drop_table('crawler_workflow_templates')
    op.drop_column('crawler_tasks', 'workflow_id')
    # ... 其他字段回滚
```

**执行迁移**:
```bash
uv run alembic upgrade head
```

---

## 二、平台抽象层

### 2.1 定义平台接口

**文件**: `packages/agent_fishing/tools/crawler/platform/base_platform.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional
from packages.agent_fishing.tools.crawler.data_persister import EquipmentData

class BasePlatform(ABC):
    """平台爬虫抽象基类"""

    @abstractmethod
    def detect_url(self, url: str) -> bool:
        """
        检测URL是否属于该平台

        Args:
            url: 待检测的URL

        Returns:
            True表示匹配，False表示不匹配
        """
        pass

    @abstractmethod
    def crawl(self, config: dict, on_progress: Optional[Callable[[str, int], None]] = None) -> List[EquipmentData]:
        """
        执行爬虫

        Args:
            config: 爬虫配置（keywords, max_pages, shop_url等）
            on_progress: 进度回调函数 (message: str, progress_percent: int)

        Returns:
            EquipmentData对象列表

        Raises:
            PlatformCrawlError: 爬虫执行失败
        """
        pass

    @abstractmethod
    def estimate_items(self, config: dict) -> int:
        """
        预估抓取数量

        Args:
            config: 爬虫配置

        Returns:
            预估的数据条数
        """
        pass

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.__class__.__name__.replace('Platform', '').lower()
```

### 2.2 淘宝平台适配器

**文件**: `packages/agent_fishing/tools/crawler/platform/taobao_platform.py`

```python
from .base_platform import BasePlatform
from packages.agent_fishing.tools.crawler.taobao_spider import TaobaoSpider
from packages.agent_fishing.tools.crawler.data_persister import EquipmentData
from typing import List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class TaobaoPlatform(BasePlatform):
    """淘宝/天猫平台适配器"""

    def __init__(self):
        self.spider = TaobaoSpider()

    def detect_url(self, url: str) -> bool:
        """检测是否为淘宝/天猫URL"""
        return 'taobao.com' in url or 'tmall.com' in url

    def crawl(self, config: dict, on_progress: Optional[Callable[[str, int], None]] = None) -> List[EquipmentData]:
        """
        执行淘宝爬虫

        支持的config参数:
        - keywords: List[str] - 关键词列表
        - max_pages: int - 每个关键词最大抓取页数
        - shop_url: str - 店铺URL（用于店铺级抓取）
        - proxy: str - 代理服务器（可选）
        """
        results = []

        # 关键词搜索模式
        if 'keywords' in config:
            keywords = config['keywords']
            max_pages = config.get('max_pages', 5)
            total_keywords = len(keywords)

            for idx, keyword in enumerate(keywords):
                if on_progress:
                    progress_percent = int((idx / total_keywords) * 100)
                    on_progress(f"正在抓取关键词: {keyword} ({idx+1}/{total_keywords})", progress_percent)

                try:
                    keyword_results = self.spider.crawl_by_keyword(keyword, max_pages=max_pages)
                    results.extend(keyword_results)
                    logger.info(f"关键词 '{keyword}' 抓取成功，获得 {len(keyword_results)} 条数据")
                except Exception as e:
                    logger.error(f"关键词 '{keyword}' 抓取失败: {e}")
                    # 继续抓取下一个关键词
                    continue

            if on_progress:
                on_progress("关键词抓取完成", 100)

        # 店铺URL模式（待实现）
        elif 'shop_url' in config:
            shop_url = config['shop_url']
            if on_progress:
                on_progress(f"正在分析店铺: {shop_url}", 10)

            # TODO: 调用TaobaoShopRPA实现店铺抓取
            # 这里需要在后续集成RPA模块
            raise NotImplementedError("店铺URL抓取功能待实现")

        else:
            raise ValueError("config必须包含keywords或shop_url参数")

        return results

    def estimate_items(self, config: dict) -> int:
        """预估抓取数量"""
        if 'keywords' in config:
            keywords_count = len(config['keywords'])
            max_pages = config.get('max_pages', 5)
            return keywords_count * max_pages * 20  # 每页约20条
        elif 'shop_url' in config:
            return 500  # 店铺默认预估500条
        return 0
```

### 2.3 京东平台适配器

**文件**: `packages/agent_fishing/tools/crawler/platform/jd_platform.py`

```python
from .base_platform import BasePlatform
from packages.agent_fishing.tools.crawler.jd_spider import JDSpider
from typing import List, Optional, Callable

class JDPlatform(BasePlatform):
    """京东平台适配器"""

    def __init__(self):
        self.spider = JDSpider()

    def detect_url(self, url: str) -> bool:
        return 'jd.com' in url

    def crawl(self, config: dict, on_progress: Optional[Callable] = None) -> List:
        keywords = config.get('keywords', [])
        max_pages = config.get('max_pages', 5)
        results = []

        total_keywords = len(keywords)
        for idx, keyword in enumerate(keywords):
            if on_progress:
                on_progress(f"正在抓取京东关键词: {keyword}", int((idx / total_keywords) * 100))

            keyword_results = self.spider.crawl_by_keyword(keyword, max_pages=max_pages)
            results.extend(keyword_results)

        if on_progress:
            on_progress("京东抓取完成", 100)

        return results

    def estimate_items(self, config: dict) -> int:
        keywords_count = len(config.get('keywords', []))
        max_pages = config.get('max_pages', 5)
        return keywords_count * max_pages * 20
```

### 2.4 平台注册中心

**文件**: `packages/agent_fishing/tools/crawler/platform/registry.py`

```python
from .base_platform import BasePlatform
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class PlatformRegistry:
    """平台注册中心（单例模式）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._platforms = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._register_builtin_platforms()
            self._initialized = True

    def _register_builtin_platforms(self):
        """注册内置平台"""
        from .taobao_platform import TaobaoPlatform
        from .jd_platform import JDPlatform

        self.register('taobao', TaobaoPlatform())
        self.register('tmall', TaobaoPlatform())  # 天猫复用淘宝适配器
        self.register('jd', JDPlatform())

        logger.info(f"已注册 {len(self._platforms)} 个内置平台")

    def register(self, name: str, platform: BasePlatform):
        """
        注册平台

        Args:
            name: 平台名称（小写，如taobao/jd）
            platform: 平台实例
        """
        if name in self._platforms:
            logger.warning(f"平台 '{name}' 已存在，将被覆盖")

        self._platforms[name] = platform
        logger.info(f"注册平台: {name}")

    def get_platform(self, name: str) -> BasePlatform:
        """
        获取平台实例

        Args:
            name: 平台名称

        Returns:
            平台实例

        Raises:
            ValueError: 平台未注册
        """
        if name not in self._platforms:
            available = ', '.join(self._platforms.keys())
            raise ValueError(f"未知平台: {name}. 可用平台: {available}")

        return self._platforms[name]

    def detect_platform(self, url: str) -> Optional[str]:
        """
        根据URL自动检测平台

        Args:
            url: 待检测的URL

        Returns:
            平台名称，如果无法识别则返回None
        """
        for name, platform in self._platforms.items():
            if platform.detect_url(url):
                logger.info(f"URL '{url}' 匹配到平台: {name}")
                return name

        logger.warning(f"无法识别URL所属平台: {url}")
        return None

    def list_platforms(self) -> Dict[str, str]:
        """列出所有已注册的平台"""
        return {name: platform.get_platform_name() for name, platform in self._platforms.items()}

# 全局单例
platform_registry = PlatformRegistry()
```

**文件**: `packages/agent_fishing/tools/crawler/platform/__init__.py`

```python
from .base_platform import BasePlatform
from .registry import PlatformRegistry, platform_registry
from .taobao_platform import TaobaoPlatform
from .jd_platform import JDPlatform

__all__ = [
    'BasePlatform',
    'PlatformRegistry',
    'platform_registry',
    'TaobaoPlatform',
    'JDPlatform',
]
```

---

## 三、任务队列与执行器

### 3.1 任务队列

**文件**: `packages/agent_fishing/tools/crawler/executor/task_queue.py`

```python
import threading
import queue
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class CrawlerTaskQueue:
    """
    爬虫任务队列（基于线程池）

    Features:
    - 多工作线程并发执行
    - 独立数据库会话（避免并发冲突）
    - 优雅关闭（完成队列中的任务）
    """

    def __init__(self, num_workers=3, db_session_factory=None):
        """
        初始化任务队列

        Args:
            num_workers: 工作线程数量
            db_session_factory: 数据库会话工厂函数（返回Session对象）
        """
        self.task_queue = queue.Queue()
        self.workers = []
        self.db_session_factory = db_session_factory
        self._stop_event = threading.Event()
        self.num_workers = num_workers

        # 启动工作线程
        self._start_workers()
        logger.info(f"任务队列初始化完成，工作线程数: {num_workers}")

    def _start_workers(self):
        """启动工作线程池"""
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True,
                name=f"CrawlerWorker-{i}"
            )
            worker.start()
            self.workers.append(worker)
            logger.info(f"工作线程 {i} 已启动")

    def submit(self, task_id: int):
        """
        提交任务到队列

        Args:
            task_id: CrawlerTask的ID
        """
        self.task_queue.put(task_id)
        logger.info(f"任务 {task_id} 已提交到队列，当前队列深度: {self.task_queue.qsize()}")

    def _worker_loop(self, worker_id: int):
        """
        工作线程主循环

        Args:
            worker_id: 工作线程ID
        """
        from packages.agent_fishing.tools.crawler.executor.crawler_executor import CrawlerExecutor

        logger.info(f"工作线程 {worker_id} 开始监听任务")

        while not self._stop_event.is_set():
            try:
                # 超时1秒获取任务（避免无限阻塞）
                task_id = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue

            # 创建独立的数据库会话
            db_session = self.db_session_factory()
            executor = CrawlerExecutor(db_session, worker_id)

            try:
                logger.info(f"工作线程 {worker_id} 开始执行任务 {task_id}")
                executor.execute(task_id)
                logger.info(f"工作线程 {worker_id} 完成任务 {task_id}")
            except Exception as e:
                logger.error(f"工作线程 {worker_id} 执行任务 {task_id} 失败: {e}", exc_info=True)
            finally:
                db_session.close()
                self.task_queue.task_done()

    def shutdown(self, wait=True, timeout=30):
        """
        关闭任务队列

        Args:
            wait: 是否等待队列中的任务完成
            timeout: 等待超时时间（秒）
        """
        logger.info(f"任务队列关闭中... (wait={wait}, timeout={timeout}s)")

        if wait:
            logger.info("等待队列中的任务完成...")
            self.task_queue.join()  # 等待所有任务完成

        # 设置停止标志
        self._stop_event.set()

        # 等待所有工作线程退出
        for i, worker in enumerate(self.workers):
            worker.join(timeout=timeout / len(self.workers))
            if worker.is_alive():
                logger.warning(f"工作线程 {i} 未能在超时时间内退出")
            else:
                logger.info(f"工作线程 {i} 已退出")

        logger.info("任务队列已关闭")

    def get_queue_size(self) -> int:
        """获取当前队列深度"""
        return self.task_queue.qsize()
```

### 3.2 爬虫执行器

**文件**: `packages/agent_fishing/tools/crawler/executor/crawler_executor.py`

```python
import json
import time
import traceback
import logging
from datetime import datetime
from typing import Optional
from packages.agent_fishing.tools.lure.models.system import CrawlerTask, CrawlerLog
from packages.agent_fishing.tools.crawler.platform.registry import platform_registry
from packages.agent_fishing.tools.crawler.data_persister import DataPersister

logger = logging.getLogger(__name__)

class CrawlerExecutor:
    """
    统一爬虫执行器

    职责:
    1. 根据task_type调用对应平台爬虫
    2. 实时更新任务状态和进度
    3. 捕获异常并记录日志
    4. 触发重试逻辑
    5. 触发工作流后续任务
    """

    def __init__(self, db_session, worker_id: int = 0):
        self.db = db_session
        self.worker_id = worker_id
        self.platform_registry = platform_registry

    def execute(self, task_id: int):
        """
        执行单个爬虫任务

        Args:
            task_id: CrawlerTask的ID
        """
        task = self.db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.error(f"任务 {task_id} 不存在")
            return

        logger.info(f"[Worker-{self.worker_id}] 开始执行任务 {task_id} (type={task.task_type}, name={task.task_name})")

        # 1. 更新状态为RUNNING
        task.status = 'RUNNING'
        task.start_time = datetime.utcnow()
        self.db.commit()

        # 2. 推送WebSocket开始消息
        self._push_ws_update(task, "任务开始执行")

        # 3. 记录开始日志
        self._log(task, 'INFO', '任务开始执行', {
            'worker_id': self.worker_id,
            'task_type': task.task_type,
            'config': task.config
        })

        try:
            # 4. 获取平台爬虫
            platform = self.platform_registry.get_platform(task.task_type)
            config = json.loads(task.config) if task.config else {}

            # 5. 执行爬虫（带进度回调）
            logger.info(f"调用平台 {task.task_type} 的爬虫，配置: {config}")
            results = platform.crawl(
                config=config,
                on_progress=lambda msg, progress: self._on_progress(task, msg, progress)
            )

            logger.info(f"爬虫执行完成，获得 {len(results)} 条原始数据")

            # 6. 持久化结果（去重+存储）
            persister = DataPersister(self.db)
            stats = persister.save_equipment_data(results)

            logger.info(f"数据持久化完成: 成功{stats['success']}条, 失败{stats['failed']}条, 去重{stats['duplicates']}条")

            # 7. 更新任务状态为SUCCESS
            task.status = 'SUCCESS'
            task.end_time = datetime.utcnow()
            task.success_items = stats['success']
            task.failed_items = stats['failed']
            task.duplicate_items = stats['duplicates']
            task.total_items = len(results)
            task.result_summary = json.dumps({
                "raw_items_count": len(results),
                "success_count": stats['success'],
                "failed_count": stats['failed'],
                "duplicate_count": stats['duplicates']
            })
            self.db.commit()

            # 8. 记录成功日志
            self._log(task, 'INFO', '任务执行成功', {
                'total_items': task.total_items,
                'success_items': task.success_items,
                'duration_seconds': (task.end_time - task.start_time).total_seconds()
            })

            # 9. 推送WebSocket完成消息
            self._push_ws_update(task, "任务执行成功", 100)

            # 10. 触发工作流后续任务
            self._trigger_workflow_next_tasks(task)

        except Exception as e:
            # 错误处理
            logger.error(f"任务 {task_id} 执行失败: {e}", exc_info=True)

            task.status = 'FAILED'
            task.error_message = str(e)
            task.end_time = datetime.utcnow()
            self.db.commit()

            # 记录错误日志
            self._log(task, 'ERROR', f'任务执行失败: {e}', {
                'traceback': traceback.format_exc()
            })

            # 推送WebSocket错误消息
            self._push_ws_update(task, f"任务执行失败: {e}", error=True)

            # 重试逻辑
            self._handle_retry(task)

    def _on_progress(self, task: CrawlerTask, message: str, progress_percent: int):
        """
        进度回调

        Args:
            task: 任务对象
            message: 进度消息
            progress_percent: 进度百分比（0-100）
        """
        logger.info(f"任务 {task.id} 进度: {progress_percent}% - {message}")

        # 更新数据库（将进度存储在config中）
        config = json.loads(task.config) if task.config else {}
        config['_progress'] = {
            'percent': progress_percent,
            'message': message,
            'updated_at': datetime.utcnow().isoformat()
        }
        task.config = json.dumps(config)
        self.db.commit()

        # 推送WebSocket进度更新
        self._push_ws_update(task, message, progress_percent)

    def _push_ws_update(self, task: CrawlerTask, message: str, progress: Optional[int] = None, error: bool = False):
        """
        推送WebSocket更新

        Args:
            task: 任务对象
            message: 消息内容
            progress: 进度百分比（可选）
            error: 是否为错误消息
        """
        try:
            # 复用现有WebSocket Manager
            from apps.api.routes.crawler import websocket_manager

            websocket_manager.send_update(task.id, {
                "task_id": task.id,
                "workflow_id": task.workflow_id,
                "status": task.status,
                "message": message,
                "progress": progress,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.warning(f"WebSocket推送失败: {e}")

    def _log(self, task: CrawlerTask, level: str, message: str, details: dict = None):
        """
        记录任务日志

        Args:
            task: 任务对象
            level: 日志级别（INFO/WARNING/ERROR）
            message: 日志消息
            details: 详细信息（JSON）
        """
        log = CrawlerLog(
            task_id=task.id,
            level=level,
            message=message,
            details=json.dumps(details) if details else None
        )
        self.db.add(log)
        self.db.commit()

    def _handle_retry(self, task: CrawlerTask):
        """
        处理任务重试

        Args:
            task: 失败的任务对象
        """
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = 'PENDING'  # 重置为PENDING
            self.db.commit()

            # 指数退避延迟
            delay = 2 ** task.retry_count
            logger.info(f"任务 {task.id} 将在 {delay} 秒后重试 (第{task.retry_count}/{task.max_retries}次)")

            # 记录重试日志
            self._log(task, 'WARNING', f'任务重试: 第{task.retry_count}次', {
                'delay_seconds': delay
            })

            # 延迟后重新提交
            time.sleep(delay)
            from apps.api.services.crawler_service import task_queue
            task_queue.submit(task.id)
        else:
            logger.error(f"任务 {task.id} 已达最大重试次数({task.max_retries})，放弃重试")
            self._log(task, 'ERROR', '任务达到最大重试次数，执行失败', {
                'max_retries': task.max_retries
            })

    def _trigger_workflow_next_tasks(self, task: CrawlerTask):
        """
        触发工作流的后续任务

        Args:
            task: 已完成的任务对象
        """
        if not task.workflow_id:
            return  # 非工作流任务，直接返回

        logger.info(f"检查工作流 {task.workflow_id} 的后续任务...")

        # 查找同一工作流的所有任务
        workflow_tasks = self.db.query(CrawlerTask).filter(
            CrawlerTask.workflow_id == task.workflow_id
        ).all()

        # 解析步骤定义，找到依赖当前任务的步骤
        for t in workflow_tasks:
            if t.status != 'PENDING':
                continue  # 只处理PENDING状态的任务

            step_config = json.loads(t.step_config) if t.step_config else {}
            depends_on = step_config.get('depends_on', [])

            # 检查是否依赖当前任务
            if task.id in depends_on or f"step_{task.step_order}" in depends_on:
                # 检查所有依赖是否都已完成
                all_deps_done = all(
                    self.db.query(CrawlerTask).filter(
                        CrawlerTask.workflow_id == task.workflow_id,
                        CrawlerTask.step_order == dep_order,
                        CrawlerTask.status == 'SUCCESS'
                    ).first() is not None
                    for dep_order in [int(dep.split('_')[1]) for dep in depends_on if dep.startswith('step_')]
                )

                if all_deps_done:
                    logger.info(f"任务 {t.id} 的所有依赖已完成，提交执行")
                    from apps.api.services.crawler_service import task_queue
                    task_queue.submit(t.id)
```

**文件**: `packages/agent_fishing/tools/crawler/executor/__init__.py`

```python
from .task_queue import CrawlerTaskQueue
from .crawler_executor import CrawlerExecutor

__all__ = ['CrawlerTaskQueue', 'CrawlerExecutor']
```

---

## 四、工作流引擎

### 4.1 工作流执行引擎

**文件**: `packages/agent_fishing/tools/crawler/workflow/engine.py`

```python
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List
from packages.agent_fishing.tools.lure.models.system import CrawlerTask

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    工作流执行引擎

    职责:
    1. 解析工作流定义JSON
    2. 创建工作流任务（根任务 + 步骤任务）
    3. 提交第一批无依赖的任务到队列
    4. 处理任务完成回调，触发后续任务
    """

    def __init__(self, db_session, task_queue):
        self.db = db_session
        self.queue = task_queue

    def execute_workflow(self, workflow_definition: dict, trigger_params: dict) -> str:
        """
        执行工作流

        Args:
            workflow_definition: 工作流定义（JSON）
                {
                    "name": "工作流名称",
                    "steps": [
                        {
                            "id": "step_1",
                            "order": 1,
                            "task_type": "taobao",
                            "name": "步骤名称",
                            "config": {"keywords": ["{{keyword}}"]},
                            "depends_on": [],
                            "max_retries": 3,
                            "timeout": 600
                        }
                    ],
                    "params": {...}
                }
            trigger_params: 触发参数（用户输入）
                {
                    "keyword": "钓鱼竿",
                    "max_pages": 5
                }

        Returns:
            workflow_id: 工作流执行ID（UUID）
        """
        workflow_id = str(uuid.uuid4())
        workflow_name = workflow_definition.get('name', 'Unnamed Workflow')
        steps = workflow_definition.get('steps', [])

        logger.info(f"开始执行工作流: {workflow_name} (ID={workflow_id}, 步骤数={len(steps)})")

        # 1. 创建工作流根任务（虚拟任务，用于分组）
        root_task = CrawlerTask(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            task_type='workflow_root',
            task_name=f"工作流: {workflow_name}",
            status='RUNNING',
            config=json.dumps(workflow_definition),
            step_order=-1  # 根任务order为-1
        )
        self.db.add(root_task)
        self.db.commit()

        logger.info(f"创建工作流根任务: {root_task.id}")

        # 2. 创建步骤任务（按order排序）
        task_map = {}  # step_id -> CrawlerTask.id
        for step in sorted(steps, key=lambda s: s.get('order', 0)):
            task = self._create_step_task(step, root_task.id, workflow_id, trigger_params)
            self.db.add(task)
            self.db.flush()  # 获取自增ID

            task_map[step['id']] = task.id
            logger.info(f"创建步骤任务: {task.id} (order={step['order']}, name={step['name']})")

        self.db.commit()

        # 3. 提交第一批无依赖的任务到队列
        submitted_count = 0
        for step in steps:
            if not step.get('depends_on'):  # 无依赖的步骤立即执行
                task_id = task_map[step['id']]
                self.queue.submit(task_id)
                submitted_count += 1
                logger.info(f"提交无依赖任务到队列: {task_id}")

        logger.info(f"工作流 {workflow_id} 初始化完成，已提交 {submitted_count} 个任务")

        return workflow_id

    def _create_step_task(self, step_def: dict, parent_id: int, workflow_id: str, params: dict) -> CrawlerTask:
        """
        创建步骤任务

        Args:
            step_def: 步骤定义
            parent_id: 父任务ID（根任务）
            workflow_id: 工作流ID
            params: 触发参数（用于替换{{变量}}）

        Returns:
            CrawlerTask对象
        """
        # 参数替换（将config中的{{变量}}替换为实际值）
        config = self._replace_params(step_def.get('config', {}), params)

        return CrawlerTask(
            workflow_id=workflow_id,
            workflow_name=f"工作流步骤: {step_def['name']}",
            parent_task_id=parent_id,
            step_order=step_def.get('order', 0),
            task_type=step_def['task_type'],
            task_name=step_def['name'],
            config=json.dumps(config),
            step_config=json.dumps(step_def),  # 保存完整步骤定义（含depends_on）
            status='PENDING',
            max_retries=step_def.get('max_retries', 3),
            timeout_seconds=step_def.get('timeout', 3600)
        )

    def _replace_params(self, config: dict, params: dict) -> dict:
        """
        替换配置中的参数占位符

        将{{param_name}}替换为params中的实际值

        Args:
            config: 原始配置
            params: 参数字典

        Returns:
            替换后的配置
        """
        config_str = json.dumps(config)

        for key, value in params.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in config_str:
                config_str = config_str.replace(placeholder, json.dumps(value))
                logger.debug(f"替换参数: {{{{{key}}}}} -> {value}")

        return json.loads(config_str)
```

**文件**: `packages/agent_fishing/tools/crawler/workflow/__init__.py`

```python
from .engine import WorkflowEngine

__all__ = ['WorkflowEngine']
```

---

## 五、服务层集成

### 5.1 初始化任务队列

**修改文件**: `apps/api/services/crawler_service.py`

在文件开头添加全局变量:

```python
from packages.agent_fishing.tools.crawler.executor import CrawlerTaskQueue
from packages.agent_fishing.tools.crawler.workflow.engine import WorkflowEngine
from packages.agent_fishing.tools.lure.models.system import CrawlerTask, CrawlerWorkflowTemplate

# 全局任务队列（应用启动时初始化）
task_queue: Optional[CrawlerTaskQueue] = None

def initialize_task_queue(db_session_factory, num_workers=3):
    """
    初始化任务队列（在main.py的lifespan中调用）

    Args:
        db_session_factory: 数据库会话工厂（如SessionLocal）
        num_workers: 工作线程数量
    """
    global task_queue
    task_queue = CrawlerTaskQueue(num_workers=num_workers, db_session_factory=db_session_factory)
    logger.info(f"任务队列初始化完成，工作线程数: {num_workers}")

def shutdown_task_queue(wait=True, timeout=30):
    """关闭任务队列（应用关闭时调用）"""
    global task_queue
    if task_queue:
        task_queue.shutdown(wait=wait, timeout=timeout)
```

修改 `trigger_crawler` 方法:

```python
class CrawlerService:
    # ... 现有代码保留 ...

    def trigger_crawler(self, request: TriggerCrawlerRequest, current_user: CurrentUser) -> CrawlerTask:
        """
        触发爬虫任务（修订版）

        Args:
            request: 触发请求
            current_user: 当前用户

        Returns:
            创建的任务对象
        """
        # 创建任务记录
        task = CrawlerTask(
            task_type=request.task_type,
            task_name=f"{request.task_type}_crawler_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            status='PENDING',
            config=json.dumps({
                "keywords": request.keywords,
                "max_pages": request.max_pages,
                "proxy": request.proxy
            }),
            created_by=current_user.user_id if current_user else None,
            platform=request.task_type  # 新增platform字段
        )
        self.db.add(task)
        self.db.commit()

        logger.info(f"创建爬虫任务: {task.id} (type={task.task_type})")

        # 提交到任务队列执行
        task_queue.submit(task.id)

        return task

    def trigger_workflow(self, template_id: int, params: dict, current_user: Optional[CurrentUser] = None) -> str:
        """
        触发工作流（新增）

        Args:
            template_id: 工作流模板ID
            params: 执行参数（替换模板中的{{变量}}）
            current_user: 当前用户（可选，定时调度时为None）

        Returns:
            workflow_id: 工作流执行ID
        """
        # 1. 加载工作流模板
        template = self.db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.id == template_id
        ).first()

        if not template:
            raise ValueError(f"工作流模板 {template_id} 不存在")

        workflow_def = json.loads(template.template_json)

        logger.info(f"加载工作流模板: {template.name} (ID={template_id})")

        # 2. 执行工作流
        engine = WorkflowEngine(self.db, task_queue)
        workflow_id = engine.execute_workflow(workflow_def, params)

        # 3. 更新模板使用计数
        template.usage_count += 1
        self.db.commit()

        logger.info(f"工作流 {workflow_id} 已启动，模板使用计数: {template.usage_count}")

        return workflow_id
```

### 5.2 应用启动时初始化

**修改文件**: `apps/api/main.py`

```python
from contextlib import asynccontextmanager
from apps.api.services.crawler_service import initialize_task_queue, shutdown_task_queue
from shared.database import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化任务队列
    logger.info("初始化任务队列...")
    initialize_task_queue(SessionLocal, num_workers=3)

    yield

    # 关闭时清理资源
    logger.info("关闭任务队列...")
    shutdown_task_queue(wait=True, timeout=30)

app = FastAPI(
    title="智能钓鱼助手 API",
    version="5.0.0",
    lifespan=lifespan  # 注册生命周期
)
```

---

## 六、测试验证

### 6.1 单元测试

**文件**: `tests/test_workflow_engine.py`

```python
import pytest
from packages.agent_fishing.tools.crawler.workflow.engine import WorkflowEngine

def test_workflow_execution():
    """测试工作流执行"""
    # TODO: 编写测试用例
    pass

def test_param_replacement():
    """测试参数替换"""
    # TODO: 编写测试用例
    pass
```

### 6.2 集成测试

**测试脚本**: `tests/integration/test_task_queue.py`

```bash
# 启动API服务器
uv run uvicorn apps.api.main:app --reload

# 测试触发爬虫任务
curl -X POST http://localhost:8000/api/v1/admin/crawler/tasks/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "task_type": "taobao",
    "keywords": ["钓鱼竿"],
    "max_pages": 2
  }'

# 查看任务状态
curl http://localhost:8000/api/v1/admin/crawler/tasks/{task_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# 查看任务日志
curl http://localhost:8000/api/v1/admin/crawler/tasks/{task_id}/logs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 七、验收标准

### 7.1 功能验收

- [x] 数据库迁移成功，新字段存在
- [ ] 任务队列启动正常，工作线程运行中
- [ ] 平台注册中心可识别taobao/jd平台
- [ ] 爬虫执行器可成功调用平台爬虫
- [ ] WebSocket推送进度信息正常
- [ ] 任务失败自动重试（指数退避）
- [ ] 工作流引擎可创建多步骤任务
- [ ] 工作流DAG依赖执行正确

### 7.2 性能验收

- [ ] 队列深度不超过100
- [ ] 任务平均执行时间 < 5分钟
- [ ] WebSocket推送延迟 < 500ms
- [ ] 数据库连接无泄漏

### 7.3 稳定性验收

- [ ] 连续执行100个任务无异常
- [ ] 工作线程无死锁
- [ ] 应用重启后队列正常恢复
- [ ] 数据库事务无死锁

---

## 八、交付清单

### 代码文件
- [x] 数据库模型扩展（system.py）
- [x] 数据库迁移脚本（alembic/versions/xxx.py）
- [x] 平台抽象层（platform/）
- [x] 任务队列（executor/task_queue.py）
- [x] 爬虫执行器（executor/crawler_executor.py）
- [x] 工作流引擎（workflow/engine.py）
- [x] 服务层集成（crawler_service.py, main.py）

### 文档
- [ ] 数据库表结构文档
- [ ] 平台适配器开发指南
- [ ] 工作流JSON格式文档
- [ ] API使用示例

### 测试
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 性能测试报告

---

**下一阶段**: [阶段2 - 工作流管理API](./workflow-phase2-api.md)
