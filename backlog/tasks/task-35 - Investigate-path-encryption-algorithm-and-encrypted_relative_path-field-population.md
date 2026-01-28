---
id: TASK-35
title: >-
  Investigate path encryption algorithm and encrypted_relative_path field
  population
status: Done
assignee: []
created_date: '2026-01-27 14:47'
updated_date: '2026-01-28 07:16'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the path encryption algorithm used by Cursor IDE to encrypt file paths before sending to backend servers. Analyze how encrypted_relative_path fields are populated in protobuf messages.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Investigation Complete

Analyzed the path encryption system in Cursor IDE 2.3.41, focusing on the `encrypted_relative_path` field population.

### Key Findings

1. **Encryption Algorithm Location**: The actual encryption is implemented in **native code** within the extension host process, not visible in JavaScript

2. **Key Distribution**:
   - Server provides keys via `GetServerConfig` (IndexingConfig)
   - Three key types: default_user_path_encryption_key, default_team_path_encryption_key, per-repository pathEncryptionKey
   - Placeholder key: `"not a real key"` used before server config received

3. **encrypted_relative_path Usage**: Found in multiple protobuf messages:
   - `LocalCodebaseFileInfo` - Merkle tree file sync
   - `GitGraphCommitFile` - Git history (encryptedFromRelativePath, encryptedToRelativePath)
   - `GetGitGraphRelatedFilesRequest` / `GitGraphRelatedFile` - Related files queries

4. **Architecture**: Proxy-based IPC pattern where JavaScript calls native code:
   - `$getIndexProviderEncryptPaths(paths)` -> native encrypt
   - `$getIndexProviderDecryptPaths(paths)` -> native decrypt
   - `$getIndexProviderGetPathEncryptionKey()` -> returns current key

5. **Key Verification**: SHA256 hash of encryption key (pathKeyHash) used for consistency verification with server

6. **Security Model**: Key escrow - server can decrypt paths (not E2E encrypted)

### Output

Analysis document written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-35-path-encryption.md`

### Gaps

- Actual encryption algorithm unknown (likely AES variant)
- IV/nonce handling not visible
- Key derivation function unknown
- Requires native code analysis for complete understanding
<!-- SECTION:FINAL_SUMMARY:END -->
