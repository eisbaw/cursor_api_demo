---
id: TASK-74
title: Analyze Plan creation and management schemas (CreatePlan tool) in Cursor
status: Done
assignee: []
created_date: '2026-01-27 14:51'
updated_date: '2026-01-27 22:36'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Analyzed the CreatePlan tool schemas and plan management system in Cursor IDE (v2.3.41).

### Key Findings

**Two Protocol Domains:**
- `aiserver.v1` - Server-side API with `CreatePlanParams` (plan, title, todos, steps, etc.) and `CreatePlanResult` (accepted/rejected/modified oneof)
- `agent.v1` - Agent-side tool calls with `CreatePlanArgs` (plan, todos, overview, name) and `CreatePlanResult` (success/error oneof)

**Plan File Format:**
- Files stored as `{name}-{uuid8}.plan.md` in `~/.cursor/plans/`
- YAML frontmatter with `name`, `overview`, and `todos` array
- Detection via `.plan.md` extension or `cursorPlan` URI scheme

**Service Architecture:**
- `ComposerPlanService` (N7) - High-level plan operations
- `PlanStorageService` (Tys) - Low-level file/registry operations
- `PlanReviewModel` (UJe) - Human review handling

**Plan Execution Flow:**
1. AI creates plan via CreatePlan tool call
2. Plan file created/updated via ComposerPlanService
3. Optional human review via PlanReviewModel
4. Execution spawns new agent with plan as context
5. Agent receives prompt with assigned todos

**Feature Gate:**
- `file_based_plan_edits` controls multi-plan mode (default: false)
- Single-plan mode: updates existing plan per composer
- Multi-plan mode: always creates new plan files

### Output
Analysis written to: `reveng_2.3.41/analysis/TASK-74-plan-schemas.md`

### Follow-up Tasks Created
- TASK-93: Investigate Plan modification flow (old_str/new_str)
- TASK-95: Analyze Todo dependency resolution and ordering
- TASK-97: Document PlanReviewModel and human approval flow
<!-- SECTION:FINAL_SUMMARY:END -->
