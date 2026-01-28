---
id: TASK-193
title: Investigate Bedrock model availability and region validation
status: To Do
assignee: []
created_date: '2026-01-28 06:47'
labels:
  - aws
  - bedrock
  - models
  - followup
dependencies:
  - TASK-90
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-90-bedrock-regional.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During TASK-90 analysis of the regional prefix system, several gaps were identified that warrant further investigation:

1. **Region validation gap**: The UI accepts any string as a region code with no validation. Invalid regions fail silently at API call time rather than being caught early.

2. **Incomplete regional support**: Only `us-`, `ap-`, `eu-`, `ca-` region prefixes are supported. Middle East (`me-`), Africa (`af-`), and South America (`sa-`) regions silently fall back to US routing, which may not work.

3. **Model list synchronization**: The `JQl` array (line 290762) is hardcoded. Need to understand:
   - How does the server's `availableModels()` response interact with this client-side list?
   - Are there mechanisms to dynamically add new Bedrock models?
   - What happens when a model is deprecated on AWS but still in the hardcoded list?

4. **Cross-region fallback**: There's no mechanism to fall back to another region if a model is unavailable in the user's selected region.

Areas to investigate:
- Server-side model availability logic
- How the `availableModels()` RPC works for Bedrock
- Model deprecation handling
- Error handling for unavailable models/regions
<!-- SECTION:DESCRIPTION:END -->
