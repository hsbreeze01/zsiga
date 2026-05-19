# Delta Spec: Construction Marker Semantic Distinction

## ADDED Requirements

### Requirement: Construction Marker Keyword Detection

The intent router SHALL define a set of "construction marker" keywords that indicate
a proposal is describing a feature to be **built**, not an action to be **performed**.

Construction markers include (but are not limited to): 新增, 面板, 模块, 功能, 卡片,
组件, 页面, feature, panel, module, component, widget, card, section, 展示, 显示,
图表, dashboard, 趋势.

#### Scenario: Proposal describes building a diagnostic feature

- **Given** a proposal text containing investigation keywords (e.g. "异常", "诊断")
- **And** the same text also contains construction markers (e.g. "面板", "新增")
- **When** the keyword scoring logic computes the INVESTIGATION score
- **Then** the INVESTIGATION score SHALL be reduced by 4 points (minimum 0)
- **And** the IMPLEMENTATION score SHALL remain unchanged

#### Scenario: Proposal describes actual debugging without construction markers

- **Given** a proposal text containing investigation keywords (e.g. "排查", "报错")
- **And** the same text does NOT contain any construction markers
- **When** the keyword scoring logic computes the INVESTIGATION score
- **Then** the INVESTIGATION score SHALL be calculated at full weight (no reduction)

#### Scenario: Construction markers have no effect on non-INVESTIGATION scores

- **Given** a proposal text containing construction markers
- **When** the keyword scoring logic computes FIX, IMPLEMENTATION, EVALUATION, or RESEARCH scores
- **Then** those scores SHALL be calculated without any construction-marker adjustment

### Requirement: Verbalization Respects Construction Context

The `_verbalize()` function SHALL check for construction markers when investigation
keywords are present. When both match, the verbalization MUST reflect implementation
semantics rather than investigation semantics.

#### Scenario: Investigation keywords + construction markers → implementation verbalization

- **Given** a message containing both investigation keywords and construction markers
- **When** `_verbalize()` processes the message
- **Then** the verbalization SHALL NOT describe the intent as "排查或调试"
- **And** the verbalization SHALL fall through to the next applicable keyword category

#### Scenario: Investigation keywords alone → investigation verbalization (unchanged)

- **Given** a message containing investigation keywords but NO construction markers
- **When** `_verbalize()` processes the message
- **Then** the verbalization SHALL describe the intent as "排查或调试某个问题" (Chinese)
  or "investigate or debug an issue" (English) — existing behavior preserved
