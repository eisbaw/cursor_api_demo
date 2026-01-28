---
id: TASK-18
title: Investigate x-cursor-checksum algorithm (Jyh cipher) for security analysis
status: Done
assignee: []
created_date: '2026-01-27 14:08'
updated_date: '2026-01-28 07:15'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Security analysis of the x-cursor-checksum algorithm and the Jyh cipher used in Cursor IDE 2.3.41.

The Jyh cipher is a simple XOR-based stream cipher with cipher feedback mode. It uses a hardcoded initial key (165/0xA5) and is trivially reversible. The algorithm is used for obfuscation rather than cryptographic security.

Key findings:
- Hardcoded initial key makes decryption trivial
- No server-side secret involved
- ~16 minute timestamp resolution (coarse)
- Deterministic output enables precomputation
- Used for device fingerprinting and basic anti-replay, NOT authentication
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Jyh function implementation documented
- [x] #2 x-cursor-checksum generation process mapped
- [x] #3 Input data (timestamp + machine IDs) identified
- [x] #4 Algorithm classified as obfuscation (not encryption)
- [x] #5 Security weaknesses enumerated with attack scenarios
- [x] #6 Reference implementations provided
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Created comprehensive security analysis at `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-18-jyh-cipher.md`

### Key Findings

**Algorithm Classification:**
- Stream cipher with cipher feedback (CFB-like)
- Hardcoded 8-bit initial key: 165 (0xA5)
- Operates on timestamp divided by 1,000,000 (~16 min resolution)
- Output is base64 URL-safe encoded and concatenated with machine IDs

**Security Assessment:**
- Classification: Obfuscation, NOT cryptographic security
- Trivially reversible given public initial key
- No shared secret between client and server
- Enables device fingerprinting but not authentication

**Attack Vectors Documented:**
1. Timestamp extraction from captured traffic
2. Request replay within ~16 minute window
3. Checksum forgery with known algorithm
4. Machine ID spoofing

**Implementation References:**
- `Jyh` function: line 268879-268883
- `Gyh` header setter: line 268885-268917
- Base64 encoder (`yO`): line 12595-12617
- URL-safe alphabet (`m3a`): line 12693

Provided working implementation code in JavaScript and Python for both encryption and decryption.
<!-- SECTION:FINAL_SUMMARY:END -->
