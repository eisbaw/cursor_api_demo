---
id: TASK-166
title: Capture and analyze encrypted path format in network traffic
status: To Do
assignee: []
created_date: '2026-01-28 06:35'
labels:
  - encryption
  - traffic-analysis
  - privacy
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-92-path-encryption.md
  - reveng_2.3.41/analysis/TASK-33-server-encryption.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Capture actual encrypted paths sent to Cursor servers to understand the encryption format.

Goals:
1. Capture FastRepoInitHandshakeV2 requests showing encrypted paths in LocalCodebaseFileInfo
2. Analyze the encrypted_relative_path field format (Base64? Hex? Binary?)
3. Check if paths include IV/nonce prefix
4. Compare encrypted path lengths to plaintext lengths (block size analysis)
5. Look for patterns that reveal the cipher mode (ECB vs CBC vs GCM)

This will help determine the encryption algorithm without needing native code access.
<!-- SECTION:DESCRIPTION:END -->
