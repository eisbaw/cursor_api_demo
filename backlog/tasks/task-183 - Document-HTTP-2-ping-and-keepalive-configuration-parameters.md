---
id: TASK-183
title: Document HTTP/2 ping and keepalive configuration parameters
status: To Do
assignee: []
created_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - protocol
  - performance
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-118-http2-config.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:295077-295082'
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The server config includes detailed HTTP/2 ping configuration (http2_ping_config) and HTTP/1.1 keepalive settings that control connection health monitoring. These parameters are dynamically configurable via experiment service.

Key areas to investigate:
- http2_ping_config parameters: enabled, pingIdleConnection, pingIntervalMs, pingTimeoutMs, idleConnectionTimeoutMs
- http1_keepalive_config: keepAliveInitialDelayMs
- Feature flags: http2_disable_pings, http1_keepalive_disabled
- How these settings affect connection pooling and reconnection behavior
- Integration with the Everything Provider's Http2Ping command
<!-- SECTION:DESCRIPTION:END -->
