---
id: TASK-84
title: Analyze server-side idempotent stream handling (inferred from client behavior)
status: Done
assignee: []
created_date: '2026-01-27 22:34'
updated_date: '2026-01-28 06:40'
labels:
  - reverse-engineering
  - security
  - protocol
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-39-stream-resumption.md
  - reveng_2.3.41/analysis/TASK-84-idempotent-streams.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Based on TASK-39 analysis of client-side idempotent streaming, investigate what server-side handling can be inferred:

1. How does server use x-idempotency-key for deduplication?
2. What is the server-side storage mechanism for stream state?
3. How long does server retain idempotency state?
4. What happens with conflicting seqno on reconnection?
5. How does server handle partial chunk re-delivery?

This could inform potential replay attack vectors or protocol weaknesses.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete: Server-Side Idempotent Stream Handling

### Key Findings

1. **Server Deduplication via x-idempotency-key**
   - Server maintains session state keyed by UUID
   - Validates encryption key on reconnection
   - Session stored for at least 2 hours (inferred from client lookback window)

2. **Bidirectional Sequence Number Protocol**
   - Client assigns incrementing seqno to each chunk
   - Server sends seqno_ack after processing
   - On reconnection, server deduplicates already-processed chunks

3. **Event ID Cursor Position**
   - Server assigns event_id to each response chunk
   - Client sends last event_id on reconnection via header
   - Server resumes from after the specified position

4. **Degraded Mode Signal**
   - Server sends WelcomeMessage.is_degraded_mode = true when state unavailable
   - Client disables reconnection, clears local state
   - Prevents amplification during server stress

5. **Non-Retriable Error Handling**
   - Server attaches ErrorDetails to indicate permanent failures
   - Client aborts without retry when ErrorDetails present
   - Covers auth errors, rate limits, permission denials

### Security Observations

- 256-bit encryption key provides session binding
- Duplicate seqno values acknowledged but not reprocessed
- Local state tampering could allow content re-delivery requests
- Server-side validation of encryption key prevents session hijacking

### Deliverable

Analysis written to: `reveng_2.3.41/analysis/TASK-84-idempotent-streams.md`
<!-- SECTION:FINAL_SUMMARY:END -->
