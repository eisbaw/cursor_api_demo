---
id: TASK-87
title: Analyze blob storage mechanism for ConversationStateStructure
status: Done
assignee: []
created_date: '2026-01-27 22:34'
updated_date: '2026-01-28 06:33'
labels:
  - protobuf
  - agent
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how blob references in ConversationStateStructure are stored and retrieved. The structure uses bytes fields for turns, todos, and other data which appear to be blob references rather than inline data.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Investigated the blob storage mechanism for ConversationStateStructure in Cursor IDE 2.3.41.

### Key Findings

1. **Content-Addressable Storage**: Blob IDs are SHA-256 hashes of content, enabling deduplication and integrity verification.

2. **Multi-Layer Architecture**:
   - ComposerBlobStore (local persistence via cursorDiskKV)
   - CachedBlobStore (in-memory LRU cache)
   - EncryptedBlobStore (AES-256-GCM encryption)
   - WritethroughBlobStore (remote sync)
   - RetryBlobStore (failure handling)

3. **Encryption Details**:
   - Algorithm: AES-256-GCM
   - IV: 12 bytes, randomly generated per blob
   - Key derivation: SHA-256(encryption_key_string)
   - Format: [12-byte IV][ciphertext]

4. **Storage Keys**:
   - `agentKv:blob:{hexBlobId}` - Raw blob data
   - `agentKv:checkpoint:{conversationId}` - Checkpoint pointers
   - `agentKv:bubbleCheckpoint:{conversationId}:{bubbleId}` - Per-bubble checkpoints

5. **ConversationStateStructure Fields Using Blobs**:
   - turns, turns_old (repeated bytes)
   - todos (repeated bytes)
   - summary, plan (optional bytes)
   - file_states (map<string, bytes>)
   - summary_archives (repeated bytes)

Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-87-blob-storage.md`
<!-- SECTION:FINAL_SUMMARY:END -->
