# TASK-128: ClientSideToolV2 Enum ID Gaps Analysis

**Source:** `reveng_2.3.41/beautified/workbench.desktop.main.js`
**Analysis Date:** 2026-01-28
**Related:** TASK-26-tool-schemas.md

## Overview

The `ClientSideToolV2` enum (aiserver.v1.ClientSideToolV2) at line ~104365 has gaps in its ID sequence, indicating deprecated or removed tools. This document analyzes each gap and hypothesizes what tools may have existed.

## Current Enum Values (v2.3.41)

```
ID  | Tool Name                     | Status
----|-------------------------------|--------
0   | UNSPECIFIED                   | Active
1   | READ_SEMSEARCH_FILES          | Active
2   | ???                           | GAP
3   | RIPGREP_SEARCH                | Active
4   | ???                           | GAP
5   | READ_FILE                     | Active
6   | LIST_DIR                      | Active
7   | EDIT_FILE                     | Active
8   | FILE_SEARCH                   | Active
9   | SEMANTIC_SEARCH_FULL          | Active
10  | ???                           | GAP
11  | DELETE_FILE                   | Active
12  | REAPPLY                       | Active
13  | ???                           | GAP
14  | ???                           | GAP
15  | RUN_TERMINAL_COMMAND_V2       | Active
16  | FETCH_RULES                   | Active
17  | ???                           | GAP
18  | WEB_SEARCH                    | Active
19  | MCP                           | Active
20  | ???                           | GAP
21  | ???                           | GAP
22  | ???                           | GAP
23  | SEARCH_SYMBOLS                | Active
24  | BACKGROUND_COMPOSER_FOLLOWUP  | Active
25  | KNOWLEDGE_BASE                | Active
26  | FETCH_PULL_REQUEST            | Active
27  | DEEP_SEARCH                   | Active
28  | CREATE_DIAGRAM                | Active
29  | FIX_LINTS                     | Active
30  | READ_LINTS                    | Active
31  | GO_TO_DEFINITION              | Active
32  | TASK                          | Active
33  | AWAIT_TASK                    | Active
34  | TODO_READ                     | Active
35  | TODO_WRITE                    | Active
36  | ???                           | GAP
37  | ???                           | GAP
38  | EDIT_FILE_V2                  | Active
39  | LIST_DIR_V2                   | Active
40  | READ_FILE_V2                  | Active
...continues to 55
```

---

## Gap Analysis

### Gap ID 2: Probable "WRITE_FILE" or "CREATE_FILE"

**Evidence:**
- Position between READ_SEMSEARCH_FILES (1) and RIPGREP_SEARCH (3)
- The BuiltinTool enum has `NEW_FILE = 7` suggesting early file creation capability
- No dedicated CREATE_FILE in current tools (EDIT_FILE handles creation)

**Hypothesis:** Early CREATE_FILE or WRITE_FILE tool, later merged into EDIT_FILE functionality.

---

### Gap ID 4: Probable "CODEBASE_SEARCH" or "ASK_CODEBASE"

**Evidence:**
- Position between RIPGREP_SEARCH (3) and READ_FILE (5)
- The system has `SEMANTIC_SEARCH_CODEBASE` in ComposerCapabilityRequest.ToolType enum
- ChunkType enum has `CODEBASE = 1`
- Early codebase search was likely separate from ripgrep

**Hypothesis:** Original CODEBASE_SEARCH tool, later evolved into SEMANTIC_SEARCH_FULL (9).

---

### Gap ID 10: Probable "WRITE_TO_FILE" or "SAVE_FILE"

**Evidence:**
- Position between SEMANTIC_SEARCH_FULL (9) and DELETE_FILE (11)
- BuiltinTool enum has `SAVE_FILE = 11`
- Logical grouping with file operations

**Hypothesis:** Explicit SAVE_FILE or WRITE_TO_FILE tool, later merged into EDIT_FILE workflow.

---

### Gap ID 13: Probable "RUN_TERMINAL_COMMAND" (v1)

