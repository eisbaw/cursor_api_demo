---
id: TASK-286
title: Investigate TOOL_FORMER capability and toolFormerData system
status: To Do
assignee: []
created_date: '2026-01-28 07:24'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - tools
  - composer
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The code reveals a TOOL_FORMER capability type that wraps tool execution in the composer system. This appears to be a central mechanism for how tools are integrated with the AI conversation flow.

Key areas to investigate:
- Gs.TOOL_FORMER capability type and its role in the capability system
- toolFormerData structure and fields (tool, status, params, result, additionalData)
- How tool results are stored and retrieved via toolFormerData
- Integration with bubble/conversation UI
- Relationship between TOOL_FORMER and other capability types (DIFF_REVIEW, AUTO_CONTEXT, CURSOR_RULES, etc.)

Found at:
- Line 117906: COMPOSER_CAPABILITY_TYPE_TOOL_FORMER enum
- Line 215168-215169: ASK_QUESTION tool handling via toolFormerData
- Line 265486-265617: toolFormerData population and TODO_WRITE parsing
- Line 266747-266787: toolFormerData parsing and error handling
- Line 296859-296939: Capability type to icon/label mapping
<!-- SECTION:DESCRIPTION:END -->
