---
name: safety
description: 安全红线
---

# 安全红线

## 绝对禁止
- 不要修改 `openspec/specs/` 下的现有 spec 文件（delta merge 由 archive 流程处理）
- 不要删除已有测试
- 不要修改 `.env`、`settings/prod*`、`migrations/`
- 不要执行 `rm -rf`、`DROP TABLE` 等破坏性操作
- 不要向外部发送数据（curl 外部 API、上传文件等）

## 限制
- 每个 task 最多修改 3 个文件
- 不要引入项目未使用过的新依赖（除非 proposal 明确要求）
- git push 只推送到配置的 remote
