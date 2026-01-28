---
id: TASK-301
title: Implement Python Agent Client with Tool Calling Support
status: To Do
assignee: []
created_date: '2026-01-28 10:04'
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
- [ ] #1 Agent mode request encoding works (unified_mode=AGENT, is_agentic=true, supported_tools list)
- [ ] #2 Bidirectional streaming established with tool call/result exchange
- [ ] #3 Basic tools implemented: read_file, list_dir, grep_search
- [ ] #4 Tool results sent back to server correctly
- [ ] #5 End-to-end agent conversation works
<!-- AC:END -->
