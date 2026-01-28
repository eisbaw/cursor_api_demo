---
id: TASK-168
title: Analyze Worktree Setup Script System
status: To Do
assignee: []
created_date: '2026-01-28 06:35'
labels:
  - reverse-engineering
  - worktree
  - configuration
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the worktree setup script mechanism that runs when worktrees are created.

Key areas to investigate:
- `.cursor/worktrees.json` configuration file format
- `setup-worktree`, `setup-worktree-unix`, `setup-worktree-windows` script types
- `ensureWorktreeSetupAndRun` function flow
- `worktreeSetupLogger` channel and logging
- Shell script generation for Unix vs PowerShell for Windows
- `ROOT_WORKTREE_PATH` environment variable injection
- `createAndOpenWorktreesConfig` helper for initial setup
- Warning system: `worktreeSetupWarningShownCount`, `hideWorktreeSetupWarning`
<!-- SECTION:DESCRIPTION:END -->
