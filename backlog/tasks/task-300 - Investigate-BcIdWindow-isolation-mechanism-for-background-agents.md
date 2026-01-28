---
id: TASK-300
title: Investigate BcIdWindow isolation mechanism for background agents
status: To Do
assignee: []
created_date: '2026-01-28 07:29'
labels:
  - windows
  - isolation
  - background-agent
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze the isBcIdWindow flag and how it creates isolated visual contexts for background agent composers.

Key areas:
- How BcId remote authority is detected
- What behavior changes when isBcIdWindow is true (repository tracking, view containers, workspace folders)
- Relationship to parentWindowId and parentWindowDimensions
- Window-in-window rendering patterns

Source locations:
- Lines 14771, 1120387: BcIdWindow initialization
- Lines 290955-290960: View container behavior changes
- Lines 1036953-1036967: Repository tracking changes
<!-- SECTION:DESCRIPTION:END -->
