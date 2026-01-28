---
id: TASK-62
title: Trace speculative-full-file execution mode in composer
status: Done
assignee: []
created_date: '2026-01-27 14:50'
updated_date: '2026-01-27 22:37'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Traced the "speculative-full-file" execution mode in Cursor Composer. Found that it comprises two distinct concepts:

1. **Source Identifier (`qZ = "speculative-full-file"`)**: A constant used to tag inline diffs created by the composer's full-file editing pipeline, enabling filtering and tracking of AI-generated changes.

2. **Speculative Summarization System**: A proactive summarization mechanism that triggers when context usage exceeds ~70-80%, generating encrypted summaries before they're needed for conversation truncation.

## Key Findings

- The constant `qZ` is defined at line 303071 and used throughout the codebase to identify composer-generated inline diffs
- Speculative summarization is configured via `client_speculative_summarization_config` with threshold, tolerance, and timeout parameters
- All speculative summaries are encrypted with a per-composer 32-byte key
- Multiple speculative systems exist independently: summarization, linting, import prediction, and GPT5 routing

## Files Changed

- Created `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-62-speculative-mode.md`

## Follow-up Tasks Created

- TASK-111: Trace speculative summarization encryption flow
- TASK-112: Analyze context window truncation strategy
- TASK-113: Map composer mode system architecture
- TASK-114: Trace speculative import prediction system
<!-- SECTION:FINAL_SUMMARY:END -->
