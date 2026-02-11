# 智能钓鱼助手 v5.1.0 - 文档中心

> 模块化 Agent 架构 + JWT认证系统 + React管理前端 + 微信小程序，基于 LangChain 1.0+ 和 7 因子科学评分系统

## 📚 文档导航

### 🚀 [用户指南](./01-user-guide/) - 面向最终用户和初学者
适合想要了解和使用智能钓鱼助手的用户

- **[快速开始](./01-user-guide/getting-started.md)** - 5分钟快速上手
- **[基础功能](./01-user-guide/basic-features.md)** - 核心功能概览
- **[故障排除](./01-user-guide/troubleshooting.md)** - 常见问题解决
- **[常见问题](./01-user-guide/faq.md)** - FAQ解答

### 💻 [开发者指南](./02-developer-guide/) - 面向项目开发者
适合想要参与项目开发、进行二次开发或集成API的开发者

- **[环境配置](./02-developer-guide/environment-setup.md)** - 开发环境搭建
- **[代码结构](./02-developer-guide/codebase-structure.md)** - 项目架构和组件说明
- **[开发流程](./02-developer-guide/development-workflows.md)** - 开发规范和最佳实践
- **[测试指南](./02-developer-guide/testing.md)** - 测试策略和规范
- **[贡献指南](./02-developer-guide/contribution-guide.md)** - 如何贡献代码
- **[开发工具](./02-developer-guide/tools-and-utilities.md)** - 可用工具和实用程序
- **[调试指南](./02-developer-guide/debugging.md)** - 调试技巧和常见问题

### 🏗️ [架构设计](./03-architecture/) - 面向系统架构师
适合想要深入了解系统设计和技术架构的读者

- **[系统设计](./03-architecture/system-design.md)** - 整体架构和设计原则
- **[模块架构](./03-architecture/module-architecture.md)** - 模块化设计和依赖关系
- **[数据库设计](./03-architecture/database-schema.md)** - 数据模型和关系设计
- **[安全架构](./03-architecture/security-design.md)** - JWT认证和安全性设计
- **[可扩展性](./03-architecture/scalability.md)** - 系统扩展和性能优化
- **[设计决策](./03-architecture/design-decisions.md)** - 重要架构决策记录

### 🔧 [运维部署](./04-operations/) - 面向运维工程师
适合负责系统部署、运维和监控的工程师

- **[部署指南](./04-operations/deployment-guide.md)** - 生产环境部署
- **[配置管理](./04-operations/configuration.md)** - 系统配置和环境变量
- **[监控告警](./04-operations/monitoring.md)** - 系统监控和告警设置
- **[备份恢复](./04-operations/backup-and-recovery.md)** - 数据备份和灾难恢复
- **[性能调优](./04-operations/performance-tuning.md)** - 性能优化指南
- **[维护指南](./04-operations/maintenance.md)** - 日常维护操作

### 📡 [API参考](./05-api-reference/) - 完整的API文档
面向需要集成或调用API的开发者

- **[认证授权](./05-api-reference/authentication.md)** - JWT认证和权限管理
- **[API端点](./05-api-reference/endpoints/)** - 详细的接口文档
  - **[钓鱼API](./05-api-reference/endpoints/fishing-api.md)** - 钓鱼推荐相关接口
  - **[内容管理API](./05-api-reference/endpoints/content-api.md)** - 文章、鱼百科、配件、拟饵、钓组管理 ⭐ v5.1.0
  - **[管理接口](./05-api-reference/endpoints/admin-api.md)** - 管理员专用接口
- **[数据结构](./05-api-reference/data-schemas.md)** - 请求/响应数据格式
- **[错误处理](./05-api-reference/error-handling.md)** - 错误码和异常处理
- **[限流规则](./05-api-reference/rate-limiting.md)** - API调用频率限制

### 📖 [专题指南](./06-guides/) - 特定功能和任务指南
深入特定功能和高级用法的详细指南

- **[图片处理](./06-guides/image-processing.md)** - OCR和图片处理功能
- **[爬虫开发](./06-guides/crawler-development.md)** - 网络爬虫开发和扩展
- **[小程序集成](./06-guides/miniprogram-integration.md)** - 微信小程序集成
- **[装备导入](./06-guides/equipment-import.md)** - 装备数据导入工作流
- **[装备排序](./06-guides/equipment-sorting.md)** - 装备排序功能详解
- **[装备排序总结](./06-guides/equipment-sorting-summary.md)** - 排序功能实现总结
- **[性能优化](./06-guides/performance-optimization.md)** - 系统性能优化技术
- **[迁移指南](./06-guides/migration-guides/)** - 版本升级和数据迁移

