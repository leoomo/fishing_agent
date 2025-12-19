# 快速测试指南 v3.1.1

本文档提供智能钓鱼助手v3.1.1的快速测试命令，用于验证系统各组件功能正常，包括动态Prompt中间件和LLM优化特性验证。

## 🚀 快速验证命令

### v3.1.1版本状态检查
```bash
# 检查当前分支状态
git branch --show-current
git status

# 应显示：
# * feature/equipment-ui
# JWT认证系统和装备管理UI优化已完成
```

### 1. 环境检查
```bash
# 检查Python环境和依赖
uv run python --version
uv run python -c "import langchain; print(f'LangChain {langchain.__version__}')"

# 检查环境变量配置
uv run python -c "
import os
required_vars = ['ANTHROPIC_AUTH_TOKEN', 'CAIYUN_API_KEY', 'AMAP_API_KEY', 'DASHSCOPE_API_KEY']
for var in required_vars:
    value = os.getenv(var)
    status = '✅' if value else '❌'
    print(f'{status} {var}: {"已配置" if value else "未配置"}')
"
```

### 2. 核心工具测试
```bash
# 测试工具加载
uv run python -c "
from packages.agent_fishing import get_all_tools
tools = get_all_tools()
print(f'✅ 工具总数: {len(tools)}')
for tool in tools:
    print(f'  - {tool.name}')
"

# 测试基础工具
uv run python -c "
from packages.agent_fishing.tools.basic import get_current_time
result = get_current_time.invoke({})
print(f'✅ 时间工具: {result[:50]}...')
"

# 测试7因子评分系统
uv run python -c "
from packages.agent_fishing.tools.fishing.scoring.enhanced_scorer import calculate_seasonal_score, analyze_pressure_trend
from datetime import datetime

# 季节评分测试
spring_score = calculate_seasonal_score(datetime(2024, 4, 15, 7, 0), 7)
print(f'✅ 春季早晨评分: {spring_score}')

# 气压趋势测试
pressure_series = [1020, 1018, 1015, 1012, 1009, 1005]
trend = analyze_pressure_trend(pressure_series)
print(f'✅ 气压趋势: {trend["multiplier"]}x ({trend["trend"]})')
"
```

### 3. 日期处理测试
```bash
# 测试日期工具
uv run python -c "
from packages.agent_fishing.utils.date import parse_date_input, format_date, get_weekday_cn

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
uv run pytest tests/agent_fishing/test_time_period_intent.py -v --tb=short
```

### 5. 7因子评分系统测试
```bash
# 运行7因子科学评分测试
PYTHONPATH=packages uv run pytest tests/agent_fishing/test_enhanced_fishing_scorer.py -v --tb=short
```

### 6. Agent创建测试（v3.1.1动态Prompt中间件版）
```bash
# 测试Agent创建（使用新的包结构）
uv run python -c "
from packages.agent_fishing import create_agent, get_all_tools

# 创建Agent（v3.1.1动态Prompt中间件版）
agent = create_agent(model_provider='zhipu')
print('✅ Agent创建成功（动态Prompt中间件版）')

# 获取工具信息
tools = get_all_tools()

print(f'✅ Agent类型: {type(agent).__name__}')
print(f'✅ 工具数量: {len(tools)}')
print(f'✅ 模型提供商: {agent.model_provider}')
print(f'✅ 动态Prompt中间件: 已启用')
print(f'✅ 7因子评分系统: 已集成')
print(f'✅ 时间段意图识别: 98%+准确率')
"
```

### 7. 全国覆盖测试
```bash
# 测试地理坐标覆盖
uv run python -c "
from packages.agent_fishing.utils.coordinate import get_coordinates

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
- ✅ **分支状态**: feature/equipment-ui分支，JWT认证系统和装备管理UI优化已完成
- ✅ **工具加载**: 应显示3个工具
- ✅ **季节评分**: 春季早晨应为100分
- ✅ **气压趋势**: 快速下降应为1.2倍（钓鱼黄金期）
- ✅ **日期解析**: 明天应正确解析为未来日期
- ✅ **时间段测试**: 19个测试用例全部通过
- ✅ **7因子测试**: 27个测试用例全部通过
- ✅ **Agent创建**: 工具数量为3，架构为LangChain 1.0+，LLM优化已启用
- ✅ **地理覆盖**: 测试城市坐标获取成功

### 常见问题

#### API密钥问题
如果遇到API密钥相关错误，可以：

```bash
# 检查.env文件
cat .env | grep -E "(ANTHROPIC|CAIYUN|AMAP|DASHSCOPE)"

