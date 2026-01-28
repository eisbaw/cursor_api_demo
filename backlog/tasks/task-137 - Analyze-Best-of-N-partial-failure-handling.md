---
id: TASK-137
title: Analyze Best-of-N partial failure handling
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - reverse-engineering
  - best-of-n
  - error-handling
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-101-best-of-n-worktrees.md
  - reveng_2.3.41/analysis/TASK-15-parallel-workflows.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how Cursor handles partial failures in Best-of-N execution. Scenarios to explore:
- What happens when some agents complete but others fail or timeout?
- How does gatherMinSuccessPercentage (default 50%) affect result synthesis?
- Does the judge run with fewer candidates if some fail?

Key areas to examine:
- ParallelAgentWorkflowGatherConfig (lines 338220-338258)
- Workflow phase transitions (CHILDREN_RUNNING -> GATHERING -> SYNTHESIZING)
- Error handling in startBestOfNJudge when candidates.length < 2
<!-- SECTION:DESCRIPTION:END -->
