# documentation Specification

## Purpose
TBD - created by archiving change update-agents-doc. Update Purpose after archive.
## Requirements
### Requirement: AI助手使用指南
系统MUST提供AGENTS.md文档作为AI助手在项目中工作的主要参考文档。

#### Scenario: AI助手快速了解项目
- **WHEN** AI助手首次进入项目或需要快速回顾项目信息
- **THEN** AGENTS.md MUST提供项目概览、核心特性、关键导入、API端点、环境变量和快速开始命令

#### Scenario: AI助手处理规划类请求
- **WHEN** AI助手收到涉及规划、提案、架构变更的请求
- **THEN** AGENTS.md SHALL引导AI助手参考openspec/AGENTS.md获取详细OpenSpec规范

### Requirement: OpenSpec指令精简版
AGENTS.md MUST包含精简的OpenSpec工作流程指令，详细规范保留在openspec/AGENTS.md中。

#### Scenario: 快速检查清单
- **WHEN** AI助手需要创建或验证变更提案
- **THEN** AGENTS.md MUST提供TL;DR快速检查清单和核心CLI命令

#### Scenario: 获取详细规范
- **WHEN** AI助手需要详细的OpenSpec规范信息
- **THEN** AGENTS.md SHALL明确指向openspec/AGENTS.md获取完整文档

### Requirement: 项目结构参考
AGENTS.md MUST包含项目的目录结构和关键文件位置说明。

#### Scenario: 定位核心代码
- **WHEN** AI助手需要查找特定功能的代码位置
- **THEN** AGENTS.md SHALL提供packages/、apps/、shared/等目录的用途说明

#### Scenario: 理解模块依赖
- **WHEN** AI助手需要理解包之间的依赖关系
- **THEN** AGENTS.md MUST说明agent_fishing、data_processing、scraper等包的独立性

### Requirement: 关键导入示例
AGENTS.md MUST提供常用的Python导入语句示例。

#### Scenario: Agent核心功能
- **WHEN** AI助手需要使用Agent核心功能
- **THEN** AGENTS.md SHALL提供从packages.agent_fishing导入FishingAgent、create_agent等的示例

#### Scenario: 数据处理功能
- **WHEN** AI助手需要使用数据处理功能
- **THEN** AGENTS.md SHALL提供从packages.data_processing导入ImageMerger、OCRMergeProcessor等的示例

### Requirement: API端点参考
AGENTS.md MUST列出项目的主要API端点及其用途。

#### Scenario: 查找核心API
- **WHEN** AI助手需要了解对话或工具API
- **THEN** AGENTS.md SHALL列出POST /api/v1/fishing/chat、GET /api/v1/fishing/tools等端点

#### Scenario: 查找管理API
- **WHEN** AI助手需要了解后台管理API
- **THEN** AGENTS.md SHALL列出爬虫、监控、配置等管理端点

### Requirement: 环境变量参考
AGENTS.md MUST列出项目必需和可选的环境变量。

#### Scenario: 配置必需环境变量
- **WHEN** AI助手设置开发环境
- **THEN** AGENTS.md SHALL列出CAIYUN_API_KEY、AMAP_API_KEY、DASHSCOPE_API_KEY等必需变量

#### Scenario: 配置JWT认证
- **WHEN** AI助手配置认证系统
- **THEN** AGENTS.md SHALL列出JWT_SECRET_KEY、JWT_ALGORITHM等认证相关变量

### Requirement: 文档导航
AGENTS.md MUST提供指向详细文档的链接。

#### Scenario: 查找用户文档
- **WHEN** AI助手需要查找用户指南或故障排除
- **THEN** AGENTS.md SHALL提供docs/01-user-guide/的链接

#### Scenario: 查找开发者文档
- **WHEN** AI助手需要查找开发规范或代码结构
- **THEN** AGENTS.md SHALL提供docs/02-developer-guide/的链接

