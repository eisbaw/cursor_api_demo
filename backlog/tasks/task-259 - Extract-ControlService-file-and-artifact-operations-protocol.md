---
id: TASK-259
title: Extract ControlService file and artifact operations protocol
status: To Do
assignee: []
created_date: '2026-01-28 07:09'
labels:
  - reverse-engineering
  - protobuf
  - cursor
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-25-agent-v1-protobuf.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ControlService has ReadTextFile, WriteTextFile, ReadBinaryFile, WriteBinaryFile, ListArtifacts, UploadArtifacts methods. Plus ArtifactUploadStatus and ArtifactUploadDispatchStatus enums. Document the file/artifact sync protocol.
<!-- SECTION:DESCRIPTION:END -->