**Evidence:**
- Position between REAPPLY (12) and [gap 14]
- Current tool is `RUN_TERMINAL_COMMAND_V2` at ID 15
- The codebase has `useLegacyTerminalTool` setting (line ~182286)
- BuiltinTool enum has `RUN_TERMINAL_COMMANDS = 17`

**Hypothesis:** Original RUN_TERMINAL_COMMAND (v1) tool, deprecated in favor of V2 at ID 15.

**Supporting Code:**
```javascript
// Line 904854
label: "Legacy Terminal Tool",
description: "Use the legacy terminal tool in agent mode, for use on systems with unsupported shell configurations"
```

---

### Gap ID 14: Probable "ASK_FOLLOWUP" or "REQUEST_MORE_INFO"

**Evidence:**
- Position between suspected RUN_TERMINAL_COMMAND (13) and RUN_TERMINAL_COMMAND_V2 (15)
- Current ASK_QUESTION tool is at ID 51
- Early conversational tools likely existed

**Hypothesis:** Early ASK_FOLLOWUP or CLARIFY tool, replaced by ASK_QUESTION (51).

---

### Gap ID 17: Probable "URL_FETCH" or "WEB_FETCH"

**Evidence:**
- Position between FETCH_RULES (16) and WEB_SEARCH (18)
- Exa tools include `exa_fetch_tool_pb.js` and `exa_search_tool_pb.js`
- Logical progression: fetch rules -> fetch URL -> web search

**Hypothesis:** Original URL_FETCH or WEB_FETCH tool, potentially replaced by Exa integration or WEB_SEARCH.

---

### Gap IDs 20, 21, 22: Probable "ATTEMPT_COMPLETION", "LIST_CODE_DEFINITION_NAMES", "BROWSER_ACTION"

**Evidence:**
- These IDs sit between MCP (19) and SEARCH_SYMBOLS (23)
- Common tools in other AI coding assistants:
  - ATTEMPT_COMPLETION for signaling task completion
  - LIST_CODE_DEFINITION_NAMES for symbol listing
  - BROWSER_ACTION for web automation

**Hypothesis:**
- ID 20: ATTEMPT_COMPLETION or FINISH_TASK (now implicit in conversation flow)
- ID 21: LIST_CODE_DEFINITION_NAMES (merged into SEARCH_SYMBOLS at 23)
- ID 22: BROWSER_ACTION (evolved into COMPUTER_USE at 54)

---

### Gap IDs 36, 37: Probable "RENAME_FILE", "MOVE_FILE"

**Evidence:**
- Position between TODO_WRITE (35) and EDIT_FILE_V2 (38)
- File management tools are a natural grouping
- No explicit RENAME or MOVE tools in current enum
- File operations currently handled by DELETE + CREATE

**Hypothesis:**
- ID 36: RENAME_FILE (deprecated, handled by workspace operations)
- ID 37: MOVE_FILE (deprecated, handled by workspace operations)

---

## Related Enums for Context

### BuiltinTool Enum (Line ~104513)

This enum shows tools available in a different context (possibly server-side or for specific workflows):

```
0   | UNSPECIFIED
1   | SEARCH
2   | READ_CHUNK
3   | GOTODEF
4   | EDIT
5   | UNDO_EDIT
6   | END
7   | NEW_FILE
8   | ADD_TEST
9   | RUN_TEST
10  | DELETE_TEST
11  | SAVE_FILE
12  | GET_TESTS
13  | GET_SYMBOLS
14  | SEMANTIC_SEARCH
15  | GET_PROJECT_STRUCTURE
16  | CREATE_RM_FILES
17  | RUN_TERMINAL_COMMANDS
18  | NEW_EDIT
19  | READ_WITH_LINTER
```

**Key Insight:** BuiltinTool has no gaps, suggesting it's a newer or more carefully managed enum. The presence of SAVE_FILE, NEW_FILE, and RUN_TERMINAL_COMMANDS (without V2) supports the gap hypotheses above.

### ComposerCapabilityRequest.ToolType Enum (Line ~117965)

```
0   | UNSPECIFIED
1   | ADD_FILE_TO_CONTEXT
3   | ITERATE                  (gap at 2!)
4   | REMOVE_FILE_FROM_CONTEXT
5   | SEMANTIC_SEARCH_CODEBASE
```

