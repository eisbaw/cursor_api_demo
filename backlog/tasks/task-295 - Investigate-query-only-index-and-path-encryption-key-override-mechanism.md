---
id: TASK-295
title: Investigate query-only index and path encryption key override mechanism
status: To Do
assignee: []
created_date: '2026-01-28 07:29'
labels: []
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-73-path-encryption-sync.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze how the query-only index feature works with path encryption key overrides. The system supports different encryption keys for different repository contexts and query-only vs full access modes.

Related findings from TASK-73:
- getOverridePathEncryptionKey() returns key based on repo name/owner match
- queryOnlyIndex stores: repositoryInfo, pathEncryptionKey, queryOnlyRepoAccess
- Different windows can have different query-only contexts with separate keys
- Background composer retrieves keys via GetBackgroundComposerRepositoryInfo

Source: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js lines 441181-441187
<!-- SECTION:DESCRIPTION:END -->
