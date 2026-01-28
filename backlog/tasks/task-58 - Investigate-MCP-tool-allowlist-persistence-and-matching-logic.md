---
id: TASK-58
title: Investigate MCP tool allowlist persistence and matching logic
status: Done
assignee: []
created_date: '2026-01-27 14:49'
updated_date: '2026-01-27 22:37'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive analysis of Cursor's MCP tool allowlist persistence and matching logic.

## Key Findings

### Allowlist Format
- Uses `serverId:toolName` format with colon separator
- Supports wildcards: `server:*`, `*:tool`, `*:*`
- Reserved characters: `:` (separator) and `*` (wildcard)

### Storage Location
- Stored in `applicationUserPersistentStorage.composerState.mcpAllowedTools`
- Accessed via `reactiveStorageService`
- Persists as array of strings

### Matching Logic (function `f4c`)
1. Parse entry into `{serverId, toolName}`
2. Match wildcards: `*:*` matches all, `server:*` matches all tools from server
3. Exact match for specific `server:tool` entries

### Permission Decision Flow (function `m4c`)
1. Validate names (no reserved characters)
2. Check if Playwright/browser tool (special handling)
3. Check admin protection settings
4. Check auto-run mode (Ask Every Time / Use Allowlist / Run Everything)
5. Match against allowlist if in allowlist mode
6. Return `{needApproval, candidatesForAllowlist}`

### Feature Gate
- Controlled by `mcp_allowlists` feature gate
- When enabled: granular allowlist matching
- When disabled: simple boolean `yoloMcpToolsDisabled` check

### Admin Override
- Team admins can control via `AutoRunControls` protobuf
- Admin settings override user allowlist completely
- Cached locally with fallback on network failure

## Deliverables
- Analysis document: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-58-mcp-allowlist.md`
- Created follow-up tasks: TASK-112, TASK-115, TASK-116
<!-- SECTION:FINAL_SUMMARY:END -->
