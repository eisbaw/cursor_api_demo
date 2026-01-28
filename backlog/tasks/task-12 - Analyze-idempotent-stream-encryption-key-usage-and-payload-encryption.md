---
id: TASK-12
title: Analyze idempotent stream encryption key usage and payload encryption
status: Done
assignee: []
created_date: '2026-01-27 14:07'
updated_date: '2026-01-28 07:22'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analysis of the x-idempotent-encryption-key header, payload encryption mechanisms, and how encryption keys are used in Cursor IDE's idempotent streaming protocol.

Key findings:
- 32-byte (256-bit) encryption key generated client-side via crypto.getRandomValues()
- Key is Base64-URL encoded and sent in HTTP header
- Encryption appears to be SERVER-SIDE, not client-side
- Enables server to cache encrypted stream chunks for resumption
- Related to persist_idempotent_stream_state feature gate
- Auto-resume mechanism with configurable lookback window (default 2 hours)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Analyzed x-idempotent-encryption-key header usage
- [x] #2 Documented payload encryption mechanism
- [x] #3 Identified server-side vs client-side encryption
- [x] #4 Documented key generation (32-byte, crypto.getRandomValues)
- [x] #5 Documented key transmission (Base64-URL in HTTP header)
- [x] #6 Analyzed related protobuf messages
- [x] #7 Documented auto-resume mechanism
- [x] #8 Created comprehensive analysis document
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

**File:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-12-idempotent-encryption.md`

### Key Findings

1. **Key Generation**: Client generates 32-byte random key via `crypto.getRandomValues()`, encoded as URL-safe Base64

2. **Header Transmission**: Key sent as `x-idempotent-encryption-key` HTTP header alongside `x-idempotency-key` and `x-idempotency-event-id`

3. **Server-Side Encryption**: No client-side encryption/decryption code found - the key is for SERVER-SIDE encryption of cached stream state

4. **Protocol**: BiDi streaming using protobuf messages `StreamUnifiedChatRequestWithToolsIdempotent` and `StreamUnifiedChatResponseWithToolsIdempotent`

5. **State Persistence**: Controlled by `persist_idempotent_stream_state` feature gate; state includes key, seqno, event ID, and playback chunks

6. **Auto-Resume**: Streams can auto-resume within 2-hour window (configurable via `idempotent_stream_config.retry_lookback_window_ms`)

7. **Degraded Mode**: Server can signal `isDegradedMode: true` to disable resumption
<!-- SECTION:FINAL_SUMMARY:END -->
