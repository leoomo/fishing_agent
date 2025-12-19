# 运维部署指南

欢迎来到智能钓鱼助手运维部署文档！本部分面向DevOps工程师、系统管理员，提供完整的部署、监控和维护指南。

## 📋 文档内容

### 🚀 [部署指南](./deployment-guide.md)
- 生产环境部署方案
- Docker容器化部署
- Kubernetes集群部署
- 环境配置管理

### ⚙️ [配置管理](./configuration.md)
- 环境变量配置
- 系统参数调优
- 安全配置指南
- 配置文件模板

### 📊 [监控告警](./monitoring.md)
- 系统监控方案
- 性能指标监控
- 日志管理和分析
- 告警策略配置

### 💾 [备份恢复](./backup-and-recovery.md)
- 数据备份策略
- 灾难恢复方案
- 数据迁移指南
- 业务连续性保障

### 🔧 [性能调优](./performance-tuning.md)
- 系统性能优化
- 数据库性能调优
- 缓存策略优化
- 负载均衡配置

### 🛠️ [维护指南](./maintenance.md)
- 日常维护操作
- 系统更新流程
- 故障排查手册
- 安全维护措施

## 🎯 运维概览

### 系统架构
```
┌─────────────────────────────────────────────────────────┐
│                    负载均衡层                              │
│                   Nginx / ALB                             │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    应用服务层                              │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   API服务   │  Web前端    │  微信小程序  │    CLI工具       │
│  (多实例)    │  (静态资源)  │ (第三方托管) │   (部署包)       │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    服务支撑层                              │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   Redis     │ PostgreSQL  │   Ollama    │   外部API       │
│   (缓存)     │  (主数据库)  │  (OCR服务)  │  (天气/地图)     │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    基础设施层                              │
│              Docker / Kubernetes / 云服务               │
└─────────────────────────────────────────────────────────┘
```

### 核心组件
- **API服务**: FastAPI应用，处理所有业务逻辑
- **Web前端**: React SPA，提供管理界面
- **数据库**: PostgreSQL存储用户数据和业务数据
- **缓存**: Redis存储会话和临时数据
- **OCR服务**: Ollama本地OCR或SiliconFlow云端OCR
- **监控系统**: Prometheus + Grafana监控方案

## 🔧 部署要求

### 硬件要求

#### 最小配置
- **CPU**: 2核
- **内存**: 4GB
- **存储**: 20GB SSD
- **网络**: 10Mbps

#### 推荐配置
- **CPU**: 4核
- **内存**: 8GB
- **存储**: 50GB SSD
- **网络**: 100Mbps

#### 生产环境配置
- **CPU**: 8核
- **内存**: 16GB
- **存储**: 100GB SSD
- **网络**: 1Gbps

### 软件要求

#### 基础环境
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **容器运行时**: Docker 20.10+ / Containerd 1.4+
- **编排工具**: Kubernetes 1.20+ / Docker Compose 2.0+
- **网络**: LoadBalancer / Ingress Controller

#### 依赖服务
- **数据库**: PostgreSQL 13+
- **缓存**: Redis 6.0+
- **代理**: Nginx 1.20+
- **监控**: Prometheus 2.30+ / Grafana 8.0+

## 🚀 快速部署

### Docker Compose部署
```bash
# 1. 克隆项目
git clone https://github.com/your-org/fishing-agent.git
cd fishing-agent

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置必要参数

# 3. 启动服务
docker-compose up -d

# 4. 验证部署
docker-compose ps
curl http://localhost:8000/health
```

### Kubernetes部署
```bash
# 1. 创建命名空间
kubectl create namespace fishing-agent

# 2. 应用配置
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/

# 3. 验证部署
kubectl get pods -n fishing-agent
kubectl get services -n fishing-agent
```

## 📊 监控指标

### 系统指标
- **CPU使用率**: < 80%
- **内存使用率**: < 85%
- **磁盘使用率**: < 90%
- **网络延迟**: < 100ms

