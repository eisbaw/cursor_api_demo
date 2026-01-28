---
id: TASK-89
title: Analyze SubagentPersistedState and nested agent conversations
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 06:48'
labels:
  - protobuf
  - agent
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Document how subagent states are managed within ConversationStateStructure. Includes computer_use and custom subagent types with their own nested conversation state.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed analysis of SubagentPersistedState and nested agent conversations in Cursor IDE 2.3.41.

Key findings documented in `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-89-subagent-state.md`:

1. **SubagentPersistedState Structure**: Each subagent maintains a complete `ConversationStateStructure` with conversation_state, created_timestamp_ms, last_used_timestamp_ms, and subagent_type fields.

2. **Recursive Nesting**: ConversationStateStructure includes a `subagent_states` map (field 16) enabling recursive subagent nesting with a hard limit of 10 levels to prevent infinite recursion.

3. **Type Systems**: Two parallel type systems exist - agent-level (unspecified, computer_use, custom) and server-level (deep_search, fix_lints, task, spec).

4. **Parent-Child Relationships**: Tracked via `subagentInfo.parentComposerId` with hierarchy traversal supporting up to 10 levels and circular reference detection.

5. **Background Subagent Lifecycle**: States include RUNNING, COMPLETED, FAILED, ABORTED with transcript and status files for persistence.

6. **State Sharing**: File changes propagate from subagents to parent composers with metadata marking origin; approvals route through parent's approval service.

7. **Custom Subagents**: Defined via markdown files in `.cursor/agents/` with frontmatter specifying name, description, model, tools, and permission mode (default or readonly).
<!-- SECTION:FINAL_SUMMARY:END -->
