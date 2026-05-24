[English](README.md) | [中文](README.zh-CN.md)

# Fishing Agent - Intelligent Fishing Assistant v5.1.0

An intelligent fishing assistant built on LangChain 1.0+, providing fishing time recommendations, weather analysis, and lure equipment management.

> Smart weather analysis for the best fishing time - **Modular Agent Architecture v5.1.0 + Fish Encyclopedia + CMS + Excel Batch Import + Vector Search + Analytics Optimization + JWT Auth + React Admin Panel + 7-Factor Scoring**

## Core Features

### What's New (v5.1.0)
- **Fish Encyclopedia** - Species knowledge base, seasonal activity patterns, equipment recommendations
- **Content Management System** - Rich text editor, auto-save drafts, semantic search, vector retrieval (ChromaDB)
- **Web Article Fetching** - Collect fishing knowledge from Wikipedia, LLM-enhanced translation, draft review workflow
- **Excel Batch Import** - Bulk import equipment data to review queue, template generation system
- **Vector Search** - Semantic search based on ChromaDB and DashScope Embedding
- **Accessory Management** - Hooks, sinkers, swivels, leader lines, and more
- **Lure Types** - Hard baits, soft baits, metal baits, fly fishing categories
- **Rig Configurations** - Texas rig, Carolina rig, drop shot rig templates
- **Equipment Sorting** - Sort by 12 fields (name/category/brand/price/length/weight/action/power/sections/created/updated), column header click sorting + advanced filter panel

