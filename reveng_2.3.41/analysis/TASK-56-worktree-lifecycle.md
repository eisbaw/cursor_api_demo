# TASK-56: Worktree Lifecycle Analysis

## Overview

Git worktrees in Cursor provide isolated working directories for AI agents to make changes without affecting the user's main workspace. This analysis documents the complete lifecycle: creation, isolation mechanisms, cleanup strategies, and error recovery.

## Core Components

### 1. Worktree Manager Service (`IWorktreeManagerService`)

**Service ID**: `worktreeManagerService` (line 296828)

**Key Interfaces**:
- `WorktreeLockLease` - Prevents concurrent worktree operations
- `WorktreeOperationCanceledError` - Error type for canceled operations
- `NoChangesToApplyError` - Error when no changes detected

**Implementation Class**: `M1o` (line 960414-960670)

### 2. Worktree Class (`lwt`)

**Location**: Lines 960136-960410

Represents a single worktree instance with methods for:
- `exists()` - Check if worktree directory exists
- `remove()` - Delete worktree from git and filesystem
- `getCurrentBranch()` - Get active branch
- `createBranch(name)` - Create and checkout new branch
- `checkoutBranch(name)` - Switch to existing branch
- `stageAllChanges()` - Stage all modifications
- `commit(message, options)` - Create commit
- `push(options)` - Push to remote
- `hasChanges()` - Check for uncommitted changes
- `getStatus()` - Get git status summary
- `createPullRequest(title, body, existingPrUrl)` - Create/update PR
- `syncFilesFromComposer(files)` - Copy files from composer
- `getDiff(ref)` - Get diff against reference
- `hasConflicts(targetBranch)` - Check merge conflicts

## Lifecycle Phases

### Phase 1: Creation

**Entry Point**: `createWorktree()` in WorktreeManager (line 960456-960488)

**Flow**:
```
1. Acquire worktree lock lease (prevents concurrent creation)
2. Generate or use provided worktree path
3. Call gitContextService.createWorktree() or createWorktreeWithBranch()
4. Create metadata entry (path, commitHash, timestamp, workspace, composerId)
5. Save metadata to storage
6. Fire onDidCreateWorktree event
7. Return Worktree instance
```

**Configuration Options**:
```javascript
{
  composerId: string,           // Associate with composer
  baseBranch: string,           // Base branch for new worktree
  branchName: string,           // Custom branch name
  targetWorktreePath: string,   // Custom path
  excludeDirtyFiles: boolean    // Skip dirty files
}
```

**Storage Location**:
- Path constant: `.cursor/worktrees` (line 267277)
- Actual root: `~/.cursor/worktrees/<workspace>/<worktree-id>/`

### Phase 2: Isolation

**Worktree Path Management**:
```javascript
// Mapping worktree URIs to workspace URIs
function Fke(uri, composerData, workspaceService) {
  if (!composerData?.gitWorktree) return uri;
  const workspace = workspaceService.getWorkspace();
  const workspaceRoot = workspace.folders[0].uri;
  return uri.with({
    path: uri.path.replace(workspaceRoot.path, composerData.gitWorktree.worktreePath)
  });
}
```

**File System Watching**:
- `_startWorktreeWatcher(composerId, worktreePath)` (line 298939-298949)
- Watches worktree directory for file changes
- Fires `fireDidFilesChange` events to composer

**Isolation Features**:
1. Separate git working directory
2. Independent branch namespace
3. File watchers per worktree
4. CursorIgnore integration for worktree paths

### Phase 3: Operations

#### Apply to Main Branch

**Method**: `applyWorktreeToCurrentBranch()` (line 945414)

**Implementation**: `_applyWorktreeToCurrentBranchViaMerge()` (line 948390-948710)

**Steps**:
1. Set `isApplyingWorktree = true` state
2. Validate worktree exists
3. Save any pending composer files
4. Get git root and resources to apply
5. Map worktree URIs to workspace URIs
6. Generate patches for each file
7. Handle merge conflicts (dialog with options: merge/overwrite/cancel)
8. Apply changes to workspace files
9. Update `appliedDiffs` in composer state
10. Clean up worktree state (set `reservedWorktree`, clear `gitWorktree`)
11. Fire telemetry event (APPLY_TO_MAIN)

**Conflict Resolution Dialog**:
```javascript
{
  primaryButton: "Merge manually",      // Keep both changes with markers
  extraButtons: [
    { id: "stash", label: "Stash changes" },  // Stash local changes
    { id: "overwrite", label: "Overwrite" }   // Replace with agent changes
  ]
}
```

