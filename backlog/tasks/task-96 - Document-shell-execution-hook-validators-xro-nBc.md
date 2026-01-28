---
id: TASK-96
title: 'Document shell execution hook validators (xro, nBc)'
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 06:34'
labels:
  - reverse-engineering
  - hooks
  - shell-exec
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The beforeShellExecution and afterShellExecution hooks use validator schemas xro and nBc. Need to trace these identifiers to understand: 1) What validations are performed before/after execution 2) How hooks can modify or reject commands 3) Integration with sandbox policy enforcement
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Documented the shell execution hook validators `xro` and `nBc` used by Cursor IDE's hooks system.

### Key Findings

1. **xro Validator (beforeShellExecution)**:
   - Validates responses for `beforeShellExecution` and `beforeMCPExecution` hooks
   - Supports three permission values: `"allow"`, `"deny"`, `"ask"`
   - Optional fields: `user_message` (shown to user) and `agent_message` (shown to AI)
   - When `"deny"` is returned, command is blocked with explicit anti-workaround messaging to the AI

2. **nBc Validator (afterShellExecution)**:
   - Minimal validation (just object type check)
   - Observational/logging only - cannot modify already-executed commands

3. **Hook Configuration Hierarchy**:
   - Enterprise (highest priority): `/etc/cursor/hooks.json` (Linux)
   - Team: Managed via dashboard API, stored in `~/.cursor/managed/team_{id}/hooks/`
   - Project: `{workspace}/.cursor/hooks.json` (requires workspace trust)
   - User: `~/.cursor/hooks.json`

4. **Execution Flow**:
   - Hooks receive JSON payload via stdin (base64 encoded)
   - Scripts output JSON response to stdout
   - First valid response from any hook wins
   - Stop hooks have loop protection (max 5 iterations)

5. **Integration Points**:
   - Sandbox policy awareness (`sandbox` parameter in hook payloads)
   - Workspace trust requirements for project hooks
   - Enterprise hooks cannot be overridden

### Output
Analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-96-shell-validators.md`
<!-- SECTION:FINAL_SUMMARY:END -->
