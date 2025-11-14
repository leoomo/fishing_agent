## 1. 创建基础设施
- [x] 1.1 新建 `interfaces/` 目录和 `__init__.py`
- [x] 1.2 新建 `config/` 目录和 `__init__.py`
- [x] 1.3 创建 `interfaces/coordinate_service.py` 坐标服务接口
- [x] 1.4 创建 `interfaces/weather_service.py` 天气服务接口
- [x] 1.5 创建 `config/service_config.py` 服务配置管理

## 2. 实现中央服务管理器
- [x] 2.1 创建 `services/service_manager.py` 中央服务管理器
- [x] 2.2 实现单例模式管理核心服务实例
- [x] 2.3 添加依赖注入支持和服务获取接口
- [x] 2.4 实现服务健康检查机制
- [x] 2.5 更新 `services/__init__.py` 导出服务管理器

## 3. 重构坐标服务为懒加载单例
- [x] 3.1 修改 `services/coordinate/amap_coordinate_service.py` 实现接口
- [x] 3.2 添加 `_initialized` 状态标志防止重复初始化
- [x] 3.3 分离数据库初始化逻辑到独立方法
- [x] 3.4 实现懒加载机制和错误处理
- [x] 3.5 添加详细的类型注解和文档字符串

## 4. 更新天气服务使用服务管理器
- [x] 4.1 修改 `services/weather/enhanced_weather_service.py` 通过服务管理器获取坐标服务
- [x] 4.2 实现天气服务接口
- [x] 4.3 优化服务初始化和依赖管理
- [x] 4.4 添加服务状态检查和重试逻辑

## 5. 修复日志服务代码质量问题
- [x] 5.1 清理 `services/logging/business_logger.py` 中的重复方法定义
- [x] 5.2 统一日志格式和错误处理机制
- [x] 5.3 添加类型注解和完善文档
- [x] 5.4 优化日志性能和内存使用

## 6. 更新工具层使用新架构
- [x] 6.1 修改 `tools/langchain_weather_tools.py` 使用服务管理器
- [x] 6.2 修改 `tools/fishing_analyzer.py` 使用服务管理器
- [x] 6.3 修改 `tools/weather_tool.py` 使用服务管理器
- [x] 6.4 更新所有工具的依赖注入方式

## 7. 测试和验证
- [x] 7.1 创建单元测试验证单例模式正确性
- [x] 7.2 集成测试验证服务依赖关系
- [x] 7.3 性能测试验证内存使用优化
- [x] 7.4 验证日志不再出现多次初始化消息

## 8. 文档和清理
- [x] 8.1 更新相关模块的 README 文档
- [x] 8.2 添加架构设计文档
- [x] 8.3 清理旧的直接实例化代码
- [x] 8.4 更新项目依赖关系说明