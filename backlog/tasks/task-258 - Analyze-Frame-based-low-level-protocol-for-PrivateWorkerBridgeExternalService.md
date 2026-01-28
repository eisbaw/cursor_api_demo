---
id: TASK-258
title: Analyze Frame-based low-level protocol for PrivateWorkerBridgeExternalService
status: To Do
assignee: []
created_date: '2026-01-28 07:09'
labels:
  - reverse-engineering
  - protobuf
  - cursor
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-25-agent-v1-protobuf.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The PrivateWorkerBridgeExternalService uses Frame messages with KIND_REQUEST/RESPONSE/ERROR for BiDi streaming. This appears to be a lower-level RPC framing layer. Investigate how this bridges to workers.
<!-- SECTION:DESCRIPTION:END -->
