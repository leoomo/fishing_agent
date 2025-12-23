# Change: 精简并更新AGENTS.md文档

## Why
当前根目录`AGENTS.md`仅包含OpenSpec指令块，内容过于冗长且缺少项目特定的AI助手使用指南。AI助手在项目中工作时需要更简洁、更有针对性的指导。

## What Changes
- **精简OpenSpec指令**：保留核心工作流程和常用命令，删除冗余说明
- **添加项目特定指南**：包含项目结构、关键导入、环境变量、API端点等
- **添加常用工具参考**：列出项目常用的命令和工具
- **保持与openspec/AGENTS.md同步**：详细OpenSpec规范仍保留在`openspec/AGENTS.md`

## Impact
- Affected specs: documentation (新建)
- Affected code: 根目录 `AGENTS.md`
- Benefits:
  - AI助手能更快找到项目关键信息
  - 降低新成员的学习曲线
  - 提高开发效率
