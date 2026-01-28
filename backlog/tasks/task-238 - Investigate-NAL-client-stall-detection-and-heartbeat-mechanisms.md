---
id: TASK-238
title: Investigate NAL client stall detection and heartbeat mechanisms
status: To Do
assignee: []
created_date: '2026-01-28 07:02'
labels:
  - reverse-engineering
  - streaming
  - reliability
  - cursor-2.3.41
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The NAL (Native Agent Layer) client includes sophisticated stream health monitoring mechanisms that should be documented:

1. **Stall Detector** (`@anysphere/agent-client:stall-detector`):
   - Threshold: 10 seconds of no activity
   - Metrics: `agent_client.stream.stall.count`, `agent_client.stream.stall.duration_ms`
   - Tracks activity type and message type

2. **Client Heartbeat**:
   - Interval: 5 seconds
   - Sends `clientHeartbeat` messages via `iBe` protobuf
   - Maintains connection during idle periods

3. **Areas to investigate**:
   - How does stall detection trigger recovery?
   - What metrics are emitted and how are they used?
   - How does heartbeat interact with server-side timeout handling?
   - What happens when stall is detected during tool execution?

Reference: Line ~465749-465850 in workbench.desktop.main.js
Related: TASK-46
<!-- SECTION:DESCRIPTION:END -->
