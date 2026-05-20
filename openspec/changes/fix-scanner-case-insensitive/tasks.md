# Tasks: Scanner 文件名大小写不敏感

## 1. Scanner 核心改造

- [ ] 1.1 在 `intake/scanner.py` 中新增 `_find_file_ci(directory, target_name)` 辅助函数，使用 `os.listdir` + `.lower()` 匹配实现大小写不敏感文件查找，返回实际文件名或 `None`
- [ ] 1.2 重构 scanner 中 proposal.md / design.md / tasks.md 的检测逻辑，全部改用 `_find_file_ci()` 替代硬编码小写文件名检测；在 change dict 中新增 `proposal_filename`、`design_filename`、`tasks_filename` 字段记录实际文件名
- [ ] 1.3 在 scanner 跳过无 proposal 的目录时，新增 warn 级别日志输出：`⚠ Scanner: directory {change_dir} exists but no proposal.md found (case-insensitive search)`

## 2. Orchestrator 联动修改

- [ ] 2.1 修改 `orchestrator.py` 的 `_process_change()` 函数，读取 proposal / design / tasks 内容时使用 change dict 中的 `*_filename` 字段构建文件路径，不再硬编码小写文件名

## 3. 测试

- [ ] 3.1 新增测试用例覆盖：全大写 `PROPOSAL.md`、混合大小写 `Proposal.md`、标准小写 `proposal.md` 均能被 scanner 正确识别
- [ ] 3.2 新增测试用例覆盖：目录存在但无 proposal 文件时，scanner 输出 warn 日志并跳过该目录
- [ ] 3.3 新增测试用例覆盖：`design.md` / `tasks.md` 的大小写不敏感检测，以及 change dict 中 `*_filename` 字段正确性