#### Undo Applied Changes

**Telemetry Event**: `UNDO_APPLY` (line 945667, 945682)

**Flow**:
1. Set `isUndoingWorktree = true`
2. Iterate through `appliedDiffs`
3. Restore original content or delete new files
4. Clear `appliedDiffs` state
5. Restore `gitWorktree` from `reservedWorktree`
6. Fire telemetry event

### Phase 4: Cleanup

#### Manual Cleanup (Delete Composer)

**Method**: `deleteComposer_DO_NOT_CALL_UNLESS_YOU_KNOW_WHAT_YOURE_DOING()` (line 298428-298469)

```javascript
try {
  const worktreePath = composerData.gitWorktree?.worktreePath;
  if (worktreePath) {
    this.updateComposerDataSetStore(composerId, s => s("gitWorktree", void 0));
    this._stopWorktreeWatcher(composerId);
    // Async cleanup - don't wait
    (async () => {
      try {
        await this._worktreeManagerService.removeWorktree(worktreePath);
      } catch (e) {
        console.info("[composer] Async worktree cleanup failed:", e);
      }
    })();
  }
} catch (e) {
  console.info("[composer] Error scheduling worktree cleanup:", e);
}
```

#### Automatic Periodic Cleanup

**Cron Service**: `A1o` (WorktreeCleanupCron, line 960068-960124)

**Configuration**:
```javascript
{
  worktreeCleanupIntervalHours: 6,  // Default interval
  worktreeMaxCount: 20              // Max worktrees per workspace
}
```

**Cleanup Algorithm**:
```javascript
async performCleanup() {
  const worktrees = await this.worktreeManagerService.listWorkspaceWorktrees();
  const maxCount = this.getMaxWorktreeCount();
  const buffer = 4;  // Remove 4 extra to avoid frequent cleanups

  if (worktrees.length <= maxCount) return;

  const removeCount = worktrees.length - maxCount + buffer;

  // Sort by lastAccessedAt ascending (oldest first)
  worktrees.sort((a, b) =>
    (a.lastAccessedAt || a.createdAt) - (b.lastAccessedAt || b.createdAt)
  );

  await this.worktreeManagerService.cleanupWorktrees({
    maxCount: maxCount,
    removeCountWhenExceeded: removeCount,
    prefetchedWorktrees: worktrees,
    dryRun: false
  });
}
```

**Protection Rules** (line 960632-960637):
1. Worktrees created within last 10 minutes (`Bom = 600 * 1000`) are protected
2. Worktrees with actively running composers are protected

#### Worktree Removal Process

**Method**: `removeWorktree()` in WorktreeManager (line 960578-960588)

```javascript
async removeWorktree(path) {
  const worktree = await this.getWorktree(path);
  if (!worktree) {
    this.logService.warn(`Cannot remove unknown worktree at ${path}`);
    return;
  }

  try {
    await worktree.remove();
    this.worktreeMetadata.delete(path);
    this.saveMetadata();
    this._onDidRemoveWorktree.fire(path);
  } catch (e) {
    throw e;
  }
}
```

**Worktree.remove()** (line 960215-960228):
```javascript
async remove() {
  this.logService.info(`Removing worktree at ${this.path}`);
  try {
    await this.gitContextService.removeWorktree(this.path);  // git worktree remove
  } catch {}  // Ignore git errors

  try {
    if (await this.exists()) {
      await this.fileService.del(this.uri, {
        recursive: true,
        useTrash: false  // Permanent deletion
      });
    }
  } catch (e) {
    throw e;
  }
}
```

## Error Recovery Mechanisms

### 1. Worktree Lock Lease

**Class**: `WorktreeLockLease` (line 296815-296824)

Prevents race conditions during worktree creation:
```javascript
acquireWorktreeLockLease() {
  const currentLock = this._worktreeCreationLock;
  let resolve;
  this._worktreeCreationLock = new Promise(r => resolve = r);
  return new WorktreeLockLease(currentLock, resolve);
}
```

### 2. Operation Cancellation

**Error Class**: `WorktreeOperationCanceledError` (line 296823-296827)

Thrown when:
- User cancels merge conflict dialog
- Timeout during apply operation
- Manual abort

### 3. Metadata Validation

**Method**: `validateAndCleanupMetadata()` (line 960432-960436)

```javascript
async validateAndCleanupMetadata() {
  const entries = Array.from(this.worktreeMetadata.entries());
  let removed = 0;

  for (const [path, metadata] of entries) {
    const worktree = this.instantiationService.createInstance(lwt, metadata);
    if (!await worktree.exists()) {
      this.worktreeMetadata.delete(path);
      removed++;
    }
  }

  if (removed > 0) {
    this.saveMetadata();
  }
}
```

