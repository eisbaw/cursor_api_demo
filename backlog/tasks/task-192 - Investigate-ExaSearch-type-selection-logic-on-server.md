---
id: TASK-192
title: Investigate ExaSearch type selection logic on server
status: To Do
assignee: []
created_date: '2026-01-28 06:43'
labels:
  - reverse-engineering
  - exa-ai
  - server-side
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-124-exasearch-params.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ExaSearch type parameter (neural, keyword, auto, fast, deep) appears to be determined server-side rather than client-side. Investigate how Cursor's server decides which Exa AI search type to use based on query context, user preferences, or other factors.

Related: TASK-124 found the type field but no client-side hardcoded values.
<!-- SECTION:DESCRIPTION:END -->
