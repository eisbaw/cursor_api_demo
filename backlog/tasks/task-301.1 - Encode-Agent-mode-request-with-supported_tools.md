---
id: TASK-301.1
title: Encode Agent mode request with supported_tools
status: To Do
assignee: []
created_date: '2026-01-28 10:04'
labels:
  - implementation
  - protobuf
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-7-protobuf-schemas.md
  - reveng_2.3.41/analysis/TASK-110-tool-enum-mapping.md
parent_task_id: TASK-301
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Modify request encoding to set:
- chatModeEnum=2 (Agent)
- chatMode="agent"
- unified_mode=2 (UNIFIED_MODE_AGENT) 
- is_agentic=true (field 27)
- supported_tools repeated field (29) with ClientSideToolV2 enum values
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Field 27 (is_agentic) set to true
- [ ] #2 Field 29 (supported_tools) contains tool enum values
- [ ] #3 Field 46 (unified_mode) set to 2
<!-- AC:END -->
