---
id: TASK-122
title: Analyze VM detection impact on Cursor behavior
status: Done
assignee: []
created_date: '2026-01-27 22:38'
updated_date: '2026-01-28 06:42'
labels:
  - reverse-engineering
  - anti-abuse
  - vm-detection
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-122-vm-detection.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:1132844-1132851'
  - main.js module jl (out-build/vs/base/node/id.js)
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-47 identified VM OUI detection in the codebase. This task should investigate:

1. How vmRatio telemetry affects server-side behavior
2. Whether VM users face different rate limits or restrictions
3. If there are service degradations for detected VMs
4. How to bypass VM detection if desired

VM OUIs detected:
- VMware: 00-50-56, 00-0C-29, 00-05-69
- HyperV: 00-03-FF  
- Parallels: 00-1C-42
- Xen: 00-16-3E
- VirtualBox: 08-00-27

Related to TASK-47 and anti-abuse systems.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Analyzed the VM detection system in Cursor IDE 2.3.41. Key findings:

### Detection Mechanism
- Uses MAC address OUI prefix matching via trie data structure
- Detects VMware, Hyper-V, Parallels, Xen, and VirtualBox MAC prefixes
- Calculates ratio of VM interfaces to total external network interfaces (0-100%)

### Telemetry Integration
- `isVMLikelyhood` percentage sent in `startupTimeVaried` telemetry event
- Displayed in Issue Reporter dialog as "VM" status
- Part of startup metrics alongside platform, memory, CPU info

### Behavior Impact
- **No client-side behavior changes** found based on VM detection
- Rate limiting is tier-based (free/pro), not VM-based
- Feature gates do not reference VM status
- x-cursor-checksum uses machineId/macMachineId but NOT vmRatio

### Bypass Methods
- MAC address spoofing (change to non-VM OUI)
- Add physical USB network adapter (reduces ratio)
- Network isolation (no external interfaces)

### Unknown: Server-Side Behavior
- VM data transmitted to Cursor servers
- Could potentially influence server-side decisions (abuse detection, rate limits)
- Cannot determine from client code alone

## Files Created
- reveng_2.3.41/analysis/TASK-122-vm-detection.md

## Detected VM OUIs
- VMware: 00-50-56, 00-0C-29, 00-05-69
- HyperV: 00-03-FF
- Parallels: 00-1C-42
- Xen: 00-16-3E
- VirtualBox: 08-00-27
<!-- SECTION:FINAL_SUMMARY:END -->
