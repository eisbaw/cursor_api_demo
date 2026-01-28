---
id: TASK-108
title: >-
  Deep dive into ComputerUseToolCall - analyze PIr/AIr action types and computer
  automation capabilities
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 00:11'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed comprehensive analysis of ComputerUseToolCall action types in Cursor IDE.

## Key Findings

### 11 Action Types Documented:
1. **MouseMoveAction** - Move cursor to coordinates
2. **ClickAction** - Single/double/triple click with button selection and modifiers
3. **MouseDownAction** - Press button down
4. **MouseUpAction** - Release button
5. **DragAction** - Drag along a path of coordinates
6. **ScrollAction** - Scroll in 4 directions with amount control
7. **TypeAction** - Type text strings
8. **KeyAction** - Press keys/combinations with optional hold duration
9. **WaitAction** - Pause execution
10. **ScreenshotAction** - Capture screen
11. **CursorPositionAction** - Query cursor position

### Enums:
- **MouseButton**: LEFT, RIGHT, MIDDLE, BACK, FORWARD
- **ScrollDirection**: UP, DOWN, LEFT, RIGHT

### Result Types:
- **ComputerUseSuccess**: action_count, duration_ms, screenshot (base64 WebP), log, cursor_position
- **ComputerUseError**: error message + same fields

### Feature Flag:
`cloud_agent_computer_use` - disabled by default, server-controlled

### Analysis Output:
`reveng_2.3.41/analysis/TASK-108-computer-use.md`

### Follow-up Tasks Created:
- TASK-131: Investigate native execution layer
- TASK-133: Analyze screenshot capture mechanism
- TASK-134: Map SubagentTypeComputerUse spawning
- TASK-135: Document modifier key syntax
<!-- SECTION:FINAL_SUMMARY:END -->