### Core Capabilities
- **Smart Fishing Recommendations** - 7-factor scoring system (temperature/weather/wind/pressure/humidity/season/moon phase)
- **Lure Equipment Management** - Rods, reels, lines, lures with smart recommendations and comparison
- **Equipment Review Workflow** - Review queue for imported equipment, Excel import review, OCR review
- **Data Analytics** - Equipment stats, trend analysis, brand rankings, price distribution (SQL-optimized)
- **JWT Authentication** - Complete user auth with RBAC permission management
- **React Admin Panel** - Modern management UI (http://localhost:5173)
- **Web Scraping** - Multi-platform crawlers, task scheduling, real-time monitoring, data persistence
- **System Configuration** - API key management, system parameter settings
- **Smart Image Merging** - Auto-detect text below images, intelligent batch merging, local processing
- **Multi-Provider OCR** - Ollama (local) and SiliconFlow (cloud) OCR support
- **Equipment Import Agent** - Text compression middleware and batch equipment extraction

## Quick Start

### Prerequisites
- Python 3.11+
- uv package manager
- Node.js 18+ (for frontend)

### Install & Run

```bash
# 1. Clone and install dependencies
git clone https://github.com/leoomo/fishing_agent.git
cd fishing_agent
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env to add your API keys

# 3. Run CLI application
uv run python main.py

# 4. Or run API server
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# 5. Run frontend (optional)
cd apps/web-admin && npm install && npm run dev
```

## Quick Examples

```python
# Agent core functionality
from packages.agents.fishing import create_agent

agent = create_agent(model_provider="zhipu")
response = agent.run("How's the fishing in Hangzhou tomorrow?")
print(response)

# Equipment Import Agent
from packages.agents.equipment_import import EquipmentImportAgent

agent = EquipmentImportAgent(model_provider="zhipu")
response = agent.run("Help me identify equipment info in this text")
result = agent.extract_and_save(text="Guangwei Chiren GT602L-M Lure Rod", source_type="forum")

# Image processing
from packages.data_processing.image import BatchMergeProcessor

processor = BatchMergeProcessor(source_dir="./images")
result = processor.process()

# Vector search
from apps.api.services.vector_store import ArticleVectorStore

vector_store = ArticleVectorStore()
results = vector_store.search("fishing techniques", top_k=5)

# Web scraping
from packages.scraper.spiders import TaobaoSpider

spider = TaobaoSpider()
results = spider.crawl("target_url")
```

## URLs

- **API Server**: http://localhost:8000
- **React Admin Panel**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## Screenshots

### Monitoring Dashboard
<img src="docs/assets/screenshots/monitoring-dashboard.png" width="48%"> <img src="docs/assets/screenshots/monitoring-charts.png" width="48%">

### Data Workflow
<img src="docs/assets/screenshots/workflow-tabs.png" width="48%"> <img src="docs/assets/screenshots/workflow-import.png" width="48%">

### Equipment & OCR
<img src="docs/assets/screenshots/equipment-review.png" width="48%"> <img src="docs/assets/screenshots/ocr-worker.png" width="48%">

### Rig Configuration & Real-time Updates
<img src="docs/assets/screenshots/rig-management.png" width="48%"> <img src="docs/assets/screenshots/realtime-progress.png" width="48%">

> WeChat Mini Program screenshots coming soon.

## Tech Stack

### Backend
- **Python 3.11+** - Language
- **LangChain 1.0+** - LLM application framework
- **FastAPI** - Web framework
- **SQLite** - Database
- **JWT** - Authentication
- **APScheduler** - Task scheduling
- **Playwright** - Browser automation

### Frontend
- **React 19.2.0** - UI framework
- **TypeScript** - Type safety
- **Ant Design 5.22.0** - UI components
- **Vite** - Build tool
- **Redux Toolkit** - State management
- **ECharts** - Data visualization

## Architecture

```
packages/                       # Modular packages
├── agents/                     # Agent directory (v5.1.0 restructured)
│   ├── agent_component/        # Shared components
│   │   └── monitoring/         # Unified monitoring callback (MonitoringCallback)
│   ├── fishing/                # Fishing Assistant Agent
│   │   ├── core/               # agent.py, model_factory.py, prompts.py
│   │   ├── tools/              # basic, weather, fishing, lure/, user_equipment/
│   │   │   ├── lure/           # Lure tools (compatibility layer, re-exports apps.api)
│   │   │   └── user_equipment/ # User equipment management (manager, recommender)
│   │   ├── middleware/         # dynamic_prompt.py
│   │   └── utils/
│   └── equipment_import/       # Equipment Import Agent
│       ├── core/               # agent.py, extractor.py
│       ├── tools/              # Import tools
│       └── middleware/         # Text compression
├── data_processing/            # Data processing package
│   ├── image/                  # Image processing (ImageMerger, BatchMergeProcessor)
│   ├── ocr/                    # OCR text detection (TextRegionDetector)
│   └── dedup/                  # Deduplication tools
└── scraper/                    # Web scraper framework
    ├── spider/                 # Core spider (BaseSpider, CrawlItem)
    ├── spiders/                # Spider implementations (taobao, jd, forum)
    ├── rpa/                    # RPA automation framework
    ├── platform/               # Platform abstraction layer
    ├── workflow/               # Workflow engine
    ├── executor/               # Task executor
    ├── monitoring/             # Monitoring & alerting
    ├── scheduler/              # Cron scheduling
    ├── persister/              # Data persistence
    └── models/                 # Scraper models
apps/                           # Application layer
├── cli/                        # CLI app (main.py)
├── api/                        # FastAPI backend
│   ├── main.py                 # API server
│   ├── auth/                   # JWT auth module
│   ├── middleware/             # Auth middleware
│   ├── routes/                 # API routes
│   ├── schemas/                # Request/response models
│   ├── services/               # Business logic
│   ├── models/                 # Database models
│   ├── orm/                    # ORM layer & repositories
│   └── database.py             # Database access
└── web-admin/                  # React admin frontend
fishing_agent_app/             # WeChat Mini Program
shared/                         # Shared resources
├── config/                     # Global config
└── data/                       # Database files (equipment.db)
```

## API Endpoints

### Core
```
POST /api/v1/fishing/chat           # Chat endpoint
GET  /api/v1/fishing/tools          # Tool list
GET  /health                        # Health check
POST /api/v1/chat/message           # Chat message
GET  /api/v1/chat/sessions          # Session list
```

### Authentication
```
POST /api/v1/auth/login             # User login
GET  /api/v1/auth/me                # Get current user
POST /api/v1/auth/wechat/login      # WeChat login
POST /api/v1/auth/wechat/bind       # Bind WeChat account
```

### Fish Encyclopedia
```
GET    /api/v1/fish-species              # Species list
POST   /api/v1/fish-species              # Create species
GET    /api/v1/fish-species/{id}         # Species detail
PUT    /api/v1/fish-species/{id}         # Update species
DELETE /api/v1/fish-species/{id}         # Delete species
GET    /api/v1/fish-knowledge            # Knowledge list
POST   /api/v1/fish-knowledge            # Create knowledge
GET    /api/v1/fish-seasons              # Seasonal activity list
POST   /api/v1/fish-seasons              # Create seasonal activity
GET    /api/v1/fish-species/{id}/equipment  # Equipment recommendations
GET    /api/v1/fish-species/stats/stats    # Category stats
GET    /api/v1/fish-species/init-data       # Initialize data
```

### Content Management (CMS)
```
POST   /api/v1/articles                  # Create article (draft)
GET    /api/v1/articles                  # Article list (with filters)
GET    /api/v1/articles/{id}             # Article detail
PUT    /api/v1/articles/{id}             # Update article (auto-save)
DELETE /api/v1/articles/{id}             # Delete article
POST   /api/v1/articles/{id}/publish     # Publish article
POST   /api/v1/articles/{id}/archive     # Archive article
GET    /api/v1/articles/search           # Semantic search
GET    /api/v1/articles/{id}/similar     # Similar articles
```

### Article Web Fetching
```
GET    /api/v1/articles/fetch/sources    # Available data sources
GET    /api/v1/articles/fetch/progress   # Fetch progress
POST   /api/v1/articles/fetch/start      # Start fetching
POST   /api/v1/articles/fetch/pause      # Pause fetching
POST   /api/v1/articles/fetch/retry      # Retry failed items
POST   /api/v1/articles/fetch/reset      # Reset progress
```

### Accessories
```
GET    /api/v1/accessory          # Accessory list
POST   /api/v1/accessory          # Create accessory
GET    /api/v1/accessory/{id}     # Accessory detail
PUT    /api/v1/accessory/{id}     # Update accessory
DELETE /api/v1/accessory/{id}     # Delete accessory
GET    /api/v1/accessory/options  # Accessory options
GET    /api/v1/accessory/init-data  # Initialize data
```

### Lure Types
```
GET    /api/v1/lure-types          # Lure type list
POST   /api/v1/lure-types          # Create lure type
GET    /api/v1/lure-types/{id}     # Lure type detail
PUT    /api/v1/lure-types/{id}     # Update lure type
DELETE /api/v1/lure-types/{id}     # Delete lure type
GET    /api/v1/lure-types/init-data  # Initialize data
```

### Rig Configurations
```
GET    /api/v1/rigs                # Rig list
POST   /api/v1/rigs                # Create rig
GET    /api/v1/rigs/{id}           # Rig detail
PUT    /api/v1/rigs/{id}           # Update rig
DELETE /api/v1/rigs/{id}           # Delete rig
GET    /api/v1/rigs/options        # Rig options
```

### User Equipment
```
GET  /api/v1/user-equipment/equipment          # User equipment list
POST /api/v1/user-equipment/equipment          # Add equipment
PUT  /api/v1/user-equipment/equipment/{id}     # Update equipment
DELETE /api/v1/user-equipment/equipment/{id}   # Delete equipment
GET  /api/v1/user-equipment/recommendations    # Equipment recommendations
POST /api/v1/user-equipment/recommend          # Get recommendations
```

### Equipment Management
```
GET  /api/v1/equipment/equipment       # Equipment list (12-field sorting)
POST /api/v1/equipment/batch            # Batch add
PUT  /api/v1/equipment/equipment/{id}   # Update equipment
DELETE /api/v1/equipment/equipment/{id} # Delete equipment
GET  /api/v1/equipment/attributes       # Attribute options
```

### Data Import/Export
```
POST /api/v1/import-export/import           # Import equipment
POST /api/v1/import-export/export           # Export equipment
POST /api/v1/import-export/preview          # Preview import
GET  /api/v1/import-export/templates        # Import templates
```

### OCR
```
POST /api/v1/ocr/recognize-table    # OCR table recognition
GET  /api/v1/ocr/status             # OCR service status
POST /api/v1/ocr/workflow/execute   # OCR workflow
```

### Web Scraper
```
GET  /api/v1/crawler/tasks                # Task list
POST /api/v1/crawler/tasks                # Create task
PUT  /api/v1/crawler/tasks/{id}           # Update task
DELETE /api/v1/crawler/tasks/{id}         # Delete task
POST /api/v1/crawler/tasks/{id}/trigger   # Trigger task
GET  /api/v1/crawler/tasks/{id}/logs      # Task logs
```

### Data Workflow
```
GET  /api/v1/admin/workflow/stats                # Workflow stats
GET  /api/v1/admin/workflow/workers              # Worker list
GET  /api/v1/admin/workflow/ocr/tasks            # OCR tasks
POST /api/v1/admin/workflow/ocr/tasks/{id}/retry # Retry OCR task
GET  /api/v1/admin/workflow/review/tasks         # Review tasks
POST /api/v1/admin/workflow/review/tasks/{id}/review  # Review task
POST /api/v1/admin/workflow/import/templates     # Generate import template
POST /api/v1/admin/workflow/import/preview       # Preview import
POST /api/v1/admin/workflow/import/execute       # Execute import
```

### Monitoring
```
GET /api/v1/admin/monitor/api-stats       # API stats
GET /api/v1/admin/monitor/llm-stats       # LLM stats
GET /api/v1/admin/monitor/crawler-stats   # Crawler stats
GET /api/v1/admin/monitor/agent-stats     # Agent stats
```

### Analytics
```
GET  /api/v1/admin/analytics/equipment/stats              # Equipment stats
GET  /api/v1/admin/analytics/equipment/trends             # Trend analysis
GET  /api/v1/admin/analytics/equipment/price-distribution # Price distribution
GET  /api/v1/admin/analytics/equipment/brand-stats        # Brand stats
GET  /api/v1/admin/analytics/users/activity               # User activity
POST /api/v1/admin/analytics/reports/generate             # Generate report
```

### System Configuration
```
GET    /api/v1/admin/config/configs          # List configs
POST   /api/v1/admin/config/configs          # Create config
PUT    /api/v1/admin/config/configs/{id}     # Update config
DELETE /api/v1/admin/config/configs/{id}     # Delete config
```

### User Management
```
GET    /api/v1/admin/users/users             # User list
GET    /api/v1/admin/users/{id}              # User detail
PUT    /api/v1/admin/users/{id}              # Update user
DELETE /api/v1/admin/users/{id}              # Delete user
GET    /api/v1/admin/users/{id}/equipment    # User equipment
```

## Environment Variables

```bash
# Required
CAIYUN_API_KEY=xxx           # Caiyun Weather API
AMAP_API_KEY=xxx             # Amap (Gaode) Maps API
DASHSCOPE_API_KEY=xxx        # Tongyi Qianwen LLM + Embedding (for vector search)
ANTHROPIC_AUTH_TOKEN=xxx     # Zhipu AI (recommended)

# JWT Authentication
JWT_SECRET_KEY=xxx           # JWT secret (required)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# WeChat Mini Program
WECHAT_APPID=xxx
WECHAT_SECRET=xxx
WECHAT_AUTO_CREATE_USER=true

# Vector Database (optional)
CHROMA_PERSIST_DIR=shared/data/chroma

# OCR Configuration
OCR_PROVIDER=ollama          # OCR provider: ollama / siliconflow
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-ocr
SILICONFLOW_API_KEY=xxx
```

## Workflow Management System

### Features
- **Visual Orchestration** - Drag-and-drop workflow designer
- **DAG Dependencies** - Complex task dependencies with parallel execution
- **Task Scheduling** - Cron-based flexible scheduling
- **Real-time Monitoring** - Live execution status tracking and log viewing
- **Version Control** - Template versioning and rollback

### Workflow API
```
POST   /api/v1/admin/crawler/workflows/templates        # Create template
GET    /api/v1/admin/crawler/workflows/templates        # List templates
PUT    /api/v1/admin/crawler/workflows/templates/{id}   # Update template
DELETE /api/v1/admin/crawler/workflows/templates/{id}   # Delete template
POST   /api/v1/admin/crawler/workflows/execute          # Execute workflow
GET    /api/v1/admin/crawler/workflows/status/{id}      # Execution status
POST   /api/v1/admin/crawler/workflows/stop/{id}        # Stop execution
POST   /api/v1/admin/crawler/schedules                  # Create schedule
GET    /api/v1/admin/crawler/schedules                  # List schedules
PUT    /api/v1/admin/crawler/schedules/{id}             # Update schedule
DELETE /api/v1/admin/crawler/schedules/{id}             # Delete schedule
```

## OCR Multi-Provider System

### Supported Providers

#### 1. Ollama (Local OCR) - Recommended
- **Model**: deepseek-ocr
- **Advantages**: Fully local processing, privacy protection, no API costs
- **Use case**: Privacy-sensitive environments with local GPU resources

#### 2. SiliconFlow (Cloud OCR)
- **Model**: deepseek-ai/DeepSeek-OCR
- **Advantages**: High accuracy, no local compute resources needed
- **Use case**: Quick testing, environments without local GPU

### Configuration
```bash
# Local Ollama (default)
OCR_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-ocr
OLLAMA_TIMEOUT=120

# SiliconFlow Cloud
OCR_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-api-key
SILICONFLOW_OCR_TIMEOUT=30
```

## Equipment Import Agent

### Features
- **Text Compression Middleware** - Auto-compress long text, remove redundant content, 50%+ compression ratio
- **Batch Equipment Extraction** - Extract multiple equipment models from a single text
- **Conversational Interaction** - Natural language dialogue with automatic tool invocation
- **Direct API Calls** - `extract_and_save` and `batch_extract_and_save` APIs
- **Smart Recognition** - LLM-based equipment info extraction across equipment types
- **Source Tracking** - Record info source (e-commerce/official website/forum) with URL association

### Usage
```python
from packages.agents.equipment_import import EquipmentImportAgent

agent = EquipmentImportAgent(
    model_provider="zhipu",
    enable_compression=True,
    compression_min_length=2000
)

# Conversational interaction
response = agent.run("Extract equipment info from this text: Guangwei Chiren GT602L-M Lure Rod...")

# Batch extract and save
results = agent.batch_extract_and_save(
    text="Long text containing multiple equipment models...",
    source_type="ecommerce",
    source_url="https://example.com"
)
```

## Smart Image Merging System

Automatically detects text below images and intelligently merges related images in batch.

### Features
- **Smart Text Detection** - Dual detection via image features and filename rules
- **Batch Processing** - Parallel processing with intelligent grouping
- **Quality Output** - JPEG/PNG support with configurable quality and dimensions
- **Metadata Management** - Auto-generates merge metadata with processing stats
- **Multi-OCR Support** - Configurable local or cloud OCR service

### Detection Strategy
1. **Text Detection** - Analyze bottom 20% of image for text content
2. **Filename Rules** - Match odd-numbered files and auto-merge with the next
3. **Confidence Scoring** - Calculate detection confidence based on dark pixel ratio and standard deviation
4. **Smart Decision** - Combine multiple factors to decide whether to merge adjacent images

### Usage
```python
from packages.data_processing.image import BatchMergeProcessor

processor = BatchMergeProcessor(
    source_dir="./images",
    output_dir="./merged",
    quality=95,
    bottom_detection_ratio=0.2,
    ocr_confidence_threshold=0.5,
    parallel_detection=True,
    max_workers=4
)

result = processor.process()
```

## Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Detailed installation guide
- [API Reference](docs/API.md) - Complete REST API docs
- [Image Processing](docs/IMAGE_PROCESSING.md) - Smart image merging
- [User Guide](docs/USER_GUIDE.md) - Usage instructions and examples
- [Architecture](docs/ARCHITECTURE.md) - System architecture
- [Changelog](CHANGELOG.md) - Version history
- [Development Guide](docs/DEVELOPMENT.md) - Dev environment setup
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues
- [React Frontend Guide](docs/REACT_FRONTEND_GUIDE.md) - Frontend development
- [Crawler Guide](docs/CRAWLER_GUIDE.md) - Web scraping system
- [Testing](docs/TESTING.md) - Testing framework

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

---

> Smart analysis, precision fishing!
>
> Current version: v5.1.0
