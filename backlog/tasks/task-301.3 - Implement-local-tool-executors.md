---
id: TASK-301.3
title: Implement local tool executors
status: Done
assignee: []
created_date: '2026-01-28 10:05'
updated_date: '2026-01-28 10:20'
labels:
  - implementation
  - tools
dependencies:
  - TASK-301.2
references:
  - reveng_2.3.41/analysis/TASK-52-toolcall-schema.md
  - reveng_2.3.41/analysis/TASK-26-tool-schemas.md
parent_task_id: TASK-301
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Python functions to execute tools locally:
- read_file(path, offset?, limit?) -> content or error
- list_dir(path) -> file list
- grep_search(pattern, path) -> matches
- edit_file(path, old_string, new_string) -> success/error
- run_terminal(command) -> stdout, stderr, exit_code

Each returns data matching the expected result schema.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 read_file executor works with offset/limit
- [ ] #2 list_dir returns proper file listing
- [ ] #3 grep_search uses ripgrep or fallback
- [ ] #4 Error handling returns proper error schema
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Local executors working: list_dir, read_file, grep_search, edit_file, run_terminal
<!-- SECTION:NOTES:END -->
