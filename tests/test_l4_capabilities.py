import json
import tempfile
from pathlib import Path

import pytest

from zsiga.agent.intent_router import classify, route, IntentType
from zsiga.agent.task_decomposer import decompose, aggregate_results
from zsiga.agent.todo import TodoList, TodoStatus
from zsiga.agent.escalation import EscalationManager, EscalationLevel, Strategy


class TestIntentRouter:
    def test_trivial_greeting(self):
        intent = classify("hi")
        assert intent.intent_type == IntentType.TRIVIAL

    def test_trivial_short_message(self):
        intent = classify("ok")
        assert intent.intent_type == IntentType.TRIVIAL

    def test_implementation_request(self):
        intent = classify("添加一个新的用户认证模块")
        assert intent.intent_type == IntentType.IMPLEMENTATION
        assert intent.confidence >= 0.7

    def test_implementation_english(self):
        intent = classify("implement a new API endpoint for user registration")
        assert intent.intent_type == IntentType.IMPLEMENTATION

    def test_exploration_request(self):
        intent = classify("这个模块是怎么工作的？")
        assert intent.intent_type == IntentType.EXPLORATION

    def test_exploration_english(self):
        intent = classify("how does the auth system work?")
        assert intent.intent_type == IntentType.EXPLORATION

    def test_ambiguous_empty(self):
        intent = classify("")
        assert intent.intent_type == IntentType.AMBIGUOUS

    def test_ambiguous_unclear(self):
        intent = classify("这个东西不太对")
        assert intent.intent_type == IntentType.AMBIGUOUS

    def test_route_trivial(self):
        assert route(classify("hello")) == "respond_directly"

    def test_route_exploration(self):
        assert route(classify("find the auth module")) == "dispatch_explore"

    def test_route_implementation(self):
        assert route(classify("create a new feature")) == "pipeline"


class TestTaskDecomposer:
    def test_generic_regression_test(self):
        result = decompose("给所有项目做回归测试")
        assert len(result.subtasks) > 0
        assert result.subtasks[0].description == "运行测试套件"
        assert len(result.parallel_groups) >= 1

    def test_specific_project(self):
        result = decompose("修复 compass 的策略组 bug", available_projects=["compass", "stockshark"])
        assert len(result.subtasks) == 1
        assert result.subtasks[0].project == "compass"

    def test_no_match_targets_all(self):
        result = decompose("do something random", available_projects=["compass", "stockshark"])
        assert len(result.subtasks) == 2

    def test_aggregate_results(self):
        results = {
            "compass": {"status": "pass"},
            "stockshark": {"status": "fail", "detail": "import error"},
            "zsiga": {"status": "pass"},
        }
        report = aggregate_results(results)
        assert report["total"] == 3
        assert report["passed"] == 2
        assert report["failed"] == 1


class TestTodoList:
    def test_add_and_get(self):
        todo = TodoList()
        todo.add("t1", "Write tests")
        item = todo.get("t1")
        assert item is not None
        assert item.content == "Write tests"
        assert item.status == TodoStatus.PENDING

    def test_start_and_complete(self):
        todo = TodoList()
        todo.add("t1", "Task 1")
        assert todo.start("t1") is True
        assert todo.in_progress[0].id == "t1"
        assert todo.complete("t1", "done") is True
        assert todo.completed[0].id == "t1"

    def test_cannot_complete_pending(self):
        todo = TodoList()
        todo.add("t1", "Task 1")
        assert todo.complete("t1") is False

    def test_cancel(self):
        todo = TodoList()
        todo.add("t1", "Task 1")
        assert todo.cancel("t1") is True
        assert todo.get("t1").status == TodoStatus.CANCELLED

    def test_summary(self):
        todo = TodoList()
        todo.add("t1", "A")
        todo.add("t2", "B")
        todo.start("t1")
        todo.complete("t1")
        s = todo.summary()
        assert s["total"] == 2
        assert s["by_status"]["completed"] == 1
        assert s["progress_pct"] == 50.0

    def test_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        todo = TodoList(persist_path=path)
        todo.add("t1", "Persist me")
        todo.start("t1")
        todo.complete("t1", "ok")

        todo2 = TodoList(persist_path=path)
        assert len(todo2.items) == 1
        assert todo2.items[0].status == TodoStatus.COMPLETED
        Path(path).unlink(missing_ok=True)


class TestEscalation:
    def test_initial_level(self):
        mgr = EscalationManager("test-change")
        assert mgr.level == EscalationLevel.NORMAL

    def test_escalate_after_3(self):
        mgr = EscalationManager("test-change")
        mgr.record_failure("error1", "implement", "same")
        mgr.record_failure("error2", "implement", "same")
        level = mgr.record_failure("error3", "implement", "same")
        assert level == EscalationLevel.RETRY_DIFFERENT
        assert mgr.should_escalate() is True

    def test_abort_after_5(self):
        mgr = EscalationManager("test-change")
        for i in range(5):
            mgr.record_failure(f"error{i}", "implement", "same")
        assert mgr.level == EscalationLevel.NEEDS_HUMAN
        assert mgr.should_abort() is True

    def test_strategy_rotation(self):
        mgr = EscalationManager("test-change")
        assert mgr.next_strategy == Strategy.SAME
        mgr.record_failure("e1", "", "same")
        assert mgr.next_strategy == Strategy.DIFFERENT_APPROACH

    def test_diagnosis_report(self):
        mgr = EscalationManager("test-change")
        mgr.record_failure("e1", "implement", "same")
        mgr.record_failure("e2", "verify", "different")
        report = mgr.generate_diagnosis()
        assert report.total_attempts == 2
        assert len(report.failures) == 2
        assert "implement" in report.root_cause_hypothesis
        assert report.to_text().startswith("# 诊断报告")

    def test_persist_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = EscalationManager("test-change", persist_dir=tmpdir)
            mgr.record_failure("e1", "impl", "same")
            report_path = Path(tmpdir) / "escalation-test-change.md"
            assert report_path.exists()
