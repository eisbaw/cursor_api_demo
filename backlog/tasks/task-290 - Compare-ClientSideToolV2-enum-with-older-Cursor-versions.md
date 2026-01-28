---
id: TASK-290
title: Compare ClientSideToolV2 enum with older Cursor versions
status: To Do
assignee: []
created_date: '2026-01-28 07:28'
labels:
  - reverse-engineering
  - cursor-ide
  - protobuf
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-128-tool-id-gaps.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Compare the ClientSideToolV2 enum between Cursor IDE versions to identify when specific tools were deprecated.

Need to obtain older Cursor versions (e.g., 1.x, 2.0, 2.1) and extract their workbench.desktop.main.js files to compare enum definitions.

This would provide definitive evidence for the deprecated tool hypotheses in TASK-128.
<!-- SECTION:DESCRIPTION:END -->
