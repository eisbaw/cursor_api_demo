---
id: TASK-140
title: Deep-dive into CPP (Cursor Predict) tier gating logic
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - reverse-engineering
  - tier-gating
  - cpp
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate the V$l and zyh functions that gate CPP features. Document:
- How shouldLetUserEnableCppEvenIfNotPro flag works
- What server-side validation exists
- How CPP models are selected based on tier
- The showingCppUpsell flow for non-pro users

Key code locations:
- Lines 268919-268924: V$l and zyh gating functions
- Line 1146108: isAllowedCpp check
- Line 1148547: CPP upsell trigger
<!-- SECTION:DESCRIPTION:END -->