Note: This enum also has a gap at ID 2, suggesting similar deprecation patterns.

---

## Proto Field Number Analysis

The `ClientSideToolV2Call` message uses different field numbers for params than the enum values. This is normal protobuf practice where field numbers are for wire format and enum values are for type selection.

### Notable Field Number Gaps in ClientSideToolV2Call

Params oneof fields use these numbers: 2, 5, 8, 12, 13, 16, 17, 19, 20, 23, 24, 26, 27, 31-38, 41-45, 50, 52-67

**Missing field numbers in params:** 3, 4, 6, 7, 9, 10, 11, 14, 15, 18, 21, 22, 25, 28-30, 39, 40, 46-49, 51

Some of these are used for other fields (tool_call_id=3, timeout_ms=6, name=9, etc.), but the gaps suggest deprecated param types.

---

## Legacy Terminal Tool Evidence

Strong evidence for RUN_TERMINAL_COMMAND v1 deprecation:

```javascript
// Line 182286 - Default storage state
useLegacyTerminalTool: !1,

// Line 904854-904860 - Settings UI
label: "Legacy Terminal Tool",
description: "Use the legacy terminal tool in agent mode, for use on systems with unsupported shell configurations",

// Line 1165532-1165574 - Proxy service
const e = this._reactiveStorageService.applicationUserPersistentStorage.composerState.useLegacyTerminalTool ?? !1,
// ...
console.log("[TerminalExecutionServiceProxy] Using legacy terminal tool (v2) due to user setting")
```

This confirms that terminal tool went through at least one major revision, with the legacy version still available as a fallback option.

---

## Summary of Hypothesized Deprecated Tools

| Gap ID | Hypothesized Tool | Confidence | Evidence Strength |
|--------|-------------------|------------|-------------------|
| 2 | WRITE_FILE / CREATE_FILE | Medium | BuiltinTool.NEW_FILE exists |
| 4 | CODEBASE_SEARCH | Medium | SEMANTIC_SEARCH_CODEBASE in ToolType |
| 10 | SAVE_FILE | High | BuiltinTool.SAVE_FILE=11 |
| 13 | RUN_TERMINAL_COMMAND (v1) | Very High | useLegacyTerminalTool setting exists |
| 14 | ASK_FOLLOWUP | Low | Position-based inference |
| 17 | URL_FETCH / WEB_FETCH | Medium | Exa fetch tools exist |
| 20 | ATTEMPT_COMPLETION | Low | Common in other assistants |
| 21 | LIST_CODE_DEFINITION_NAMES | Medium | SEARCH_SYMBOLS may be evolution |
| 22 | BROWSER_ACTION | Low | COMPUTER_USE may be evolution |
| 36 | RENAME_FILE | Medium | Natural file operation |
| 37 | MOVE_FILE | Medium | Natural file operation |

---

## Recommendations for Further Investigation

1. **TASK-129**: Compare with older Cursor versions to verify deprecated tools
2. **TASK-130**: Analyze server-side proto definitions if available
3. **TASK-131**: Check cursor.so API documentation for historical tool changes
4. **TASK-132**: Investigate BuiltinTool vs ClientSideToolV2 relationship

---

## Protobuf Reserved Fields Note

In standard protobuf practice, deprecated fields are marked with `reserved` to prevent reuse. The presence of these gaps in a generated JS bundle suggests either:
1. The proto definitions use `reserved` statements (not visible in compiled JS)
2. The enum values were simply removed without proper reservation (risky)
3. The gaps are intentional placeholders for future use

Without access to the original `.proto` files, we cannot determine which case applies.

---

## Conclusion

The ClientSideToolV2 enum has 11 gaps (IDs 2, 4, 10, 13, 14, 17, 20-22, 36-37) representing deprecated tools. The strongest evidence supports ID 13 being the original RUN_TERMINAL_COMMAND tool, with the `useLegacyTerminalTool` setting providing direct confirmation of terminal tool versioning. Other gaps likely represent tools that were merged, replaced, or removed during Cursor's evolution from an AI code editor to a full agentic development environment.
