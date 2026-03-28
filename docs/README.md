# 文档导航

`docs/` 目录用于存放项目使用说明、架构设计、数据库工作台和训练流程文档。建议按照下面顺序阅读。

## 入门

- [快速开始](./quickstart.md): 从依赖安装、服务启动到第一次训练
- [Makefile 使用说明](./Makefile-docs.md): 本地开发常用命令

## 核心说明

- [架构说明](./architecture.md): Rust、FastAPI、Celery、Vue 的协作方式
- [训练与数据指南](./training-guide.md): 任务配置、网络架构、数据集导入和结果查看
- [数据库工作台](./database-workspace.md): 本地 MySQL、SSH 云端 SQL、建库建表和 CSV 导入

## 排障

- [常见问题](./faq.md): 模块缺失、GPU/CPU 选择、MySQL、路由 404 和任务卡住

## 文档边界

当前文档以仓库现有实现为准，重点覆盖:

- Rust 原生求解与 Python/Torch 回退机制
- FastAPI + Celery 后端任务系统
- Vue 前端配置、监控、结果和数据库工作台
- MySQL 连接与训练数据集导入

未覆盖的生产级主题:

- Kubernetes 部署
- 多租户权限体系
- 面向公网的高可用数据库架构
- 完整 SQL 方言兼容
