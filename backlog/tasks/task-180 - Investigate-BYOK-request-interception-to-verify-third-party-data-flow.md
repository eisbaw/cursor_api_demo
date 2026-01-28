---
id: TASK-180
title: Investigate BYOK request interception to verify third-party data flow
status: To Do
assignee: []
created_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - privacy
  - network-analysis
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-100-partner-data.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When using Bring Your Own Key (BYOK), verify whether requests bypass Cursor servers entirely or if Cursor still intermediates requests. Capture network traffic when using BYOK with OpenAI, Claude, and Google keys to understand the actual data flow and what information is sent to third-party providers versus Cursor servers.
<!-- SECTION:DESCRIPTION:END -->
