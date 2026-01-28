---
id: TASK-75
title: Investigate DevcontainerStartingPoint and environment snapshot mechanism
status: Done
assignee: []
created_date: '2026-01-27 14:51'
updated_date: '2026-01-28 07:08'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analysis of DevcontainerStartingPoint protobuf message and the environment snapshot mechanism used by Cursor IDE's Background Composer feature for cloud agent execution environments.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Investigated the DevcontainerStartingPoint and environment snapshot mechanism in Cursor IDE 2.3.41.

### Key Findings:

1. **DevcontainerStartingPoint** (`aiserver.v1.DevcontainerStartingPoint`):
   - Defines starting configuration for cloud VM/pod creation
   - Fields: url, ref, userExtensions, cursorServerCommit, environmentJsonOverride, gitDiffToApply, skipBuildCaches

2. **Environment.json Configuration** (`.cursor/environment.json`):
   - Defines build (Dockerfile), snapshot ID, install/start scripts, terminal configs
   - File watcher auto-detects changes to this configuration
   - Three states: "none", "snapshot", "dockerfile"

3. **Snapshot API Operations**:
   - CreateBackgroundComposerPodSnapshot: Creates snapshot from running pod
   - ChangeBackgroundComposerSnapshotVisibility: Modify visibility (USER, REPO_READ_WRITE, PUBLIC)
   - GetBackgroundComposerSnapshotInfo: Retrieve snapshot metadata
   - StartBackgroundComposerFromSnapshot: Restore environment from snapshot

4. **Workspace Persistent Data**:
   - Stored at `workbench.backgroundComposer.workspacePersistentData`
   - Contains: vmSnapshotId, defaultVmPod, testingVmPod, installScript, startScript, terminals

5. **Snapshot Visibility Levels**:
   - UNSPECIFIED (0), USER (1), REPO_READ_WRITE (2), PUBLIC (4)
   - USER = private, REPO_READ_WRITE = shared with repo collaborators

6. **Blob Storage**:
   - LEGACY_UNSPECIFIED and V1 formats supported
   - ExternalSnapshot contains presignedUrl for blob access

### Analysis written to:
`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-75-devcontainer-snapshot.md`
<!-- SECTION:FINAL_SUMMARY:END -->
