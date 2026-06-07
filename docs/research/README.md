# 调研目录

本目录用于沉淀 Physical AI 数据层项目的竞品、开源生态、技术路线和二次开发可行性调研。

当前第一阶段聚焦 Rerun.io。调研目标不是做产品介绍，而是判断它对本项目的价值：

- 哪些理念和数据模型值得借鉴；
- 哪些能力可以直接复用；
- 哪些模块适合封装或二次开发；
- 哪些关键能力必须自研或另行建设。

## 当前文档

- [Rerun.io 调研框架与原子能力清单](01-rerun调研框架与原子能力清单.md)
- [Rerun.io 第一轮公开资料调研](02-rerun.io第一轮公开资料调研.md)
- [Rerun.io 二次开发路线判断矩阵](03-rerun二次开发路线判断矩阵.md)
- [Rerun.io 阶段二本地技术评测报告](04-rerun阶段二本地技术评测报告.md)

## 调研基线

- 调研日期：2026-06-06
- 第一轮调研对象：Rerun.io / rerun-sdk `0.33.0`
- 调研方法：官方文档、官方 GitHub 仓库、PyPI 包信息和公开开源资料交叉验证
- 当前状态：已完成第一轮公开资料调研和阶段二本地技术评测；Viewer/Blueprint GUI 视觉检查、性能压测和真实现场数据适配实验尚未完成

## 主要来源

- Rerun 官方文档索引：<https://rerun.io/llms.txt>
- Rerun 概览：<https://rerun.io/docs/overview/what-is-rerun>
- Rerun Getting Started：<https://rerun.io/docs/getting-started.md>
- Rerun Concepts：<https://rerun.io/docs/concepts.md>
- Rerun GitHub 仓库：<https://github.com/rerun-io/rerun>
- rerun-sdk PyPI：<https://pypi.org/project/rerun-sdk/>

## 维护约定

- 每轮调研应标注日期、信息来源和调研基线版本。
- 涉及技术判断时，优先给出证据链接，再给出判断。
- 涉及路线选择时，必须区分“可直接复用”“可封装复用”“可二次开发”“建议自研”“暂缓判断”。
- 性能、稳定性、部署和数据安全相关结论，在未完成实验前只能作为假设或风险记录。
