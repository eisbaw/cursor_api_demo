---
id: TASK-47
title: >-
  TASK-18 follow-up: Investigate machineId/macMachineId derivation from hardware
  identifiers
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-27 22:38'
labels: []
dependencies: []
references:
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:268885'
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:831668'
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:1098225'
  - 'reveng_2.3.41/original/main.js:jl module (out-build/vs/base/node/id.js)'
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigation of machineId/macMachineId derivation from hardware identifiers in Cursor IDE.

Follow-up from TASK-18 checksum algorithm analysis - needed to understand the machine ID components used in the x-cursor-checksum header.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Analyzed the machine ID fingerprinting system used by Cursor IDE. Documented four distinct machine identifiers:

1. **machineId** - SHA-256 hash of platform-specific UUID:
   - macOS: IOPlatformExpertDevice UUID
   - Windows: HKLM\...\Cryptography\MachineGuid
   - Linux: /etc/machine-id or /var/lib/dbus/machine-id

2. **macMachineId** - SHA-256 hash of first valid MAC address (filters null/broadcast/Docker MACs)

3. **sqmId** - Windows-only SQM Client registry key (unmodified)

4. **devDeviceId** - From @vscode/deviceid npm package

Also documented:
- Virtual machine detection via MAC address OUI prefixes (VMware, HyperV, Parallels, Xen, VirtualBox)
- Integration with AbuseService for anti-fraud detection
- Usage in x-cursor-checksum header (combines obfuscated timestamp with machineId/macMachineId)

## Files Created
- reveng_2.3.41/analysis/TASK-47-machine-id.md

## Follow-up Tasks Created
- TASK-121: Investigate @vscode/deviceid package implementation
- TASK-122: Analyze VM detection impact on Cursor behavior
- TASK-123: Document machine ID spoofing techniques
<!-- SECTION:FINAL_SUMMARY:END -->
