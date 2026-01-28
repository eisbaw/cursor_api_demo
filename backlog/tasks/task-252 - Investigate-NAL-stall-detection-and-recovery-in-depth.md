---
id: TASK-252
title: Investigate NAL stall detection and recovery in depth
status: To Do
assignee: []
created_date: '2026-01-28 07:09'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - streaming
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-53-stream-recovery.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deep dive into the NAL (Next Agent Layer) client stall detector mechanism:

- What thresholds trigger stall detection?
- How does it interact with the idempotent stream recovery?
- What metrics are reported (VOc, $Oc counters)?
- How does the activity tracking work (inbound/outbound messages)?

Reference: TASK-53 found stall detector implementation at lines 465816-465853.
<!-- SECTION:DESCRIPTION:END -->
