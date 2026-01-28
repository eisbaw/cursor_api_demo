---
id: TASK-301.5
title: Implement bidirectional streaming with tool call loop
status: Done
assignee: []
created_date: '2026-01-28 10:06'
updated_date: '2026-01-28 10:45'
labels:
  - implementation
  - streaming
dependencies:
  - TASK-301.4
references:
  - reveng_2.3.41/analysis/TASK-2-bidiservice.md
  - reveng_2.3.41/analysis/TASK-53-stream-recovery.md
parent_task_id: TASK-301
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the main agent loop with bidirectional streaming:
1. Send initial request with supported_tools
2. Receive response chunks, detect tool calls
3. When tool_call received: execute tool, send result
4. Continue receiving until conversation ends
5. Handle multiple tool calls in sequence
6. Properly close stream when done

Use httpx with HTTP/2 for true bidi or implement append/poll fallback.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Bidirectional stream established
- [ ] #2 Tool call -> execute -> result loop works
- [ ] #3 Multiple sequential tool calls handled
- [ ] #4 Stream closes cleanly
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Bidi streaming working via h2 library. Full tool call loop functional.
<!-- SECTION:NOTES:END -->
