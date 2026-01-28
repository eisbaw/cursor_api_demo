---
id: TASK-170
title: Analyze network diagnostic command implementations
status: To Do
assignee: []
created_date: '2026-01-28 06:36'
labels:
  - network
  - diagnostics
  - internals
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-93-traffic-capture.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-93 discovered built-in network diagnostic commands in Cursor:
- `connectDebug.dnsLookup`: DNS resolution testing
- `connectDebug.inspectTLSInfo`: TLS certificate inspection
- `connectDebug.http2Ping`: HTTP/2 connectivity check

These commands are executed via `everythingProviderService.onlyLocalProvider.runCommand()` and provide detailed network information including:
- DNS servers and resolution times
- TLS certificate chain details (issuer, subject, validity)
- HTTP/2 protocol negotiation status

This task should analyze:
1. How these commands are implemented in the local provider
2. What APIs they use (Node.js net/tls modules?)
3. Whether they can be extended or used for custom network analysis
4. The full response schema for each command
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Document connectDebug command implementations
- [ ] #2 Identify underlying Node.js APIs used
- [ ] #3 Document response schemas for each command
<!-- AC:END -->
