---
id: TASK-233
title: Analyze Connect protocol transport layer implementation
status: To Do
assignee: []
created_date: '2026-01-28 07:02'
labels:
  - reverse-engineering
  - networking
  - connect-protocol
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js:267724
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how Cursor implements the bufbuild/connect-es transport layer for HTTP/2 and HTTP/1.1 fallback. Look at protocol-connect/transport.js, protocol-grpc-web components, and how the client switches between transports based on network capabilities. This could reveal how to intercept or proxy Cursor's AI traffic.
<!-- SECTION:DESCRIPTION:END -->
