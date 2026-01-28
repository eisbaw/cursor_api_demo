---
id: TASK-211
title: Investigate Cursor Rules system integration with hooks
status: To Do
assignee: []
created_date: '2026-01-28 06:54'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - rules
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The hooks system integrates with Cursor Rules via the mBh() function and attachments. The beforeSubmitPrompt hook receives rule attachments that can influence behavior. Investigate:
- How rules are retrieved and filtered
- Rule types and capabilities
- Integration between .cursor/rules/ and hooks
- alwaysApply vs globs-based rules
<!-- SECTION:DESCRIPTION:END -->
