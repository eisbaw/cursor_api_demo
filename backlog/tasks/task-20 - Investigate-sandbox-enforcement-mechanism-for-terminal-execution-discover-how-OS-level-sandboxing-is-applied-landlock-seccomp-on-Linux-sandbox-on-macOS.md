---
id: TASK-20
title: >-
  Investigate sandbox enforcement mechanism for terminal execution - discover
  how OS-level sandboxing is applied (landlock/seccomp on Linux, sandbox on
  macOS)
status: Done
assignee: []
created_date: '2026-01-27 14:08'
updated_date: '2026-01-28 07:16'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Investigated the sandbox enforcement mechanism for terminal execution in Cursor 2.3.41.

### Key Findings

1. **No OS-Level Primitives in JavaScript**: Exhaustive search found NO landlock, seccomp, sandbox-exec, bwrap, or other OS-level sandbox primitives in the JavaScript workbench code.

2. **Sandbox Policy System Documented**:
   - Four policy types: UNSPECIFIED, INSECURE_NONE, WORKSPACE_READWRITE, WORKSPACE_READONLY
   - SandboxPolicy protobuf message with fields for type, networkAccess, additionalReadwritePaths, additionalReadonlyPaths, blockGitWrites, ignore_mapping
   - Security level hierarchy for policy merging (lower = more restrictive)

3. **V3 Service Requirement**: Sandboxing ONLY works with Terminal Execution Service V3

4. **Native Enforcement Boundary**: The JavaScript layer (MainThreadShellExec) converts and sends policies via IPC to ExtHostShellExec, which delegates to the `anysphere.cursor-agent-exec` extension for actual OS-level enforcement

5. **Platform-Specific Gates**: Feature flags can force-disable sandbox on Linux and Windows; macOS has no force-disable flag

6. **Admin Controls**: Enterprise admins can force-enable sandboxing, disable network access, or disable git writes via server-side controls

### Created Follow-up Task

Created task for investigating the native sandbox implementation in cursor-agent-exec extension, which requires access to actual Cursor IDE installation files.

### Output

Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-20-sandbox-enforcement.md`
<!-- SECTION:FINAL_SUMMARY:END -->
