# 快速测试指南 v3.0.1

本文档提供智能钓鱼助手v3.0.1的快速测试命令，用于验证系统各组件功能正常。

## 🚀 快速验证命令

### 1. 环境检查
```bash
# 检查Python环境和依赖
uv run python --version
uv run python -c "import langchain; print(f'LangChain {langchain.__version__}')"

# 检查环境变量配置
uv run python -c "
import os
required_vars = ['ANTHROPIC_AUTH_TOKEN', 'CAIYUN_API_KEY', 'AMAP_API_KEY']
for var in required_vars:
    value = os.getenv(var)
    status = '✅' if value else '❌'
    print(f'{status} {var}: {\"已配置\" if value else \"未配置\"}')
"
```

### 2. 核心工具测试
```bash
# 测试工具加载
uv run python -c "
from src.tools import get_all_tools
tools = get_all_tools()
print(f'✅ 工具总数: {len(tools)}')
for tool in tools:
    print(f'  - {tool.name}')
"

# 测试基础工具
uv run python -c "
from src.tools.basic_tools import get_current_time
result = get_current_time.invoke({})
print(f'✅ 时间工具: {result[:50]}...')
"

# 测试7因子评分系统
uv run python -c "
from src.tools.scoring.enhanced_scorer import calculate_seasonal_score, analyze_pressure_trend
from datetime import datetime

# 季节评分测试
spring_score = calculate_seasonal_score(datetime(2024, 4, 15, 7, 0), 7)
print(f'✅ 春季早晨评分: {spring_score}')

# 气压趋势测试
pressure_series = [1020, 1018, 1015, 1012, 1009, 1005]
trend = analyze_pressure_trend(pressure_series)
print(f'✅ 气压趋势: {trend[\"multiplier\"]}x ({trend[\"trend\"]})')
"
```

### 3. 日期处理测试
```bash
# 测试日期工具
uv run python -c "
from src.utils.date_utils import parse_date_input, format_date, get_weekday_cn

# 相对日期解析
tomorrow = parse_date_input('明天')
print(f'✅ 明天: {format_date(tomorrow)} {get_weekday_cn(tomorrow)}')

# 绝对日期解析
christmas = parse_date_input('2024-12-25')
print(f'✅ 圣诞节: {format_date(christmas)} {get_weekday_cn(christmas)}')
"
```

### 4. 时间段意图测试
```bash
# 运行时间段意图识别测试
uv run python src/tests/test_time_period_intent.py -v --tb=short
```

### 5. 7因子评分系统测试
```bash
# 运行7因子科学评分测试（27个用例）
PYTHONPATH=src uv run pytest src/tests/scoring/test_enhanced_scorer.py -v --tb=short
```

### 6. Agent创建测试
```bash
# 测试Agent创建（不需要有效API密钥）
uv run python -c "
import sys
sys.path.append('src')
from agent import create_optimized_fishing_agent

# 创建Agent
agent = create_optimized_fishing_agent(model_provider='zhipu')
print('✅ Agent创建成功')

# 检查agent信息
print(f'✅ Agent创建成功: {type(agent).__name__}')
print(f'✅ 工具数量: {len(agent.tools)}')
print(f'✅ 模型提供商: {agent.model_provider}')
"
```

### 7. 全国覆盖测试
```bash
# 测试地理坐标覆盖
uv run python -c "
from src.utils.coordinate_utils import get_coordinates

test_locations = ['北京市', '上海市', '广州市', '深圳市', '杭州市']
for location in test_locations:
    try:
        coords = get_coordinates(location)
        print(f'✅ {location}: {coords}')
    except Exception as e:
        print(f'❌ {location}: {e}')
"
```

## 📊 预期结果

### 成功标准
- ✅ **工具加载**: 应显示3个工具
- ✅ **季节评分**: 春季早晨应为100分
- ✅ **气压趋势**: 快速下降应为1.2倍（钓鱼黄金期）
- ✅ **日期解析**: 明天应正确解析为未来日期
- ✅ **时间段测试**: 19个测试用例全部通过
- ✅ **7因子测试**: 27个测试用例全部通过
- ✅ **Agent创建**: 工具数量为3，架构为LangChain 1.0+
- ✅ **地理覆盖**: 测试城市坐标获取成功

