---
id: TASK-178
title: Map SCIM/SSO enterprise authentication flow
status: To Do
assignee: []
created_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - api
  - enterprise
  - authentication
dependencies:
  - TASK-115
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-115 analysis revealed enterprise features including SCIM directory groups and SSO configuration. This task should map the complete enterprise authentication flow. Key areas: How do DirectoryGroups interact with SCIM provisioning? What SSO protocols are supported? How are group-level permissions inherited?

Protobuf types identified:
- aiserver.v1.DirectoryGroup (line 285598)
- aiserver.v1.ScimConflictDirectoryGroup (line 287148)
- aiserver.v1.ScimConflictUser (line 287183)
- GetSsoConfigurationLinks / GetScimConfigurationLinks endpoints

References:
- /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-115-admin-settings.md
- /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js lines 285590-285776, 287140-287219
<!-- SECTION:DESCRIPTION:END -->
