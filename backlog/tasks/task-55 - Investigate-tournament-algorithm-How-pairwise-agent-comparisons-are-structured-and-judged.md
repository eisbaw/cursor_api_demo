---
id: TASK-55
title: >-
  Investigate tournament algorithm: How pairwise agent comparisons are
  structured and judged
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-28 07:28'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Investigated the tournament algorithm used for pairwise agent comparisons in Cursor IDE 2.3.41. The analysis reveals a sophisticated parallel agent workflow system with three synthesis strategies (SINGLE_AGENT, FANOUT_VOTING, PAIRWISE_TOURNAMENT), where PAIRWISE_TOURNAMENT is the default.

## Key Findings

### Tournament Structure
- **SynthesisTournamentProgress** protobuf tracks: current_round, total_rounds, candidates_remaining, initial_candidates
- Round calculation: total_rounds = ceil(log2(initial_candidates))
- Workflow phases: STARTING → CHILDREN_RUNNING → GATHERING → SYNTHESIZING → COMPLETED

### Comparison Logic
- Each agent runs in an isolated git worktree
- Candidates are compared based on git diffs (changes made, not final state)
- **UiBestOfNJudgeCandidate** contains: composer_id + diff
- Minimum 2 candidates with file edits required
- 5-second timeout waiting for file edits per candidate

### Winner Selection
- Server-side **StreamUiBestOfNJudge** bidirectional streaming RPC
- Returns **UiBestOfNJudgeFinalResult** with: winner_composer_id + reasoning
- Reasoning format: "summary\n---\njustification"

### Configuration
- Ensemble models: ["gpt-5.1-codex-high", "claude-4.5-sonnet-thinking", ...]
- Gather timeout: 5 minutes (300,000ms)
- Min success percentage: 50%
- Synthesis model (judge): "gpt-5.1-codex-high"

### Group Tracking
- **best_of_n_group_id** correlates all agents in a tournament
- **try_use_best_of_n_promotion** requests priority resource allocation
- User preferences stored in **bestOfNEnsemblePreferences** JSON map

## Analysis File
Written to: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-55-tournament-algorithm.md
<!-- SECTION:FINAL_SUMMARY:END -->
