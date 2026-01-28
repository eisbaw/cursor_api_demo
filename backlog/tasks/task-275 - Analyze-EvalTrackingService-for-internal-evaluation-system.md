---
id: TASK-275
title: Analyze EvalTrackingService for internal evaluation system
status: To Do
assignee: []
created_date: '2026-01-28 07:18'
labels:
  - reverse-engineering
  - protobuf
  - evaluation
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-7-protobuf-schemas.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cursor has an internal evaluation system for testing AI models and features. Key components discovered:
- EvalTrackingService (line ~820999)
- EvalRunStatus enum: PENDING, BUILDING, SUBMITTED, RUNNING, FINISHED, FAILED, KILLED
- EvalRolloutStatus enum for rollout management
- EvalSummary, EvalRunRecord, RunMetricItem messages

This system appears to be used for A/B testing and model evaluation internally. Understanding it could reveal how Cursor validates their AI features.
<!-- SECTION:DESCRIPTION:END -->
