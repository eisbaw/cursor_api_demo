---
id: TASK-21
title: >-
  Investigate terminal execution service v3 vs v2 differences - why the
  VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION env var check exists
status: Done
assignee: []
created_date: '2026-01-27 14:08'
updated_date: '2026-01-28 07:14'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate why the VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION environment variable exists in Cursor IDE 2.3.41. This variable controls which terminal execution service version is used (v1, v2, or v3), with significant implications for sandbox support and terminal functionality.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Completed comprehensive analysis of terminal execution service versions v1, v2, and v3 in Cursor IDE 2.3.41.

Key findings:
- VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION env var provides direct override in ShadowWorkspaceServer for testing/debugging
- Three service versions with different architectures: v1 (direct terminal), v2 (warm pool), v3 (shellExec IPC)
- V3 is the ONLY version that enables sandbox support - sandboxSupported flag requires v3
- V3 uses pseudo-terminals with OSC 633 shell integration emulation and mirror terminal support
- Version selection controlled by feature gates (terminal_ide_shell_exec, terminal_execution_service_2), cached health check results, and user settings
- Proxy pattern (TerminalExecutionServiceProxy) handles dynamic version switching based on health checks and feature gates

Analysis written to: reveng_2.3.41/analysis/TASK-21-terminal-versions.md
<!-- SECTION:FINAL_SUMMARY:END -->
