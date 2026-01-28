---
id: TASK-118
title: Map server-side Http2Config enforcement logic
status: Done
assignee: []
created_date: '2026-01-27 22:37'
updated_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - protocol
  - server-config
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-43-sse-poll-fallback.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:826343-826361'
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The server can override client HTTP protocol preferences via Http2Config enum values. Investigate how server config enforcement works.

Key areas to investigate:
- How FORCE_ALL_DISABLED/FORCE_ALL_ENABLED affects client behavior
- FORCE_BIDI_DISABLED vs FORCE_BIDI_ENABLED distinction
- ServerConfig.http2Config propagation to client
- Interaction with client-side disableHttp2/disableHttp1SSE settings
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Investigated Http2Config server-side enforcement logic in Cursor IDE 2.3.41. Key findings:

### Http2Config Enum
- Defined at line 826343 with 5 values: UNSPECIFIED (0), FORCE_ALL_DISABLED (1), FORCE_ALL_ENABLED (2), FORCE_BIDI_DISABLED (3), FORCE_BIDI_ENABLED (4)
- Part of `aiserver.v1.Http2Config` protobuf namespace

### Server Config Delivery
- Http2Config is field 7 in GetServerConfigResponse (line 827828)
- Fetched via serverConfigClient.getServerConfig() every 5 minutes
- Stored in localStorage with key "cursorai/serverConfig"
- Default value is UNSPECIFIED

### HTTP/2 Ping Configuration
- Comprehensive ping config schema (line 295077-295082): enabled, pingIdleConnection, pingIntervalMs, pingTimeoutMs, idleConnectionTimeoutMs
- Feature flag `http2_disable_pings` (default: false)
- HTTP/1.1 keepalive config also available

### Client-Side Settings
- `cursor.general.disableHttp2` - disables HTTP/2 entirely
- `cursor.general.disableHttp1SSE` - forces polling fallback

### Key Finding
The http2Config enum is defined and delivered but **no consumer code was found that reads cachedServerConfig.http2Config to override client behavior**. The infrastructure exists but enforcement is not actively implemented.

### Analysis Document
Written to: reveng_2.3.41/analysis/TASK-118-http2-config.md
<!-- SECTION:FINAL_SUMMARY:END -->
