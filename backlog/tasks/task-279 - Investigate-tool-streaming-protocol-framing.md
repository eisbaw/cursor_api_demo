---
id: TASK-279
title: Investigate tool streaming protocol framing
status: To Do
assignee: []
created_date: '2026-01-28 07:23'
labels:
  - reverse-engineering
  - protobuf
  - streaming
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze how StreamedBackToolCall messages are framed and multiplexed in the gRPC stream. Each tool has Params, Result, and Stream message types - investigate the streaming protocol details.
<!-- SECTION:DESCRIPTION:END -->
