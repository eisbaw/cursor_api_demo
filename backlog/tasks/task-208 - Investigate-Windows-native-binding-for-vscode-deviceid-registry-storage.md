---
id: TASK-208
title: Investigate Windows native binding for @vscode/deviceid registry storage
status: To Do
assignee: []
created_date: '2026-01-28 06:50'
labels:
  - reverse-engineering
  - windows
  - native-bindings
  - registry
dependencies:
  - TASK-121
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The @vscode/deviceid package uses a native C++ binding (`windows.node`) on Windows to store the device ID in the Windows Registry. The specific registry key is not documented.

Investigation should:
1. Examine the windows.node native binding source code
2. Identify the exact registry key used for storage
3. Determine what additional functionality the native module provides
4. Document registry permissions required

Source: microsoft/vscode-deviceid repository, specifically the C++ source files.

Discovered during TASK-121 analysis.
<!-- SECTION:DESCRIPTION:END -->
