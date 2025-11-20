# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "fishing-agent" v2.3.1 - an intelligent fishing assistant built with **simplified LangChain 1.0+ architecture**. The project focuses on fishing time recommendations and weather analysis, supporting multiple LLM providers (Zhipu AI, Qwen, Doubao) with real-time weather data integration.

### 🏗️ **Simplified Architecture** (v2.3.1)
**Major architectural simplification completed**: Reduced from 75+ files to 5 core files while maintaining all functionality.

- ✅ **Direct LangChain 1.0+**: Removed LangGraph wrapper layer, uses native LangChain agents
- ✅ **Synchronous-first**: Eliminates async complexity and event loop issues
- ✅ **Zero abstraction**: Direct API calls without middleware layers
- ✅ **Ethical data constraints**: Never generates fake data, graceful degradation on API failures
- ✅ **LLM Optimization**: feature/llm-optimization branch integration, enhanced reasoning capabilities
- ✅ **Enhanced Date Processing**: Unified date parsing with date_utils module
- ✅ **Time Period Intent Recognition**: Few-Shot enhanced intent understanding for time periods

## Current Architecture (v2.3.1)

### 🎯 Core Files (5-file architecture)
- **`src/agent.py`** - Main LangChain 1.0+ intelligent agent entry point (backward compatibility)
- **`src/tools/__init__.py`** - Unified tool interface and exports
- **`src/tools/basic_tools.py`** - Basic utility tools (time, math, coordinates)
- **`src/tools/weather_tools.py`** - Weather query and forecast tools
- **`src/tools/fishing_tools.py`** - Fishing recommendation and scoring tools (with time period support)

### 🔧 Supporting Infrastructure
- **`src/utils/`** - Utility classes (API client, coordinate utils, cache, date_utils)
  - **`date_utils.py`** - 🆕 Enhanced date parsing and formatting utilities
- **`src/fishing_agent/`** - Core agent implementation with LLM optimization
  - **`prompts.py`** - Enhanced system prompts with Few-Shot examples
- **`src/config/`** - Configuration management
- **`main.py`** - Interactive CLI entry point
- **`src/tests/`** - Comprehensive test suite (including time period intent tests)

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the interactive application
uv run python main.py
# OR
python main.py

# Run the agent directly (simplified - no PYTHONPATH needed)
uv run python src/agent.py
# OR from src directory:
cd src && uv run python agent.py
```

### Testing
```bash
# Run all tests
uv run pytest src/tests/

# Run specific test modules
uv run python src/tests/test_enhanced_fishing_scorer.py
uv run python src/tests/integration/verify_national_integration.py

# Test time period intent recognition (v2.3.0+)
uv run python src/tests/test_time_period_intent.py -v

# Test weather API
uv run python src/tests/weather/test_real_weather_api.py

# Test national coverage
uv run python src/tests/test_national_coverage.py

# Test date utilities (v2.3.1+)
uv run python -c "
from src.utils.date_utils import parse_date_input, format_date, get_weekday_cn
print('Date utils test:')
print(f'Tomorrow: {format_date(parse_date_input(\"明天\"))} {get_weekday_cn(parse_date_input(\"明天\"))}')
print(f'Christmas: {format_date(parse_date_input(\"2024-12-25\"))} {get_weekday_cn(parse_date_input(\"2024-12-25\"))}')
"
```

### Tool Development
```bash
# Test tools directly
uv run python -c "
from src.tools import get_all_tools
tools = get_all_tools()
print(f'Available tools: {len(tools)}')
for tool in tools:
    print(f'- {tool.name}: {tool.description}')
"

# Test weather tools
uv run python -c "
from src.tools.weather_tools import get_current_weather
result = get_current_weather.invoke({'place': '北京'})
print(result)
"

# Test fishing recommendations
uv run python -c "
from src.tools.fishing_tools import query_fishing_recommendation
result = query_fishing_recommendation.invoke({'location': '杭州', 'date': '明天'})
print(result)
"