### 4. Discovery of Unknown Worktrees

**Method**: `discoverUnknownWorktrees()` (line 960524-960543)

Scans worktrees root directory and adds any untracked worktrees to metadata.

### 5. Stale Directory Cleanup

**In `discoverWorktree()`** (line 960545-960576):
```javascript
// If discovery fails, clean up stale directory
catch (e) {
  this.logService.info(`Cleaning up stale worktree directory at ${path}`);
  try {
    await this.fileService.del(_e.file(path), {
      recursive: true,
      useTrash: false
    });
  } catch {}
}
```

### 6. CursorIgnore Cleanup

**Method**: `cleanupWorktreeCursorIgnoreEntries()` (line 441839-441848)

When worktree is removed, cleans up any cached .cursorignore entries for that path.

## Data Structures

### Worktree Metadata

```typescript
interface WorktreeMetadata {
  path: string;              // Filesystem path
  commitHash: string;        // Base commit
  createdAt: number;         // Creation timestamp
  workspaceName: string;     // Parent workspace
  id: string;                // Unique identifier
  composerId?: string;       // Associated composer
  lastAccessedAt?: number;   // Last touch timestamp
  branchName?: string;       // Current branch
  sizeInBytes?: number;      // Disk usage
}
```

### Composer Worktree State

```typescript
interface ComposerWorktreeState {
  gitWorktree?: {
    worktreePath: string;
    commitHash: string;
    branchName?: string;
  };
  reservedWorktree?: {     // Saved after apply
    worktreePath: string;
    commitHash: string;
    branchName?: string;
  };
  isCreatingWorktree: boolean;
  isApplyingWorktree: boolean;
  isUndoingWorktree: boolean;
  applied: boolean;
  appliedDiffs?: AppliedDiff[];
  pendingCreateWorktree: boolean;
  pendingCreateWorktreeBaseBranchName?: string;
  pendingCreateWorktreeExcludeDirtyFiles?: boolean;
  userPinnedWorktree?: boolean;
}
```

### WorktreeEvent (Protobuf)

```protobuf
message WorktreeEvent {
  enum EventType {
    UNSPECIFIED = 0;
    APPLY_TO_MAIN = 1;
    UNDO_APPLY = 2;
    VIEW_SUBCOMPOSER = 3;
  }

  EventType event_type = 1;
  string model_name = 2;
  string best_of_n_group_id = 3;
  repeated string all_worktree_paths = 4;
  string applied_worktree_path = 5;
  repeated WorktreeComposerMapping worktree_composer_mappings = 6;
  repeated BackgroundAgentComposerMapping background_agent_composer_mappings = 7;
  string applied_composer_id = 8;
}
```

## Setup Script System

### Configuration File

Location: `.cursor/worktrees.json`

```json
{
  "setup-worktree": ["npm install"],
  "setup-worktree-unix": ["./setup.sh"],
  "setup-worktree-windows": ["setup.bat"]
}
```

### Execution Flow (`ensureWorktreeSetupAndRun`)

**Location**: Lines 487323-487447

1. Check for config in worktree, then root workspace
2. Parse platform-specific setup commands
3. Start terminal session in worktree directory
4. Set `ROOT_WORKTREE_PATH` environment variable
5. Execute commands sequentially with logging
6. Handle errors gracefully

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `worktrees_bon_judge` | true | Best-of-N judging for worktrees |
| `replace_files_on_worktree_apply` | false | Replace vs merge on apply |
| `worktree_nal_only` | true | NAL-only mode for worktrees |

## Key File Locations in Source

| Component | Line Number |
|-----------|-------------|
| WorktreeManager class | 960414-960670 |
| Worktree class | 960136-960410 |
| WorktreeCleanupCron | 960068-960124 |
| createWorktree (ComposerDataService) | 298880-298912 |
| applyWorktreeToCurrentBranch | 945414-945417 |
| _applyWorktreeToCurrentBranchViaMerge | 948390-948710 |
| removeComposerWorktreeIfPresent | 298450-298470 |
| Setup script runner | 487323-487447 |
| Worktree constants | 267275-267278 |

## Further Investigation Areas

1. **Best-of-N Integration** - How multiple parallel worktrees are managed and judged
2. **Background Agent Worktrees** - Cloud-based worktree synchronization
3. **Merge Conflict Resolution** - Detailed patch generation algorithm
4. **PR Creation Flow** - GitHub integration for worktree PRs
