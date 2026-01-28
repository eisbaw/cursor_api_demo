---
id: TASK-165
title: Reverse engineer extension host native encryption implementation
status: To Do
assignee: []
created_date: '2026-01-28 06:35'
labels:
  - encryption
  - native-code
  - reverse-engineering
dependencies: []
references:
  - reveng_2.3.41/original/extensionHostProcess.js
  - reveng_2.3.41/analysis/TASK-92-path-encryption.md
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The path encryption/decryption functions are called via IPC proxy from the browser context to the extension host process. The actual implementation is in extensionHostProcess.js or in native Node.js addons.

Investigate:
1. Beautify and analyze extensionHostProcess.js (~4MB)
2. Look for .node native addon files in Cursor installation
3. Find the actual encryptPaths/decryptPaths implementations
4. Determine the encryption algorithm (likely AES-GCM or AES-CBC)
5. Document IV generation and key derivation if any

Key search terms:
- $getIndexProviderEncryptPaths
- $getIndexProviderDecryptPaths
- crypto.createCipheriv / crypto.createDecipheriv
- AES, GCM, CBC
<!-- SECTION:DESCRIPTION:END -->
