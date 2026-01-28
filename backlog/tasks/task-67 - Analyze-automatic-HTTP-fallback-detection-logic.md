---
id: TASK-67
title: Analyze automatic HTTP fallback detection logic
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-28 07:09'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyzed HTTP/2 to HTTP/1.1 fallback detection logic in Cursor IDE 2.3.41. Key finding: Cursor implements a **manual** fallback system rather than automatic protocol detection. Users must configure HTTP Compatibility Mode based on network diagnostic results.

Key components analyzed:
- Network diagnostics panel (Mmu function)
- HTTP/2, SSE, and polling protocol variants
- LostConnection error handling and stream resumption
- Stall detection system
- Server-side Http2Config enum
- Retry interceptor configuration

The system provides three protocol tiers (HTTP/2, HTTP/1.1 SSE, HTTP/1.0 polling) with comprehensive diagnostics, but does NOT automatically switch between them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Analyzed HTTP/2 to HTTP/1.1 fallback detection logic
- [x] #2 Documented protocol detection mechanisms
- [x] #3 Identified automatic fallback triggers
- [x] #4 Analyzed network capability detection system
- [x] #5 Documented fallback configuration options
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete: HTTP Fallback Detection Logic

### Key Finding
Cursor implements a **manual HTTP fallback system**, NOT automatic protocol detection. Users must configure HTTP Compatibility Mode in Settings > Network based on diagnostic results.

### Components Analyzed
1. **Network Diagnostics Panel** (Mmu function, lines 911491-911757)
   - DNS lookup, HTTP/2 ping, TLS certificate, unary RPC, streaming, bidirectional tests
   - Detects proxy buffering (first chunk > 2000ms threshold)
   - Identifies incomplete responses (< 5 valid chunks)

2. **Protocol Tiers**
   - HTTP/2: BiDiStreaming (default, optimal latency)
   - HTTP/1.1: Server-Sent Events (SSE) fallback
   - HTTP/1.0: Long polling (most restrictive environments)

3. **Configuration Keys**
   - `cursor.general.disableHttp2` - Forces HTTP/1.x
   - `cursor.general.disableHttp1SSE` - Forces polling mode

4. **Automatic Behaviors**
   - Stream resumption on LostConnection (same protocol)
   - Stall detection with metrics
   - Retry on transient errors (Unavailable, Internal, DeadlineExceeded)

5. **Server-Side Control**
   - Http2Config enum exists (FORCE_ALL_DISABLED, FORCE_BIDI_DISABLED, etc.)
   - Infrastructure defined but active enforcement not found in client code

### Output
Analysis written to: `reveng_2.3.41/analysis/TASK-67-http-fallback.md`

### Related Tasks
- TASK-43: SSE/Poll Fallback Mechanism
- TASK-118: Server-Side Http2Config Enforcement Logic
- TASK-119: Polling Backoff Strategy
- TASK-120: HTTP Keepalive Configuration
<!-- SECTION:FINAL_SUMMARY:END -->
