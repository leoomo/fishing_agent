# 智能钓鱼助手 - RPA爬虫使用指南 v3.2.1

## 概述

智能钓鱼助手现在支持三种不同的RPA爬虫模式，可以满足不同的数据采集需求。本版本更新包含淘宝店铺分类爬虫的最新功能优化、商品详情提取改进、新增标签页处理逻辑优化等。

## 🚀 快速开始

```bash
# 1. 安装依赖
uv sync --extra rpa
uv run playwright install chromium

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置必要的环境变量

# 3. 运行爬虫
uv run python run_crawler.py
```

## 📋 爬虫模式

### 1. 关键词搜索模式 (`keyword_search`)

传统的关键词搜索模式，通过淘宝搜索页面获取商品信息。

**特点：**
- 支持多个关键词
- 自动翻页
- 从商品详情页获取完整信息

**配置：**
```python
CRAWLER_MODE = "keyword_search"

KEYWORDS = [
    {"keyword": "禧玛诺鱼竿", "category": "鱼竿", "max_results": 10},
    {"keyword": "达亿瓦渔轮", "category": "渔轮", "max_results": 10},
]
```

### 2. 店铺分类模式 (`shop_category`) 🔥 NEW & UPDATED

访问指定店铺，点击特定分类，获取商品详情。

**特点：**
- 精准定位店铺和分类
- 自动点击分类导航
- 竖向滚动加载所有商品（测试期间暂时注释）
- 点击商品进入详情页获取完整信息
- 自动下载商品图片到 `shared/images/` 目录
- **v3.2.1新增**：支持ariaTipText属性提取商品名称
- **v3.2.1新增**：优化新标签页处理逻辑
- **v3.2.1新增**：增强商品详情提取能力

**配置：**
```python
CRAWLER_MODE = "shop_category"

SHOP_CATEGORY_CONFIG = {
    "shop_url": "https://shop437350870.taobao.com",  # 店铺地址
    "category_name": "路亚竿",                       # 目标分类
    "max_results": 5,                              # 最大结果数
    "download_images": True,                       # 是否下载图片
}
```

**业务流程：**
1. 登录淘宝账号（扫码登录，Cookie自动保存）
2. 进入指定店铺页面
3. 查找并点击目标分类（如"路亚竿"）
4. 等待分类页面加载完成
5. 竖向滚动直到所有商品加载完成（测试期间暂时注释）
6. 点击第一个商品进入详情页面（自动处理新标签页）
7. 提取商品信息（名称、价格、规格、图片等）
8. 下载所有商品图片
9. 返回结构化的商品数据

**v3.2.1 核心改进：**
- **交互式登录确认**：首次运行需要扫码登录，登录后等待用户确认是否成功
- **ariaTipText支持**：从aria-label属性提取商品名称，提高提取准确率
- **新标签页优化**：使用expect_popup()方法处理新打开的商品详情页
- **详情页等待优化**：等待domcontentloaded状态，不等待networkidle（更快）
- **选择器增强**：提供多组备选选择器，提高商品元素定位成功率

### 3. 店铺爬取模式 (`shop_crawl`) 🔥 NEW

批量爬取整个店铺或多个店铺的商品信息。

**特点：**
- 支持多个店铺批量爬取
- 可指定特定分类或爬取全部商品
- 支持分页爬取
- 自动保存店铺配置

**配置：**
```python
CRAWLER_MODE = "shop_crawl"

SHOP_CRAWL_CONFIG = {
    "shop_urls": [
        "https://shop437350870.taobao.com",
        "https://shop123456789.taobao.com",
    ],
    "categories": ["路亚竿"],  # None表示爬取所有分类
    "max_items_per_category": 20,
    "crawl_default_shops": True,  # 是否也爬取默认配置的店铺
}
```

## ⚙️ 完整配置示例

```python
# ==================== 配置区域 ====================

# 爬虫模式选择
CRAWLER_MODE = "shop_category"  # 可选: "keyword_search", "shop_category", "shop_crawl"

# 关键词搜索模式配置
KEYWORDS = [
    {"keyword": "禧玛诺鱼竿", "category": "鱼竿", "max_results": 10},
    {"keyword": "达亿瓦渔轮", "category": "渔轮", "max_results": 10},
]

# 店铺分类模式配置
SHOP_CATEGORY_CONFIG = {
    "shop_url": "https://shop437350870.taobao.com",
    "category_name": "路亚竿",
    "max_results": 5,
    "download_images": True,
}

# 店铺爬取模式配置
SHOP_CRAWL_CONFIG = {
    "shop_urls": [
        "https://shop437350870.taobao.com",
    ],
    "categories": ["路亚竿"],  # None表示爬取所有分类
    "max_items_per_category": 10,
    "crawl_default_shops": True,
}

# 通用配置
SAVE_TO_DB = True           # 是否保存到数据库
UPDATE_EXISTING = True      # 是否更新已存在的装备
```

