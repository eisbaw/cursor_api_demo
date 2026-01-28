---
id: TASK-77
title: Investigate server-side geo-routing for agent.api5.cursor.sh default endpoint
status: Done
assignee: []
created_date: '2026-01-27 14:51'
updated_date: '2026-01-28 07:23'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigated server-side geo-routing for agent.api5.cursor.sh. Found that routing is primarily server-side (Cloudflare/GCP), not client-side. Client always uses 'default' endpoint key; server routes to nearest region and returns region via x-cursor-server-region header.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Analyzed endpoint URL patterns and naming conventions
- [x] #2 Documented getAgentBackendUrls function logic
- [x] #3 Identified x-cursor-server-region header usage
- [x] #4 Confirmed server-side (not client-side) geo-routing
- [x] #5 Documented privacy vs non-privacy endpoint selection
- [x] #6 Created comprehensive analysis markdown
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Key Findings

### Server-Side Geo-Routing
- Client connects to `agent.api5.cursor.sh` (privacy) or `agentn.api5.cursor.sh` (non-privacy)
- Server infrastructure (likely Cloudflare + GCP) handles geographic routing
- Server returns actual region via `x-cursor-server-region` response header

### Endpoint Configuration
- `u6t` = https://agent.api5.cursor.sh (privacy, geo-routed)
- `d6t` = https://agentn.api5.cursor.sh (non-privacy, geo-routed)  
- `h6t` = https://agent-gcpp-uswest.api5.cursor.sh (privacy, US West direct)
- `f6t` = https://agentn-gcpp-uswest.api5.cursor.sh (non-privacy, US West direct)
- `qEl` = https://agent-gcpp-eucentral.api5.cursor.sh (privacy, EU Central direct)
- `JEl` = https://agentn-gcpp-eucentral.api5.cursor.sh (non-privacy, EU Central direct)

### Client Behavior
- Always uses `default` key from endpoint map (not regional keys)
- `us-west-1` key exists but unused - likely future feature infrastructure
- EU Central is developer-only override via cursor.selectBackend command
- No client-side latency measurement or geographic detection
- No client-side failover to alternative regions

### Region Header Usage
```javascript
const serverRegion = headers.get("x-cursor-server-region");
// Used for metrics tagging and OpenTelemetry tracing
```

## Analysis Document
`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-77-geo-routing.md`
<!-- SECTION:FINAL_SUMMARY:END -->