# Test time period functionality (v2.3.0+)
uv run python -c "
from src.tools.fishing_tools import query_fishing_recommendation
result = query_fishing_recommendation.invoke({
    'location': '北京',
    'date': '明天',
    'time_period': '白天'
})
print('Daytime fishing recommendation:')
print(result)
"
```

## Key Dependencies & Tech Stack

### Core Framework (v2.3.1)
- **langchain>=0.3.0** - Modern LangChain 1.0+ API (direct usage, no LangGraph)
- **langchain-openai>=1.0.1** - OpenAI GPT integration (also used for Zhipu AI)
- **langchain-community>=0.3.0** - Community tools and integrations
- **langchain-anthropic>=0.3.0** - Anthropic Claude integration

### Data & APIs
- **requests>=2.25.0** - Primary HTTP client (synchronous)
- **httpx>=0.24.0** - Alternative HTTP client
- **pydantic>=2.0.0** - Data validation and settings
- **python-dotenv>=1.1.1** - Environment variable management
- **pandas>=2.3.3** - Data analysis and weather processing

### LLM Providers
- **智谱AI GLM** - Default LLM provider (ANTHROPIC_AUTH_TOKEN)
- **通义千问** - Alibaba Qwen (DASHSCOPE_API_KEY)
- **豆包** - Bytedance Doubao (optional)

### External Services
- **彩云天气 API** - Real-time weather data (CAIYUN_API_KEY required)
- **高德地图 API** - Geographic coordinate service (AMAP_API_KEY required)

## Current Project Structure (v2.3.1)

```
fishing-agent/
├── src/                          # 源代码目录
│   ├── agent.py                  # 🤖 Main LangChain 1.0+ agent (backward compatibility)
│   ├── fishing_agent/            # 🧠 Core agent implementation
│   │   ├── __init__.py          # Agent exports and factory functions
│   │   ├── core.py              # Core agent class with LLM optimization
│   │   ├── model_factory.py     # Multi-model factory
│   │   ├── prompts.py           # Enhanced system prompts with Few-Shot
│   │   └── callbacks.py         # Callback handling
│   ├── tools/                    # 🛠️ Simplified tool modules
│   │   ├── __init__.py          # Tool exports and interfaces
│   │   ├── basic_tools.py       # Basic utilities (time, math, coords)
│   │   ├── weather_tools.py     # Weather and forecast tools
│   │   └── fishing_tools.py     # Fishing recommendations and scoring (time period support)
│   ├── utils/                    # 🔧 Utility classes
│   │   ├── api_client.py        # Unified API client
│   │   ├── coordinate_utils.py  # Coordinate and location utilities
│   │   ├── cache.py             # Simple caching system
│   │   └── date_utils.py        # 🆕 Enhanced date parsing and formatting
│   ├── config/                   # ⚙️ Configuration management
│   └── tests/                    # 🧪 Comprehensive test suite
│       └── test_time_period_intent.py  # 🆕 Time period intent tests
├── main.py                       # 🚀 Interactive CLI entry point
├── pyproject.toml                # 📦 Project configuration (v2.3.1)
├── .env.example                  # 🔑 Environment variable template
├── CLAUDE.md                     # 📖 This development guide
├── README.md                     # 📋 Project documentation
└── CHANGELOG.md                  # 📋 Version history
```

### Critical Files for Development (v2.3.1)
- **`src/agent.py`** - Backward compatibility shim for agent functionality
- **`src/fishing_agent/`** - Core agent implementation with LLM optimization
  - **`core.py`** - Main OptimizedFishingAgent class using LangChain 1.0+ create_agent
  - **`prompts.py`** - Enhanced system prompts with Few-Shot examples for time period intent
- **`src/tools/__init__.py`** - Unified tool interface and backward compatibility
- **`src/tools/weather_tools.py`** - Weather tools with direct API calls
- **`src/tools/fishing_tools.py`** - 7-factor fishing scoring algorithm with time period support
- **`src/utils/date_utils.py`** - 🆕 Enhanced date parsing and formatting utilities
- **`src/utils/api_client.py`** - Unified HTTP client for weather and coordinate APIs
- **`src/tests/test_time_period_intent.py`** - 🆕 Time period intent recognition tests
- **`main.py`** - Interactive command-line interface

## Core Features (v2.3.1)

### 🎣 Fishing Recommendation System
- **7-Factor Algorithm**: Temperature, weather, wind, pressure, humidity, season, moon phase
- **Time Period Intent Recognition**: Few-Shot enhanced understanding of time-limited queries (95%+ accuracy)
- **Enhanced Date Processing**: Unified parsing for relative ("明天") and absolute ("2024-12-25") dates
- **Ethical Data Constraints**: Never generates fake weather data, graceful API failure handling
- **Intelligent Time Recommendations**: Solves the "86-score problem" with professional fishing research
- **National Coverage**: Supports 3,142+ administrative regions (95%+ coverage)
- **Natural Language Processing**: Chinese query support with direct tool integration
- **LLM Optimization**: Enhanced reasoning capabilities from feature/llm-optimization branch

### 🌤️ Weather Service (Simplified)
- **Direct API Calls**: No middleware layers, direct Caiyun Weather API integration
- **Enhanced Date Queries**: Unified date parsing with date_utils module for relative/absolute dates
- **72-hour Forecasts**: Extended hourly weather predictions
- **Smart Fallback**: Honest error reporting when API unavailable (no fake data)
- **Zero Configuration**: Works out of the box with proper API keys

### 🗺️ Coordinate Service (Unified)
- **Direct Amap API Integration**: Precise geographic coordinate queries
- **Simplified Caching**: Effective caching with 90%+ hit rate
- **Intelligent Matching**: Supports aliases and fuzzy matching
- **National Coverage**: 95%+ coverage of Chinese administrative regions
- **Utility-based Design**: Simple coordinate utilities without service abstractions

## Development Guidelines (v2.3.1)

### Architecture Principles
1. **Synchronous-first**: Use direct API calls with `requests`, avoid async complexity
2. **Zero Abstraction**: Direct tool implementations without middleware layers
3. **Ethical Data**: Never generate fake data, provide honest error messages
4. **LangChain 1.0+ Native**: Use `@tool` decorator and `create_agent` directly
5. **Simple Configuration**: Environment variables with `.env.example` template
6. **LLM Optimization**: Utilize enhanced prompts and Few-Shot examples for better reasoning
7. **Unified Date Handling**: Use date_utils module for consistent date parsing across the codebase

### Common Import Patterns (v2.3.1)
```python
# Agent creation (LLM optimized)
from src.agent import create_optimized_fishing_agent

