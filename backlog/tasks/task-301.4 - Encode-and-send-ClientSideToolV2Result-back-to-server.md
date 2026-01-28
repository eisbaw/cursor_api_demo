---
id: TASK-301.4
title: Encode and send ClientSideToolV2Result back to server
status: To Do
assignee: []
created_date: '2026-01-28 10:06'
updated_date: '2026-01-28 10:20'
labels:
  - implementation
  - protobuf
dependencies:
  - TASK-301.3
references:
  - reveng_2.3.41/analysis/TASK-52-toolcall-schema.md
  - reveng_2.3.41/analysis/TASK-110-tool-enum-mapping.md
parent_task_id: TASK-301
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement encoding of tool results to send back:
- Encode ClientSideToolV2Result with matching tool_call_id
- Pack into StreamUnifiedChatRequestWithTools (client_side_tool_v2_result field)
- Apply framing (magic byte + length + protobuf)
- Send via bidirectional stream
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ClientSideToolV2Result encoded with correct field names
- [ ] #2 tool_call_id matches original request
- [ ] #3 Result framing matches request framing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Blocked: httpx doesn't support HTTP/2 bidi streaming. Options: grpclib, raw h2, SSE+BidiAppend
<!-- SECTION:NOTES:END -->
