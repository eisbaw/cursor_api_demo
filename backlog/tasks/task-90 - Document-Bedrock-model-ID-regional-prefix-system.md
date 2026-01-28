---
id: TASK-90
title: Document Bedrock model ID regional prefix system
status: Done
assignee: []
created_date: '2026-01-27 22:35'
updated_date: '2026-01-28 06:47'
labels:
  - aws
  - bedrock
  - models
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The client has logic to transform model IDs based on region:
- `us-*` regions: `us.anthropic.claude-*`
- `ap-*` regions: `apac.anthropic.claude-*`
- `eu-*` regions: `eu.anthropic.claude-*`
- `ca-*` regions: `ca.anthropic.claude-*`

Need to:
1. Map all supported Bedrock regions to their prefixes
2. Document which models are available in which regions
3. Understand if this is a Cursor convention or AWS Bedrock standard
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documented all regional prefix mappings (us., eu., apac., ca.)
- [x] #2 Identified the prefix selection algorithm (region prefix matching)
- [x] #3 Documented model ID transformation in regionalBedrockId() function
- [x] #4 Documented fallback behavior (unknown regions use us. prefix)
- [x] #5 Listed all supported Bedrock models from JQl array
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Completed Investigation: Bedrock Regional Prefix System

### Key Findings

1. **Prefix Mapping Logic** - The `regionalBedrockId()` function at line 894673-894676 transforms model IDs based on AWS region:
   - `us-*` regions or empty: keeps `us.` prefix (default)
   - `ap-*` regions: transforms to `apac.` prefix
   - `eu-*` regions: transforms to `eu.` prefix
   - `ca-*` regions: transforms to `ca.` prefix
   - Unknown regions: falls back to `us.` prefix (no error)

2. **AWS Standard** - This is an AWS Bedrock Cross-Region Inference (CRI) convention, not Cursor-specific. The prefixes route requests to regional inference profiles.

3. **Supported Models** - Seven Claude models hardcoded in `JQl` array (line 290762):
   - claude-sonnet-4-20250514-v1:0
   - claude-sonnet-4-5-20250929-v1:0
   - claude-3-5-haiku-20241022-v1:0
   - claude-haiku-4-5-20251001-v1:0
   - claude-opus-4-20250514-v1:0
   - claude-opus-4-1-20250805-v1:0
   - claude-opus-4-5-20251101-v1:0

4. **Transformation Points** - Model IDs are transformed in two places:
   - `refreshDefaultModels()` at line 894688-894695 (server response processing)
   - Bedrock toggle handler at line 910567-910574 (adding/removing models)

5. **Gaps Identified**:
   - No support for `me-`, `af-`, `sa-` regions
   - No region validation (accepts any string)
   - Hardcoded model list requires Cursor updates for new models
   - No cross-region fallback mechanism

### Analysis Document
Written to: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-90-bedrock-regional.md`
<!-- SECTION:FINAL_SUMMARY:END -->
