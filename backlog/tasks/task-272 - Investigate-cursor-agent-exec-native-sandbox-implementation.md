---
id: TASK-272
title: Investigate cursor-agent-exec native sandbox implementation
status: To Do
assignee: []
created_date: '2026-01-28 07:16'
labels:
  - reverse-engineering
  - sandbox
  - native-code
  - security
dependencies:
  - TASK-20
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-20 found that OS-level sandbox enforcement (landlock/seccomp/sandbox-exec) is NOT in the JavaScript workbench code. The actual enforcement must be in the `anysphere.cursor-agent-exec` extension or a native binary.

Investigation needed:
1. Locate the cursor-agent-exec extension in Cursor's resources folder
2. Examine for native binaries (.node addons, executables)
3. Determine what OS primitives are used for:
   - Filesystem isolation (landlock? namespaces? sandbox-exec profiles?)
   - Network blocking (seccomp? network namespaces?)
   - Git write blocking
4. Process trace sandboxed commands with strace/dtruss
5. Verify the sandbox actually works

This requires access to the actual Cursor IDE installation, not just the beautified JavaScript code.
<!-- SECTION:DESCRIPTION:END -->
