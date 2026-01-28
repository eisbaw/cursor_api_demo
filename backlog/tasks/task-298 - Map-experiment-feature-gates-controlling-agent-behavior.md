---
id: TASK-298
title: Map experiment feature gates controlling agent behavior
status: To Do
assignee: []
created_date: '2026-01-28 07:29'
labels:
  - reverse-engineering
  - experiments
  - feature-flags
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-79-endpoint-failover.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cursor uses Statsig experiments to control various agent behaviors. Key feature gates discovered:

Feature Gates:
- retry_interceptor_enabled_for_streaming
- persist_idempotent_stream_state
- retry_interceptor_disabled

Dynamic Configs:
- retry_interceptor_config (retriableErrors array)
- retry_interceptor_params_config (maxRetries, baseDelayMs, maxDelayMs)
- idempotent_stream_config (retry_lookback_window_ms)
- disable_infinite_cloud_agent_stream_retries

Create a comprehensive map of all experiment gates that affect agent/streaming behavior, their default values, and what they control.

Code location: lines 294145-295510
<!-- SECTION:DESCRIPTION:END -->
