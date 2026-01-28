---
id: TASK-301
title: Implement Python Agent Client with Tool Calling Support
status: Done
assignee: []
created_date: '2026-01-28 10:04'
updated_date: '2026-01-28 10:45'
labels:
  - implementation
  - agent
  - tools
  - python
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-7-protobuf-schemas.md
  - reveng_2.3.41/analysis/TASK-110-tool-enum-mapping.md
  - reveng_2.3.41/analysis/TASK-52-toolcall-schema.md
  - reveng_2.3.41/analysis/TASK-2-bidiservice.md
  - reveng_2.3.41/analysis/TASK-129-agent-tool-schemas.md
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create cursor_agent_client.py - a full agent client supporting bidirectional streaming with tool execution (read_file, list_dir, grep, edit_file, run_terminal). Based on analysis of Cursor 2.3.41 protocol.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Agent mode request encoding works (unified_mode=AGENT, is_agentic=true, supported_tools list)
- [x] #2 Bidirectional streaming established with tool call/result exchange
- [x] #3 Basic tools implemented: read_file, list_dir, grep_search
- [x] #4 Tool results sent back to server correctly
- [x] #5 End-to-end agent conversation works
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
3/5 subtasks done. AC#1 and AC#3 met. Blocking: httpx lacks HTTP/2 bidi support for AC#2 and AC#4.

All subtasks complete. cursor_bidi_client.py provides full agent mode with tool calling.
<!-- SECTION:NOTES:END -->
