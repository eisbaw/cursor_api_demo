---
id: TASK-288
title: Investigate usage event pricing calculation
status: To Do
assignee: []
created_date: '2026-01-28 07:28'
labels:
  - reverse-engineering
  - cursor-ide
  - billing
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-130-spend-limits.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up from TASK-130. Analyze how costs are calculated for different UsageEventKind types. The TokenUsage schema includes total_cents field but the calculation logic needs investigation. Look for cost multipliers, model-specific pricing, and how cache tokens affect pricing.
<!-- SECTION:DESCRIPTION:END -->
