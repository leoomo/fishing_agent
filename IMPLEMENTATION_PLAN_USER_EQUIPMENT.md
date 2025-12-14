# 装备信息获取模块完整实现方案

**版本**: v1.0  
**日期**: 2025-12-02  
**目标**: 实现电商装备爬虫 + 用户装备库管理功能

---

## 执行摘要

本方案为智能钓鱼助手v5.0.0设计**装备信息获取模块**，包含两大核心功能：

1. **优先级1 - 电商装备爬虫**：爬取淘宝/京东/论坛装备数据，自动入库并去重
2. **优先级2 - 用户装备库管理**：用户可添加/管理自己的装备，Agent提供基于用户装备的推荐

**技术约束**：
- Python 3.11+ + uv包管理
- 同步优先（requests）
- 遵循现有架构模式
- 诚实数据原则（不使用假数据）
- 完整功能开发（非MVP）

**预计工期**：13-18天

---

## 目录

1. [架构分析总结](#一架构分析总结)
2. [总体设计方案](#二总体设计方案)
3. [Phase 1: 电商爬虫模块](#三phase-1-电商爬虫模块设计)
4. [Phase 2: 用户装备管理](#四phase-2-用户装备管理模块设计)
5. [Phase 3: 测试和文档](#五phase-3-测试和文档)
6. [实施计划](#六实施计划)
7. [风险和解决方案](#七潜在风险和解决方案)
8. [关键文件列表](#critical-files-for-implementation)

---

## 一、架构分析总结

### 1.1 现有数据库架构

**装备表系统**：
- `equipment` (主表) - 包含 equipment_id, name, category, brand_id, model, price_min/max, description, user_level
- `rod_specs`, `reel_specs`, `line_specs`, `lure_specs` (规格表)
- `brands` (品牌表) - 包含 name_cn, name_en, country, tier (品牌等级)
- `product_images` (图片表) - 支持 equipment_id, rig_type_id, fish_species_id 关联

**知识表系统**：
- `fish_species`, `fish_knowledge` (鱼类)
- `rig_types`, `rig_specs` (钓组)
- `lure_types` (拟饵类型字典)

**缺失表**：
- `users` (用户信息表)
- `user_equipment` (用户装备库关联表)

### 1.2 现有工具层架构

**路径**: `/packages/agent_fishing/tools/lure_tools.py`

4个 LangChain `@tool` 装饰器工具：
1. `recommend_equipment` - 四因子评分推荐 (价格35% + 规格35% + 品牌15% + 用户水平15%)
2. `compare_equipment` - 多款装备对比
3. `lookup_fishing_knowledge` - 知识查询
4. `identify_from_image` - 图片识别

**关键服务**:
- `LureRecommender` (/lure/recommender.py) - 推荐算法核心
- `ImageManager` (/lure/image_manager.py) - 图片管理
- `LocalImageStorage` - 本地文件存储适配器
- `LureDatabase` (/lure/database.py) - 线程安全SQLite访问

### 1.3 现有API架构

**路径**: `/apps/api/`

**端点**：
- `POST /api/v1/fishing/chat` - 无状态对话接口
- `GET /api/v1/fishing/tools` - 工具列表
- `GET /health` - 健康检查

**Schema**: 
- `ChatRequest(query: str, model_provider: str)`
- `ChatResponse(response: str, status: str, error: Optional[str])`

**限制**：
- 无 user_id 支持
- 无用户上下文管理
- 完全无状态设计

### 1.4 技术栈

- Python 3.11+ + uv
- LangChain 1.0+ (@tool装饰器 + 动态Prompt中间件)
- SQLite (WAL模式，线程安全)
- requests (同步优先原则)
- FastAPI + Pydantic v2
- 图片存储：LocalImageStorage (file:// URL)

---

## 二、总体设计方案

### 2.1 模块拆分策略

```
packages/agent_fishing/tools/
├── lure/                          # 现有装备推荐模块
│   ├── database.py                # 现有：数据库访问
│   ├── recommender.py             # 现有：推荐算法
│   ├── image_manager.py           # 现有：图片管理
│   └── ...
├── lure_tools.py                  # 现有：4个LangChain工具
├── crawler/                       # 新增：电商爬虫模块
│   ├── __init__.py
│   ├── base_spider.py             # 基础爬虫类
│   ├── taobao_spider.py           # 淘宝爬虫
│   ├── jd_spider.py               # 京东爬虫
│   ├── forum_spider.py            # 论坛爬虫
│   ├── anti_crawler.py            # 反爬虫策略（UA轮换、代理池、延迟）
│   ├── parser.py                  # HTML/JSON解析器
│   ├── deduplicator.py            # 数据去重逻辑
│   ├── downloader.py              # 图片下载器
│   └── cli.py                     # 爬虫CLI工具
└── user_equipment/                # 新增：用户装备管理模块
    ├── __init__.py
    ├── manager.py                 # 用户装备管理器
    ├── tools.py                   # LangChain工具（@tool装饰器）
    └── recommender.py             # 基于用户装备的推荐增强

apps/api/routes/
├── fishing.py                     # 现有：对话接口
└── user_equipment.py              # 新增：用户装备管理API

apps/api/schemas/
├── chat.py                        # 现有：对话Schema
└── user_equipment.py              # 新增：用户装备Schema
```

### 2.2 数据流设计

**爬虫数据流**：
```
淘宝/京东/论坛 → BaseSpider.search_equipment()
    ↓
EquipmentData对象列表
    ↓
EquipmentDeduplicator.find_duplicates() （去重检查）
    ↓
DataPersister.save_equipment()
    ├→ 确保品牌存在
    ├→ 插入equipment主表
    ├→ 插入规格表（rod_specs/reel_specs等）
    └→ ImageDownloader下载图片 → LocalImageStorage保存
```

**用户装备管理数据流**：
```
用户添加装备 (API) → UserEquipmentManager.add_equipment()
    ↓
检查装备存在 + 去重
    ↓
插入user_equipment表
    ↓
Agent调用 → list_my_equipment工具 → 查询并格式化输出
```

**推荐增强数据流**：
```
用户请求推荐 → recommend_based_on_my_equipment工具
    ↓
UserBasedRecommender分析用户装备
    ├→ upgrade: 找出低端装备，推荐升级
    ├→ complete: 检查缺失类别，推荐补齐
    └→ match: 分析鱼竿渔轮匹配度
    ↓
调用LureRecommender基础推荐算法
    ↓
返回Markdown格式推荐报告
```

---

## 三、Phase 1: 电商爬虫模块设计

### 3.1 数据库表扩展

**扩展equipment表**：

```sql
ALTER TABLE equipment ADD COLUMN source TEXT DEFAULT 'manual';
ALTER TABLE equipment ADD COLUMN source_url TEXT;
ALTER TABLE equipment ADD COLUMN crawled_at TIMESTAMP;
ALTER TABLE equipment ADD COLUMN last_synced_at TIMESTAMP;
```

- `source`: 数据来源（crawler/manual/import）
- `source_url`: 原始商品URL
- `crawled_at`: 爬取时间
- `last_synced_at`: 最后同步时间

### 3.2 核心类设计

#### 3.2.1 数据结构 (`base_spider.py`)

```python
@dataclass
class EquipmentData:
    """爬取的装备数据结构"""
    name: str                           # 装备名称
    category: str                       # 类别（鱼竿/渔轮/鱼线/拟饵）
    brand_name: str                     # 品牌名称
    model: Optional[str]                # 型号
    price_min: float                    # 最低价格
    price_max: Optional[float]          # 最高价格
    description: Optional[str]          # 描述
    features: Optional[str]             # 特性（JSON字符串）
    target_fish: Optional[str]          # 目标鱼种
    user_level: Optional[str]           # 用户水平
    source_url: str                     # 来源URL
    images: List[Dict[str, str]]        # [{"url": "...", "type": "main/detail"}]
    specs: Dict[str, Any]               # 规格参数（根据category不同）
```

#### 3.2.2 基础爬虫类 (`base_spider.py`)

```python
class BaseSpider(ABC):
    """基础爬虫类"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.request_delay = config.get("request_delay", 2)  # 请求延迟
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 30)
        
    @abstractmethod
    def search_equipment(
        self, keyword: str, category: Optional[str] = None, max_results: int = 50
    ) -> List[EquipmentData]:
        """搜索装备"""
        pass
    
    @abstractmethod
    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """获取商品详情"""
        pass
    
    def fetch_with_retry(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """带重试的请求"""
        # 实现重试逻辑 + 延迟
        pass
```

#### 3.2.3 反爬虫策略 (`anti_crawler.py`)

```python
class UserAgentRotator:
    """User-Agent轮换器"""
    USER_AGENTS = [...]  # 10+ 真实浏览器UA
    
    def get_random_ua(self) -> str:
        return random.choice(self.USER_AGENTS)
    
    def get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        return {
            "User-Agent": self.get_random_ua(),
            "Accept": "text/html,application/xhtml+xml,...",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            # ... 更多真实请求头
        }

class RequestThrottler:
    """请求节流器"""
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        
    def wait(self):
        """智能延迟（随机 + 指数退避）"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
```

#### 3.2.4 数据去重器 (`deduplicator.py`)

```python
class EquipmentDeduplicator:
    """装备去重器"""
    
    def find_duplicates(self, equipment: EquipmentData) -> Optional[int]:
        """
        查找重复装备
        
        去重规则（按优先级）：
        1. 完全匹配：brand_name + model
        2. 模糊匹配：brand_name + name（相似度>80%）
        3. 规格匹配：category + 关键规格
        
        Returns:
            如果找到重复，返回existing equipment_id；否则返回None
        """
        # 1. 精确匹配 brand + model
        if equipment.model:
            query = "SELECT e.equipment_id FROM equipment e JOIN brands b ON e.brand_id = b.id WHERE b.name_cn = ? AND e.model = ?"
            # ...
        
        # 2. 模糊匹配（使用difflib.SequenceMatcher）
        # ...
        
        return None
```

#### 3.2.5 图片下载器 (`downloader.py`)

```python
class ImageDownloader:
    """图片下载器"""
    
    def download_and_save(
        self, image_url: str, equipment_name: str, image_type: str = "main"
    ) -> Optional[str]:
        """下载并保存图片到LocalImageStorage"""
        # 1. 下载图片
        response = requests.get(image_url, timeout=30, stream=True)
        image_data = response.content
        
        # 2. 生成相对路径（规范化文件名）
        suffix = self._guess_image_format(image_data)
        relative_path = f"crawler/{safe_name}_{image_type}_{hash}.{suffix}"
        
        # 3. 保存到存储
        local_url = self.storage.save(image_data, relative_path)
        return local_url
```

#### 3.2.6 数据持久化器 (`data_persister.py`)

```python
class DataPersister:
    """数据持久化器"""
    
    def save_equipment(
        self, equipment: EquipmentData, update_if_exists: bool = True
    ) -> Optional[int]:
        """保存装备数据"""
        # 1. 检查去重
        existing_id = self.deduplicator.find_duplicates(equipment)
        if existing_id:
            if update_if_exists:
                self._update_equipment(existing_id, equipment)
            return existing_id
        
        # 2. 确保品牌存在（不存在则创建）
        brand_id = self._ensure_brand_exists(equipment.brand_name)
        
        # 3. 插入装备主表
        equipment_id = self._insert_equipment(equipment, brand_id)
        
        # 4. 插入规格表（根据category不同）
        self._insert_specs(equipment_id, equipment)
        
        # 5. 下载并保存图片
        self._save_images(equipment_id, equipment)
        
        return equipment_id
```

### 3.3 爬虫实现策略

#### 3.3.1 淘宝爬虫 (`taobao_spider.py`)

**挑战**：
- 反爬虫最严格
- JS动态渲染
- 滑块验证码

**策略**：
1. 使用移动版API（更宽松）
2. Selenium无头浏览器（备选）
3. Cookie池管理
4. 请求延迟2-5秒

```python
class TaobaoSpider(BaseSpider):
    BASE_URL = "https://s.taobao.com/search"
    
    def search_equipment(self, keyword: str, category: Optional[str] = None, max_results: int = 50):
        # 1. 构建搜索关键词（添加类别前缀：路亚竿、路亚轮等）
        search_keyword = self._build_search_keyword(keyword, category)
        
        # 2. 发起请求（带UA轮换 + 延迟）
        self.throttler.wait()
        headers = self.ua_rotator.get_headers(referer="https://www.taobao.com")
        response = self.fetch_with_retry(self.BASE_URL, params={"q": search_keyword})
        
        # 3. 解析HTML（BeautifulSoup）
        products = self._parse_search_results(response.text)
        
        # 4. 提取装备信息
        results = []
        for product in products[:max_results]:
            equipment = self._extract_equipment_from_listing(product)
            if equipment:
                results.append(equipment)
        
        return results
```

#### 3.3.2 京东爬虫 (`jd_spider.py`)

**优势**：
- API结构清晰
- 反爬虫相对宽松
- 商品信息规范

```python
class JDSpider(BaseSpider):
    SEARCH_API = "https://search.jd.com/Search"
    
    def search_equipment(self, keyword: str, category: Optional[str] = None, max_results: int = 50):
        # 类似实现，但API调用更简单
        pass
```

#### 3.3.3 论坛爬虫 (`forum_spider.py`)

**目标论坛**：
- 路亚之家
- 中国钓鱼论坛

**特点**：
- 装备测评帖子
- 用户真实评价
- 装备实拍图

```python
class ForumSpider(BaseSpider):
    FORUMS = {
        "路亚之家": "http://www.luya.com/forum.php",
    }
    
    def extract_from_review_post(self, post_url: str) -> Optional[EquipmentData]:
        """从测评帖提取信息"""
        # 提取装备名称、参数、图片、评价
        pass
```

### 3.4 CLI工具 (`cli.py`)

```python
import click

@click.group()
def crawler_cli():
    """装备爬虫CLI工具"""
    pass

@crawler_cli.command()
@click.option("--source", type=click.Choice(["taobao", "jd", "forum", "all"]), default="all")
@click.option("--keyword", default="路亚竿")
@click.option("--category", type=click.Choice(["鱼竿", "渔轮", "鱼线", "拟饵"]))
@click.option("--max-results", default=50)
@click.option("--update-existing/--no-update", default=True)
def crawl(source, keyword, category, max_results, update_existing):
    """
    爬取装备数据
    
    示例：
    python -m packages.agent_fishing.tools.crawler.cli crawl --source taobao --keyword "禧玛诺" --category 鱼竿
    """
    # 初始化服务
    db = get_db()
    storage = LocalImageStorage(...)
    image_manager = ImageManager(db, storage)
    deduplicator = EquipmentDeduplicator(db)
    persister = DataPersister(db, image_manager, deduplicator)
    
    # 选择爬虫
    spiders = []
    if source in ["taobao", "all"]:
        spiders.append(("淘宝", TaobaoSpider()))
    # ...
    
    # 执行爬取
    for spider_name, spider in spiders:
        results = spider.search_equipment(keyword, category, max_results)
        for equipment in results:
            persister.save_equipment(equipment, update_existing)
```

### 3.5 反爬虫策略总结

1. **请求延迟**：2-5秒随机延迟
2. **User-Agent轮换**：10+真实浏览器UA
3. **Headers伪装**：模拟真实浏览器
4. **代理池（可选）**：预留接口
5. **错误重试**：最多3次，指数退避
6. **Cookie管理**：维护会话状态

### 3.6 数据去重策略

**优先级去重规则**：
1. **品牌+型号**完全匹配 → 认为是同一产品
2. **品牌+名称**相似度>80% → 可能是同一产品
3. **关键规格**匹配（鱼竿：长度+硬度）

**增量更新策略**：
- 如果装备来源为crawler，更新价格、图片、描述
- 如果装备来源为manual（手动录入），保留不更新

---

## 四、Phase 2: 用户装备管理模块设计

### 4.1 数据库表设计

#### 4.1.1 users表

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,           -- 用户名
    nickname TEXT,                           -- 昵称
    email TEXT UNIQUE,                       -- 邮箱
    phone TEXT,                              -- 手机号
    user_level TEXT DEFAULT '新手',          -- 用户水平
    fishing_experience_years INTEGER,        -- 钓龄（年）
    preferred_fish TEXT,                     -- 偏好鱼种
    preferred_scenarios TEXT,                -- 偏好场景
    avatar_url TEXT,                         -- 头像URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### 4.1.2 user_equipment表

```sql
CREATE TABLE user_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                -- 用户ID
    equipment_id INTEGER NOT NULL,           -- 装备ID
    purchase_date TEXT,                      -- 购买日期
    purchase_price REAL,                     -- 购买价格
    purchase_source TEXT,                    -- 购买渠道
    condition TEXT DEFAULT '正常',           -- 状态
    usage_frequency TEXT,                    -- 使用频率
    notes TEXT,                              -- 备注
    is_favorite INTEGER DEFAULT 0,           -- 是否收藏
    tags TEXT,                               -- 标签
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    UNIQUE(user_id, equipment_id)            -- 防止重复添加
);

CREATE INDEX idx_user_equipment_user ON user_equipment(user_id);
CREATE INDEX idx_user_equipment_equipment ON user_equipment(equipment_id);
CREATE INDEX idx_user_equipment_favorite ON user_equipment(is_favorite);
```

### 4.2 用户装备管理器 (`manager.py`)

```python
class UserEquipmentManager:
    """用户装备管理器"""
    
    def __init__(self, db):
        self.db = db
    
    # ========== 用户管理 ==========
    
    def create_user(self, username: str, nickname: Optional[str] = None, 
                    email: Optional[str] = None, user_level: str = "新手") -> int:
        """创建用户"""
        query = "INSERT INTO users (username, nickname, email, user_level) VALUES (?, ?, ?, ?)"
        return self.db.execute_write(query, (username, nickname, email, user_level))
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """获取用户信息"""
        query = "SELECT * FROM users WHERE user_id = ?"
        rows = self.db.execute(query, (user_id,))
        return rows[0] if rows else None
    
    # ========== 装备管理 ==========
    
    def add_equipment(
        self, user_id: int, equipment_id: int, 
        purchase_price: Optional[float] = None, 
        notes: Optional[str] = None, 
        tags: Optional[List[str]] = None
    ) -> Optional[int]:
        """添加装备到用户库"""
        # 1. 检查装备是否存在
        # 2. 检查是否已添加（UNIQUE约束）
        # 3. 插入user_equipment表
        pass
    
    def remove_equipment(self, user_id: int, equipment_id: int) -> bool:
        """从装备库删除"""
        query = "DELETE FROM user_equipment WHERE user_id = ? AND equipment_id = ?"
        affected = self.db.execute_write(query, (user_id, equipment_id))
        return affected > 0
    
    def list_user_equipment(
        self, user_id: int, category: Optional[str] = None, 
        only_favorites: bool = False
    ) -> List[UserEquipment]:
        """查询用户装备列表"""
        # JOIN equipment表和brands表获取完整信息
        # 返回UserEquipment对象列表
        pass
    
    def toggle_favorite(self, user_id: int, equipment_id: int) -> bool:
        """切换收藏状态"""
        query = "UPDATE user_equipment SET is_favorite = 1 - is_favorite WHERE user_id = ? AND equipment_id = ?"
        affected = self.db.execute_write(query, (user_id, equipment_id))
        return affected > 0
    
    # ========== 统计分析 ==========
    
    def get_equipment_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取用户装备统计"""
        # 按类别统计数量、平均价格、总花费
        pass
    
    def get_missing_equipment_types(self, user_id: int) -> List[str]:
        """分析缺失的装备类型"""
        # 返回用户未拥有的装备类别
        pass
```

### 4.3 LangChain工具扩展 (`tools.py`)

```python
from langchain.tools import tool

@tool
def list_my_equipment(
    user_id: int,
    category: Optional[str] = None,
    only_favorites: bool = False
) -> str:
    """
    查看我的装备库
    
    触发关键词：我的装备、我有哪些、查看装备库、装备清单
    
    Returns:
        Markdown格式的装备列表
    """
    manager = _get_manager()
    equipment_list = manager.list_user_equipment(user_id, category, only_favorites)
    
    # 格式化输出Markdown
    output = "# 我的装备库\n\n"
    # 按类别分组展示
    # ...
    return output


@tool
def add_equipment_to_profile(
    user_id: int,
    equipment_id: int,
    purchase_price: Optional[float] = None,
    notes: Optional[str] = None
) -> str:
    """
    添加装备到我的装备库
    
    触发关键词：添加装备、我买了、记录一下
    """
    manager = _get_manager()
    try:
        result_id = manager.add_equipment(user_id, equipment_id, purchase_price, notes)
        return f"✅ 成功添加装备\n\n可以使用 list_my_equipment 查看装备库"
    except ValueError as e:
        return f"❌ 添加失败：{str(e)}"


@tool
def remove_equipment_from_profile(user_id: int, equipment_id: int) -> str:
    """从装备库删除装备"""
    manager = _get_manager()
    success = manager.remove_equipment(user_id, equipment_id)
    return "✅ 装备已移除" if success else "❌ 删除失败"


@tool
def recommend_based_on_my_equipment(user_id: int, need_type: str) -> str:
    """
    基于我的装备推荐新装备
    
    触发关键词：升级、搭配、配什么、买什么好
    
    Args:
        need_type: 需求类型
            - upgrade: 升级现有装备
            - complete: 完善装备配置
            - match: 装备搭配建议
    """
    from .recommender import UserBasedRecommender
    
    recommender = UserBasedRecommender(...)
    
    if need_type == "upgrade":
        return recommender.recommend_upgrade(user_id)
    elif need_type == "complete":
        return recommender.recommend_complete_set(user_id)
    elif need_type == "match":
        return recommender.recommend_matching(user_id)
```

### 4.4 基于用户装备的推荐增强 (`recommender.py`)

```python
class UserBasedRecommender:
    """基于用户装备的推荐器"""
    
    def __init__(self, db, user_equipment_manager):
        self.db = db
        self.user_manager = user_equipment_manager
        self.base_recommender = LureRecommender(db)
    
    def recommend_upgrade(self, user_id: int) -> str:
        """
        推荐装备升级路线
        
        策略：
        1. 分析用户当前装备水平（入门/中端/高端）
        2. 找出薄弱环节（低端装备）
        3. 推荐同类更高一级的装备
        """
        user_equipment = self.user_manager.list_user_equipment(user_id)
        
        # 分析装备水平
        analysis = self._analyze_equipment_level(user_equipment)
        
        # 找出需要升级的装备
        upgrade_targets = self._find_upgrade_targets(user_equipment)
        
        # 使用基础推荐器推荐更高级装备
        output = "# 装备升级建议\n\n"
        for target in upgrade_targets:
            recommendations = self.base_recommender.recommend(
                equipment_type=target['category'],
                user_specs={
                    "budget": target['suggested_budget'],
                    "user_level": "进阶"
                },
                top_k=2
            )
            # 格式化输出
        
        return output
    
    def recommend_complete_set(self, user_id: int) -> str:
        """
        推荐完善装备配置
        
        策略：
        1. 检查基础装备是否齐全（鱼竿、渔轮、鱼线）
        2. 推荐缺失的装备
        3. 推荐拟饵组合
        """
        user_equipment = self.user_manager.list_user_equipment(user_id)
        
        # 统计已有类别
        owned_categories = set(eq.category for eq in user_equipment)
        required_categories = {"鱼竿", "渔轮", "鱼线"}
        missing_categories = required_categories - owned_categories
        
        # 推荐缺失装备
        output = "# 装备配置完善建议\n\n"
        # ...
        
        return output
    
    def recommend_matching(self, user_id: int) -> str:
        """
        推荐装备搭配
        
        策略：
        1. 检查鱼竿和渔轮是否匹配
        2. 检查鱼线是否适配
        3. 给出搭配建议
        """
        # 分析每个鱼竿的最佳搭配
        # 根据鱼竿硬度推荐匹配的渔轮型号
        # 根据鱼竿推荐线号
        pass
```

### 4.5 API端点设计

#### 4.5.1 Schema定义 (`schemas/user_equipment.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    nickname: Optional[str] = None
    email: Optional[str] = None
    user_level: str = Field(default="新手", pattern="^(新手|进阶|高手)$")

class AddEquipmentRequest(BaseModel):
    equipment_id: int = Field(..., gt=0)
    purchase_price: Optional[float] = Field(None, ge=0)
    purchase_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None

class UserEquipmentResponse(BaseModel):
    id: int
    user_id: int
    equipment_id: int
    equipment_name: str
    category: str
    brand_name: Optional[str]
    purchase_price: Optional[float]
    # ... 更多字段
```

#### 4.5.2 路由实现 (`routes/user_equipment.py`)

```python
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()

@router.post("/users", status_code=201)
async def create_user(request: UserCreate):
    """创建用户"""
    # 实现逻辑
    pass

@router.post("/users/{user_id}/equipment", status_code=201)
async def add_equipment(user_id: int, request: AddEquipmentRequest):
    """添加装备到用户库"""
    # 实现逻辑
    pass

@router.get("/users/{user_id}/equipment")
async def list_equipment(user_id: int, category: Optional[str] = None):
    """查询用户装备列表"""
    # 实现逻辑
    pass

@router.delete("/users/{user_id}/equipment/{equipment_id}")
async def remove_equipment(user_id: int, equipment_id: int):
    """删除装备"""
    # 实现逻辑
    pass

@router.post("/users/{user_id}/recommend")
async def recommend_equipment(user_id: int, need_type: str):
    """基于用户装备推荐"""
    # 调用UserBasedRecommender
    pass

@router.get("/users/{user_id}/statistics")
async def get_statistics(user_id: int):
    """获取用户装备统计"""
    # 实现逻辑
    pass
```

### 4.6 Agent集成设计

#### 扩展ChatRequest Schema

```python
class ChatRequest(BaseModel):
    query: str = Field(..., description="用户查询内容")
    user_id: Optional[int] = Field(None, description="用户ID（可选）")
    model_provider: str = Field(default="zhipu")
```

#### 修改Agent调用逻辑

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    agent = create_agent(model_provider=request.model_provider)
    
    # 如果提供了user_id，将其注入到查询上下文
    query = request.query
    if request.user_id:
        query = f"[USER_ID:{request.user_id}] {query}"
    
    response = agent.run(query)
    return ChatResponse(response=response, status="success")
```

#### 工具集成到Agent

```python
# /packages/agent_fishing/tools/__init__.py
def get_all_tools():
    from .user_equipment.tools import USER_EQUIPMENT_TOOLS  # 新增
    
    return [
        *get_basic_tools(),
        *get_weather_tools(),
        *get_fishing_tools(),
        *get_lure_tools(),
        *USER_EQUIPMENT_TOOLS  # 新增
    ]
```

---

## 五、Phase 3: 测试和文档

### 5.1 单元测试

```python
# /tests/test_user_equipment.py
import pytest
from packages.agent_fishing.tools.user_equipment.manager import UserEquipmentManager

def test_create_user():
    """测试创建用户"""
    pass

def test_add_equipment():
    """测试添加装备"""
    pass

def test_duplicate_equipment():
    """测试重复添加装备"""
    pass

# /tests/test_crawler.py
def test_deduplicator():
    """测试去重器"""
    pass
```

### 5.2 API文档更新

更新 `/README.md`:

```markdown
## 新增API端点

### 用户管理
POST   /api/v1/user-equipment/users                     # 创建用户
GET    /api/v1/user-equipment/users/{user_id}           # 获取用户信息

### 装备管理
POST   /api/v1/user-equipment/users/{user_id}/equipment           # 添加装备
GET    /api/v1/user-equipment/users/{user_id}/equipment           # 查询装备列表
DELETE /api/v1/user-equipment/users/{user_id}/equipment/{eq_id}  # 删除装备

### 推荐
POST   /api/v1/user-equipment/users/{user_id}/recommend  # 基于用户装备推荐

### 爬虫CLI
```bash
# 爬取淘宝数据
python -m packages.agent_fishing.tools.crawler.cli crawl --source taobao --keyword "禧玛诺" --category 鱼竿

# 增量同步
python -m packages.agent_fishing.tools.crawler.cli sync --days 30
```
```

### 5.3 环境变量更新

```bash
# ========== 用户装备管理配置 ==========
ENABLE_USER_EQUIPMENT=true

# ========== 爬虫配置 ==========
ENABLE_CRAWLER=false
CRAWLER_REQUEST_DELAY=2
CRAWLER_MAX_RETRIES=3
# CRAWLER_PROXY_LIST=http://proxy1:8080,http://proxy2:8080
```

---

## 六、实施计划

### Phase 1: 爬虫模块（5-7天）

**Day 1-2: 基础架构**
- [ ] 创建crawler目录结构
- [ ] 实现BaseSpider抽象类
- [ ] 实现反爬虫策略模块
- [ ] 实现数据去重器

**Day 3-4: 爬虫实现**
- [ ] 实现TaobaoSpider
- [ ] 实现JDSpider
- [ ] 实现ForumSpider
- [ ] 实现ImageDownloader

**Day 5-6: 数据持久化**
- [ ] 实现DataPersister
- [ ] 数据库表扩展
- [ ] 集成ImageManager
- [ ] 增量更新逻辑

**Day 7: CLI和测试**
- [ ] 实现爬虫CLI工具
- [ ] 编写单元测试
- [ ] 手动测试爬取数据

### Phase 2: 用户装备管理（6-8天）

**Day 1-2: 数据库和核心逻辑**
- [ ] 创建users和user_equipment表
- [ ] 实现UserEquipmentManager
- [ ] 实现基础CRUD方法
- [ ] 编写Manager单元测试

**Day 3-4: LangChain工具**
- [ ] 实现4个@tool工具
- [ ] 实现UserBasedRecommender
- [ ] 集成到Agent工具集

**Day 5-6: API端点**
- [ ] 创建Schema
- [ ] 实现routes
- [ ] 扩展ChatRequest支持user_id
- [ ] 修改Agent调用逻辑

**Day 7-8: 推荐算法增强**
- [ ] 实现装备升级推荐
- [ ] 实现配置完善推荐
- [ ] 实现装备搭配分析
- [ ] 测试推荐准确性

### Phase 3: 测试和文档（2-3天）

**Day 1: 集成测试**
- [ ] 端到端测试
- [ ] 测试Agent调用
- [ ] 测试API所有端点
- [ ] 性能测试

**Day 2: 文档编写**
- [ ] 更新README
- [ ] 编写爬虫使用指南
- [ ] 编写API文档
- [ ] 创建示例代码

**Day 3: 优化和发布**
- [ ] 代码审查和重构
- [ ] 错误处理优化
- [ ] 日志优化
- [ ] 准备v3.2.0版本发布

**总工期**：13-18天

---

## 七、潜在风险和解决方案

### 7.1 爬虫风险

**风险1：反爬虫封禁**
- 表现：IP被封、验证码、请求频率限制
- 解决方案：
  - 增加请求延迟（2-5秒）
  - 使用代理池（可选）
  - 模拟真实用户行为
  - 降级方案：手动录入数据

**风险2：网站结构变化**
- 表现：HTML结构改变导致解析失败
- 解决方案：
  - 定期维护爬虫代码
  - 使用CSS选择器（更稳定）
  - 添加解析失败告警
  - 支持多个备选解析方案

**风险3：数据质量问题**
- 表现：爬取数据不完整、错误
- 解决方案：
  - 严格的数据验证
  - 人工审核机制
  - 允许手动修正
  - 标记数据来源

### 7.2 数据库风险

**风险1：数据重复**
- 表现：同一装备多次入库
- 解决方案：
  - 完善去重算法
  - 使用UNIQUE约束
  - 定期去重清理脚本

**风险2：迁移复杂性**
- 表现：新增表后现有数据迁移困难
- 解决方案：
  - 使用Alembic管理迁移
  - 提供迁移脚本
  - 保持向后兼容

### 7.3 性能风险

**风险1：爬虫阻塞主线程**
- 表现：爬取时API响应变慢
- 解决方案：
  - 爬虫使用独立CLI运行
  - 不在API请求中直接调用爬虫

**风险2：用户装备查询慢**
- 表现：装备库很大时查询变慢
- 解决方案：
  - 添加数据库索引
  - 分页查询
  - 缓存热门查询（可选）

### 7.4 安全风险

**风险1：用户ID伪造**
- 表现：用户可以访问他人装备库
- 解决方案：
  - 实现用户认证（JWT Token）
  - API鉴权中间件
  - 权限检查

**风险2：SQL注入**
- 表现：恶意用户注入SQL
- 解决方案：
  - 使用参数化查询（已实现）
  - Pydantic模型验证
  - 输入过滤

---

## 八、技术选型总结

### 8.1 爬虫技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| HTTP客户端 | requests | 同步优先，简单易用 |
| HTML解析 | BeautifulSoup4 | 容错性好，API友好 |
| 备选解析器 | lxml | 性能更高 |
| 无头浏览器 | Selenium（可选） | 处理JS渲染 |
| 图片处理 | Pillow | 获取元数据 |
| 反爬虫 | fake-useragent | UA轮换 |

### 8.2 不使用的技术

- ❌ **Scrapy**: 过于重量级
- ❌ **异步爬虫**: 同步优先原则
- ❌ **Redis缓存**: MVP阶段不需要
- ❌ **Celery**: CLI运行足够简单

---

## Critical Files for Implementation

基于以上设计，以下是实施时最关键的5个文件：

1. **`/packages/agent_fishing/tools/lure/database.py`**
   - 理由：需要添加users和user_equipment表初始化逻辑，以及equipment表字段扩展（source, source_url, crawled_at）
   - 关键点：数据库迁移脚本，保持向后兼容

2. **`/packages/agent_fishing/tools/crawler/base_spider.py`**
   - 理由：爬虫核心基类，定义EquipmentData数据结构和反爬虫策略接口
   - 关键点：抽象方法设计，重试机制，延迟策略

3. **`/packages/agent_fishing/tools/user_equipment/manager.py`**
   - 理由：用户装备管理核心逻辑，包含所有CRUD和统计分析方法
   - 关键点：数据验证，去重检查，JOIN查询优化

4. **`/packages/agent_fishing/tools/user_equipment/tools.py`**
   - 理由：4个LangChain工具实现，直接供Agent调用
   - 关键点：工具描述清晰，参数验证，Markdown格式化输出

5. **`/apps/api/routes/user_equipment.py`**
   - 理由：RESTful API端点实现，前后端集成的关键接口
   - 关键点：Schema验证，错误处理，依赖注入

---

## 附录：数据库迁移SQL

```sql
-- /packages/agent_fishing/tools/lure/migrations/001_add_user_equipment.sql

-- 1. 扩展equipment表
ALTER TABLE equipment ADD COLUMN source TEXT DEFAULT 'manual';
ALTER TABLE equipment ADD COLUMN source_url TEXT;
ALTER TABLE equipment ADD COLUMN crawled_at TIMESTAMP;
ALTER TABLE equipment ADD COLUMN last_synced_at TIMESTAMP;

-- 2. 创建users表
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    nickname TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    user_level TEXT DEFAULT '新手',
    fishing_experience_years INTEGER,
    preferred_fish TEXT,
    preferred_scenarios TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- 3. 创建user_equipment表
CREATE TABLE user_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    equipment_id INTEGER NOT NULL,
    purchase_date TEXT,
    purchase_price REAL,
    purchase_source TEXT,
    condition TEXT DEFAULT '正常',
    usage_frequency TEXT,
    notes TEXT,
    is_favorite INTEGER DEFAULT 0,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    UNIQUE(user_id, equipment_id)
);

CREATE INDEX idx_user_equipment_user ON user_equipment(user_id);
CREATE INDEX idx_user_equipment_equipment ON user_equipment(equipment_id);
CREATE INDEX idx_user_equipment_favorite ON user_equipment(is_favorite);
```

## pyproject.toml 依赖更新

```toml
[project]
dependencies = [
    # 现有依赖...
    "beautifulsoup4>=4.12.0",      # 新增：HTML解析
    "lxml>=5.0.0",                 # 新增：高性能解析器
    "fake-useragent>=1.4.0",       # 新增：UA轮换
    # "selenium>=4.16.0",          # 可选：无头浏览器
]
```

---

**方案总结**：
- ✅ 完整爬虫架构（支持淘宝/京东/论坛）
- ✅ 数据去重和增量更新
- ✅ 用户装备管理（CRUD + 推荐 + 统计）
- ✅ 4个LangChain工具集成
- ✅ RESTful API完整实现
- ✅ 反爬虫策略和错误处理
- ✅ 测试和文档规划
- ✅ 风险评估和解决方案

**设计原则**：
- 遵循现有架构模式
- 同步优先（requests）
- 诚实数据（不使用假数据）
- 完整功能（非MVP）
- LangChain 1.0+标准（@tool装饰器）
