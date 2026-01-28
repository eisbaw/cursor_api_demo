---
id: TASK-138
title: Investigate server-side Best-of-N judge prompts and criteria
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - reverse-engineering
  - best-of-n
  - server-side
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-101-best-of-n-worktrees.md
  - reveng_2.3.41/analysis/TASK-57-best-of-n-judge.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Best-of-N judge logic runs entirely server-side. While we cannot see the actual prompts, investigate:
- What information is sent to the server (diffs, task description)?
- How the reasoning string is structured (summary + justification)?
- What the exec_server_message flow enables (tool execution during judging)?

This may require API traffic analysis or inference from the client's expectations. The judge can apparently run tools during evaluation (agentExecProvider integration).
<!-- SECTION:DESCRIPTION:END -->
