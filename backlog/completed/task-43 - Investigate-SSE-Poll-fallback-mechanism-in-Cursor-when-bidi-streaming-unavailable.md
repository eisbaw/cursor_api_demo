---
id: TASK-43
title: >-
  Investigate SSE/Poll fallback mechanism in Cursor - when bidi streaming
  unavailable
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-28 07:17'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Investigation Summary: SSE/Poll Fallback Mechanism in Cursor IDE 2.3.41

### Protocol Hierarchy Discovered
Cursor implements a three-tier fallback system for streaming:

1. **HTTP/2 BiDi Streaming** (default) - Full bidirectional gRPC streaming
2. **HTTP/1.1 SSE** - Server-Sent Events fallback with BidiAppend for client data
3. **HTTP/1.0 Polling** - Long polling as last resort for restrictive proxies

### Key Protobuf Messages
- `BidiRequestId` - Stream identifier for SSE mode
- `BidiPollRequest` - Poll request with request_id and start_request flag
- `BidiPollResponse` - Poll response with seqno, data, and eof flag
- `BidiAppendRequest` - Client-to-server data in SSE mode
- `WelcomeMessage` - Server signals degraded mode via is_degraded_mode field

### Configuration Controls
- `cursor.general.disableHttp2` - Forces HTTP/1.1 mode
- `cursor.general.disableHttp1SSE` - Forces polling mode
- `Http2Config` enum - Server-side protocol enforcement
- HTTP Compatibility Mode UI in settings (http2, http1.1, http1.0)

### Idempotent Streaming (Feature-gated)
- `idempotent_agentic_composer` - Enables reliable streaming
- `persist_idempotent_stream_state` - Enables stream state persistence
- Uses x-idempotency-key, x-idempotency-event-id, x-idempotent-encryption-key headers
- 2-hour lookback window for auto-resume of interrupted streams
- 1-second delay between reconnection attempts

### Service Endpoint Pattern
Multiple services follow the same three-method pattern:
- `StreamXxx` - BiDiStreaming
- `StreamXxxSSE` - ServerStreaming (SSE fallback)
- `StreamXxxPoll` - ServerStreaming (Polling fallback)

Applied to: StreamUnifiedChatWithTools, StreamBugBotAgentic, StreamComposerEnhancer, StreamStt, Run (agent), etc.

### Key Source Locations
- Protocol buffers: Lines 439107-439279
- Service definitions: Lines 823808-823831, 466434-466469
- Settings: Lines 450674-450698
- Reliable stream: Lines 488771-488960
- Auto-resume: Lines 945194-945210

### Analysis Document
Updated: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-43-sse-poll-fallback.md`
<!-- SECTION:FINAL_SUMMARY:END -->
