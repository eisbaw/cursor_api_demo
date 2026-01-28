---
id: TASK-129
title: >-
  Extract tool schema definitions for agent-related tools (TASK, TASK_V2,
  AWAIT_TASK, BACKGROUND_COMPOSER_FOLLOWUP)
status: Done
assignee: []
created_date: '2026-01-28 00:10'
updated_date: '2026-01-28 07:28'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Extracted comprehensive schema definitions for TASK, TASK_V2, AWAIT_TASK, and BACKGROUND_COMPOSER_FOLLOWUP tools from Cursor IDE 2.3.41.

## Key Findings

### Tool Enum Values (ClientSideToolV2)
- TASK = 32 (original)
- AWAIT_TASK = 33 (synchronization)
- TASK_V2 = 48 (enhanced)
- BACKGROUND_COMPOSER_FOLLOWUP = 24

### Schema Highlights

**TASK (v1)**: Parameters include task_description, task_title, async flag, allowed_write_directories, model_override, and max_mode_override. Results are either CompletedTaskResult (with summary, file_results, abort/error flags) or AsyncTaskResult (with task_id).

**TASK_V2**: Simpler params (description, prompt, subagent_type, model) with typed subagent selection supporting unspecified, computer_use, and custom types. Returns agent_id and is_background flag.

**AWAIT_TASK**: Takes array of task IDs, returns TaskResultItem array with completed results and missing_task_ids. Handler uses Promise.all for concurrent waiting.

**BACKGROUND_COMPOSER_FOLLOWUP**: Params are proposed_followup and bc_id. Requires user approval ("Send to background composer" / "Skip").

### SubagentType System
- aiserver.v1 enum: UNSPECIFIED, DEEP_SEARCH, FIX_LINTS, TASK, SPEC
- agent.v1 oneof: unspecified, computer_use, custom (with name field)

### Agent Spawning
- SubagentInfo tracks type, id, type-specific params, and parent_request_id for hierarchy
- CustomSubagent supports user-defined agents with full_path, name, description, tools, model, prompt, and permission_mode

## Output
Analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-129-agent-tool-schemas.md`
<!-- SECTION:FINAL_SUMMARY:END -->
