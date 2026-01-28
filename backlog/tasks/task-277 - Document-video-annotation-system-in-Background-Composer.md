---
id: TASK-277
title: Document video annotation system in Background Composer
status: To Do
assignee: []
created_date: '2026-01-28 07:22'
labels:
  - reverse-engineering
  - cloud-agent
  - media
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-72-artifact-schemas.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the video annotation system used by the Background Composer.

Found evidence during TASK-72 analysis:
- aiserver.v1.VideoAnnotationEntry with artifactPath and annotation fields (line 340328)
- Video annotation entries contain labeled chapters with timestamps
- F7s video resource class with videoUrl, chapters, artifactPath (line 744023)
- Video annotations fetched via backgroundComposerService.getBackgroundComposerInfo()

Need to investigate:
- How video recordings are created during cloud agent sessions
- What the annotation schema looks like
- How chapters are labeled and used
- Integration with screen recording functionality
<!-- SECTION:DESCRIPTION:END -->
