# 部署本地基础设施代码到远端仓库

## 问题

当前 zsiga-l5-autonomous-engineer 分支本地有 26 个 commit 未部署到 origin。
其中包括 9-role sub-agent 系统、确定性事实提取、Design Gate 修复等关键基础设施代码。
远端 origin/zsiga-l5-autonomous-engineer 停在 commit 1027dbb，严重落后于本地。

## 操作

执行部署操作：git push origin zsiga-l5-autonomous-engineer 将本地 commit 部署到远端。

如果部署失败（如远端有新的 commit），先 git pull --rebase origin zsiga-l5-autonomous-engineer 解决冲突后再部署。

## 验收标准

1. git log origin/zsiga-l5-autonomous-engineer -1 显示最新的本地 commit
2. 无部署错误
