# WeatherApiRouter 规范说明

## 组件概述

**组件名称**: WeatherApiRouter (天气API智能路由器)  
**版本**: 1.0.0  
**类型**: 核心服务组件  
**负责人**: AI Assistant  

## 功能描述

WeatherApiRouter是一个智能路由器，根据天气预报查询的时间范围自动选择最优的天气服务API。它实现了3天内使用逐小时预报、3-7天使用逐天预报、7天以上使用模拟数据的智能路由策略，显著提升系统性能并减少不必要的API调用。

## 接口规范

### 主要接口

#### `get_forecast(location_info: dict, date_str: str) -> WeatherResult`

获取天气预报数据的主要接口，根据时间范围自动路由到对应的服务。

**参数**:
- `location_info: dict` - 地理位置信息
  - `name: str` - 地点名称
  - `lng: float` - 经度
  - `lat: float` - 纬度
  - `adcode: str` - 行政区划代码 (可选)
- `date_str: str` - 查询日期，格式为"YYYY-MM-DD"

**返回值**:
- `WeatherResult` - 统一格式的天气查询结果
  - `data_source: str` - 数据源标识
  - `hourly_data: list` - 24小时详细数据
  - `confidence: float` - 置信度 (0.0-1.0)
  - `api_url: str` - API端点标识
  - `error_code: int` - 错误码 (0表示成功)
  - `error_message: str` - 错误信息
  - `cached: bool` - 是否来自缓存

**异常**:
- `ValueError` - 参数格式错误
- `LocationNotFoundError` - 地点信息无效
- `WeatherServiceError` - 天气服务异常

#### `_determine_forecast_range(days_from_now: int) -> ForecastRange`

根据距离今天的天数确定使用哪种预报服务。

**参数**:
- `days_from_now: int` - 距离今天的天数

**返回值**:
- `ForecastRange` - 预报范围枚举
  - `HOURLY` - 0-3天，使用逐小时预报
  - `DAILY` - 3-7天，使用逐天预报
  - `SIMULATION` - 7天以上，使用模拟数据

#### `get_service_by_range(forecast_range: ForecastRange) -> WeatherService`

根据预报范围获取对应的服务实例。

**参数**:
- `forecast_range: ForecastRange` - 预报范围

**返回值**:
- `WeatherService` - 对应的天气服务实例

### 辅助接口

#### `_normalize_result(result: WeatherResult, forecast_range: ForecastRange) -> WeatherResult`

标准化不同服务返回的结果格式，确保数据格式一致性。

#### `_log_api_call(forecast_range: ForecastRange, location: str, duration: float)`

记录API调用信息，用于监控和调试。

## 实现要求

### 核心逻辑

1. **时间范围判断**:
   ```python
   def _determine_forecast_range(self, days_from_now: int) -> ForecastRange:
       if days_from_now <= 3:
           return ForecastRange.HOURLY
       elif days_from_now <= 7:
           return ForecastRange.DAILY
       else:
           return ForecastRange.SIMULATION
   ```

2. **服务选择**:
   ```python
   def _get_service_by_range(self, forecast_range: ForecastRange) -> WeatherService:
       service_map = {
           ForecastRange.HOURLY: self._hourly_service,
           ForecastRange.DAILY: self._daily_service,
           ForecastRange.SIMULATION: self._simulation_service
       }
       return service_map[forecast_range]
   ```

3. **路由流程**:
   ```python
   async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
       # 1. 计算时间范围
       days_from_now = calculate_days_from_now(date_str)
       forecast_range = self._determine_forecast_range(days_from_now)
       
       # 2. 选择服务
       service = self._get_service_by_range(forecast_range)
       
       # 3. 执行查询
       result = await service.get_forecast(location_info, date_str)
       
       # 4. 标准化结果
       return self._normalize_result(result, forecast_range)
   ```

### 性能要求

1. **响应时间**: 正常情况下API调用响应时间 < 2秒
2. **并发处理**: 支持至少50个并发请求
3. **错误恢复**: 服务异常时能在100ms内切换到备用服务
4. **内存使用**: 路由器内存占用 < 50MB

### 可靠性要求

1. **服务可用性**: 99.9%+的可用性
2. **错误处理**: 完善的异常处理和错误恢复机制
3. **数据一致性**: 确保不同服务返回数据格式一致
4. **监控支持**: 提供完整的监控指标和日志

## 配置规范

### 必需配置项

```python
# 服务配置
WEATHER_ROUTER_CONFIG = {
    'enable_hourly_service': True,      # 是否启用逐小时服务
    'enable_daily_service': True,       # 是否启用逐天服务
    'enable_simulation_service': True,  # 是否启用模拟服务
    'default_timeout': 10.0,            # 默认超时时间(秒)
    'retry_attempts': 3,                # 重试次数
    'fallback_enabled': True            # 是否启用回退机制
}
```

### 可选配置项

```python
# 性能优化配置
PERFORMANCE_CONFIG = {
    'max_concurrent_requests': 100,     # 最大并发请求数
    'connection_pool_size': 20,         # 连接池大小
    'request_timeout': 5.0,             # 请求超时时间
    'circuit_breaker_threshold': 10,    # 熔断器阈值
    'cache_enabled': True               # 是否启用缓存
}

# 监控配置
MONITORING_CONFIG = {
    'metrics_enabled': True,            # 是否启用指标收集
    'logging_level': 'INFO',            # 日志级别
    'health_check_interval': 60,        # 健康检查间隔(秒)
    'alert_threshold': 0.95             # 告警阈值
}
```

