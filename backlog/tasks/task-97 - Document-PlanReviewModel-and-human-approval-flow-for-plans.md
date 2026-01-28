---
id: TASK-97
title: Document PlanReviewModel and human approval flow for plans
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:55'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Documented PlanReviewModel and human approval flow for plans in Cursor IDE 2.3.41.

Key findings:
- PlanReviewModel (UJe) extends base ReviewModel (qht) class
- Three-state machine: NONE -> REQUESTED -> DONE
- User options: APPROVE, REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY, EDIT
- Plans are non-blocking (isExecutionBlocking=false) unlike terminal/MCP reviews
- Plan approval triggers acceptPlan() which registers build and starts execution
- Plan rejection opens feedback input for alternative instructions
- Edit option opens plan in editor for manual modification
- builtBy registry field tracks executed plans (empty = pending approval)
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Documented the PlanReviewModel class and human approval flow for AI-generated plans.

### Key Components Identified:
- **PlanReviewModel (UJe)**: Extends base ReviewModel, handles plan-specific approval logic
- **ToolCallHumanReviewStatus (Zv)**: NONE/REQUESTED/DONE state machine
- **PlanToolHumanReviewOption (HW)**: APPROVE/REJECT/EDIT user choices
- **ToolCallHumanReviewService (JW)**: Service managing all review models
- **ComposerPlanService (N7)**: Plan lifecycle and execution management

### Architecture Highlights:
- Plans use CREATE_PLAN tool type in conversation bubbles
- Non-blocking review (unlike terminal/MCP which block execution)
- Approval source tracked as "manual" vs "auto" for analytics
- Plan registry tracks builds via builtBy field (empty = pending)

### Analysis file: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-97-plan-review.md`
<!-- SECTION:FINAL_SUMMARY:END -->
