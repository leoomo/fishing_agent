# 钓鱼推荐服务规范

**版本**: 1.0.0
**创建时间**: 2025-11-05
**状态**: 📋 已部署

## Purpose

为钓鱼爱好者提供基于天气数据分析的最佳钓鱼时间推荐系统，包括科学的时间建议和详细的环境分析。

## Requirements

### Requirement: 基础评分系统
系统 SHALL 基于温度、天气、风力三个核心因子计算钓鱼适宜性评分。

#### Scenario: 基础评分计算
- **WHEN** 提供温度、天气状况、风速数据
- **THEN** 系统计算各因子评分并返回0-100的综合评分

### Requirement: 数据模型扩展
系统 SHALL 扩展FishingCondition数据结构以支持增强7因子评分系统。

#### Scenario: 向后兼容性
- **WHEN** 系统运行在传统评分模式
- **THEN** FishingCondition保持原有字段和结构不变

### Requirement: 评分算法接口
系统 SHALL 提供支持双模式评分的统一接口。

#### Scenario: 双模式支持
- **WHEN** 环境变量 `ENABLE_ENHANCED_FISHING_SCORING` 为false
- **THEN** 系统使用传统3因子评分算法

### Requirement: 权重配置管理
系统 SHALL 提供灵活的权重配置管理机制。

#### Scenario: 权重验证
- **WHEN** 系统初始化权重配置
- **THEN** 系统验证权重总和等于1.0，否则使用默认配置

### Requirement: 接口兼容性保障
系统 SHALL 在提供新功能的同时保持完全的向后兼容性。

#### Scenario: 接口签名保持
- **WHEN** 调用现有的find_best_fishing_time接口
- **THEN** 接口签名和返回格式保持完全不变，确保向后兼容

### Requirement: 时间段分析
系统 SHALL 分析一天中不同时间段的钓鱼适宜性。

#### Scenario: 时间段分组
- **WHEN** 分析全天24小时数据
- **THEN** 系统按早上、上午、中午、下午、傍晚等时间段分组计算平均评分

### Requirement: 推荐生成
系统 SHALL 基于评分结果生成钓鱼时间推荐。

#### Scenario: 最佳时间推荐
- **WHEN** 完成时间段分析
- **THEN** 系统返回评分最高的前3个时间段作为最佳钓鱼时间

### Requirement: 评分系统
系统 SHALL 实现钓鱼适宜性评分算法。

#### Scenario: 基础评分
- **WHEN** 提供天气条件数据
- **THEN** 系统计算0-100的综合评分

## 系统架构

### 核心组件

#### FishingAnalyzer - 钓鱼分析器
负责分析和计算钓鱼适宜性评分的核心引擎。

#### WeatherTrendAnalyzer - 天气趋势分析器
分析天气数据的趋势变化，包括温度、湿度、气压等指标。

#### FishingCondition - 钓鱼条件
单小时钓鱼条件的数据模型。

#### FishingRecommendation - 钓鱼推荐
钓鱼推荐结果的数据模型。

## 数据模型

### FishingCondition 数据结构
```python
@dataclass
class FishingCondition:
    hour: int                    # 小时 (0-23)
    temperature: float           # 温度 (°C)
    condition: str              # 天气状况
    wind_speed: float           # 风速 (km/h)
    humidity: float             # 湿度 (%)
    pressure: float             # 气压 (hPa)

    # 传统3因子评分 (0-100)
    temperature_score: float    # 温度评分
    weather_score: float        # 天气评分
    wind_score: float          # 风力评分
    overall_score: float       # 综合评分

    # 时间段名称
    period_name: str           # 时间段名称

    # 评分模式标识
    is_enhanced: bool = False  # 是否使用增强评分
```

### FishingRecommendation 数据结构
```python
@dataclass
class FishingRecommendation:
    location: str                              # 地点
    date: str                                  # 日期
    best_time_slots: List[Tuple[str, float]]   # 最佳时间段
    detailed_analysis: str                     # 详细分析
    hourly_conditions: List[FishingCondition] # 每小时条件
    summary: str                               # 总结建议
    weather_overview: Optional[str] = None     # 天气概况
    temperature_range: Optional[str] = None     # 温度范围
    weather_summaries: Optional[Dict[str, str]] = None  # 各时间段天气摘要
```

## 钓鱼评分系统

### Requirement: 评分系统
系统 SHALL 实现钓鱼适宜性评分算法。

#### Scenario: 基础评分
- **WHEN** 提供天气条件数据
- **THEN** 系统计算0-100的综合评分

### 温度评分算法
- **最佳范围**: 15-25°C
- **评分规则**: 在最佳范围内得满分，超出范围线性递减

### 天气评分算法
- **最佳天气**: 多云、阴天
- **良好天气**: 晴天、小雨
- **较差天气**: 大雨、暴雨、雷阵雨

### 风力评分算法
- **最佳范围**: 0-15 km/h
- **评分规则**: 在最佳范围内得满分，超出范围递减

### 权重分配
- 温度权重: 40%
- 天气权重: 35%
- 风力权重: 25%

## 接口规范

### 异步接口

#### `find_best_fishing_time(location: str, date: str) -> FishingRecommendation`
分析指定地点和日期的最佳钓鱼时间。

**参数**:
- location: 地点名称
- date: 日期 (YYYY-MM-DD格式，可选，默认明天)

**返回值**: 钓鱼推荐结果

**示例**:
```python
result = await find_best_fishing_time("杭州市", "2024-11-06")
```

## 错误处理

### 系统错误
- **API调用失败**: 返回包含错误信息的推荐结果
- **数据解析失败**: 使用模拟数据并记录日志
- **计算异常**: 返回默认推荐结果并记录详细错误

### 数据质量
- **数据不完整**: 使用合理的默认值
- **历史数据缺失**: 仅使用当前可用数据
- **异常数据**: 过滤并使用历史平均值替代

## 性能要求

### 响应时间
- **平均响应时间**: < 5秒
- **95%分位响应时间**: < 10秒

### 并发支持
- 支持多用户并发查询
- 资源使用限制合理

## 依赖关系

### 外部依赖
- 彩云天气API: 提供天气预报数据
- 坐标服务: 提供地理坐标转换

### 内部依赖
- 天气服务: 数据获取和缓存
- 工具系统: LangChain工具集成

## 部署要求

### 环境变量
- `CAIYUN_API_KEY`: 彩云天气API密钥
- `ANTHROPIC_API_KEY`: Anthropic API密钥 (可选)

### 运行环境
- Python 3.11+
- 网络连接 (天气API调用)

## 质量保证

### 测试要求
- 单元测试覆盖率 > 80%
- 集成测试覆盖主要场景
- 性能测试验证响应时间

### 监控指标
- API调用成功率
- 响应时间分布
- 错误率统计