## 📊 运行输出示例

### 店铺分类模式输出：
```
🎣 智能钓鱼助手 - 淘宝RPA爬虫 v3.2.1
============================================================

🔧 当前模式: 店铺分类模式

📦 初始化店铺分类RPA爬虫...
✅ RPA爬虫初始化成功
ℹ️  首次运行需要扫码登录，Cookie会自动保存

💾 初始化数据库...
✅ 数据库初始化成功

------------------------------------------------------------

🏪 店铺分类爬取:
   店铺地址: https://shop437350870.taobao.com
   目标分类: 路亚竿
   最大结果: 5
   下载图片: 是

✅ 店铺分类爬取完成，获取到 1 件装备

📦 装备预览（前5条）:
  1. 精品路亚竿超轻硬调碳素鱼竿 (ID: 123456789) - 知境 - ¥298

💾 保存到数据库...
✅ 保存完成: 成功 1 件，跳过 0 件，失败 0 件

============================================================
📊 爬取任务完成！
   爬取模式: 店铺分类模式
   成功保存: 1 件装备
   总获取: 1 件装备
============================================================
```

## 🗂️ 数据结构

### EquipmentData 字段：
```python
{
    "name": "商品名称",              # 商品完整名称
    "brand": "品牌名称",             # 商品品牌
    "price": "价格",                # 商品价格
    "url": "详情页URL",             # 商品详情页链接
    "category": "商品类别",         # 商品分类
    "source": "数据源",             # 如 "taobao_shop_rpa"
    "description": "商品描述",       # 详细描述
    "images": ["图片URL1", "图片URL2"],  # 图片链接列表
    "specs": {"规格名": "规格值"},    # 规格参数字典
    "id": "商品ID"                  # 商品ID（店铺模式特有）
}
```

## 📁 图片下载

店铺分类模式支持自动下载商品图片：

```
shared/images/
├── 123456789/              # 商品ID目录
│   ├── image_1.jpg
│   ├── image_2.png
│   └── image_3.webp
└── 987654321/
    ├── image_1.jpg
    └── image_2.png
```

## 🔧 v3.2.1 技术改进详解

### 1. 竖向滑动逻辑优化

**状态**：已完成优化，测试期间暂时注释

为了解决原滚动实现太快（1秒内完成）导致的问题，我们实现了渐进式滚动：

**优化前的问题**：
- 无法充分加载懒加载内容
- 滚动行为不自然，容易被检测
- 错过动态加载的商品

**优化后的特性**：
- **渐进式滚动**：每次滚动0.8-1.5个视窗高度，模拟人类浏览
- **智能等待**：每次滚动后等待1.5-2.5秒随机时间
- **平滑动画**：使用`behavior: 'smooth'`让滚动更自然
- **智能检测**：检测页面高度变化，连续5次无新内容则认为完成

**配置参数**：
```python
@dataclass
class RPAConfig:
    # 滚动配置
    scroll_step_min: float = 0.8        # 最小滚动步长（视窗高度倍数）
    scroll_step_max: float = 1.5        # 最大滚动步长（视窗高度倍数）
    scroll_wait_min: float = 1.5        # 最小等待时间（秒）
    scroll_wait_max: float = 2.5        # 最大等待时间（秒）
    scroll_max_attempts: int = 50       # 最大滚动尝试次数
    scroll_completion_threshold: int = 5  # 完成检测阈值
```

### 2. 新标签页处理逻辑

**改进前**：使用传统的点击方法，可能无法正确处理新打开的标签页

**改进后**：
```python
# 监听新页面打开
with page.expect_popup() as popup_info:
    first_product.click()

# 获取新打开的页面
new_page = popup_info.value
# 等待页面基本加载完成
new_page.wait_for_load_state('domcontentloaded', timeout=10000)
```

**优势**：
- 可靠捕获新打开的标签页
- 更快的页面加载检测（domcontentloaded vs networkidle）
- 更好的错误处理机制

### 3. 商品名称提取增强

**新增 ariaTipText 支持**：
```python
def _extract_product_name(self, page: Page) -> Optional[str]:
    # 常规选择器
    selectors = [
        "h1[data-spm='1000983']",
        ".tb-main-title",
        "h1",
    ]

    # 尝试从 aria-label 属性提取
    element = page.locator("#ariaTipText")
    if element.count() > 0:
        aria_label = element.get_attribute("aria-label")
        if aria_label:
            # 从 aria-label 中提取商品名称
            # 格式类似: "欢迎进入 DOOP多普灵感/轻鸿KINHON/知境/信号钟芳斌路亚竿虫竿鲈鱼鳜鱼杆-淘宝网,盲人用户使用操作智能引导..."
            name = aria_label.split("欢迎进入 ")[1].split("-淘宝网")[0]
            return name.strip()
```

