---
id: TASK-117
title: Investigate BidiAppend mechanism for SSE mode client-to-server data
status: Done
assignee: []
created_date: '2026-01-27 22:37'
updated_date: '2026-01-28 06:42'
labels:
  - reverse-engineering
  - protocol
  - networking
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-43-sse-poll-fallback.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:439137-439176'
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When operating in SSE fallback mode, the client cannot use bidirectional streaming. Investigate how BidiAppend unary calls are used to send client data to the server in this mode.

Key areas to investigate:
- BidiAppend request/response schemas (aiserver.v1.BidiAppendRequest, aiserver.v1.BidiAppendResponse)
- How append_seqno is used for ordering
- Relationship between BidiRequestId and active SSE streams
- Error handling and retry logic for append failures
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 BidiAppend schema documented with field types and purposes
- [ ] #2 SSE mode communication flow documented
- [ ] #3 Sequence number semantics explained
- [ ] #4 Relationship to BidiPollRequest/Response documented
- [ ] #5 HTTP Compatibility Mode configuration documented
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed analysis of BidiAppend mechanism for SSE mode client-to-server data.

Key findings:
1. BidiAppend is a unary RPC in aiserver.v1.BidiService that enables client-to-server communication when HTTP/2 bidirectional streaming is unavailable
2. In SSE mode, server-to-client uses ServerStreaming (SSE) while client-to-server uses separate BidiAppend unary calls
3. BidiAppendRequest contains: data (serialized payload), request_id (links to SSE stream), append_seqno (ordering)
4. BidiAppendResponse is empty - acknowledgment only
5. Sequence numbers (append_seqno) enable ordering and deduplication of client messages
6. Configuration via cursor.general.disableHttp2 and cursor.general.disableHttp1SSE settings
7. Poll mode (HTTP/1.0) uses BidiPollRequest/BidiPollResponse as additional fallback
8. In Cursor 2.3.41, this infrastructure exists but HTTP/2 BiDiStreaming or idempotent streaming is preferred

Output: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-117-bidiappend-sse.md
<!-- SECTION:FINAL_SUMMARY:END -->
