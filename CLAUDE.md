# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "fishing-agent" - an intelligent fishing assistant built with LangChain 1.0+ and LangGraph. The project focuses on fishing time recommendations and weather analysis, supporting multiple LLM providers (Zhipu AI, OpenAI, Anthropic) with real-time weather data integration.

## Core Architecture

### 🏗️ Central Service Management
- **Service Manager**: `src/services/service_manager.py` - Singleton pattern for unified service instance management
- **Interface Abstraction**: `src/interfaces/` - Loose coupling design with dependency injection support
- **Configuration Management**: `src/config/service_config.py` - Centralized configuration system

### 🎯 Key Modules
- **Agent**: `src/agent.py` - Modern LangChain 1.0+ intelligent agent with refactored architecture
- **Tools**: `src/tools/` - Modular tool system with independent tool modules
  - `basic_tools.py` - Independent basic utility tools (time, math, search)
  - `langchain_weather_tools_sync.py` - Weather and fishing analysis tools
- **Services**: `src/services/` - Weather, coordinate, matching, and middleware services
- **Core**: `src/core/` - Base classes, interfaces, and registry systems

### 🔄 Synchronous Architecture
The project has been completely refactored to use synchronous architecture for stability:
- All `*_sync.py` files are production-ready
- Eliminates "Event loop is closed" errors
- Uses `requests` instead of `aiohttp` for API calls

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run the application
uv run python main.py
# OR
python main.py
```

### Testing
```bash
# Run all tests
uv run pytest src/tests/

# Run specific tests
uv run python src/tests/test_enhanced_fishing_scorer.py
uv run python src/tests/integration/verify_national_integration.py
```

### Service Development
```bash
# Test coordinate service
uv run python -c "from src.services.coordinate.amap_coordinate_service import AmapCoordinateService; print(AmapCoordinateService().get_coordinate('北京'))"

# Test weather service
uv run python -c "from src.services.weather.enhanced_caiyun_weather_service import EnhancedCaiyunWeatherService; print(EnhancedCaiyunWeatherService().get_weather('杭州'))"
```

## Key Dependencies & Tech Stack

### Core Framework
- **langchain>=1.0.5** - Modern LangChain 1.0+ API
- **langgraph-cli>=0.4.7** - LangGraph for agent development
- **langchain-anthropic>=1.0.0** - Anthropic Claude integration
- **langchain-openai>=1.0.1** - OpenAI GPT integration

### Data & APIs
- **requests>=2.25.0** - HTTP client (synchronous)
- **httpx>=0.24.0** - Alternative HTTP client
- **pydantic>=2.0.0** - Data validation
- **pandas>=2.3.3** - Data analysis
- **transformers>=4.21.0** - Hugging Face transformers
- **torch>=1.12.0** - PyTorch for ML

### External Services
- **彩云天气 API** - Real-time weather data (CAIYUN_API_KEY required)
- **高德地图 API** - Geographic coordinate service (AMAP_API_KEY required)
- **智谱AI GLM** - Default LLM provider (ANTHROPIC_AUTH_TOKEN)

## Project Structure & Important Files

```
src/
├── agent.py                    # 🤖 Main LangChain agent entry point
├── core/                       # 🏗️ Core architecture
├── tools/                      # 🛠️ Synchronous tools (weather, fishing)
├── services/                   # 🌐 Service layer with manager
├── interfaces/                 # 🔧 Service interfaces
├── config/                     # ⚙️ Configuration management
└── tests/                      # 🧪 Test suites
```

### Critical Files for Development
- `src/services/service_manager.py` - Central service management
- `src/tools/basic_tools.py` - Independent basic utility tools (time, math, search)
- `src/tools/langchain_weather_tools_sync.py` - Weather and fishing analysis tools
- `src/tools/fishing_analyzer_sync.py` - Fishing analysis engine
- `src/services/coordinate/amap_coordinate_service.py` - Coordinate service
- `src/services/weather/enhanced_caiyun_weather_service.py` - Weather service

## Core Features

### 🎣 Fishing Recommendation System
- **7-Factor Algorithm**: Temperature, weather, wind, pressure, humidity, season, moon phase
- **Intelligent Time Recommendations**: Solves the "86-score problem" with professional fishing research
- **National Coverage**: Supports 3,142+ administrative regions (95%+ coverage)
- **Natural Language Processing**: Chinese query support

### 🌤️ Weather Service
- **Real-time Data**: Caiyun Weather API integration
- **Date Queries**: Supports relative ("tomorrow") and absolute ("2024-12-25") dates
- **24-hour Forecasts**: Hourly weather predictions
- **Smart Fallback**: Automatic degradation to simulated data when API unavailable

### 🗺️ Coordinate Service
- **Amap API Integration**: Precise geographic coordinate queries
- **Multi-level Caching**: 90%+ hit rate, <1ms response time
- **Intelligent Matching**: Supports aliases and fuzzy matching
- **National Coverage**: 95%+ coverage of Chinese administrative regions

## Development Guidelines

### When Working with This Codebase

1. **Use Synchronous Patterns**: Always prefer `*_sync.py` files for production code
2. **Service Manager**: Access services through `ServiceManager` for proper singleton behavior
3. **Error Handling**: All services have comprehensive error handling and retry mechanisms
4. **Caching Strategy**: Leverage the multi-level caching system for performance
5. **Testing**: Write tests for new tools and services

### Common Import Patterns
```python
# Agent creation
from src.agent import create_optimized_fishing_agent

# Service access
from src.services.service_manager import ServiceManager
sm = ServiceManager()
weather_service = sm.get_weather_service()

# Tool usage - Basic tools
from src.tools.basic_tools import get_basic_tools, get_current_time, calculate

# Tool usage - Weather tools
from src.tools.langchain_weather_tools_sync import query_current_weather
```

### Environment Variables Required
- `CAIYUN_API_KEY` - Weather API (required)
- `AMAP_API_KEY` - Coordinate API (required)
- `ANTHROPIC_AUTH_TOKEN` - Zhipu AI (recommended)
- `OPENAI_API_KEY` - OpenAI (optional)
- `ANTHROPIC_API_KEY` - Anthropic (optional)

## Python Environment
- Requires Python >=3.11
- Uses `uv` for dependency management (as specified in user instructions)
- Synchronous-first architecture for stability