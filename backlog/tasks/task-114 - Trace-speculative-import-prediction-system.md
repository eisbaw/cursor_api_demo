---
id: TASK-114
title: Trace speculative import prediction system
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:55'
labels: []
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze how Cursor speculatively executes import commands before LSP responses arrive. Key: speculativeInFlightAction, maybeInterceptBulkEdit, actionApplyTimeout.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

Traced the speculative import prediction system in Cursor IDE 2.3.41. Key findings:

### Core Architecture
- **ImportPredictionService** (`pUo` class) at lines 1149848-1150703
- Service ID: `q$e = on("importPredictionService")`
- Uses `speculativeInFlightAction` pattern with 10s timeout

### Speculative Execution Flow
1. Detects lint errors (TS codes 2304/2503/2552, Pylance reportUndefinedVariable)
2. Fetches code actions from language server
3. Sends to backend via `getCppEditClassification` gRPC
4. Speculatively executes import command
5. Intercepts bulk edit via `maybeInterceptBulkEdit`
6. Matches edits to pending actions using symbol name regex

### Caching System
- `seenLintErrors`: LRU cache (100 entries) with status tracking
- `pendingImports`: Queue limited to 20 entries
- `recentGreenRanges`: 30s expiry for AI-generated code regions

### Autocomplete Integration
- Coordinates with CPP via `isShowingImportSuggestion()`
- Blocks CPP suggestions while import widget is shown
- Tab key handler delegates to `maybeAcceptShownImport()`

### AI Classification
- Backend returns `scoredEdits`, `shouldNoop`, `generationEdit`
- Local `shouldNoop()` uses log probability thresholds (0.02, 0.1)
- Boosts confidence 2x if marker touches "green" AI code

Full analysis: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-114-speculative-imports.md`
<!-- SECTION:FINAL_SUMMARY:END -->
