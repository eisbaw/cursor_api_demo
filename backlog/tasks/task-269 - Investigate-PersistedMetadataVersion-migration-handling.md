---
id: TASK-269
title: Investigate PersistedMetadataVersion migration handling
status: To Do
assignee: []
created_date: '2026-01-28 07:15'
labels:
  - reverse-engineering
  - protobuf
  - storage
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js:342704
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The CloudAgentState has a PersistedMetadataVersion enum (currently version 1). Investigate how version migrations are handled:
- What triggers version upgrades
- How old state data is migrated
- Backwards compatibility mechanisms
- Version validation on load

Found at line 342704 in workbench.desktop.main.js
<!-- SECTION:DESCRIPTION:END -->
