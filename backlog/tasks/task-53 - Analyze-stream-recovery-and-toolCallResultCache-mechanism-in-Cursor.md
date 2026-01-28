---
id: TASK-53
title: Analyze stream recovery and toolCallResultCache mechanism in Cursor
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-28 07:09'
labels: []
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze the stream recovery and toolCallResultCache mechanism in Cursor IDE 2.3.41 to understand how tool execution results are cached and replayed during stream reconnection.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Comprehensive reverse engineering of Cursor IDE 2.3.41's idempotent streaming and tool result caching mechanism.

### Key Findings

1. **Idempotent Stream Protocol**: Cursor uses a bidirectional streaming protocol (`StreamUnifiedChatWithToolsIdempotent`) with sequence numbers and server acknowledgments for exactly-once message delivery.

2. **toolCallResultCache Implementation**:
   - Caches tool execution results keyed by `toolCallId`
   - Results stored as `ClientSideToolV2Result` protobuf messages
   - Serialized to JSON for persistence, deserialized on load
   - Prevents duplicate tool execution during stream recovery

3. **Stream Recovery Mechanism**:
   - `playbackChunks` stores unacknowledged messages for replay
   - `idempotencyEventId` tracks last processed server event
   - Auto-resume logic checks for interrupted streams within 2-hour window
   - HTTP headers (`x-idempotency-key`, `x-idempotency-event-id`, `x-idempotent-encryption-key`) used for session identification

4. **Cache Invalidation**:
   - Cleared when new text/thinking response received
   - Cleared on deserialization failure
   - Implicitly cleared when stream completes

5. **Degraded Mode**: Server can indicate reconnection unavailable, disabling retry logic

### Files Created
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-53-stream-recovery.md`

### Follow-up Tasks Created
- TASK-251: Analyze idempotent stream encryption mechanism
- TASK-252: Investigate NAL stall detection and recovery in depth
- TASK-253: Analyze subagent interaction with stream recovery
<!-- SECTION:FINAL_SUMMARY:END -->
