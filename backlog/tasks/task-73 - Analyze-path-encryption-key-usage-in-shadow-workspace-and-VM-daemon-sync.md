---
id: TASK-73
title: Analyze path encryption key usage in shadow workspace and VM daemon sync
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-28 07:29'
labels: []
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-73-path-encryption-sync.md
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete: Path Encryption Key Usage in Shadow Workspace and VM Daemon Sync

### Key Findings

1. **Path Encryption Key Data Structures**: Identified key proto messages including `RepositoryIndexingInfo`, `SyncIndexRequest`, and `SwSyncIndexRequest` that carry the `pathEncryptionKey` field.

2. **Server-Provisioned Keys**: Keys come from server configuration (`defaultTeamPathEncryptionKey`, `defaultUserPathEncryptionKey`) with placeholder value `"not a real key"` replaced at runtime.

3. **Key Sharing Mechanisms**:
   - Background composers retrieve keys via `GetBackgroundComposerRepositoryInfo` RPC
   - Window-to-window sharing via native host IPC (`runActionInWindow`)
   - IndexingProvider interface exposes `encryptPaths`, `decryptPaths`, `getPathEncryptionKey`

4. **VM Daemon Integration**: `VmDaemonService.syncIndex` includes `pathEncryptionKey` in requests, enabling remote VMs to work with encrypted paths.

5. **Shadow Workspace Integration**: Shadow workspaces receive encryption keys and use them when syncing indexes and compiling file filters.

6. **Query-Only Index Override**: System supports per-repository encryption key overrides based on repo name/owner matching.

### Output
Analysis written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-73-path-encryption-sync.md`

### Follow-up Tasks Created
- TASK-293: Investigate team path encryption key distribution mechanism
- TASK-294: Analyze VmDaemonService file sync protocol with encrypted paths
- TASK-295: Investigate query-only index and path encryption key override mechanism
<!-- SECTION:FINAL_SUMMARY:END -->
