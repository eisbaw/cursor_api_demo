---
id: TASK-154
title: Investigate WritethroughBlobStore remote sync protocol
status: To Do
assignee: []
created_date: '2026-01-28 06:33'
labels:
  - protobuf
  - network
  - storage
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The blob storage uses a WritethroughBlobStore middleware for syncing blobs to remote servers. Investigate:
- How blobs are synced to Cursor's servers
- What triggers sync (flush operations)
- Conflict resolution when syncing
- Network protocol used for blob transfer

Discovered during TASK-87 analysis of blob storage architecture.
<!-- SECTION:DESCRIPTION:END -->
