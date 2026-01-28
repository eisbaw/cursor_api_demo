---
id: TASK-199
title: Document getFaultInjectionAbortSignal testing mechanism
status: To Do
assignee: []
created_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - testing
  - reliability
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-83-persist-idempotent.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During TASK-83 analysis, discovered a fault injection mechanism used for testing stream reliability:

```javascript
getFaultInjectionAbortSignal() {
    const {signal, dispose} = {
        signal: new AbortController().signal,
        dispose: () => {}
    };
    const n = yn.setInterval(() => {
        const s = Math.random();
        s < e.exponentialFactor && (
            console.log("[composer] getFaultInjectionAbortSignal injecting fault"),
            t.abort()
        )
    }, e.baseIntervalMs);
    return {signal, dispose: () => yn.clearInterval(n)};
}
```

Located at line 488760-488769. Investigate:
1. What triggers this (what is `e.exponentialFactor`)?
2. Is this controlled by experiment flags or config?
3. How is this used for reliability testing?
4. Document the probabilistic abort mechanism
<!-- SECTION:DESCRIPTION:END -->