## 依赖关系

### 外部依赖

1. **datetime_utils** - 时间计算工具
   - `calculate_days_from_now(date_str: str) -> int`
   
2. **weather_services** - 各种天气服务
   - `HourlyWeatherService`
   - `DailyWeatherService`
   - `SimulationService`

3. **logging** - 日志系统
   - 结构化日志记录

### 内部依赖

1. **缓存系统** - 用于性能优化
2. **监控系统** - 用于性能监控
3. **配置系统** - 用于参数管理

## 测试规范

### 单元测试要求

1. **时间范围判断测试**:
   - 边界值测试 (0, 3, 7, 8天)
   - 负数和异常值测试
   - 性能测试 (1000次调用 < 100ms)

2. **服务选择测试**:
   - 所有服务类型的选择正确性
   - 服务不可用时的处理
   - 动态服务切换测试

3. **路由逻辑测试**:
   - 完整路由流程测试
   - 异常情况处理测试
   - 并发路由测试

### 集成测试要求

1. **端到端测试**:
   - 不同时间范围的查询正确性
   - 不同地点的查询正确性
   - 数据格式一致性验证

2. **性能测试**:
   - 响应时间测试
   - 并发能力测试
   - 内存使用测试

3. **可靠性测试**:
   - 故障恢复测试
   - 长时间运行稳定性测试
   - 边界条件测试

### 测试覆盖率要求

- **代码覆盖率**: ≥ 95%
- **分支覆盖率**: ≥ 90%
- **功能覆盖率**: 100%

## 部署规范

### 部署要求

1. **环境要求**:
   - Python 3.11+
   - 内存 ≥ 512MB
   - CPU ≥ 2核心
   - 网络延迟 < 100ms

2. **依赖包**:
   ```python
   # 必需依赖
   - asyncio
   - datetime
   - typing
   - logging
   
   # 可选依赖
   - prometheus_client (监控)
   - pydantic (数据验证)
   ```

### 配置管理

1. **环境变量**:
   ```bash
   WEATHER_ROUTER_CONFIG_PATH=/path/to/config.yaml
   WEATHER_ROUTER_LOG_LEVEL=INFO
   WEATHER_ROUTER_METRICS_ENABLED=true
   ```

2. **配置文件**:
   ```yaml
   weather_router:
     enabled: true
     timeout: 10.0
     retry_attempts: 3
     
   services:
     hourly:
       enabled: true
       timeout: 5.0
     daily:
       enabled: true
       timeout: 8.0
     simulation:
       enabled: true
       timeout: 2.0
   ```

## 监控规范

### 关键指标

1. **性能指标**:
   - API调用次数 (按服务类型分类)
   - 响应时间分布
   - 错误率
   - 并发请求数

2. **业务指标**:
   - 路由准确率
   - 服务可用性
   - 缓存命中率
   - 用户满意度

3. **系统指标**:
   - 内存使用率
   - CPU使用率
   - 网络I/O
   - 磁盘I/O

### 告警规则

1. **紧急告警**:
   - 服务不可用 > 1分钟
   - 错误率 > 5%
   - 响应时间 > 5秒

2. **警告告警**:
   - 错误率 > 1%
   - 响应时间 > 3秒
   - 缓存命中率 < 50%

### 日志规范

1. **日志级别**:
   - ERROR: 服务异常和错误
   - WARN: 性能问题和警告
   - INFO: 关键操作和状态
   - DEBUG: 详细调试信息

2. **日志格式**:
   ```json
   {
     "timestamp": "2025-11-04T10:30:00Z",
     "level": "INFO",
     "component": "WeatherApiRouter",
     "operation": "get_forecast",
     "location": "杭州",
     "date": "2025-11-05",
     "forecast_range": "HOURLY",
     "service": "HourlyWeatherService",
     "duration": 1.2,
     "success": true
   }
   ```

## 安全规范

### 数据安全

1. **敏感信息保护**:
   - API密钥加密存储
   - 日志脱敏处理
   - 内存中敏感数据及时清理

2. **访问控制**:
   - 接口访问权限控制
   - IP白名单机制
   - 请求频率限制

### 网络安全

1. **通信安全**:
   - HTTPS加密传输
   - 证书验证
   - 请求签名验证

2. **防护措施**:
   - SQL注入防护
   - XSS攻击防护
   - CSRF攻击防护

## 版本管理

### 版本号规范

采用语义化版本号: `MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

### 发布流程

1. **开发阶段**: 开发和自测
2. **测试阶段**: 单元测试、集成测试
3. **预发布**: 灰度发布验证
4. **正式发布**: 全量发布
5. **监控验证**: 发布后监控验证

### 向后兼容性

1. **API兼容**: 保证现有API向后兼容
2. **数据兼容**: 保证返回数据格式兼容
3. **配置兼容**: 保证现有配置兼容
4. **行为兼容**: 保证功能行为兼容

---

**文档版本**: 1.0  
**最后更新**: 2025-11-04  
**审核状态**: 待审核  