### 应用指标
- **API响应时间**: P95 < 1s
- **请求成功率**: > 99.5%
- **并发连接数**: 监控峰值
- **错误率**: < 0.5%

### 业务指标
- **日活用户数**: DAU统计
- **API调用量**: 接口使用统计
- **OCR识别量**: 图片处理统计
- **钓鱼推荐成功率**: 业务效果指标

## 🔒 安全配置

### 网络安全
- **HTTPS**: 强制使用HTTPS加密传输
- **防火墙**: 配置访问控制列表
- **DDoS防护**: 启用DDoS防护服务
- **WAF**: Web应用防火墙保护

### 应用安全
- **认证**: JWT Token + 会话管理
- **授权**: RBAC权限控制
- **数据加密**: 敏感数据加密存储
- **API限流**: 防止恶意调用

### 基础安全
- **系统加固**: 操作系统安全加固
- **漏洞扫描**: 定期安全漏洞扫描
- **访问控制**: 最小权限原则
- **审计日志**: 完整的操作审计

## 🔄 运维流程

### 部署流程
1. **环境准备** - 检查环境和依赖
2. **配置更新** - 更新配置文件
3. **应用部署** - 部署新版本应用
4. **健康检查** - 验证服务健康状态
5. **监控验证** - 确认监控正常工作

### 更新流程
1. **备份数据** - 创建数据备份
2. **滚动更新** - 零停机更新
3. **版本验证** - 验证新版本功能
4. **回滚准备** - 准备回滚方案
5. **清理资源** - 清理旧版本资源

### 故障处理
1. **故障发现** - 监控告警发现
2. **影响评估** - 评估故障影响范围
3. **应急响应** - 快速恢复服务
4. **根因分析** - 分析故障根本原因
5. **预防改进** - 制定预防措施

## 📱 运维工具

### 监控工具
- **Prometheus**: 指标收集和存储
- **Grafana**: 监控面板和可视化
- **AlertManager**: 告警管理和通知
- **Jaeger**: 分布式链路追踪

### 日志工具
- **ELK Stack**: Elasticsearch + Logstash + Kibana
- **Fluentd**: 日志收集和转发
- **Loki**: 轻量级日志聚合
- **Sentry**: 错误监控和追踪

### 部署工具
- **Helm**: Kubernetes包管理
- **ArgoCD**: GitOps持续部署
- **Terraform**: 基础设施即代码
- **Ansible**: 自动化运维工具

## 🔗 相关资源

### 官方文档
- [Docker文档](https://docs.docker.com/)
- [Kubernetes文档](https://kubernetes.io/docs/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)
- [Redis文档](https://redis.io/documentation/)

### 运维指南
- [系统设计](../03-architecture/system-design.md) - 了解系统架构
- [API文档](../05-api-reference/) - 接口详细说明
- [开发指南](../02-developer-guide/) - 开发相关文档

### 最佳实践
- [12-Factor App](https://12factor.net/) - 现代应用开发原则
- [Kubernetes最佳实践](https://kubernetes.io/docs/concepts/cluster-administration/)
- [Docker最佳实践](https://docs.docker.com/develop/dev-best-practices/)

## 🎯 运维团队

### 角色分工
- **运维工程师**: 日常运维和故障处理
- **DevOps工程师**: CI/CD和自动化运维
- **安全工程师**: 安全配置和漏洞管理
- **系统架构师**: 架构优化和技术选型

### 联系方式
- **技术支持**: ops@fishing-agent.com
- **紧急响应**: +86-xxx-xxxx-xxxx
- **在线支持**: 企业微信群 / Slack频道
- **文档更新**: GitHub仓库Issue反馈

---

**文档版本**: v5.0.2  
**适用系统版本**: v5.0.2+  
**更新时间**: 2024-12-20  
**维护团队**: 智能钓鱼助手运维团队