---
id: TASK-215
title: Investigate server-side judge prompt reconstruction
status: To Do
assignee: []
created_date: '2026-01-28 06:54'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - best-of-n
  - prompts
dependencies: []
references:
  - TASK-103
  - reveng_2.3.41/analysis/TASK-103-tournament-prompts.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The tournament evaluation happens server-side via StreamUiBestOfNJudge RPC. The client sends:
- task (original user prompt)
- candidates (array of {composerId, diff})

And receives:
- winnerComposerId
- reasoning

The actual comparison prompts used by the judge model (gpt-5.1-codex-high) are not visible in client code. 

Investigation avenues:
1. Network traffic capture during tournament to see request/response payloads
2. Look for server-side code in other decompiled components
3. Analyze the reasoning field format to infer prompt structure
4. Check for any prompt templates in the codebase

Related to TASK-103 findings.
<!-- SECTION:DESCRIPTION:END -->
