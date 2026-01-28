---
id: TASK-119
title: Analyze polling backoff and interval strategy
status: Done
assignee: []
created_date: '2026-01-27 22:37'
updated_date: '2026-01-28 06:49'
labels:
  - reverse-engineering
  - protocol
  - performance
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-43-sse-poll-fallback.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:295107-295116'
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When using HTTP/1.0 polling fallback mode, the client must repeatedly poll for responses. Investigate the timing and backoff strategies used.

Key areas to investigate:
- background_agent_polling_config.defaultPollingDelayMs (5000ms default)
- Adaptive polling based on response patterns
- subsample_polling_rate_sec and sample_polling_rate_min configurations
- Poll request throttling under load
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Completed Analysis: Polling Backoff and Interval Strategy

### Summary
Comprehensive analysis of all polling mechanisms, backoff algorithms, and retry strategies in Cursor IDE 2.3.41. Documented 12+ distinct polling subsystems with their timing parameters and backoff logic.

### Key Findings

**Polling Subsystems Identified:**
1. **Background Agent Polling** - 5s default for HTTP/1.0 fallback mode
2. **Statsig Experiments** - 5 min base with 0-20% jitter, 30s minimum
3. **GitHub PR Auto-Refresh** - 30s base with exponential 2^failures backoff (capped at 5 min)
4. **Usage Data Service** - 5 min normal / 30 min on error
5. **Conversation Classification** - 10 min with +/-10% jitter
6. **Git Commit Tracking** - Fixed 10 min interval
7. **Proclist Monitoring** - 1-30 min configurable (default 5 min)
8. **Manual Login Polling** - 500ms for 15s max
9. **Remote Connection Reconnection** - Progressive delays [0, 5, 5, 10...30s] with 3hr grace period
10. **Terminal Extension Host** - 100ms start with 2x backoff to 1s cap
11. **File Watcher** - 5s polling when enabled
12. **Event Loop Heartbeat** - 500ms fixed

**Backoff Algorithm Patterns:**
- Pure exponential (2x multiplier) for generic retry
- Exponential with cap for file operations and remote reconnect
- Exponential with jitter (+/-10%) for GitHub PR refresh
- Step delays [0,5,5,10,10,10,10,10,30] for remote connection
- Slow growth (1.5x) for wait-for-changes operations

**Rate Limiting:**
- HTTP 429 handling with Retry-After header support
- Local rate limiting with sliding window
- Sentry-specific rate limit parsing from x-sentry-rate-limits header
- Default 60s backoff when no retry-after provided

**Server-Side Configuration:**
- `background_agent_polling_config.defaultPollingDelayMs`
- `clientStatsigPollIntervalMs` in chatConfig
- `retry_interceptor_params_config` (maxRetries, baseDelayMs, maxDelayMs)
- `idempotent_stream_config.retry_lookback_window_ms` (2 hours default)
- `extension_monitor_control.subsample_polling_rate_sec` and `sample_polling_rate_min`

### Files Created
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-119-polling-backoff.md`

### Analysis Approach
- Searched for polling, backoff, retry, jitter, and rate limit patterns
- Traced configuration schemas and default values
- Documented exponential backoff implementations
- Mapped server-configurable intervals via Statsig dynamic configs
<!-- SECTION:FINAL_SUMMARY:END -->
