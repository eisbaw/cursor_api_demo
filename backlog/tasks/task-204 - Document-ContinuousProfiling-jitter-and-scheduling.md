---
id: TASK-204
title: Document ContinuousProfiling jitter and scheduling
status: To Do
assignee: []
created_date: '2026-01-28 06:49'
labels:
  - reverse-engineering
  - performance
  - profiling
dependencies: []
references:
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:1170090'
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During TASK-119 analysis, discovered continuous profiling with jitter configuration at line 1170090:

```javascript
this._scheduledProfiles.set(e.id, a);
this.logService.debug(`ContinuousProfilingService: Scheduled profile ${e.id} with interval ${e.schedule.interval}s, duration ${e.schedule.duration}s, activityTimeout: ${n}s, jitter: ${o}ms`);
```

Investigate:
- How profiling schedules are configured
- Jitter calculation for profile collection
- Activity timeout triggering
- Integration with performance monitoring subsystem

Related to performance monitoring and diagnostics subsystem.
<!-- SECTION:DESCRIPTION:END -->
