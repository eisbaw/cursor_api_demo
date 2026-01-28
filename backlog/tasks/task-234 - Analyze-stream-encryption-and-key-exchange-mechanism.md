---
id: TASK-234
title: Analyze stream encryption and key exchange mechanism
status: To Do
assignee: []
created_date: '2026-01-28 07:02'
labels:
  - reverse-engineering
  - security
  - encryption
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-2-bidiservice.md
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the x-idempotent-encryption-key header and how stream data is encrypted. The key is a random 32-byte value encoded to base64. Understand the encryption algorithm used and whether the server decrypts this data. This is important for understanding Cursor's security model.
<!-- SECTION:DESCRIPTION:END -->
