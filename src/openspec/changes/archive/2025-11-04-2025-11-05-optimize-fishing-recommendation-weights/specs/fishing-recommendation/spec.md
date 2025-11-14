# 钓鱼推荐服务规格变更

**变更提案**: optimize-fishing-recommendation-weights
**变更类型**: 功能增强
**变更日期**: 2025-11-05

## ADDED Requirements

### Requirement: 增强7因子评分系统
系统 SHALL 扩展评分算法，从传统的3因子（温度、天气、风力）增加到7因子评分系统，包含气压、湿度、季节性、月相等专业因子。

#### Scenario: 增强评分计算
- **WHEN** 系统启用增强评分模式且提供完整的天气数据
- **THEN** 系统计算温度、天气、风力、气压、湿度、季节性、月相七个因子的综合评分

### Requirement: EnhancedFishingScorer 增强评分器
系统 SHALL 提供 EnhancedFishingScorer 类，实现精细化的7因子评分算法。

#### Scenario: 增强评分器初始化
- **WHEN** 创建增强评分器实例
- **THEN** 系统初始化天气趋势分析器、天文计算器、季节分析器和气压趋势分析器

### Requirement: 气压趋势评分
系统 SHALL 实现气压趋势分析算法，识别气压变化模式并对钓鱼适宜性进行评分。

#### Scenario: 气压下降评分奖励
- **WHEN** 检测到气压快速下降趋势 (>2hPa/6小时)
- **THEN** 系统额外奖励评分至115分，反映钓鱼黄金期

#### Scenario: 气压稳定评分
- **WHEN** 气压在最佳范围(1005-1029 hPa)内保持稳定
- **THEN** 系统给予满分100分的气压评分

### Requirement: 湿度评分算法
系统 SHALL 基于湿度数据计算钓鱼适宜性评分，高湿度通常伴随低气压系统。

#### Scenario: 高湿度奖励评分
- **WHEN** 湿度在80-90%范围内且气压呈下降趋势
- **THEN** 系统额外奖励5分，识别有利钓鱼条件

#### Scenario: 理想湿度评分
- **WHEN** 湿度在60-80%的理想范围内
- **THEN** 系统给予满分100分的湿度评分

### Requirement: 季节性评分算法
系统 SHALL 基于季节和时间段计算钓鱼适宜性评分，反映鱼类在不同季节的活跃规律。

#### Scenario: 春季早晚最佳评分
- **WHEN** 春季(3-5月)的早上(6-9点)或傍晚(17-19点)
- **THEN** 系统给予满分100分的季节性评分

#### Scenario: 夏季避开高温评分
- **WHEN** 夏季(6-8月)的中午(11-15点)
- **THEN** 系统给予60分的较低评分，避开高温时段

### Requirement: 月相评分算法
系统 SHALL 基于天文计算的月相信息评估对钓鱼的影响。

#### Scenario: 满月夜间评分
- **WHEN** 日期为满月且时间段为夜间
- **THEN** 系统给予90分的较高评分，利用鱼类夜间活跃特性

#### Scenario: 新月温和评分
- **WHEN** 日期为新月期
- **THEN** 系统给予85分的良好评分，反映温和天气条件

### Requirement: 天气趋势分析
系统 SHALL 分析历史天气数据的趋势变化，为评分提供额外的科学依据。

#### Scenario: 温度变化趋势分析
- **WHEN** 检测到温度快速上升趋势 (>3°C/6小时)
- **THEN** 系统应用1.10倍评分乘数，反映鱼类活跃度提升

#### Scenario: 风速稳定性分析
- **WHEN** 风速标准差 < 1km/h (非常稳定)
- **THEN** 系统应用1.05倍评分乘数，奖励稳定条件

### Requirement: 增强数据结构
系统 SHALL 扩展数据模型以支持7因子评分系统。

#### Scenario: FishingScore 增强评分结果
- **WHEN** 系统完成7因子评分计算
- **THEN** 系统返回包含各因子详细评分和分析信息的FishingScore对象

#### Scenario: FishingCondition 增强条件
- **WHEN** 系统完成单小时条件分析
- **THEN** FishingCondition对象包含增强评分结果和评分模式标识

