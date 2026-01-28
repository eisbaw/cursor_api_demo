---
id: TASK-221
title: Build gRPC proxy to intercept judge prompts in transit
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - api-interception
  - grpc
  - best-of-n
dependencies:
  - TASK-102
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-102-judge-prompts.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create a mitmproxy-based tool to intercept and decode the StreamUiBestOfNJudge gRPC calls between Cursor client and api2.cursor.sh server. This would allow capturing:
1. The exact protobuf request with task + diffs
2. The server response with winner + reasoning
3. Any intermediate exec messages during judging

Technical approach:
- Use mitmproxy with grpc-web addon
- Decode aiserver.v1.StreamUiBestOfNJudgeClientMessage and StreamUiBestOfNJudgeServerMessage
- Handle TLS certificate issues (may need to disable pinning)
- Log all judge sessions for analysis
<!-- SECTION:DESCRIPTION:END -->
