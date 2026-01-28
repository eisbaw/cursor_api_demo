---
id: TASK-218
title: Analyze CPP (Cursor Prediction Provider) suggestion system
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - cursor
  - autocomplete
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-114-speculative-imports.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The import prediction system coordinates closely with CPP (Cursor Prediction Provider). Investigate the CPP suggestion lifecycle, ghost text rendering, and how it integrates with the import prediction service.

Key areas discovered:
- `getCurrentSuggestion()` method
- CPP/import prediction mutual exclusion
- `hideWidgetsIfConflictsWithCppSuggestion()`
- Tab key handling coordination

Related: TASK-114 speculative imports
<!-- SECTION:DESCRIPTION:END -->
