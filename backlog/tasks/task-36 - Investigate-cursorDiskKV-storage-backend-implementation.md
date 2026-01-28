---
id: TASK-36
title: Investigate cursorDiskKV storage backend implementation
status: Done
assignee: []
created_date: '2026-01-27 14:47'
updated_date: '2026-01-27 22:36'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive investigation of the cursorDiskKV storage backend implementation in Cursor IDE v2.3.41.

## Key Findings

### Storage Backend
- Uses SQLite database file `state.vscdb` in globalStorageHome
- Built on top of VS Code's storage infrastructure
- Supports optional WAL mode via `client_database_wal` feature gate

### API Methods Documented
1. `cursorDiskKVGet(key)` - String value retrieval
2. `cursorDiskKVGetWithLogs(key)` - Retrieval with debug logs
3. `cursorDiskKVGetBatch(keys)` - Bulk key retrieval
4. `cursorDiskKVSet(key, value)` - String value storage
5. `cursorDiskKVSetBinary(key, data)` - Binary data storage
6. `cursorDiskKVGetBinary(key)` - Binary data retrieval
7. `cursorDiskKVClearPrefix(prefix)` - Prefix-based deletion
8. `cursorDiskKVOnShouldSave(callback)` - Pre-save hooks

### Key Prefix Patterns Identified
- `agentKv:blob:` - Binary blob storage
- `agentKv:checkpoint:` - Conversation checkpoints
- `composerData:` - Main composer state
- `checkpointId:` / `bubbleId:` / `codeBlockDiff:` - Composer data
- `{bcId}:cloudAgent:metadata` - Cloud agent metadata
- `bcCachedDetails:` - Background composer cache
- `ai_hashes.` / `ai_accepted_diffs.` - AI code tracking

### Architecture
- IPC-based communication between renderer and main process
- Application storage scope (-1) always used
- Batch operations chunked for IPC threshold limits
- Dual format support: binary (new) and hex-encoded (legacy)

## Output
- Analysis document: `reveng_2.3.41/analysis/TASK-36-cursor-disk-kv.md`
- Created follow-up tasks: TASK-107, TASK-108, TASK-109
<!-- SECTION:FINAL_SUMMARY:END -->
