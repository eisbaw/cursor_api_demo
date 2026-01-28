---
id: TASK-188
title: Document reactive storage persistence layer (xct configuration)
status: To Do
assignee: []
created_date: '2026-01-28 06:42'
labels:
  - investigation
  - storage
  - reactive-system
dependencies:
  - TASK-106
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js:182505-182600
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js:182744
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cursor's reactive storage system uses a configuration object (`xct`) that defines:
- Storage keys and default values
- Serialization/deserialization functions (`fromStorage`/`toStorage`)
- Storage scope (application, profile, workspace)
- Storage target (user, machine)

Investigate:
1. Complete list of reactive storage keys and their purposes
2. Migration patterns (e.g., `modelConfigMigrated`)
3. How reactive storage integrates with VS Code's storage service
4. The `_nh()` factory function that creates reactive storage bindings
5. Scoped storage via `createScoped()` method
<!-- SECTION:DESCRIPTION:END -->
