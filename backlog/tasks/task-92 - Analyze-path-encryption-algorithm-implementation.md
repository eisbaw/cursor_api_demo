---
id: TASK-92
title: Analyze path encryption algorithm implementation
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 06:35'
labels:
  - encryption
  - privacy
  - reverse-engineering
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-33-server-encryption.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:831981'
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how Cursor encrypts file paths before sending to server. The client has path_encryption_key fields but the actual encryption algorithm is not visible in client code. Need to: 1) Find encryptPaths/decryptPaths implementation in native code 2) Determine if AES-GCM or another algorithm is used 3) Document IV handling for path encryption 4) Understand how encrypted_relative_path field is populated
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Analyzed path encryption implementation in Cursor IDE 2.3.41. Key findings:

1. **Architecture:** Encryption happens in native extension host process via IPC proxy, not in visible JavaScript
2. **Key Sources:** Server-provided (defaultUserPathEncryptionKey, defaultTeamPathEncryptionKey) and repository-specific keys
3. **Placeholder:** Client uses "not a real key" placeholder until server provides actual key
4. **Call Sites:** `encryptPaths()` and `decryptPaths()` called via `$getIndexProviderEncryptPaths` / `$getIndexProviderDecryptPaths` proxy methods
5. **Key Verification:** SHA256 hash used for path key verification with server

**Encrypted paths used in:**
- LocalCodebaseFileInfo (Merkle tree sync)
- GitGraphCommitFile (git history)
- Search results (codeBlock.relativeWorkspacePath)

**Plaintext paths used in:**
- FastUpdateFileRequest.LocalFile.unencrypted_relative_workspace_path

**Limitation:** Actual encryption algorithm not visible in JS code - requires native code analysis.

Analysis written to: reveng_2.3.41/analysis/TASK-92-path-encryption.md

Created follow-up tasks for:
- Native extension host code analysis
- Network traffic analysis for encrypted path format
<!-- SECTION:FINAL_SUMMARY:END -->
