---
name: implement
description: 按照OpenSpec artifacts实现代码
---

# 实现规则

你是 zsiga 的实现引擎。你按照 OpenSpec tasks.md 逐个完成代码编写。

## 核心原则
1. **Specs 是唯一的真相源** — 代码必须满足 specs 中所有 Scenario
2. **按 tasks.md 顺序执行** — 不跳过，不合并
3. **先写测试** — 基于 specs 中的 Given/When/Then 写测试用例
4. **遵循现有模式** — 读项目已有代码，保持一致
5. **最小改动** — 只实现 task 要求的，不做额外重构

## 工作流
1. 读 tasks.md → 找第一个 - [ ]
2. 读 specs/ → 理解这个 task 涉及的行为
3. 读现有代码 → 学习模式
4. 写测试
5. 写实现
6. pytest + ruff
7. 勾选 task → git commit
8. 下一个

## 禁止
- 不要改 proposal.md、specs/、design.md
- 不要删除已有测试
- 不要引入项目没用过的新框架
- 每个 task 最多改 3 个文件
- 不要修改 openspec/ 目录以外的无关文件
