---
id: TASK-80
title: Investigate rate limiting schemas related to authentication in Cursor
status: Done
assignee: []
created_date: '2026-01-27 14:51'
updated_date: '2026-01-28 07:28'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate rate limiting schemas related to authentication in Cursor IDE 2.3.41. Analysis covers protobuf schemas, client-side throttling, HTTP header handling, usage tracking, queue position monitoring, and billing integration.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Comprehensive analysis of Cursor IDE 2.3.41 rate limiting mechanisms completed. Key findings:

### Server-Side Rate Limiting
- **ErrorDetails.Error enum**: 12+ rate limit error codes including tier-based limits (FREE_USER_RATE_LIMIT_EXCEEDED, PRO_USER_RATE_LIMIT_EXCEEDED)
- **Changeable vs Non-Changeable limits**: ERROR_RATE_LIMITED (50) vs ERROR_RATE_LIMITED_CHANGEABLE (51)
- **Queue Position Monitoring**: CheckQueuePosition RPC with position, wait time, and slow pool nudge data
- **Hard Limits**: GetHardLimit/SetHardLimit RPCs for spending caps

### Client-Side Rate Limiting
- **Leaky Bucket Algorithm**: Statsig SDK with 50 request capacity, 50 RPS leak rate
- **Rerun Rate Limiting**: Max 2 retries within 5 seconds
- **HTTP 429 Handling**: Retry-After header support with donotMakeRequestsUntil storage
- **Retry Interceptor Headers**: X-Cursor-RetryInterceptor-* headers for configurable retry behavior

### Usage Tracking
- **UsageEventKind**: 10 billing categories (USAGE_BASED, USER_API_KEY, INCLUDED_IN_PRO/PRO_PLUS/ULTRA, etc.)
- **Feature-level tracking**: chat, composer, cmd_k, terminal_cmd_k, fast_apply, etc.
- **Team member usage**: Per-user spend tracking with hard limit overrides

### Third-Party API Limits
- OpenAI rate and account limits
- GitHub x-ratelimit-* headers
- Sentry x-sentry-rate-limits header
- User Data Sync HTTP 429 handling

### File Sync Rate Limiter
- Configurable RPS, burst capacity, and circuit breaker reset time

Analysis written to: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-80-rate-limiting.md
<!-- SECTION:FINAL_SUMMARY:END -->