### 常见问题

#### API密钥问题
如果遇到API密钥相关错误，可以：

```bash
# 检查.env文件
cat .env | grep -E "(ANTHROPIC|CAIYUN|AMAP)"

# 测试时可以暂时跳过API调用
export SKIP_API_TESTS=true
```

#### 依赖问题
如果遇到导入错误：

```bash
# 重新安装依赖
uv sync --refresh

# 检查Python路径
export PYTHONPATH=src
```

#### 路径问题
如果遇到模块导入错误：

```bash
# 确保在项目根目录
cd /path/to/fishing_agent

# 设置Python路径
export PYTHONPATH=src:$PYTHONPATH
```

## 🔧 完整功能测试

如果需要测试完整功能（需要有效API密钥）：

```bash
# 1. 配置API密钥
cp .env.example .env
# 编辑.env文件，填入实际的API密钥

# 2. 测试完整Agent对话
uv run python main.py
# 然后输入测试问题：
# - "现在几点了？"
# - "北京今天天气怎么样？"
# - "明天杭州钓鱼怎么样？"

# 3. 测试时间段功能
uv run python -c "
from src.tools.fishing_tools import query_fishing_recommendation

# 测试白天时段推荐
try:
    result = query_fishing_recommendation.invoke({
        'location': '杭州',
        'date': '明天',
        'time_period': '白天'
    })
    print(f'✅ 白天推荐: {result[:100]}...')
except Exception as e:
    print(f'❌ 错误: {e}')
"
```

## 📈 性能测试

```bash
# 测试7因子评分性能
uv run python -c "
import time
from src.tools.scoring.enhanced_scorer import (
    calculate_seasonal_score, analyze_pressure_trend,
    analyze_temperature_trend, analyze_wind_stability
)
from datetime import datetime

start_time = time.time()
# 运行100次评分计算
for i in range(100):
    spring_score = calculate_seasonal_score(datetime(2024, 4, 15, 7, 0), 7)
    pressure_trend = analyze_pressure_trend([1020, 1018, 1015, 1012, 1009, 1005])
    temp_trend = analyze_temperature_trend([15, 17, 19, 21, 23, 25])
    wind_stability = analyze_wind_stability([5, 6, 5, 7, 6, 5])

end_time = time.time()
avg_time = (end_time - start_time) / 100
print(f'✅ 7因子评分平均耗时: {avg_time*1000:.2f}ms')
"
```

## ✅ 快速验证脚本

创建一个一键验证脚本：

```bash
# 保存为 quick_verify.sh
#!/bin/bash

echo "🚀 智能钓鱼助手v3.0.1 快速验证"
echo "================================"

# 环境检查
echo "1. 环境检查..."
uv run python --version
echo ""

# 工具测试
echo "2. 工具测试..."
uv run python -c "
from src.tools import get_all_tools
tools = get_all_tools()
print(f'✅ 工具数量: {len(tools)}')
"
echo ""

# 7因子评分测试
echo "3. 7因子评分测试..."
uv run python -c "
from src.tools.scoring.enhanced_scorer import calculate_seasonal_score
from datetime import datetime
score = calculate_seasonal_score(datetime(2024, 4, 15, 7, 0), 7)
print(f'✅ 春季早晨评分: {score}')
"
echo ""

# Agent测试
echo "4. Agent创建测试..."
uv run python -c "
import sys
sys.path.append('src')
from agent import create_optimized_fishing_agent
agent = create_optimized_fishing_agent()
print(f'✅ Agent创建成功: {type(agent).__name__}')
print(f'✅ 工具数量: {len(agent.tools)}')
"
echo ""

echo "✅ 快速验证完成！如需完整测试，请查看TESTING.md"
```

运行脚本：
```bash
chmod +x quick_verify.sh
./quick_verify.sh
```

---

**文档版本**: v3.0.1
**最后更新**: 2025-11-21
**适用版本**: 智能钓鱼助手 v3.0.1+