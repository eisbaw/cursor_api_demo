---
id: TASK-139
title: Analyze blob encryption key derivation in EncryptedBlobStore
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - security
  - agent-kv
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The EncryptedBlobStore uses SHA-256 of a key string for AES-256 encryption. Investigate where the encryption key comes from, how it's managed, and whether proper key derivation (like PBKDF2/Argon2) should be used instead. Related to TASK-70.
<!-- SECTION:DESCRIPTION:END -->
