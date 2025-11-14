## Why
当前系统存在多个服务实例重复初始化问题，坐标缓存数据库被多次创建，导致资源浪费和日志混乱。缺乏统一的服务管理机制，代码耦合度高，难以维护和扩展。

## What Changes
- 创建统一的服务管理器：新建 `services/service_manager.py` 作为中央服务管理器，实现单例模式管理所有核心服务实例，提供清晰的服务获取接口，支持依赖注入
- 重构 AmapCoordinateService 为懒加载单例：在 `services/coordinate/amap_coordinate_service.py` 中实现懒加载机制，添加 `_initialized` 状态标志防止重复初始化，分离数据库初始化逻辑到独立方法
- 创建服务接口抽象：新建 `interfaces/coordinate_service.py` 定义坐标服务接口，让 AmapCoordinateService 实现该接口提高可扩展性，便于后续替换或扩展不同的坐标服务实现
- 优化依赖关系：修改 EnhancedCaiyunWeatherService 通过服务管理器获取坐标服务，更新所有工具文件使用服务管理器而非直接实例化，实现清晰的依赖链：工具 → 天气服务 → 服务管理器 → 坐标服务
- 修复代码质量问题：清理 BusinessLogger 中的重复方法定义，添加详细的类型注解和文档字符串，统一日志格式和错误处理机制
- 增强配置管理：新建 `config/service_config.py` 集中管理服务配置，支持环境变量配置服务行为，添加服务健康检查和重试机制

## Impact
- **影响的服务**: coordinate-service, weather-service, logging-service
- **影响的代码**:
  - services/coordinate/amap_coordinate_service.py
  - services/weather/enhanced_weather_service.py
  - services/logging/business_logger.py
  - tools/langchain_weather_tools.py
  - tools/fishing_analyzer.py
  - tools/weather_tool.py
- **新增模块**:
  - services/service_manager.py（中央服务管理器）
  - interfaces/（服务接口抽象层）
  - config/service_config.py（配置管理）
- **架构改进**: 实现解耦、模块化、可读性、可维护性、可扩展性的服务架构
- **性能提升**: 懒加载避免重复初始化，减少内存占用