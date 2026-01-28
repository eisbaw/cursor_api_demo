---
id: TASK-169
title: Decrypt captured ServerChunk payloads using idempotent key
status: To Do
assignee: []
created_date: '2026-01-28 06:36'
labels:
  - encryption
  - traffic-analysis
  - verification
dependencies:
  - TASK-93
references:
  - reveng_2.3.41/analysis/TASK-93-traffic-capture.md
  - reveng_2.3.41/analysis/TASK-12-stream-encryption.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up from TASK-93: Now that we know how to capture traffic, the next step is to actually capture encrypted ServerChunk payloads and attempt to decrypt them using the `x-idempotent-encryption-key` from the same request. This will verify:
1. Whether ServerChunk data is actually encrypted or plaintext
2. If encrypted, whether the format matches EncryptedBlobStore (12-byte IV + AES-GCM ciphertext)
3. If the client-provided key actually decrypts the data

Approach:
1. Set up mitmproxy with Cursor configured per TASK-93 methodology
2. Capture a complete idempotent stream conversation
3. Extract the encryption key from request headers
4. Attempt to decode ServerChunk as protobuf (if succeeds, plaintext)
5. If protobuf decode fails, attempt AES-256-GCM decryption with extracted key
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Capture complete idempotent stream session
- [ ] #2 Extract and decode encryption key from headers
- [ ] #3 Attempt protobuf decode of ServerChunk
- [ ] #4 Attempt AES-GCM decryption if needed
- [ ] #5 Document actual encryption status of stream data
<!-- AC:END -->
