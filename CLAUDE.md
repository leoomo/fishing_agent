# CLAUDE.md

智能钓鱼助手 v3.0.2.1 - 基于 LangChain 1.0+ 架构和 7 因子科学评分系统，专注于钓鱼时间推荐、天气分析，支持多种 LLM 提供商。

**当前版本**: v3.0.2.1 (架构优化和文档更新完善)

### 核心特性
- ✅ **LangChain 1.0+**: 原生 LangChain agents，移除 LangGraph 封装
- ✅ **同步优先**: 消除异步复杂性和事件循环问题
- ✅ **零抽象**: 直接 API 调用，无中间层
- ✅ **7 因子科学评分**: 温度、天气、风力、气压、湿度、季节、月相
- ✅ **动态趋势分析**: 识别"黄金钓鱼时段"
- ✅ **LLM 优化**: 95%+ 准确率的推理能力
- ✅ **时间意图识别**: 95%+ 准确率的时间段理解
- ✅ **架构优化**: 健康检查功能迁移至utils，代码组织更清晰
- ✅ **向量搜索**: 基于 DashScope Embedding API 的语义搜索（路亚装备知识）

## 架构概览

### 核心文件（3个工具模块）
- **`src/agent.py`** - 主智能代理入口
- **`src/tools/__init__.py`** - 统一工具接口，导出3个核心工具
- **`src/tools/basic_tools.py`** - 基础工具（时间功能）
- **`src/tools/weather_tools.py`** - 天气查询工具
- **`src/tools/fishing_tools.py`** - 钓鱼推荐工具（7因子评分系统）

### 扩展模块（已开发但未集成）
- **`src/tools/lure_tools.py`** - 路亚装备工具（推荐/对比/查询/识别）
- **`src/tools/lure/`** - 路亚装备完整模块

### 支持模块
- **`src/utils/`** - 核心工具类（包含health_check.py）
- **`src/fishing_agent/`** - 智能代理实现
- **`src/tools/scoring/`** - 7 因子科学评分系统
- **`src/data/`** - 数据存储和缓存
- **`src/tests/`** - 测试套件
- **`main.py`** - 交互式 CLI 入口

## 开发指南

### 环境配置
```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env

# 运行应用
uv run python main.py
```

### 测试
```bash
# 运行所有测试
uv run pytest src/tests/

# 测试评分系统
PYTHONPATH=src uv run pytest src/tests/scoring/test_enhanced_scorer.py -v

# 测试工具
uv run python -c "from src.tools import get_all_tools; print(f'工具数量: {len(get_all_tools())}')"
```

## 技术栈

### 核心框架
- **langchain>=0.3.0** - LangChain 1.0+ API
- **requests>=2.25.0** - HTTP 客户端
- **pydantic>=2.0.0** - 数据验证
- **python-dotenv>=1.1.1** - 环境变量管理
- **pandas>=2.3.3** - 数据分析
- **chromadb>=0.4.22** - 向量数据库
- **click>=8.1.0** - CLI 工具

### LLM 提供商
- **智谱AI GLM** (ANTHROPIC_AUTH_TOKEN)
- **通义千问** (DASHSCOPE_API_KEY) - 同时用于 Embedding API
- **OpenAI GPT** (OPENAI_API_KEY)

### 外部服务
- **彩云天气 API** (CAIYUN_API_KEY)
- **高德地图 API** (AMAP_API_KEY)
- **DashScope Embedding API** (DASHSCOPE_API_KEY) - 向量化服务

## 项目结构

```
fishing-agent/
├── src/                          # 源代码
│   ├── agent.py                  # 主代理入口
│   ├── tools/                    # 工具模块
│   │   ├── basic_tools.py        # 基础工具
│   │   ├── weather_tools.py      # 天气工具
│   │   ├── fishing_tools.py      # 钓鱼工具
│   │   ├── lure_tools.py         # 路亚工具
│   │   └── scoring/              # 评分系统
│   ├── fishing_agent/            # 代理实现
│   ├── utils/                    # 工具类
│   ├── data/                     # 数据存储
│   └── tests/                    # 测试套件
├── docs/                         # 项目文档
├── main.py                       # CLI 入口
└── pyproject.toml                # 项目配置
```

### 关键文件
- **`src/agent.py`** - 代理功能
- **`src/tools/fishing_tools.py`** - 7 因子钓鱼评分
- **`src/tools/lure_tools.py`** - 路亚装备推荐
- **`src/tools/scoring/enhanced_scorer.py`** - 评分算法
- **`main.py`** - 命令行界面

## 核心功能

### 钓鱼推荐系统
- **7 因子科学算法**: 温度、天气、风力、气压、湿度、季节、月相
- **动态趋势分析**: 识别"黄金钓鱼时段"
- **时间意图识别**: 95%+ 准确率的时间段理解
- **全国覆盖**: 支持 3,142+ 行政区域
- **中文查询**: 自然语言处理支持

### 天气服务
- **直接 API 调用**: 彩云天气 API 集成
- **72 小时预报**: 逐小时天气预测
- **智能降级**: API 失败时诚实报告

### 路亚装备推荐
- **智能建议**: 基于目标鱼种和环境条件
- **装备匹配**: 路亚、鱼线、配件推荐

## 开发指南

### 架构原则
1. **同步优先**: 使用 `requests` 直接 API 调用
2. **诚实数据**: 不生成假数据，提供诚实错误信息
3. **LangChain 1.0+**: 直接使用 `@tool` 装饰器
4. **统一日期处理**: 使用 date_utils 模块

### 常用导入
```python
# 代理创建
from src.agent import create_optimized_fishing_agent

# 工具导入
from src.tools import get_all_tools
from src.tools.weather_tools import get_current_weather
from src.tools.fishing_tools import query_fishing_recommendation
from src.tools.lure_tools import query_lure_recommendation

# 评分系统
from src.tools.scoring.enhanced_scorer import (
    calculate_seasonal_score, analyze_pressure_trend
)

# 工具类
from src.utils.date_utils import parse_date_input, format_date
from src.utils.coordinate_utils import get_coordinates

# 向量搜索（路亚装备）
from src.tools.lure.embeddings import DashScopeEmbedding
from src.tools.lure.vector_store import get_vector_store
from src.tools.lure.knowledge_search import KnowledgeSearchService
```

### 向量存储管理（路亚装备知识搜索）

#### CLI 命令
```bash
# 查看索引状态
uv run python -m src.tools.lure.cli status

# 重建向量索引
uv run python -m src.tools.lure.cli rebuild --force

# 测试搜索功能
uv run python -m src.tools.lure.cli search "鲈鱼习性" --type fish --top-k 3

# 查看配置
uv run python -m src.tools.lure.cli config
```

#### 懒加载索引
- 默认启用懒加载：首次搜索时自动触发索引
- 无需手动初始化，对用户透明
- 可通过环境变量 `VECTOR_AUTO_INDEX=false` 禁用

### 环境变量
```bash
# 必需 API
CAIYUN_API_KEY=your-caiyun-api-key
AMAP_API_KEY=your-amap-api-key

# LLM 提供商（DASHSCOPE同时用于 Embedding）
ANTHROPIC_AUTH_TOKEN=your-zhipu-token
DASHSCOPE_API_KEY=your-qwen-key

# 向量存储配置（可选）
VECTOR_EMBEDDING_MODEL=text-embedding-v3  # 1024维（推荐）
VECTOR_AUTO_INDEX=true  # 懒加载索引
```

### Python 环境
- **Python >=3.11**
- **uv 依赖管理**
- **同步优先架构**
- **LangChain 1.0+ 原生**