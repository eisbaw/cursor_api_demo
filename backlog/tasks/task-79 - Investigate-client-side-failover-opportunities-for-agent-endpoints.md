---
id: TASK-79
title: Investigate client-side failover opportunities for agent endpoints
status: Done
assignee: []
created_date: '2026-01-27 14:51'
updated_date: '2026-01-28 07:29'
labels: []
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-79-endpoint-failover.md
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigated client-side failover mechanisms in Cursor IDE 2.3.41 for agent endpoints. Found retry interceptor pattern, exponential backoff, idempotent streaming with reconnection, and Statsig-specific fallback URL system. Agent endpoints lack automatic failover - identified as improvement opportunity.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Analyzed endpoint failover mechanisms in Cursor IDE 2.3.41 beautified source.

### Key Findings:
1. **Agent Endpoints**: Multiple geo-based endpoints (agent.api5.cursor.sh, gcpp-uswest, gcpp-eucentral) but no automatic failover between them
2. **Retry Interceptor**: Server-controlled retry via X-Cursor-RetryInterceptor headers with configurable maxRetries, baseDelayMs, maxDelayMs
3. **Retryable Errors**: HTTP 408, 500, 502, 503, 504, 522, 524, 599; gRPC Unavailable, Internal, DeadlineExceeded
4. **Exponential Backoff**: 500ms base, 30s max delay with square growth
5. **Idempotent Streaming**: Reconnection support with 2-hour lookback window, sequence numbering, playback chunks
6. **Statsig Fallback**: Robust DNS-based fallback system exists but only for Statsig SDK, not agent endpoints

### Failover Gaps:
- No automatic agent endpoint switching on failure
- Static region selection
- Server-controlled retry parameters limit client autonomy
- No circuit breaker pattern

### Output:
Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-79-endpoint-failover.md`
<!-- SECTION:FINAL_SUMMARY:END -->
