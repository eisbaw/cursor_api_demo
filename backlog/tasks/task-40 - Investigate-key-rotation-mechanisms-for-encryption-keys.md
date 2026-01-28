---
id: TASK-40
title: Investigate key rotation mechanisms for encryption keys
status: Done
assignee: []
created_date: '2026-01-27 14:47'
updated_date: '2026-01-28 07:08'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate key rotation mechanisms for encryption keys in Cursor IDE 2.3.41
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Key Rotation Mechanisms Analysis - Cursor IDE 2.3.41

### Primary Finding
**No formal key rotation mechanism exists.** Keys are generated once on first use and persist indefinitely until a decryption failure triggers data loss and key regeneration.

### Encryption Systems Identified

1. **SecretStorageService** (line 466779): Platform-agnostic secret storage wrapping OS keychains
   - Falls back to in-memory storage if encryption unavailable
   - Deletes secrets on decryption failure (no recovery)

2. **MCP Encryption** (line 1005452): AES-256-GCM for MCP server inputs
   - Key stored in secret storage as JWK
   - Version field (v=1) for data format, not key versioning
   - Clears all secrets on unsealing error

3. **EncryptedBlobStore** (line 263050): AES-256-GCM for blob encryption
   - Key derived from SHA-256 hash of string
   - Session-scoped, no persistence

### Platform Encryption Backends
- Windows: DPAPI
- macOS: Keychain Access
- Linux: gnome-libsecret, kwallet5/6

### Migration Found (NOT Rotation)
- One-time Linux backend migration: gnome-keyring to gnome-libsecret
- Data format migrations (v0-v11) for composer data structures

### What Does NOT Exist
- Automatic key rotation schedules
- Key versioning/generations
- Graceful re-encryption with new keys
- Key expiry/TTL enforcement
- Rollback protection

### Security Implications
- Key compromise = indefinite exposure
- Platform keychain reset = complete data loss
- No forward secrecy
<!-- SECTION:FINAL_SUMMARY:END -->
