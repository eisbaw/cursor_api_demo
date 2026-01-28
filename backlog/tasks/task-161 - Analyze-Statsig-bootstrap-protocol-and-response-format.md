---
id: TASK-161
title: Analyze Statsig bootstrap protocol and response format
status: To Do
assignee: []
created_date: '2026-01-28 06:34'
labels:
  - reverse-engineering
  - feature-flags
  - grpc
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deep dive into the Statsig bootstrap protocol. The `bootstrapStatsig` gRPC method returns a JSON config that contains feature_gates, dynamic_configs, experiments, and layer_configs. Understanding this format could enable: 1) Local testing by injecting bootstrap data 2) Understanding how user targeting works 3) Discovering additional server-side feature gates not visible in client defaults. Reference: gRPC definition at line 811525, bootstrap parsing at line 295986.
<!-- SECTION:DESCRIPTION:END -->
