---
id: TASK-297
title: Analyze idempotent streaming protocol for reliability patterns
status: To Do
assignee: []
created_date: '2026-01-28 07:29'
labels:
  - reverse-engineering
  - streaming
  - reliability
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-79-endpoint-failover.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cursor 2.3.41 implements idempotent streaming with reconnection support for the composer/agent. This uses:
- x-idempotency-key, x-idempotency-event-id, x-idempotent-encryption-key headers
- Sequence number acknowledgment (seqnoAck)
- Playback chunks for message replay
- 2-hour lookback window (retry_lookback_window_ms: 7200000)
- Degraded mode detection

Deep dive into the StreamUnifiedChatWithToolsIdempotent RPC to understand:
1. How playback chunks work
2. The encryption key usage
3. When degraded mode triggers
4. Error recovery flow

Code locations: lines 488772-488960, 466453-466466
<!-- SECTION:DESCRIPTION:END -->
