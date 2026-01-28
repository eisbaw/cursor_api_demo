---
id: TASK-220
title: Document getCppEditClassification gRPC API
status: To Do
assignee: []
created_date: '2026-01-28 06:55'
labels:
  - reverse-engineering
  - cursor
  - grpc
  - protobuf
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-114-speculative-imports.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The speculative import system calls `getCppEditClassification` gRPC endpoint to rank import suggestions. Document the full request/response schema.

Key protobuf types discovered:
- Request: `oMr` (aiserver.v1.GetCppEditClassificationRequest)
  - cpp_request (field 1)
  - suggested_edits (field 25, repeated)
  - marker_touches_green (field 26, bool)
  - current_file_contents_for_linter_errors (field 27, string)
  
- Response: `kml` (aiserver.v1.GetCppEditClassificationResponse)
  - scored_edits (field 1, repeated)
  - noop_edit (field 2)
  - should_noop (field 3, bool)
  - generation_edit (likely field 4)

Related: TASK-114 speculative imports
<!-- SECTION:DESCRIPTION:END -->
