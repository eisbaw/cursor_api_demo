---
id: TASK-111
title: Trace speculative summarization encryption flow
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:40'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deep dive into how speculative summaries are encrypted and decrypted. Key areas: speculativeSummarizationEncryptionKey generation, BH serialization, server-side encryption handling.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Traced the speculative summarization encryption flow in Cursor IDE 2.3.41. Key findings:

### Encryption Key
- Generated client-side using `crypto.getRandomValues(new Uint8Array(32))` (256 bits)
- Stored per-composer session
- Serialized as base64 for localStorage persistence using custom `yO()` encoder
- Deserialized using custom `BH()` base64 decoder
- Regenerated if corrupted or empty

### Triggering Logic
- Activated when context window usage >= 80% (configurable via `tokenUsageThresholdPercentage`)
- Skipped if cached summary exists within 10% tolerance (configurable via `tolerancePercentage`)
- 5-minute timeout for in-flight operations
- Streaming timeout also 5 minutes

### Server Communication
- Key sent via protobuf field 79: `speculative_summarization_encryption_key` (bytes type)
- Uses `StreamSpeculativeSummaries` gRPC endpoint (server streaming)
- Returns `ConversationSummary` objects with strategy information

### Summary Storage
- Cached at bubble level: `conversationMap[bubbleId].cachedConversationSummary`
- Also stored as `latestConversationSummary` on composer data
- Includes truncation points and strategy metadata

### Architecture Insight
The encryption key is generated client-side but used server-side, suggesting Cursor's server encrypts/decrypts summary data using the client-provided key. This is a privacy-preserving pattern where the server cannot read summaries without the client's key.

### Documentation
Full analysis written to: `reveng_2.3.41/analysis/TASK-111-speculative-summarization.md`
<!-- SECTION:FINAL_SUMMARY:END -->
