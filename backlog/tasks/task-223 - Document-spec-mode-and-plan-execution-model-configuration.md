---
id: TASK-223
title: Document spec mode and plan execution model configuration
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - plan-system
  - feature-gates
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-97-plan-review.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Discovered during TASK-97 analysis that plan mode has specialized model configuration:
- Feature gate: "spec_mode" controls availability
- Model config key: "plan-execution"
- Proto field: "supports_plan_mode" (no: 22)
- planExecUseChatModel and planExecMode reactive storage fields

Need to investigate:
- How spec mode differs from regular plan mode
- Model selection for plan execution vs plan creation
- Feature gating mechanism (experimentService.checkFeatureGate)
- Plan execution model config migration

Key locations:
- Line ~309217: isSpecModeEnabled()
- Line ~165265: supports_plan_mode proto field
- Line ~182705-182706: planExecUseChatModel, planExecMode storage
- Line ~268017-268064: Model config migration for plan-execution
<!-- SECTION:DESCRIPTION:END -->