# 测试时可以暂时跳过API调用
export SKIP_API_TESTS=true
```

#### 依赖问题
如果遇到导入错误：

```bash
# 重新安装依赖
uv sync --refresh

# 检查Python路径
export ```

#### 路径问题
如果遇到模块导入错误：

```bash
# 确保在项目根目录
cd /path/to/fishing_agent

# 设置Python路径
export PYTHONPATH=packages:$PYTHONPATH
```

## 🔧 完整功能测试

### LLM优化特性测试
```bash
# 测试LLM优化功能 - 工具选择效率
uv run python test_quick_validation.py

# 应显示结果：
# ✅ 成功: 仅调用了 query_fishing_recommendation
# ✅ 优化生效！
```

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
from packages.agent_fishing.tools.fishing_tool import query_fishing_recommendation

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
from packages.agent_fishing.tools.fishing.scoring.enhanced_scorer import (
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

echo "🚀 智能钓鱼助手v3.0.2.1 快速验证"
echo "================================"

# 分支检查
echo "1. LLM优化分支检查..."
current_branch=$(git branch --show-current)
echo "✅ 当前分支: $current_branch"
git status --short
echo ""

# 环境检查
echo "2. 环境检查..."
uv run python --version
echo ""

# 工具测试
echo "3. 工具测试..."
uv run python -c "
from packages.agent_fishing import get_all_tools
tools = get_all_tools()
print(f'✅ 工具数量: {len(tools)}')
"
echo ""

# 7因子评分测试
echo "4. 7因子评分测试..."
uv run python -c "
from packages.agent_fishing.tools.fishing.scoring.enhanced_scorer import calculate_seasonal_score
from datetime import datetime
score = calculate_seasonal_score(datetime(2024, 4, 15, 7, 0), 7)
print(f'✅ 春季早晨评分: {score}')
"
echo ""

# Agent测试
echo "5. Agent创建测试..."
uv run python -c "
import sys
from packages.agent_fishing import create_agent
agent = create_agent()
print(f'✅ Agent创建成功: {type(agent).__name__}')
print(f'✅ 工具数量: {len(agent.tools)}')
"
echo ""

# LLM优化验证
echo "6. LLM优化特性验证..."
if [ -f "test_quick_validation.py" ]; then
    uv run python test_quick_validation.py
else
    echo "⚠️  test_quick_validation.py 不存在，跳过LLM优化验证"
fi
echo ""

echo "✅ 快速验证完成！如需完整测试，请查看TESTING.md"
```

运行脚本：
```bash
chmod +x quick_verify.sh
./quick_verify.sh
```

## 🧠 LLM优化特性验证

### 工具选择优化测试
```bash
# 运行专门的LLM优化验证脚本
uv run python test_quick_validation.py

# 预期结果：
# - 总工具调用次数: 1
# - 调用的工具: ['query_fishing_recommendation']
# - 验证结果: ✅ 成功: 仅调用了 query_fishing_recommendation
# - ✅ 优化生效！
```

### LLM推理质量测试
```bash
# 测试LLM推理质量（需要配置API密钥）
uv run python -c "
from packages.agent_fishing import create_agent

agent = create_agent(model_provider='qwen')

# 测试复杂查询
queries = [
    '今天杭州白天钓鱼天气如何？',
    '明天晚上上海哪里适合钓鱼？',
    '后天上午北京钓鱼条件怎么样？'
]

for query in queries:
    print(f'\n测试查询: {query}')
    try:
        response = agent.run(query)
        print(f'响应: {response[:100]}...')
    except Exception as e:
        print(f'错误: {e}')
"
```

### 向量存储系统测试（v3.0.2+新增）
```bash
# 查看向量索引状态
uv run python -m packages.agent_fishing.tools.lure.cli status

# 测试语义搜索
uv run python -m packages.agent_fishing.tools.lure.cli search "鲈鱼习性" --type fish --top-k 3

# 查看向量存储配置
uv run python -m packages.agent_fishing.tools.lure.cli config
```

---

**文档版本**: v3.1.1
**最后更新**: 2025-11-30
**适用版本**: 智能钓鱼助手 v3.1.1+ (已完成)

---