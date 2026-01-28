---
id: TASK-98
title: Analyze ShellExecPseudoTerminal UI integration
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - shell-exec
  - terminal-ui
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ShellExecPseudoTerminal class (lines 1127552-1127673) handles terminal UI integration. Need to understand: 1) How shell output is rendered in the terminal 2) OSC 633 escape sequences for shell integration 3) Command completion detection and UI feedback 4) Integration with VS Code terminal APIs
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Analyzed the ShellExecPseudoTerminal class (W2m) which provides the terminal UI integration for Cursor's AI shell execution system.

### Key Findings

1. **Read-Only Pseudo-Terminal**: Implements VS Code's ITerminalChildProcess interface as a read-only terminal that displays AI-executed commands and their outputs.

2. **OSC 633 Shell Integration**: Full implementation of VS Code's shell integration protocol:
   - `A/B` - Prompt markers
   - `C` - Command execution start
   - `D` - Command finished with exit code
   - `E` - Command line text
   - `P` - Properties (Cwd, HasRichCommandDetection)

3. **History Replay System**: Can reconstruct terminal state from session history, enabling reconnection to ongoing sessions.

4. **Input Handling**: Only processes Ctrl+C to cancel running commands; all other input triggers a visual "flash-read-only" warning.

5. **Multi-PTY Registration**: Sessions can have multiple registered pseudo-terminals that all receive command start notifications.

6. **Output Buffer Management**: Uses oPu class for output truncation with configurable buffer sizes based on terminal scrollback settings.

### Documentation
Analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-98-shellexec-pty.md`
<!-- SECTION:FINAL_SUMMARY:END -->
