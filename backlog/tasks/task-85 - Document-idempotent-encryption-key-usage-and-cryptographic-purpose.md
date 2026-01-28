---
id: TASK-85
title: Document idempotent encryption key usage and cryptographic purpose
status: Done
assignee: []
created_date: '2026-01-27 22:34'
updated_date: '2026-01-28 06:33'
labels:
  - reverse-engineering
  - cryptography
  - security
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-39-stream-resumption.md
  - reveng_2.3.41/analysis/TASK-12-stream-encryption.md
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The idempotent stream protocol uses a 256-bit encryption key (x-idempotent-encryption-key header).

Investigate:
1. What is this key actually used for? (The name suggests encryption but client code doesn't show encryption usage)
2. Is it used for server-side encryption at rest?
3. Is it a shared secret for HMAC verification?
4. How does the server validate/use this key?
5. What happens if client sends wrong key on reconnection?

Source locations:
- Key generation: workbench.desktop.main.js:488774-488776
- Header transmission: workbench.desktop.main.js:488865
- Base64 encoding: yO() function at line 12595
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Analysis document created with key generation details
- [x] #2 Documented that key has no client-side cryptographic usage
- [x] #3 Hypothesized server-side purpose based on design patterns
- [x] #4 Compared with other encryption keys in the system
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed analysis of the idempotent encryption key in Cursor IDE 2.3.41.

### Key Findings

1. **Client-Side Only Generation**: The 256-bit key is generated client-side using `crypto.getRandomValues()` and encoded in Base64-URL format.

2. **No Client-Side Encryption**: After exhaustive code search, **no client-side encryption or decryption operations** use this key. The key is:
   - Generated (line 488774-488777)
   - Transmitted via HTTP header `x-idempotent-encryption-key`
   - Persisted in `idempotentStreamState`
   - But never used for local crypto operations

3. **Server-Side Purpose**: The key appears to be for server-side encryption of persisted stream state, enabling:
   - Secure storage of stream resumption data
   - Authentication of reconnection attempts
   - Client-controlled encryption (server cannot decrypt without client key)

4. **Security Model**: "Client-provided server encryption" - client generates and controls the key, server uses it for encryption at rest.

### Deliverable

Analysis document created at:
`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-85-idempotent-encryption.md`
<!-- SECTION:FINAL_SUMMARY:END -->
