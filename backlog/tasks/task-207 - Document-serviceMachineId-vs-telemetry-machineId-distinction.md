---
id: TASK-207
title: Document serviceMachineId vs telemetry machineId distinction
status: To Do
assignee: []
created_date: '2026-01-28 06:50'
labels:
  - reverse-engineering
  - fingerprinting
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During TASK-123 analysis, discovered two separate machine ID concepts:

1. `serviceMachineId` - Stored in `{userDataPath}/machineid` file, used for X-Machine-Id header in extension gallery requests
2. `telemetry.machineId` - Stored in telemetry storage, used in x-cursor-checksum header

Need to investigate:
- Are these always the same value or can they diverge?
- What triggers regeneration of each?
- Which one does Cursor's AbuseService actually use?
- Can they be independently spoofed?

Reference: Pft function at line 352912-352927 handles serviceMachineId generation.
<!-- SECTION:DESCRIPTION:END -->
