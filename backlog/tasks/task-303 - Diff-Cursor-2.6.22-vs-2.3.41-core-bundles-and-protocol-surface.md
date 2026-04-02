---
id: TASK-303
title: Diff Cursor 2.6.22 vs 2.3.41 core bundles and protocol surface
status: To Do
assignee: []
created_date: '2026-04-02 10:31'
updated_date: '2026-04-02 10:31'
labels:
  - analysis
  - diff
  - protocol
  - version-2.6.22
dependencies:
  - TASK-302
references:
  - reveng_2.6.22/original/workbench.desktop.main.js
  - reveng_2.3.41/original/workbench.desktop.main.js
  - reveng_2.6.22/FINDINGS.md
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Perform a structured diff of the `2.6.22` and `2.3.41` core bundles and record
all observable protocol-surface changes: endpoints, headers, request fields,
service names, and feature gates relevant to auth/chat/agent flow.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Identify version/commit and service list deltas
- [ ] #2 Document header key additions/removals/renames
- [ ] #3 Document request payload shape deltas for chat + agent
- [ ] #4 Write analysis file under `reveng_2.6.22/analysis/TASK-303-*.md`
- [ ] #5 Update `reveng_2.6.22/FINDINGS.md` with confirmed deltas
<!-- AC:END -->
