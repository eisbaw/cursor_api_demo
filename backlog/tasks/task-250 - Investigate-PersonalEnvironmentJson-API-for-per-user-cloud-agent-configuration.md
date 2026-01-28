---
id: TASK-250
title: Investigate PersonalEnvironmentJson API for per-user cloud agent configuration
status: To Do
assignee: []
created_date: '2026-01-28 07:08'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - background-composer
  - api
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-75-devcontainer-snapshot.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The DevcontainerStartingPoint analysis revealed server-side APIs for per-user environment configuration:
- SetPersonalEnvironmentJson
- GetPersonalEnvironmentJson 
- ListPersonalEnvironments
- DeletePersonalEnvironmentJson

These APIs appear to allow users to store environment.json configurations server-side rather than in the repository. Investigate how these APIs work and how they integrate with the snapshot/devcontainer system.
<!-- SECTION:DESCRIPTION:END -->