# Tool access - simplified unified interface
from src.tools import get_all_tools, get_weather_tools, get_fishing_tools

# Direct tool usage
from src.tools.weather_tools import get_current_weather, get_weather_forecast
from src.tools.fishing_tools import query_fishing_recommendation
from src.tools.basic_tools import get_current_time, calculate

# Utility classes
from src.utils.api_client import WeatherAPIClient, CoordinateAPIClient
from src.utils.coordinate_utils import get_coordinates
from src.utils.date_utils import parse_date_input, format_date, get_weekday_cn

# Date handling examples
tomorrow = parse_date_input("明天")
formatted_date = format_date(tomorrow)
weekday = get_weekday_cn(tomorrow)
```

### Adding New Tools (v2.3.1)
```python
from langchain.tools import tool
from src.utils.date_utils import parse_date_input  # Use unified date parsing

@tool
def my_new_tool(param: str, date: str = None) -> str:
    """
    Tool description that will be shown to the LLM

    Args:
        param: Description of parameter
        date: Date string (supports relative dates like "明天" or absolute like "2024-12-25")

    Returns:
        Description of return value
    """
    try:
        # Use unified date parsing if date parameter provided
        if date:
            parsed_date = parse_date_input(date)
            formatted_date = format_date(parsed_date)

        # Direct API call or processing
        result = do_something(param)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# Export in tools/__init__.py
MY_TOOLS = [my_new_tool]
```

### Date Utilities Usage (v2.3.1)
```python
from src.utils.date_utils import parse_date_input, parse_dates_list, format_date, get_weekday_cn

# Parse single date
tomorrow = parse_date_input("明天")
christmas = parse_date_input("2024-12-25")
today = parse_date_input()  # Defaults to tomorrow if no input

# Parse date list
dates = parse_dates_list(["今天", "明天", "后天"])
week_dates = parse_dates_list(["2024-12-25", "2024-12-26", "2024-12-27"])

# Format dates
formatted = format_date(tomorrow, '%Y年%m月%d日')  # Custom format
weekday = get_weekday_cn(tomorrow)  # Chinese weekday
```

### Required Environment Variables
Create `.env` from `.env.example`:

```bash
# Required APIs
CAIYUN_API_KEY=your-caiyun-api-key      # Weather API (required)
AMAP_API_KEY=your-amap-api-key          # Coordinate API (required)

# LLM Providers (at least one recommended)
ANTHROPIC_AUTH_TOKEN=your-zhipu-token   # Zhipu AI GLM (recommended)
DASHSCOPE_API_KEY=your-qwen-key         # Alibaba Qwen
OPENAI_API_KEY=your-openai-key          # OpenAI GPT
ANTHROPIC_API_KEY=your-claude-key       # Anthropic Claude
```

### Testing Guidelines (v2.3.1)
- Write tests for new tools in `src/tests/`
- Test both success and error scenarios
- Verify API integration with real keys
- Use mock APIs for unit tests when possible
- Test national coverage for location-based features
- Test time period intent recognition for time-limited queries
- Test date parsing utilities with various input formats
- Include LLM optimization scenarios in test cases

## Python Environment
- **Requires Python >=3.11**
- **Uses `uv` for dependency management** (as specified in user instructions)
- **Synchronous-first architecture** for stability
- **LangChain 1.0+ native** for tool and agent development
- **Zero-config deployment** with proper environment variables