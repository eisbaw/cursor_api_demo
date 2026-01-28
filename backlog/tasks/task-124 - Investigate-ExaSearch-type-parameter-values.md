---
id: TASK-124
title: Investigate ExaSearch type parameter values
status: Done
assignee: []
created_date: '2026-01-28 00:09'
updated_date: '2026-01-28 06:43'
labels:
  - reverse-engineering
  - exa-ai
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ExaSearchArgs has a 'type' field that likely maps to Exa AI search modes (semantic, keyword, auto, etc.). Analyze the codebase to find what values are used and how they affect search behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Identified type field in ExaSearchArgs protobuf schema
- [x] #2 Documented Exa AI search type values (auto, neural, fast, deep, keyword)
- [x] #3 Found internal keyword/vector enum mapping
- [x] #4 Analyzed request/response flow for type parameter
- [x] #5 Created comprehensive analysis document
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Investigated ExaSearch type parameter values in Cursor IDE 2.3.41.

### Key Findings

1. **Type Field Structure:**
   - Protobuf field #2 in `agent.v1.ExaSearchArgs`
   - String type (T:9), default empty string
   - Found at lines 136314-136348

2. **Exa AI Search Types:**
   - `auto` (default): Balanced, ~1000ms latency
   - `neural`: Semantic/embeddings-based search
   - `fast`: <350ms latency, streamlined models
   - `deep`: 3.5s latency, highest quality results
   - `keyword`: Traditional keyword matching

3. **Internal Mapping Found (line 268942):**
   - `keyword = "keyword"`
   - `vector = "vector"` (likely maps to neural)

4. **No Hardcoded Values:**
   - Type selection appears server-side
   - No UI selector found in client code
   - CLI mode auto-approves searches

### Output
Analysis written to: `reveng_2.3.41/analysis/TASK-124-exasearch-params.md`
<!-- SECTION:FINAL_SUMMARY:END -->
