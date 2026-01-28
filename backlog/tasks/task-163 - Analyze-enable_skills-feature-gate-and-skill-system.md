---
id: TASK-163
title: Analyze enable_skills feature gate and skill system
status: To Do
assignee: []
created_date: '2026-01-28 06:34'
labels:
  - reverse-engineering
  - feature-flags
  - extensibility
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-116-feature-gates.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The `enable_skills` feature gate (default: false) suggests a skill/capability system similar to plugins. Need to investigate: 1) What skills are available 2) How skills are registered/discovered 3) Skill execution model 4) Relationship to MCP servers. This could reveal an extensibility mechanism.
<!-- SECTION:DESCRIPTION:END -->