### 🗄️ [文档归档](./archive/) - 历史和过时文档
存放不再维护的历史文档和草稿

## 🎯 快速查找

| 我是... | 我需要... | 推荐文档 |
|--------|----------|----------|
| **新用户** | 快速开始使用 | [用户指南 - 快速开始](./01-user-guide/getting-started.md) |
| **开发者** | 参与项目开发 | [开发者指南 - 环境配置](./02-developer-guide/environment-setup.md) |
| **架构师** | 了解系统设计 | [架构设计 - 系统设计](./03-architecture/system-design.md) |
| **运维工程师** | 部署生产环境 | [运维部署 - 部署指南](./04-operations/deployment-guide.md) |
| **API集成者** | 调用API接口 | [API参考 - 认证授权](./05-api-reference/authentication.md) |

## 🔍 核心特性概览

### 🆕 v5.1.0 新增功能

- **🐟 鱼百科管理** - 鱼种知识库、季节活动规律、装备推荐查询
- **📚 内容管理系统** - 富文本编辑器、自动保存草稿、语义搜索、向量检索（ChromaDB）
- **📊 Excel批量导入** - 批量导入装备数据到待审核队列、模板生成系统
- **🔍 向量搜索** - 基于ChromaDB的语义搜索和DashScope Embedding
- **🎯 配件管理** - 钩子、铅坠、转环、前导线等配件完整管理
- **🪝 拟饵类型** - 硬饵、软饵、金属饵、飞蝇分类体系
- **🔧 钓组配置** - 德州钓组、卡罗莱纳钓组、倒吊钓组等模板
- **🔄 装备管理增强排序** - 支持12个字段排序（名称/类别/品牌/价格/竿长/自重/动作/调性/节数/创建时间/更新时间）

### 核心功能

- **🧩 模块化Agent架构** - 4个独立包，完全自包含
  - `packages/agents/fishing` - 钓鱼助手 Agent
  - `packages/agents/equipment_import` - 装备导入 Agent
  - `packages/agents/agent_component` - 统一监控组件
  - `packages/data_processing` - 图片处理和OCR
  - `packages/scraper` - 分布式爬虫框架
- **🔄 动态Prompt中间件** - 智能选择提示词，Token效率提升50%+
- **🎯 7因子科学评分** - 温度、天气、风力、气压、湿度、季节、月相
- **🔐 JWT认证系统** - RBAC权限管理 + 微信小程序支持
- **🤖 智能处理系统** - OCR多提供商 + 图片合并 + 装备导入
- **🌐 多端支持** - CLI、API、React管理前端、微信小程序

## 📝 文档规范

本文档遵循以下组织原则：
- **受众导向**：按用户角色组织，便于快速定位
- **层次清晰**：最多3层目录结构，避免深层嵌套
- **命名一致**：使用英文文件名，中文内容描述
- **导航友好**：每个目录都有README.md作为入口
- **交叉引用**：相关文档间建立清晰的引用关系
- **版本同步**：所有文档版本号与项目版本保持一致

## 🔗 相关资源

- **项目主页**：[智能钓鱼助手 GitHub](https://github.com/your-org/fishing-agent)
- **问题反馈**：[GitHub Issues](https://github.com/your-org/fishing-agent/issues)
- **更新日志**：[CHANGELOG.md](../CHANGELOG.md)
- **许可证**：[LICENSE](../LICENSE)

## 📦 技术栈概览

### 后端技术
- **Python 3.11+** - 主要开发语言
- **LangChain 1.0+** - AI Agent框架
- **FastAPI** - 高性能Web框架
- **SQLAlchemy** - ORM数据访问
- **uv** - 现代Python包管理器

### 前端技术
- **React 19.2.0** - 用户界面框架
- **TypeScript** - 类型安全的JavaScript
- **Ant Design 5.22.0** - 企业级UI组件库
- **Vite** - 快速构建工具

### AI和数据
- **通义千问** - 阿里云LLM服务
- **智谱AI** - GLM-4.6模型
- **Ollama** - 本地OCR模型
- **SiliconFlow** - 云端OCR服务
- **彩云天气** - 气象数据API
- **高德地图** - 地理位置服务

---

**文档版本**: v5.1.0
**最后更新**: 2026-01-17
**维护团队**: 智能钓鱼助手开发团队
