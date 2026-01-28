---
id: TASK-273
title: Investigate AutopilotService response types and sub-agent architecture
status: To Do
assignee: []
created_date: '2026-01-28 07:17'
labels:
  - reverse-engineering
  - protobuf
  - autopilot
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-7-protobuf-schemas.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The AutopilotService uses a sophisticated response structure with sub-agents (Terminal, Web, Programmer). Located at line ~815685. Key messages include:
- AutopilotResponse with action, done, stream_thought, start_sub_agent, done_sub_agent
- AutopilotActionResponse with terminal_command, web_search, ask_user, ask_oracle, file_edit, open_file
- SubAgent enum with TERMINAL_AGENT, WEB_AGENT, PROGRAMMER_AGENT

Investigate how these sub-agents coordinate and what triggers their invocation.
<!-- SECTION:DESCRIPTION:END -->
