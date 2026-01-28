---
id: TASK-276
title: Document Slack integration for cloud agent artifacts
status: To Do
assignee: []
created_date: '2026-01-28 07:22'
labels:
  - reverse-engineering
  - cloud-agent
  - integrations
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-72-artifact-schemas.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how Cursor IDE integrates with Slack for sharing cloud agent artifacts.

Found evidence in TASK-72 analysis:
- `slack_upload_url` field in ArtifactUploadInstruction (line 807372)
- `slack_file_id` fields in both instruction and result messages
- Suggests artifacts can be shared to Slack channels/threads as part of cloud agent workflow

Need to investigate:
- How Slack OAuth is configured
- What triggers Slack uploads
- How artifact sharing notifications work
- SlackThread context in InvocationContext (line 138716)
<!-- SECTION:DESCRIPTION:END -->
