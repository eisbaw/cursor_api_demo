---
id: TASK-102
title: Reverse engineer server-side judge prompts via API interception
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:55'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyzed the Best-of-N judge system to understand server-side judge prompt construction. Key finding: judge prompts are entirely server-side and not visible in client code. The client only sends task description + git diffs, and receives winner ID + reasoning text. Documented all protobuf schemas, API endpoints, and potential interception strategies.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Documented judge request/response protobuf schemas
- [ ] #2 Identified gRPC service endpoints (StreamUiBestOfNJudge, StreamUiBestOfNJudgeSSE, StreamUiBestOfNJudgePoll)
- [ ] #3 Documented server configuration (judgeModel: gpt-5-high, strategy: pairwise_tournament)
- [ ] #4 Identified API interception points for future reverse engineering
- [ ] #5 Documented reasoning format (summary + optional justification separated by ---)
- [ ] #6 Confirmed judge prompts are server-side only - not in client code
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Analysis Complete

### Key Findings

1. **Judge prompts are server-side only** - The actual judging criteria and system prompts are not present in the client code.

2. **Data sent to server**:
   - User's original task string
   - GitDiff objects from each candidate worktree (includes file paths, line changes, diff chunks, and optionally full before/after file contents)

3. **Data received from server**:
   - `winner_composer_id` - The selected candidate
   - `reasoning` - Text explanation in format: "Summary\n---\nJustification (optional)"

4. **Server configuration reveals**:
   - Judge model: `gpt-5-high`
   - Strategy: `pairwise_tournament`
   - Synthesis model: `gpt-5.1-codex-high`

5. **Three RPC variants exist**:
   - `StreamUiBestOfNJudge` (BiDi streaming)
   - `StreamUiBestOfNJudgeSSE` (Server streaming fallback)
   - `StreamUiBestOfNJudgePoll` (Polling fallback)

### Interception Strategies Documented
- Network MITM proxy with gRPC decoding
- Electron IPC hook via Connect transport
- Code injection to log judge calls

### Output
Analysis written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-102-judge-prompts.md`
<!-- SECTION:FINAL_SUMMARY:END -->
