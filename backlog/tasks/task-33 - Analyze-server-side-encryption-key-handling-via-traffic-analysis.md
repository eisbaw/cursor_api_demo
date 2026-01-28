---
id: TASK-33
title: Analyze server-side encryption key handling via traffic analysis
status: Done
assignee: []
created_date: '2026-01-27 14:47'
updated_date: '2026-01-27 22:36'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Server-Side Encryption Key Handling Analysis Complete

### Key Findings

1. **Key Exchange Model**: Cursor uses a client-generated, server-acknowledged pattern - NOT a traditional key exchange protocol. Keys are created locally using `crypto.getRandomValues()` and transmitted to the server.

2. **Seven Key Types Identified**:
   - **Idempotent Stream Key**: 32-byte key sent in `x-idempotent-encryption-key` HTTP header
   - **Path Encryption Key**: Server-provided via `GetServerConfig`, used for file path privacy
   - **Speculative Summarization Key**: Client-generated for conversation summaries
   - **Context Bank Key**: Encrypts conversation context storage
   - **File Sync Encryption Header**: Metadata for file synchronization
   - **Deeplink Encryption Key**: For shared deeplinks
   - **Bug Report Encryption Key**: For encrypted bug reports in Redis

3. **Server Configuration Exchange**:
   - Client fetches config via `ServerConfigService.GetServerConfig()`
   - Server provides `defaultUserPathEncryptionKey` and `defaultTeamPathEncryptionKey`
   - Client replaces placeholder `$Ut = "not a real key"` with real keys
   - Config refreshed every 5 minutes

4. **Handshake Protocols**:
   - `FastRepoInitHandshake` and `FastRepoInitHandshakeV2` for repository sync (not key exchange)
   - `RepoHistoryInitHandshake` for history synchronization
   - `WelcomeMessage` indicates `isDegradedMode` when encryption unavailable

### Security Observations
- All keys transmitted to server (key escrow model)
- No perfect forward secrecy
- Server has plaintext access to all keys
- Relies entirely on TLS for transport security

### Output
- Analysis document: `reveng_2.3.41/analysis/TASK-33-server-encryption.md`

### Follow-up Tasks Created
- TASK-92: Analyze path encryption algorithm implementation
- TASK-93: Traffic capture to verify idempotent stream encryption
- TASK-94: Analyze key lifecycle and rotation mechanisms
- TASK-95: Document ServerConfigService response schema
<!-- SECTION:FINAL_SUMMARY:END -->
