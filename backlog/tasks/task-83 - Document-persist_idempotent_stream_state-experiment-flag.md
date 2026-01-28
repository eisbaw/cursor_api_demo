---
id: TASK-83
title: Document persist_idempotent_stream_state experiment flag
status: Done
assignee: []
created_date: '2026-01-27 22:34'
updated_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - experiments
  - feature-flags
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The tool batching code references an experiment flag called 'persist_idempotent_stream_state' (line 484524). Document:

- What this experiment controls
- How it affects tool result caching (toolCallResultCache)
- Impact on replay/resume of tool streams
- Whether it's enabled by default
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Documented the `persist_idempotent_stream_state` experiment flag which enables persistent storage of idempotent stream state for crash recovery.

### Key Findings

1. **Flag Configuration**: Client-side flag, disabled by default (line 294169)

2. **State Persisted**:
   - `idempotencyKey`: UUID for server deduplication
   - `idempotencyEventId`: Last processed event ID
   - `idempotentEncryptionKey`: 32-byte encryption key
   - `nextSeqno`: Client chunk sequence counter
   - `playbackChunks`: Unacknowledged chunks as [seqno, JSON] pairs
   - `toolCallResultCache`: Cached tool results keyed by toolCallId

3. **Storage Mechanism**: Via ReactiveStorageService, scoped to workspace or application

4. **Reconnection Behavior**:
   - Immediate retry on network failure with 1-second delay
   - Auto-resume on IDE startup via `_autoResumeInterruptedStreams()`
   - 2-hour default lookback window (`idempotent_stream_config.retry_lookback_window_ms`)

5. **Protocol**: Uses HTTP headers (`x-idempotency-key`, `x-idempotency-event-id`, `x-idempotent-encryption-key`) and BiDi streaming with seqno acknowledgments

6. **Related Flag**: Requires `idempotent_agentic_composer` to enable reliable streaming infrastructure

### Analysis Document
Created: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-83-persist-idempotent.md`
<!-- SECTION:FINAL_SUMMARY:END -->
