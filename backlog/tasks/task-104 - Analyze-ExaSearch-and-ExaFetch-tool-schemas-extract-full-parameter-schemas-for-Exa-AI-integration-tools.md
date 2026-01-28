---
id: TASK-104
title: >-
  Analyze ExaSearch and ExaFetch tool schemas - extract full parameter schemas
  for Exa AI integration tools
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 07:21'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete: ExaSearch and ExaFetch Tool Schemas

### Key Findings

**ExaSearch (agent.v1.ExaSearchArgs):**
- Field 1: `query` (string) - Search query
- Field 2: `type` (string) - Search mode (auto, neural, keyword, fast, deep)
- Field 3: `num_results` (int32) - Result count limit
- Field 4: `tool_call_id` (string) - Correlation ID

**ExaFetch (agent.v1.ExaFetchArgs):**
- Field 1: `ids` (repeated string) - IDs from search results
- Field 2: `tool_call_id` (string) - Correlation ID

**Result Schemas:**
- Both use oneof pattern: success/error/rejected
- ExaSearchSuccess contains repeated ExaSearchReference (title, url, text, published_date)
- ExaFetchSuccess contains repeated ExaFetchContent (title, url, text, published_date)

**User Approval Flow:**
- RequestQuery/RequestResponse pattern for both tools
- Auto-approved in CLI mode
- Interactive approval in UI mode

**Tool Registration:**
- ExaSearch: ToolCall field 26
- ExaFetch: ToolCall field 27

### Analysis File
`/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-104-exa-schemas.md`
<!-- SECTION:FINAL_SUMMARY:END -->
