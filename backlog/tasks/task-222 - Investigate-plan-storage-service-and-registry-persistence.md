---
id: TASK-222
title: Investigate plan storage service and registry persistence
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - plan-system
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-97-plan-review.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During TASK-97 analysis, discovered PlanStorageService (nWt) manages plan persistence with a registry tracking system. The registry stores:
- Plan URI and metadata
- createdBy/editedBy/referencedBy composer IDs
- builtBy map (empty = pending, populated = executed)
- YAML frontmatter format for plan files

Need to investigate:
- Registry persistence mechanism (storageService.get/set)
- Plan file format (YAML frontmatter + markdown body)
- Migration logic in loadRegistry()
- How plans are shared between composers (referencedBy tracking)

Key locations:
- Line ~308417: planStorageService.js module
- Line ~308427: Registry loading with migration
- Line ~308600: Registry entry structure
<!-- SECTION:DESCRIPTION:END -->
