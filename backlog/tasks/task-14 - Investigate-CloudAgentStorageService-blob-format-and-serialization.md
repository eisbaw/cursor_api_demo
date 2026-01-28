---
id: TASK-14
title: Investigate CloudAgentStorageService blob format and serialization
status: Done
assignee: []
created_date: '2026-01-27 14:08'
updated_date: '2026-01-28 07:01'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigated the CloudAgentStorageService blob format and serialization in Cursor IDE 2.3.41. Documented:
- CloudAgentStatePersistedMetadata protobuf schema
- CloudAgentState (xbs) full field listing with 30+ fields
- EncryptedBlobStore AES-256-GCM encryption implementation
- Cloud sync via GetBlobForAgentKV and StreamConversation
- PreFetchedBlob format and blob storage versioning
- InMemoryBlobStore fallback implementation
- CheckpointHandler integration for recovery
- ExternalSnapshot with presigned URLs
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Investigation Summary

Analyzed CloudAgentStorageService blob format and serialization from decompiled Cursor IDE 2.3.41 source.

### Key Findings

1. **Storage Architecture**: Two-tier system with lightweight metadata (CloudAgentStatePersistedMetadata) for quick lookups and full state (CloudAgentState) for hydration

2. **Serialization**: Uses @bufbuild/protobuf with base64 encoding for protobuf binary data

3. **Blob Storage**:
   - Key format: `agentKv:blob:{hexBlobId}`
   - Content-addressable via hex-encoded blob IDs
   - Supports both binary and legacy hex-encoded string formats

4. **Encryption**: Optional AES-256-GCM encryption layer with 12-byte random IV prepended to ciphertext

5. **Cloud Sync**:
   - GetBlobForAgentKV for on-demand blob fetching
   - StreamConversation for state synchronization with offset-based resumption
   - PreFetchedBlobs for proactive blob caching

6. **CloudAgentState Fields**: 30+ fields including conversation state, PR data, branch info, git commits, grind mode config, etc.

### Files Updated
- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-14-cloud-agent-storage.md`
<!-- SECTION:FINAL_SUMMARY:END -->
