---
id: TASK-112
title: >-
  Analyze tool execution approval flow - document how user approval is requested
  and handled for tool calls
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 00:12'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Analyzed the tool execution approval flow in Cursor 2.3.41, documenting:

### Key Findings

1. **Core Services Identified**:
   - `composerDecisionsService` (Sxe) - Central approval coordinator at line 476421
   - `toolCallHumanReviewService` (JW, rWt) - UI review model management at line 309551
   - `asyncOperationRegistry` - Tracks pending approval operations

2. **Approval Decision Types**:
   - Terminal commands: RUN, SKIP, REJECT, ALLOWLIST_COMMANDS
   - MCP tools: RUN, SKIP, REJECT, ALLOWLIST_TOOL
   - File edits: ACCEPT, REJECT, SKIP, SWITCH_TO_DEFAULT_AGENT_MODE

3. **YOLO Mode Configuration**:
   - `useYoloMode` - Master toggle for auto-run
   - `yoloCommandAllowlist` / `yoloCommandDenylist` - Command filtering
   - Protection flags: deleteFileProtection, dotFilesProtection, outsideWorkspaceProtection, mcpToolsProtection

4. **Security Mechanisms**:
   - `sudo` commands always require approval
   - `rm` commands blocked with deleteFileProtection
   - Hook system can override and force approval/rejection
   - Background agents have different approval bypass logic

### Output
- Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-112-tool-approval.md`

### Follow-up Tasks Created
- TASK-148: Analyze approval dialog UI components
- TASK-149: Analyze background agent approval bypass
- TASK-150: Analyze cursorHooksService hook system
<!-- SECTION:FINAL_SUMMARY:END -->
