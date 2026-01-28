---
id: TASK-120
title: Document HTTP keepalive and ping configurations
status: Done
assignee: []
created_date: '2026-01-27 22:37'
updated_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - protocol
  - networking
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-43-sse-poll-fallback.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:295077-295084'
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cursor has specific keepalive configurations for both HTTP/1.1 and HTTP/2. Document these settings and their impact on connection management.

Key areas to investigate:
- http2_ping_config schema and defaults
- http1_keepalive_config schema and defaults
- cursor.debug.timeoutPrevention setting for debugging
- Connection pool management and reuse
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document http2_ping_config schema and defaults
- [x] #2 Document http1_keepalive_config schema and defaults
- [x] #3 Document cursor.debug.timeoutPrevention setting for debugging
- [x] #4 Document internal socket keepalive protocol constants
- [x] #5 Document agent heartbeat configuration
- [x] #6 Document retry interceptor configuration
- [x] #7 Identify connection timeout thresholds
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Documented comprehensive HTTP keepalive and ping configurations in Cursor IDE 2.3.41:

### Internal Protocol Layer
- **Keepalive Interval**: 5 seconds for IPC socket protocol
- **Timeout Detection**: 20 seconds threshold with load awareness
- **Message Type 9**: Dedicated KeepAlive message type
- **Reconnection Grace**: 3 hours (long) / 5 minutes (short)

### HTTP/2 Ping Configuration
- Schema: `http2_ping_config` with `pingIdleConnection`, `pingIntervalMs`, `pingTimeoutMs`, `idleConnectionTimeoutMs`
- Feature flag: `http2_disable_pings` (default: false)
- All values nullable/configurable via server config

### HTTP/1.1 Keepalive
- Schema: `http1_keepalive_config` with `keepAliveInitialDelayMs`
- Feature flag: `http1_keepalive_disabled` (default: false)

### Agent Heartbeat
- Client heartbeat: 5 second interval
- Background composer ping: 10 seconds default (configurable via `windowInWindowPingIntervalMs`)

### Debugging Support
- `cursor.debug.timeoutPrevention` setting: local_only/always/never
- Prevents breakpoint debugging from triggering HTTP/2 ping timeouts

### Retry Interceptor
- Retriable errors: Unavailable, Internal, DeadlineExceeded
- Configurable: maxRetries, baseDelayMs, maxDelayMs
- Headers: X-Cursor-RetryInterceptor-* for server-side control

### Key Locations
- Protocol constants: Line 794916-794919
- HTTP/2 config: Lines 295077-295083, 295389-295397
- Debug setting: Lines 450685-450692
- Agent heartbeat: Lines 466025-466043

Analysis written to: reveng_2.3.41/analysis/TASK-120-http-keepalive.md
<!-- SECTION:FINAL_SUMMARY:END -->