### Requirement: 精细化权重分配
系统 SHALL 重新分配评分权重，从3因子的粗放分配调整为7因子的精细化分配。

#### Scenario: 7因子权重应用
- **WHEN** 系统计算综合评分
- **THEN** 系统应用以下权重：
  - 温度: 26.3%
  - 天气: 21.1%
  - 风力: 15.8%
  - 气压: 15.8%
  - 湿度: 10.5%
  - 季节性: 5.3%
  - 月相: 5.3%

## MODIFIED Requirements

### Requirement: 数据模型扩展
系统 SHALL 扩展FishingCondition数据结构以支持增强7因子评分系统。

**原内容**: FishingCondition包含传统的3因子评分字段：温度评分、天气评分、风力评分和综合评分。

**修改内容**: 扩展FishingCondition数据结构，增加enhanced_score字段支持FishingScore对象，包含所有7个因子的详细评分，并添加is_enhanced标识符指示使用的评分模式。

#### Scenario: 向后兼容性
- **WHEN** 系统运行在传统评分模式
- **THEN** FishingCondition保持原有字段和结构不变

#### Scenario: 增强评分支持
- **WHEN** 系统运行在增强评分模式
- **THEN** FishingCondition包含enhanced_score字段和is_enhanced标识

### Requirement: 评分算法接口
系统 SHALL 提供支持双模式评分的统一接口。

**原内容**: 系统提供基于温度、天气、风力三个核心因子的评分接口，使用固定的40%、35%、25%权重分配。

**修改内容**: 扩展评分接口支持3因子和7因子两种评分模式。通过环境变量`ENABLE_ENHANCED_FISHING_SCORING`控制模式选择，在增强模式下使用26.3%、21.1%、15.8%、15.8%、10.5%、5.3%、5.3%的精细权重分配，传统模式下保持原有3因子权重。

#### Scenario: 双模式支持
- **WHEN** 环境变量 `ENABLE_ENHANCED_FISHING_SCORING` 为false
- **THEN** 系统使用传统3因子评分算法

#### Scenario: 增强模式启用
- **WHEN** 环境变量 `ENABLE_ENHANCED_FISHING_SCORING` 为true且有足够的历史数据
- **THEN** 系统自动切换到7因子增强评分算法

### Requirement: 权重配置管理
系统 SHALL 提供灵活的权重配置管理机制。

**原内容**: 系统使用硬编码的3因子权重分配：温度40%、天气35%、风力25%。

**修改内容**: 系统支持通过SCORING_CONFIG字典管理可配置的7因子权重分配。支持运行时动态调整权重系数，并提供配置验证机制确保权重总和为1.0。增强模式下的默认权重为：温度26.3%、天气21.1%、风力15.8%、气压15.8%、湿度10.5%、季节性5.3%、月相5.3%。

#### Scenario: 动态权重调整
- **WHEN** 系统启动或配置更新
- **THEN** 系统加载最新权重配置到EnhancedFishingScorer实例

#### Scenario: 权重验证
- **WHEN** 系统初始化权重配置
- **THEN** 系统验证权重总和等于1.0，否则使用默认配置

### Requirement: 接口兼容性保障
系统 SHALL 在提供新功能的同时保持完全的向后兼容性。

**原内容**: 系统提供基于3因子评分的基础异步接口`find_best_fishing_time()`，返回包含综合评分和时间推荐的FishingRecommendation对象。

**修改内容**: 系统保持所有现有接口签名完全不变，包括参数类型、返回类型和异常处理行为。内部实现根据环境变量自动选择3因子或7因子评分模式，确保现有客户端代码无需任何修改即可继续使用。新功能通过扩展数据结构实现，不影响接口契约。

#### Scenario: 接口签名保持
- **WHEN** 调用现有的find_best_fishing_time接口
- **THEN** 接口签名和返回格式保持完全不变，确保向后兼容

## RENAMED Requirements

### Requirement: 评分系统
**原名称**: 评分系统

**重命名为**: 钓鱼评分系统

### Reason
为了更准确地反映系统的核心功能，从泛化的"评分系统"重命名为更具体的"钓鱼评分系统"。