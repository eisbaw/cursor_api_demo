---
id: TASK-284
title: >-
  Trace nested message types in ClientSideToolV2Call parameters (Hb, Pos, Ros,
  Vos, I1e, etc.)
status: To Do
assignee: []
created_date: '2026-01-28 07:23'
labels:
  - reverse-engineering
  - protobuf
  - cursor-2.3.41
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-126-toolv2-params.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Several parameter messages in ClientSideToolV2Call reference nested message types that need further investigation:

- Hb: RepositoryInfo (used by ReadSemsearchFilesParams, SemanticSearchFullParams)
- Pos: RipgrepOptions (used by RipgrepSearchParams)
- Ros: PatternInfo (used by RipgrepSearchParams)
- eR: CodeResult (used by ReadSemsearchFilesParams)
- zos: PrReference (used by ReadSemsearchFilesParams)
- Vos: TerminalCommandOptions (used by RunTerminalCommandV2Params)
- I1e: MCPTool (used by MCPParams)
- ZD: google.protobuf.Struct (used by CallMcpToolParams)
- JR: TodoItem (used by TodoWriteParams)
- LIr: ComputerAction (used by ComputerUseParams)
- HIr/\$Ir: StreamingEdit text/code variants

These nested types define the complete schema for tool parameters.
<!-- SECTION:DESCRIPTION:END -->
