---
id: TASK-265
title: Investigate VM pod snapshot mechanism - snapshotUsedForDefaultVMPod
status: To Do
assignee: []
created_date: '2026-01-28 07:11'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - background-composer
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-23 investigation revealed snapshot functionality for VM pods:
- `snapshotUsedForDefaultVMPod` - persistent data field
- `takeSnapshotOfDefaultVMPod()` method
- `createBackgroundComposerPodSnapshot` RPC call
- Visibility levels: REPO_READ_WRITE vs USER

Questions to investigate:
- How are snapshots created and stored?
- What is the retention policy?
- How do snapshots speed up pod startup?
- What is the difference between visibility levels?

Reference: Lines 1142946-1142970, 756926-756927 in workbench.desktop.main.js
<!-- SECTION:DESCRIPTION:END -->
