---
id: TASK-113
title: Map composer mode system architecture
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:34'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Document the full composer modes system: agent, plan, spec, debug, background, chat, triage. Understand protected modes, mode switching, and tool availability per mode.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Analyzing composerModesService.js for mode architecture

Found 10 protected modes: agent, chat, edit, background, plan, spec, debug, triage, review-edits, yolo-mode

Mode configurations include: enabledTools, autoRun, fullAutoRun, thinkingLevel, enabledMcpServers

Mode switching via setComposerUnifiedMode and switchModeToolCall
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Composer Mode System Architecture Analysis Complete

### Key Findings

**10 Protected Modes Identified:**
- `agent` - Default mode with full tool access, auto-run enabled
- `triage` - Subagent delegation (requires `nal_async_task_tool` feature gate)
- `plan` - Detailed task planning, special model filtering
- `spec` - Structured implementation specs (requires `spec_mode` feature gate)
- `debug` - Bug diagnosis with debugServerService integration
- `chat` (Ask) - Q&A without edit tools
- `background` (Cloud) - Cloud-based execution, privacy mode restrictions
- `edit` - Legacy mode, migrated away
- `review-edits` - Edit review, auto-run always disabled
- `yolo-mode` - Unrestricted execution

**Mode Configuration Schema:**
- `enabledTools[]` - Restrict available tools per mode
- `enabledMcpServers[]` - Restrict MCP server access
- `autoRun` / `fullAutoRun` - Control tool auto-execution
- `shouldAutoApplyIfNoEditTool` - Auto-apply behavior
- `thinkingLevel` - AI thinking visibility

**Core Service:** `ComposerModesService` at line ~310126
- Manages mode configurations via `reactiveStorageService.applicationUserPersistentStorage.composerState.modes4`
- Mode switching via `setComposerUnifiedMode()` and SWITCH_MODE tool
- Keybinding management with conflict detection

**Tool Availability Logic:** Line ~450906
- Edit mode returns empty tools
- Core modes (agent, chat, plan, spec, debug) get full tool set with filtering
- Custom modes restricted by `enabledTools` array
- Web search gated per mode + user setting
- MCP tools always filtered from supportedTools

### Files Created
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-113-composer-architecture.md`

### Follow-up Tasks Created
- TASK-155: MCP server restrictions per mode
- TASK-156: Debug mode + debugServerService integration
- TASK-157: SWITCH_MODE tool protocol documentation
<!-- SECTION:FINAL_SUMMARY:END -->
