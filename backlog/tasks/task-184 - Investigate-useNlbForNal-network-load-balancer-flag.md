---
id: TASK-184
title: Investigate useNlbForNal network load balancer flag
status: To Do
assignee: []
created_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - networking
  - infrastructure
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-118-http2-config.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:827787'
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The GetServerConfigResponse includes a `useNlbForNal` boolean field that appears to control whether to use a Network Load Balancer for NAL (Network Access Layer) connections.

Key areas to investigate:
- What NAL connections are and how they differ from standard AI server connections
- When useNlbForNal is set to true by the server
- How this affects connection routing and geographic distribution
- Relationship to the use-usw1-agent-for-nal experiment flag
- Performance implications of NLB vs non-NLB routing
<!-- SECTION:DESCRIPTION:END -->
