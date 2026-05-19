# Proposal: Intent Router OpenSpec 上下文感知 + 功能描述语义区分

## Summary
修复 intent router 对 openspec/changes/ 目录下 proposal 的误判。当前 proposal "Dashboard 实时监控与异常诊断增强" 被分类为 investigation（9个关键词匹配：异常、诊断、排查、错误），但实际是 implementation 意图（描述要构建什么功能）。根因：描述诊断功能 ≠ 执行诊断动作，关键词匹配无法区分。

## Motivation
以下 proposal 被误判为 investigation：

```
INVESTIGATION: 9 matches（异常×4、诊断×3、排查×1、错误×1）
FIX: 4 matches（失败×3、修复×1）
IMPL: 1 matches（部署×1）
```

"异常诊断面板" 是要**构建的功能**，不是要**诊断的问题**。但关键词匹配把"诊断"、"异常"当成了调试意图。

在 daemon 模式下，误判意味着 proposal 被路由到 dispatch_diagnoser 而非 pipeline，直接导致 change 被跳过不处理。

## Expected Behavior

### 修复 1：OpenSpec 来源感知（agent/intent_router.py）

在 classify() 函数中增加 source 参数：

```python
def classify(message: str, config=None, source: str = None) -> Intent:
```

当 source="openspec" 时，直接返回 implementation 意图。逻辑：
- openspec/changes/ 目录下的文件 100% 是待实现的 change，不存在歧义
- 不需要关键词匹配或 LLM 分类

实现位置：classify() 函数开头，在空消息检查之后：

```python
if source == "openspec":
    return Intent(
        verbalization="OpenSpec proposal — implementation intent",
        intent_type=IntentType.IMPLEMENTATION,
        confidence=0.95,
        reasoning="Proposal from openspec/changes/ — always implementation",
        suggested_action="pipeline: ENRICH → IMPLEMENT → VERIFY → DELIVER",
    )
```

调用方修改（pipeline/orchestrator.py）：
- _process_change() 中读取 proposal 后调用 classify() 时传入 source="openspec"
- 搜索所有 classify(proposal_text) 调用，统一改为 classify(proposal_text, source="openspec")
- 注意：只有从 openspec/changes/ 目录读取的 proposal 才传 source="openspec"

### 修复 2：功能描述语义区分（agent/intent_router.py）

当关键词匹配到 INVESTIGATION 时，检查是否存在"构建标记词"。如果同时存在，说明是在描述要构建的诊断功能，降权 INVESTIGATION：

新增构建标记词正则：

```python
_CONSTRUCTION_MARKERS = re.compile(
    r"新增|面板|模块|功能|卡片|组件|页面|feature|panel|module|component|"
    r"widget|card|section|新增|展示|显示|图表|dashboard|趋势",
    re.IGNORECASE,
)
```

在关键词评分逻辑中（classify 函数的 scores 构建部分），当 invest_matches 和 _CONSTRUCTION_MARKERS 同时命中时：

```python
if invest_matches:
    has_construction = bool(_CONSTRUCTION_MARKERS.search(text))
    invest_score = len(invest_matches)
    if has_construction:
        invest_score = max(0, invest_score - 4)
    if invest_score > 0:
        scores.append((invest_score, IntentType.INVESTIGATION, ...))
```

### 修复 3：_verbalize() 同步修复（agent/intent_router.py）

当前 _verbalize() 按优先级检查 FIX > INVESTIGATION > IMPL > EVAL > RESEARCH。INVESTIGATION 优先级高于 IMPL，导致"异常诊断"相关的 proposal 总是 verbalize 为"用户想要排查或调试某个问题"。

修复：当同时匹配 INVESTIGATION 和 _CONSTRUCTION_MARKERS 时，verbalize 应该反映 implementation 语义：

```python
if _INVESTIGATION_KEYWORDS.search(text):
    has_construction = bool(_CONSTRUCTION_MARKERS.search(text)) if '_CONSTRUCTION_MARKERS' in dir() else False
    if not has_construction:
        if has_chinese:
            return "用户想要排查或调试某个问题"
        return "User wants to investigate or debug an issue"
```

## Constraints
- 只修改 agent/intent_router.py 和 pipeline/orchestrator.py
- 不改变 LLM classification 的 system prompt（方案 A+B 不依赖 LLM）
- 不改变 IntentType 枚举或 route() 函数
- 保持向后兼容：source 参数默认 None，不影响非 openspec 来源的调用
- 所有改动完成后必须 git commit 并 git push
