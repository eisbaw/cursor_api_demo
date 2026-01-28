---
id: TASK-2
title: Analyze BidiService bidirectional streaming protocol
status: Done
assignee: []
created_date: '2026-01-27 13:37'
updated_date: '2026-01-28 07:02'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate aiserver.v1.BidiService which handles bidirectional streaming communication. Understand the message format, handshake protocol, and how it differs from the previous unidirectional streaming in ChatService. Find where this is used in the agent workflow.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive analysis of BidiService bidirectional streaming protocol in Cursor IDE 2.3.41.

### Key Findings

1. **BidiService.BidiAppend is Unary**: Despite the naming, `aiserver.v1.BidiService.BidiAppend` is actually a unary RPC method, not bidirectional streaming. True bidi streaming happens through `StreamUnifiedChatWithTools` and `StreamUnifiedChatWithToolsIdempotent`.

2. **Three-Tier Streaming Architecture**:
   - Tier 1: True BiDi (HTTP/2)
   - Tier 2: SSE fallback (Server-Sent Events)
   - Tier 3: Polling fallback using BidiPollRequest/BidiPollResponse

3. **Idempotent Streaming Protocol**: Implements automatic reconnection with:
   - Idempotency keys for deduplication
   - Sequence numbers for ordering
   - Playback chunks for unacknowledged message replay
   - Encryption keys for stream security

4. **Stall Detection**: Monitors stream health with metrics for stall count, duration, and activity tracking including heartbeat support.

5. **Error Handling**: Comprehensive ErrorDetails type with 53+ error codes covering auth, rate limiting, resource exhaustion, and user actions.

### Protobuf Types Documented
- BidiRequestId, BidiAppendRequest, BidiAppendResponse
- BidiPollRequest, BidiPollResponse
- StreamUnifiedChatRequestWithToolsIdempotent
- StreamUnifiedChatResponseWithToolsIdempotent
- WelcomeMessage (with degraded mode flag)
- ErrorDetails enum

### Files Created
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-2-bidiservice.md`
<!-- SECTION:FINAL_SUMMARY:END -->
