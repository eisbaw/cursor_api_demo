---
id: TASK-103
title: >-
  Investigate server-side tournament prompts - how pairwise comparisons are
  evaluated
status: Done
assignee: []
created_date: '2026-01-27 22:36'
updated_date: '2026-01-28 06:54'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyzed server-side tournament prompts and pairwise comparison evaluation in Cursor IDE 2.3.41.

Key findings:
- Default synthesis strategy is `pairwise_tournament` for parallel agent workflows
- Tournament uses `gpt-5.1-codex-high` as the judge model
- Evaluation happens server-side via `StreamUiBestOfNJudge` bidirectional streaming RPC
- Candidates are compared by their git diffs against the merge base
- Tournament progress tracks rounds, remaining candidates, and initial count
- Winner receives `bestOfNJudgeWinner` flag and reasoning explanation

Analysis written to: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-103-tournament-prompts.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Document tournament synthesis strategies
- [x] #2 Identify comparison request/response format
- [x] #3 Analyze winner selection logic
- [x] #4 Document tournament bracket progress tracking
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Tournament Prompts Analysis Complete

### Key Discoveries

1. **Synthesis Strategies**: Three strategies available - SINGLE_AGENT, FANOUT_VOTING, and PAIRWISE_TOURNAMENT (default)

2. **Judge Protocol**: StreamUiBestOfNJudge BiDi RPC with:
   - Request: task prompt + array of {composerId, diff} candidates
   - Response: winnerComposerId + reasoning

3. **Tournament Progress**: Tracks current_round, total_rounds, candidates_remaining, initial_candidates

4. **Default Config**:
   - Judge model: gpt-5.1-codex-high
   - Ensemble models: gpt-5.1-codex-high, claude-4.5-sonnet-thinking (alternating)
   - Timeout: 300s, min success: 50%

### Server-Side Logic (Not Visible)

The actual comparison prompts and bracket evaluation logic happen server-side. Client only:
- Collects diffs from git worktrees
- Sends candidates to server
- Receives winner ID and reasoning

### Related Protocol Buffers

- aiserver.v1.ParallelAgentWorkflowSynthesisStrategy
- aiserver.v1.SynthesisTournamentProgress
- aiserver.v1.UiBestOfNJudgeCandidate
- aiserver.v1.UiBestOfNJudgeFinalResult
- aiserver.v1.ParallelAgentWorkflowStatusUpdate
<!-- SECTION:FINAL_SUMMARY:END -->
