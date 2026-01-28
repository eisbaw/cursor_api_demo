---
id: TASK-217
title: Investigate server-side BuiltinTool handling in gRPC service definitions
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - grpc
  - tools
  - server-protocol
dependencies:
  - TASK-125
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-125 revealed that BuiltinToolCall/BuiltinToolResult messages are used in server communication but have no client-side handlers. Investigate the gRPC service definitions to understand:

1. Which BuiltinTool enum values are actively used by the server
2. Whether test tools (ADD_TEST, RUN_TEST, DELETE_TEST, GET_TESTS) are server-only features
3. The relationship between server-orchestrated tools and client-executed tools
4. Any feature flags that might enable/disable BuiltinTool functionality

Related: TASK-125-builtin-test-tools.md
<!-- SECTION:DESCRIPTION:END -->
