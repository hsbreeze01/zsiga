# zsiga Active Context

## Identity
zsiga is an independent autonomous agent. It operates on external projects through OpenSpec-driven development.

## Principles
- OpenSpec specs are the single source of truth
- Every change must pass pytest + ruff before commit
- Revert on failure, never leave code broken
- Follow existing project patterns

## Session History: 79 lessons recorded
## Pattern Warnings (auto-mined)

🔴 **daemon.cycle_error** — 出现 22 次 (严重度: high)
   - RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/daemon_state.json
	data/zsiga.db
	memory/active_context.md
	memory/learnings.jsonl
	openspec/changes/dashboard-proposal-queue-mobile/.phase_state
	openspec/changes/dashboard-proposal-queue-mobile/clarify.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/mobile-responsiveness-js-cleanup.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/proposal-queue-panel.md
	site/dashboard.html
Please commit your changes or stash them before you switch branches.
Aborting
   - RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/zsiga.db
	memory/learnings.jsonl
	openspec/changes/validate-pipeline-fixes-20260520/.phase_state
	openspec/changes/validate-pipeline-fixes-20260520/clarify.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/dashboard-pipeline-flow-indicator.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/phase-table-completeness.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/validation-constraints.md
Please commit your changes or stash them before you switch branches.
Aborting

🟢 **pipeline.pass.deliver** — 出现 17 次 (严重度: low)
   - Success
   - Success

🟡 **pipeline.cross_project** — 出现 16 次 (严重度: medium)
   - Results: 1/4 passed
   - Results: 0/4 passed

🔴 **pipeline.fail.implement** — 出现 6 次 (严重度: high)
   - Failed at implement: lint:
E701 Multiple statements on one line (colon)
   --> src/intelligent_data_agent/tasks/multi_source_crawl.py:196:35
    |
194 |             matched = _match_keywords(it.title, keywords)
195 |     
   - Failed at implement: lint:
E701 Multiple statements on one line (colon)
   --> src/intelligent_data_agent/tasks/multi_source_crawl.py:201:35
    |
199 |             matched = _match_keywords(it.title, keywords)
200 |     

🟡 **code.unknown** — 出现 6 次 (严重度: medium)
   - review error and adjust approach
   - review error and adjust approach

🟡 **pipeline.review.critical** — 出现 3 次 (严重度: medium)
   - Review found critical issues: No implementation changes exist for any spec requirement. The repository contain
   - Review found critical issues: No implementation changes exist for any spec requirement. The repository contain


## Recent Lessons
- [daemon.cycle_error] TypeError: clarify() got an unexpected keyword argument 'supplementary_context'
- [daemon.cycle_error] TypeError: clarify() got an unexpected keyword argument 'supplementary_context'
- [daemon.cycle_error] TypeError: clarify() got an unexpected keyword argument 'supplementary_context'
- [daemon.cycle_error] TypeError: clarify() got an unexpected keyword argument 'supplementary_context'
- [daemon.cycle_error] TypeError: clarify() got an unexpected keyword argument 'supplementary_context'
- [code.unknown] review error and adjust approach
- [pipeline.review.critical] Review found critical issues: No implementation changes exist for any spec requirement. The repository contain
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/zsiga.db
	memory/learnings.jsonl
Please commit your changes or stash them before you switch branches.
Aborting
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/daemon.log
	data/daemon_state.json
	data/lock.pid
	data/zsiga.db
	openspec/changes/dashboard-proposal-queue-mobile/.phase_state
	openspec/changes/dashboard-proposal-queue-mobile/clarify.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/mobile-responsiveness-js-cleanup.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/phase-progress-bar.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/proposal-queue-panel.md
	site/dashboard.html
Please commit your changes or stash them before you switch branches.
Aborting
- [code.unknown] review error and adjust approach
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/daemon_state.json
	data/zsiga.db
	memory/learnings.jsonl
	metrics/changes.jsonl
	openspec/changes/dashboard-proposal-queue-mobile/.phase_state
	openspec/changes/dashboard-proposal-queue-mobile/clarify.md
	site/dashboard.html
Please commit your changes or stash them before you switch branches.
Aborting
- [code.unknown] review error and adjust approach
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/daemon_state.json
	data/zsiga.db
	memory/active_context.md
	memory/learnings.jsonl
	metrics/changes.jsonl
	openspec/changes/dashboard-proposal-queue-mobile/.phase_state
	openspec/changes/dashboard-proposal-queue-mobile/clarify.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/mobile-responsiveness-js-cleanup.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/phase-progress-bar.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/proposal-queue-panel.md
	site/dashboard.html
Please commit your changes or stash them before you switch branches.
Aborting
- [pipeline.review.critical] Review found critical issues: No implementation changes exist for any spec requirement. The repository contain
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/daemon_state.json
	data/zsiga.db
	memory/active_context.md
	openspec/changes/dashboard-proposal-queue-mobile/.phase_state
	openspec/changes/dashboard-proposal-queue-mobile/clarify.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/mobile-responsiveness-js-cleanup.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/phase-progress-bar.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/proposal-queue-panel.md
	site/dashboard.html
Please commit your changes or stash them before you switch branches.
Aborting
- [pipeline.review.critical] Review found critical issues: No implementation changes exist for any spec requirement. The repository contain
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/daemon.log
	data/daemon_state.json
	data/lock.pid
	data/zsiga.db
	openspec/changes/dashboard-proposal-queue-mobile/.phase_state
	openspec/changes/dashboard-proposal-queue-mobile/clarify.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/phase-progress-bar.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/proposal-queue-panel.md
	site/dashboard.html
Please commit your changes or stash them before you switch branches.
Aborting
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/daemon_state.json
	data/zsiga.db
	memory/active_context.md
	memory/learnings.jsonl
	openspec/changes/dashboard-proposal-queue-mobile/.phase_state
	openspec/changes/dashboard-proposal-queue-mobile/clarify.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/mobile-responsiveness-js-cleanup.md
	openspec/changes/dashboard-proposal-queue-mobile/specs/proposal-queue-panel.md
	site/dashboard.html
Please commit your changes or stash them before you switch branches.
Aborting
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/zsiga.db
	memory/learnings.jsonl
	openspec/changes/validate-pipeline-fixes-20260520/.phase_state
	openspec/changes/validate-pipeline-fixes-20260520/clarify.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/dashboard-pipeline-flow-indicator.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/phase-table-completeness.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/validation-constraints.md
Please commit your changes or stash them before you switch branches.
Aborting
- [daemon.cycle_error] RuntimeError: error: Your local changes to the following files would be overwritten by checkout:
	data/zsiga.db
	memory/learnings.jsonl
	openspec/changes/validate-pipeline-fixes-20260520/.phase_state
	openspec/changes/validate-pipeline-fixes-20260520/clarify.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/dashboard-pipeline-flow-indicator.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/phase-table-completeness.md
	openspec/changes/validate-pipeline-fixes-20260520/specs/validation-constraints.md
Please commit your changes or stash them before you switch branches.
Aborting