### 4. 交互式登录确认

**流程改进**：
1. 显示二维码供用户扫码
2. 等待用户扫码登录
3. **新增**：弹出确认对话框，询问用户是否成功登录
4. 根据用户反馈决定是否继续执行

```python
# 等待用户确认登录成功
import tkinter as tk
from tkinter import messagebox

def ask_login_confirmation():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    result = messagebox.askyesno("登录确认", "请确认是否已成功登录淘宝账号？")
    root.destroy()
    return result

if not ask_login_confirmation():
    logger.error("用户确认未登录成功，终止流程")
    return False
```

### 5. 登录页面刷新问题修复

**问题**：扫码登录页面频繁自动刷新，导致无法完成扫码

**解决方案**：
- 登录成功后等待更长时间（5秒）
- 检查登录状态的循环，最多尝试10次
- 保存Cookie，下次运行时复用

## 🛠️ 故障排除

### 常见问题：

1. **登录失败**
   - 确保网络连接正常
   - 检查浏览器是否能正常启动
   - 手动登录淘宝账号后再试
   - v3.2.1新增：确认登录对话框是否正确弹出

2. **找不到分类**
   - 检查店铺页面结构是否发生变化
   - 确认分类名称是否正确
   - 查看日志中的选择器尝试情况
   - v3.2.1新增：尝试多个选择器，提高成功率

3. **图片下载失败**
   - 检查 `shared/images` 目录权限
   - 确认网络连接稳定
   - 查看图片URL是否有效

4. **数据库保存失败**
   - 检查数据库连接配置
   - 确认表结构是否正确
   - 查看错误日志详情

5. **新标签页无法打开（v3.2.1）**
   - 检查浏览器是否允许弹窗
   - 确认点击操作是否触发新页面
   - 查expect_popup()超时错误日志

## 📝 开发说明

### 核心类：

1. **TaobaoRPA** - 关键词搜索模式
   - 文件：`packages/agent_fishing/tools/crawler/rpa/taobao_rpa.py`
   - 方法：`search_equipment()`

2. **TaobaoShopCategoryRPA** - 店铺分类模式
   - 文件：`packages/agent_fishing/tools/crawler/rpa/taobao_shop_category_rpa.py`
   - 方法：`crawl_shop_category()`

3. **TaobaoShopRPA** - 店铺爬取模式
   - 文件：`packages/agent_fishing/tools/crawler/rpa/taobao_shop_rpa.py`
   - 方法：`crawl_shop()`, `crawl_default_shops()`

### 扩展新模式：

1. 在相应的RPA类中实现新的爬取逻辑
2. 在 `run_crawler.py` 中添加配置和处理函数
3. 更新 `CRAWLER_MODE` 选项
4. 添加相应的配置结构

## 🎯 使用建议

1. **首次使用**：建议先用店铺分类模式测试，功能最完整
2. **数据采集**：店铺爬取模式适合大量数据采集
3. **精准搜索**：关键词搜索模式适合特定商品搜索
4. **图片收集**：店铺分类模式支持自动图片下载

## 🔗 相关文件

- **主脚本**：`run_crawler.py`
- **RPA基类**：`packages/agent_fishing/tools/crawler/rpa/playwright_spider.py`
- **配置管理**：`packages/agent_fishing/tools/crawler/rpa/config.py`
- **登录管理**：`packages/agent_fishing/tools/crawler/rpa/login_manager.py`
- **数据模型**：`packages/agent_fishing/tools/crawler/base_spider.py`

## 📋 版本更新日志

### v3.2.1 (2025-01-05)
**核心改进**：
- ✅ **登录流程优化**：添加交互式确认模式，解决登录页面频繁刷新问题
- ✅ **ariaTipText支持**：新增从aria-label属性提取商品名称的能力
- ✅ **新标签页处理**：优化expect_popup()方法，正确处理商品详情页
- ✅ **竖向滚动优化**：实现渐进式滚动，支持配置化参数（测试期间注释）
- ✅ **页面加载优化**：使用domcontentloaded替代networkidle，提升响应速度

**技术细节**：
- 滚动步长：0.8-1.5个视窗高度
- 滚动等待：1.5-2.5秒随机
- 滚动检测：连续5次无新内容认为完成
- 页面对象创建和清理逻辑完善

### v3.2.0 (2024-12-XX)
**初始版本**：
- ✅ 三种爬虫模式：关键词搜索、店铺分类、店铺爬取
- ✅ RPA自动化：基于Playwright的浏览器自动化
- ✅ 数据持久化：自动保存到数据库
- ✅ 图片下载：支持商品图片自动下载

---

📞 **技术支持**：如遇问题请检查日志文件或联系开发团队。