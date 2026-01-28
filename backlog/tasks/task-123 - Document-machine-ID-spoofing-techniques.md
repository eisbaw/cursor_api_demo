---
id: TASK-123
title: Document machine ID spoofing techniques
status: Done
assignee: []
created_date: '2026-01-27 22:38'
updated_date: '2026-01-28 06:49'
labels:
  - reverse-engineering
  - fingerprinting
  - security-research
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Based on TASK-47 analysis, document methods to modify machine IDs:

1. How to change machineId (modify /etc/machine-id on Linux, registry on Windows, etc.)
2. How to spoof macMachineId (virtual network adapter with custom MAC)
3. Impact of ID changes on Cursor authentication and rate limits
4. Whether ID changes are detected server-side
5. Risks and legal considerations

This is for research/testing purposes only.

Related to TASK-47 machine ID fingerprinting analysis.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document machineId generation and storage mechanisms
- [x] #2 Document macMachineId (MAC-based) generation
- [x] #3 Identify platform-specific ID sources
- [x] #4 Document storage locations and persistence
- [x] #5 Analyze x-cursor-checksum header integration
- [x] #6 List practical spoofing techniques per platform
- [x] #7 Assess detection risks and mitigation strategies
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Created comprehensive analysis document at `reveng_2.3.41/analysis/TASK-123-machine-id-spoofing.md` covering:

### Key Findings

1. **Four Machine ID Types Analyzed:**
   - `machineId`: SHA-256 of platform UUID (Linux: /etc/machine-id, Windows: MachineGuid registry, macOS: IOPlatformUUID)
   - `macMachineId`: SHA-256 of first valid MAC address (falls back to random UUID)
   - `sqmId`: Windows-only SQM registry key (unhashed)
   - `devDeviceId`: From @vscode/deviceid package

2. **Spoofing Vectors Documented:**
   - Linux: Edit /etc/machine-id directly
   - Windows: Modify HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid
   - All platforms: MAC address spoofing for macMachineId
   - Direct storage modification (~/.config/Cursor/machineid)
   - VM with custom platform UUID and MAC address (cleanest approach)
   - LD_PRELOAD interception (Linux advanced technique)

3. **Integration Points:**
   - Machine IDs flow into `x-cursor-checksum` header (documented in TASK-18)
   - All IDs included in telemetry common properties
   - AbuseService provides IPC methods: `$getMachineId()`, `$getMacMachineId()`

4. **Server-Side Considerations:**
   - Cannot determine exact validation logic from client code
   - Likely checks: timestamp validation, ID consistency, rate limiting by ID
   - VM ratio (`isVMLikelyhood`) also transmitted via telemetry

5. **Detection Risks:**
   - Frequent ID changes may trigger flags
   - ID collision across accounts
   - Pattern matching on obviously fake values

### Related Tasks
- TASK-47: Foundational machine ID fingerprinting analysis
- TASK-18: x-cursor-checksum algorithm
- TASK-121: @vscode/deviceid package investigation (pending)
- TASK-122: VM detection impact
<!-- SECTION:FINAL_SUMMARY:END -->
