---
id: TASK-121
title: Investigate @vscode/deviceid package implementation
status: Done
assignee: []
created_date: '2026-01-27 22:38'
updated_date: '2026-01-28 06:50'
labels:
  - reverse-engineering
  - fingerprinting
  - npm-package
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The devDeviceId is generated using the @vscode/deviceid npm package. This task should investigate:

1. What hardware identifiers the package uses on each platform
2. How it differs from the built-in machineId generation
3. Whether it's more or less stable across system updates
4. The fallback mechanisms when primary identification fails

Related to TASK-47 analysis of machine ID fingerprinting.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documented @vscode/deviceid package implementation
- [x] #2 Identified platform-specific storage mechanisms
- [x] #3 Compared with built-in machineId generation
- [x] #4 Analyzed stability across system updates
- [x] #5 Documented fallback mechanisms
- [x] #6 Created comprehensive analysis report
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Completed Analysis

Investigated the @vscode/deviceid npm package implementation used by Cursor IDE for the `devDeviceId` telemetry identifier.

### Key Findings

1. **Random UUID Generation:** Unlike hardware-derived identifiers (machineId, macMachineId), devDeviceId uses a random UUID v4 - no hardware fingerprinting involved.

2. **Platform-Specific Storage:**
   - Windows: Native C++ bindings to Windows Registry
   - macOS: `~/Library/Application Support/Microsoft/DeveloperTools/deviceid`
   - Linux: `$XDG_CACHE_HOME/Microsoft/DeveloperTools/deviceid`

3. **Stability Characteristics:** More stable than MAC-based IDs (survives network changes), less tied to specific hardware than machineId.

4. **Privacy Implications:** Storage location is shared across Microsoft dev tools, creating cross-application tracking potential.

5. **Fallback Mechanism:** On package failure, falls back to non-persistent random UUID.

### Documentation Created
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-121-deviceid.md`

### Related to TASK-47
Updated understanding of the machine ID ecosystem - devDeviceId is complementary to hardware-derived IDs.
<!-- SECTION:FINAL_SUMMARY:END -->
