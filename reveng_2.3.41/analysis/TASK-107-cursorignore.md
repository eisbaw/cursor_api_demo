# TASK-107: CursorIgnore Service and Pattern Compilation Analysis

## Overview

The CursorIgnore service (`cursorIgnoreService`) is a critical security component in Cursor IDE that controls which files can be read by AI features. It implements a multi-layered ignore system similar to `.gitignore`, but specifically designed to prevent AI tools from accessing sensitive files.

**Source File:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
**Primary Implementation:** Lines 441728-442344 (nTs class)

## Service Registration

The service is registered as a singleton with the identifier `cursorIgnoreService`:

```javascript
// Line 441730
Vk = on("cursorIgnoreService")

// Registration (Line 442344)
Rn(Vk, nTs, 1)
```

## Core Data Structures

### Internal State

```javascript
// Lines 441731-441733
this._ignoreMapping = {};           // Map: directory URI -> ignore instance or "no-ignore"
this._ignorePatternsMapping = {};   // Map: directory URI -> pattern strings array
this._pendingIgnorePaths = new Set; // Paths being loaded
this._globalIgnorePatterns = [];    // Global ignore patterns from settings
this._ignoreLoadedCallbacks = [];   // Callbacks waiting for initialization
this._ignoreLoaded = false;         // Initialization complete flag
this._gitRepoLocations = [];        // Git repository paths
this._gitRepoUpstreamUrls = new Map; // Git root -> upstream URL mapping
this._cache = new Xp(2000, 0.5);    // LRU cache for shouldIgnore results
```

### Ignore Result Types

The service returns structured ignore results with different types:

```javascript
// Type definitions (from shouldIgnoreUriWithWorkspaceFolders)
{ type: "adminBlock" }        // Blocked by admin/team settings
{ type: "cursorIgnore", source: string }  // Blocked by .cursorignore pattern
{ type: "outOfWorkspace" }    // File outside workspace
{ type: "dotFile" }           // Hidden file (starts with .)
```

## Pattern Compilation Engine (XPc class)

The pattern compilation is handled by the `XPc` class (lines 436486-436556), which is an implementation of gitignore-style pattern matching:

### Pattern to Regex Transformation Rules

The `qPc` array (lines 436450-436470) defines the transformation pipeline:

```javascript
const qPc = [
    // Remove BOM
    [/^\uFEFF/, () => ""],

    // Handle trailing whitespace
    [/\\?\s+$/, i => i.indexOf("\\") === 0 ? " " : ""],

    // Escape special characters
    [/[\\$.|*+(){^]/g, i => `\\${i}`],

    // Convert ? to [^/] (any char except /)
    [/(?!\\)\?/g, () => "[^/]"],

    // Handle leading slash (anchored)
    [/^\//, () => "^"],

    // Escape forward slashes
    [/\//g, () => "\\/"],

    // Handle ** at start (match any path prefix)
    [/^\^*\\\*\\\*\\\//, () => "^(?:.*\\/)?"],

    // Handle non-anchored patterns
    [/^(?=[^^])/, function() {
        return /\/(?!$)/.test(this) ? "^" : "(?:^|\\/)"
    }],

    // Handle **/ in middle (match any directory depth)
    [/\\\/\\\*\\\*(?=\\\/|$)/g, (i, e, t) =>
        e + 6 < t.length ? "(?:\\/[^\\/]+)*" : "\\/.+"],

    // Handle * (any chars except /)
    [/(^|[^\\]+)(\\\*)+(?=.+)/g, (i, e, t) => {
        const n = t.replace(/\\\*/g, "[^\\/]*");
        return e + n
    }],

    // Handle character classes
    [/(\\)?\[([^\]/]*?)(\\*)($|\])/g, ...],

    // Handle end of pattern (match files or directories)
    [/(?:[^*])$/, i => /\/$/.test(i) ? `${i}$` : `${i}(?=$|\\/$)`],

    // Handle trailing *
    [/(\^|\\\/)?\\\*$/, (i, e) =>
        `${e?`${e}[^/]+`:"[^/]*"}(?=$|\\/$)`]
];
```

### Pattern Class Structure

```javascript
// Lines 436474-436477
class jPc {
    constructor(origin, pattern, negative, regex) {
        this.origin = origin;    // Original pattern string
        this.pattern = pattern;  // Processed pattern
        this.negative = negative; // Is negation pattern (!pattern)
        this.regex = regex;       // Compiled RegExp
    }
}
```

### XPc Ignore Instance

```javascript
// Lines 436486-436556
class XPc {
    constructor({ ignorecase = true, allowRelativePaths = false } = {}) {
        this._rules = [];
        this._ignoreCase = ignorecase;
        this._allowRelativePaths = allowRelativePaths;
        this._initCache();
    }

    add(patterns) {
        // Add patterns (string or array)
        // Splits multiline strings by newline
        // Creates jPc rule objects
    }

    ignores(path) {
        // Returns true if path should be ignored
        return this._test(path, this._ignoreCache, false).ignored;
    }

    test(path) {
        // Returns { ignored: boolean, unignored: boolean }
        // unignored is true if negation pattern matched
    }

    _testOne(path, checkNegative) {
        // Tests single path against all rules
        // Returns { ignored, unignored }
    }
}

// Factory function
dbe = (options) => new XPc(options);
```

## File Parsing Logic

### parseIgnoreRules Method

```javascript
// Lines 442249-442251
parseIgnoreRules(content) {
    return content.split('\n')
        .map(line => line.replace(/\r$/, '').trimStart())
        .filter(line => line !== '' && !line.startsWith('#'));
}
```

This:
1. Splits content by newlines
2. Removes carriage returns (Windows line endings)
3. Trims leading whitespace
4. Filters out empty lines and comments (#)

## Initialization Flow

### 1. Constructor Initialization

```javascript
// Line 441788
this.initializeGlobalIgnoreList();
this.initializeIgnoreMapping();
this.repositoryService.setIsUriCursorIgnored(
    uri => this.shouldBlockUriFromReading(uri)
);
```

### 2. Global Ignore List (cursor.general.globalCursorIgnoreList)

```javascript
// Lines 441856-441860
initializeGlobalIgnoreList() {
    const patterns = this.configurationService.getValue(hes) || [];
    // hes = "cursor.general.globalCursorIgnoreList" (Line 14777)
    this._globalIgnorePatterns = patterns;
    if (patterns.length > 0) {
        this._globalIgnore = dbe({ allowRelativePaths: true }).add(patterns);
    } else {
        this._globalIgnore = undefined;
    }
}
```

### 3. Workspace Ignore Files

```javascript
// Lines 441865-441917
async initializeIgnoreMapping() {
    const folders = this.workspaceContextService.getWorkspace().folders;

    // Search for all .cursorignore files in workspace
    const query = this._queryBuilder.file(folders, {
        _reason: "cursorIgnoreCheck",
        includePattern: ["**/.cursorignore"],
        maxResults: 0,
        ignoreSymlinks: ignoreSymlinksOption
    });

    const results = await this.searchService.fileSearch(query, token);

    // Process each .cursorignore file
    for (const result of results.results) {
        const content = await this.fileService.readFile(result.resource);
        const rules = this.parseIgnoreRules(content.value.toString());
        const baseDir = result.resource.toString()
            .substring(0, result.resource.toString().lastIndexOf(".cursorignore"));

        if (rules.length > 0) {
            this._ignoreMapping[baseDir] = dbe().add(rules);
            this._ignorePatternsMapping[baseDir] = rules;
        } else {
            this._ignoreMapping[baseDir] = "no-ignore";
            this._ignorePatternsMapping[baseDir] = "no-ignore";
        }
    }

    // Load hierarchical .cursorignore files if enabled
    if (hierarchicalEnabled) {
        for (const folder of folders) {
            const dirs = this.collectHierarchicalDirectories(folder.uri);
            for (const dir of dirs) {
                await this.handleNewHierarchyCursorIgnore(dir);
            }
        }
    }

    this._ignoreLoaded = true;
    this._ignoreLoadedCallbacks.forEach(cb => cb());
}
```

## Hierarchical Mode

When `cursorIgnore.hierarchicalEnabled` is true, the service looks for `.cursorignore` files in parent directories:

```javascript
// Lines 441933-441947
collectHierarchicalDirectories(uri, options = { skipWorkspace: false }) {
    const dirs = [];
    let current = uri;
    let depth = 0;
    const maxDepth = 100;

    while (parent(current) !== current) {
        if (depth >= maxDepth) break;
        current = parent(current);

        // Ensure trailing slash
        if (!current.toString().endsWith("/")) {
            current = URI.parse(current.toString() + "/");
        }

        // Skip if already loaded or in workspace
        if (options.skipWorkspace &&
            this.workspaceContextService.isInsideWorkspace(current) &&
            this._ignoreLoaded) continue;

        if (this._ignoreMapping[current.toString()] === undefined) {
            dirs.push(current);
            depth++;
        }
    }
    return dirs;
}
```

## File Watcher Integration

The service monitors `.cursorignore` file changes in real-time:

```javascript
// Lines 441740-441771
this._register(this.fileService.onDidFilesChange(async event => {
    // Handle added .cursorignore files
    if (event.gotAdded()) {
        const added = event.rawAdded.filter(f => f.path.endsWith(".cursorignore"));
        for (const file of added) {
            const content = await this.fileService.readFile(URI.parse(file.path));
            const rules = this.parseIgnoreRules(content.value.toString());
            const baseDir = file.path.substring(0, file.path.lastIndexOf(".cursorignore"));

            if (rules.length > 0) {
                this._ignoreMapping[baseDir] = dbe().add(rules);
                this._ignorePatternsMapping[baseDir] = rules;
            } else {
                this._ignoreMapping[baseDir] = "no-ignore";
                this._ignorePatternsMapping[baseDir] = "no-ignore";
            }
            this._onDidCursorIgnoreChange.fire({});
        }
    }

    // Handle deleted .cursorignore files
    if (event.gotDeleted()) {
        const deleted = event.rawDeleted.filter(f => f.path.endsWith(".cursorignore"));
        for (const file of deleted) {
            const baseDir = file.path.substring(0, file.path.lastIndexOf(".cursorignore"));
            delete this._ignoreMapping[baseDir];
            delete this._ignorePatternsMapping[baseDir];
        }
        if (deleted.length > 0) this._onDidCursorIgnoreChange.fire({});
    }

    // Handle modified .cursorignore files
    for (const dir of Object.keys(this._ignoreMapping)) {
        const ignoreFile = URI.parse(dir + ".cursorignore");
        if (event.contains(ignoreFile)) {
            const content = await this.fileService.readFile(ignoreFile);
            const rules = this.parseIgnoreRules(content.value.toString());
            // Update mapping...
        }
    }
}));
```

## Path Matching Logic

### shouldIgnoreUriWithWorkspaceFolders (Core Logic)

```javascript
// Lines 441978-442066
shouldIgnoreUriWithWorkspaceFolders(uri, options, workspaceFolders) {
    // 1. Check admin blocklist first
    if (this.isAdminBlocked(uri)) {
        return { type: "adminBlock" };
    }

    // 2. Only handle file:// and vscode-remote:// schemes
    if (uri.scheme !== "file" && uri.scheme !== "vscodeRemote") {
        return undefined;
    }

    // 3. Check if outside workspace
    if (workspaceFolders.length === 0 && !options?.gitWorktree) {
        return { type: "outOfWorkspace" };
    }

    // 4. Check pending hierarchical loading
    const stillLoading = options?.gitWorktree ? false :
        this.populatesHierarchyCursorIgnore(uri);

    // 5. Check all .cursorignore mappings
    let wasUnignored = false;
    for (const [dirPath, ignoreInstance] of Object.entries(this._ignoreMapping)) {
        const dir = URI.parse(dirPath);

        // Skip if URI is not under this directory
        if (!this.uriIdentityService.extUri.isEqualOrParent(uri, dir)) continue;

        // Get relative path
        const relativePath = this.uriIdentityService.extUri.relativePath(dir, uri) ?? "";

        if (ignoreInstance === "no-ignore") continue;

        // Test against patterns
        const result = ignoreInstance.test(relativePath);

        if (result.ignored && !result.unignored) {
            return { type: "cursorIgnore", source: dirPath };
        }

        if (result.unignored) wasUnignored = true;
    }

    // 6. Check global ignore patterns
    if (!wasUnignored && this._globalIgnore) {
        // Get relative path from workspace
        let relativePath;
        const folder = workspaceFolders.find(f =>
            this.uriIdentityService.extUri.isEqualOrParent(uri, f.uri));

        if (folder) {
            relativePath = this.uriIdentityService.extUri.relativePath(folder.uri, uri) ?? "";
        } else {
            // Use just filename for out-of-workspace files
            const parts = uri.path.split("/");
            relativePath = parts[parts.length - 1];
        }

        if (this._globalIgnore.ignores(relativePath)) {
            return { type: "cursorIgnore", source: "globalIgnore" };
        }
    }

    // 7. Check for dot files (hidden files)
    const folder = workspaceFolders.find(f =>
        this.uriIdentityService.extUri.isEqualOrParent(uri, f.uri));

    if (!folder) {
        return { type: "outOfWorkspace" };
    }

    const relativePath = this.uriIdentityService.extUri.relativePath(folder.uri, uri);

    // Check each path segment for dot prefix (except .cursor)
    const segments = (isWindows ? normalizeWindowsPath(relativePath) : relativePath).split("/");
    if (segments.some(segment =>
        segment.startsWith(".") && segment !== ".cursor" && segment.length > 1) &&
        !wasUnignored) {
        return { type: "dotFile" };
    }

    // 8. Return loading state if hierarchical still loading
    if (stillLoading) {
        return { type: "cursorIgnore", source: "hierarchical allow file list is still loading..." };
    }

    return undefined; // Not ignored
}
```

## Admin/Team Blocklist Integration

### isAdminBlocked Method

```javascript
// Lines 442154-442195
isAdminBlocked(uri) {
    const revived = URI.revive(uri);
    const fsPath = revived.scheme === "vscodeRemote" ? revived.path : revived.fsPath;
    const normalizedPath = this.normalizePathForComparison(fsPath);

    // Find longest matching git repo
    let matchedRepo = null;
    let matchedNormalized = null;
    let maxLength = 0;

    for (const repoPath of this._gitRepoUpstreamUrls.keys()) {
        const url = this._gitRepoUpstreamUrls.get(repoPath);
        if (url === undefined) continue;

        const normalizedRepo = this.normalizePathForComparison(repoPath);
        if (normalizedPath.startsWith(normalizedRepo) &&
            (normalizedPath.length === normalizedRepo.length ||
             normalizedPath[normalizedRepo.length] === "/") &&
            normalizedRepo.length > maxLength) {
            matchedRepo = repoPath;
            matchedNormalized = normalizedRepo;
            maxLength = normalizedRepo.length;
        }
    }

    // Check against team block repos
    if (this._gitReposInitialized && matchedRepo && matchedNormalized) {
        const upstreamUrl = this._gitRepoUpstreamUrls.get(matchedRepo);
        if (upstreamUrl) {
            const blockRepos = this.getAdminBlockRepos();
            const relativePath = normalizedPath.substring(matchedNormalized.length + 1);

            for (const blockRepo of blockRepos) {
                if (this.doesRepoUrlMatch(blockRepo.url, upstreamUrl) &&
                    blockRepo.patterns.some(p => glob(p.pattern, relativePath))) {
                    return true;
                }
            }
        }
        return false;
    }

    // Fallback: check blocklist patterns directly
    const blocklistPatterns = this.getAdminBlocklistPatterns();
    if (blocklistPatterns.length > 0) {
        for (const pattern of blocklistPatterns) {
            if (glob(pattern, uri.path)) return true;
        }
    }

    return false;
}
```

### Data Sources

```javascript
// Lines 441919-441923
getAdminBlocklistPatterns() {
    return this.reactiveStorageService.applicationUserPersistentStorage.teamBlocklist ?? [];
}

getAdminBlockRepos() {
    return this.reactiveStorageService.applicationUserPersistentStorage.teamBlockRepos ?? [];
}
```

## Sandbox Integration

### getSerializableIgnoreMapping

This method provides ignore patterns to the sandbox policy for terminal command execution:

```javascript
// Lines 442076-442088
getSerializableIgnoreMapping() {
    const result = { ...this._ignorePatternsMapping };

    // Merge global patterns into workspace folder entries
    if (this._globalIgnore && this._globalIgnorePatterns.length > 0) {
        const folders = this.workspaceContextService.getWorkspace().folders;
        for (const folder of folders) {
            const key = folder.uri.toString();
            const existing = result[key];

            if (existing === "no-ignore") {
                result[key] = [...this._globalIgnorePatterns];
            } else if (Array.isArray(existing)) {
                result[key] = [...this._globalIgnorePatterns, ...existing];
            } else {
                result[key] = [...this._globalIgnorePatterns];
            }
        }
    }
    return result;
}
```

### enrichPolicyWithCursorIgnore

Used by ShadowWorkspaceServer to add ignore mappings to sandbox policies:

```javascript
// Lines 1128664-1128672
enrichPolicyWithCursorIgnore(policy) {
    if (!policy || policy.type === INSECURE_NONE) return policy;
    try {
        const ignoreMapping = this.cursorIgnoreService.getSerializableIgnoreMapping();
        policy.ignore_mapping = ignoreMapping;
    } catch (error) {
        this.logService.warn("[ShadowWorkspaceServer] Failed to attach cursorignore mapping", error);
    }
    return policy;
}
```

### Sandbox Policy Serialization

```javascript
// Lines 835138-835159
function convertSandboxPolicy(policy, log) {
    // ...
    let ignoreMappingJson;
    if (policy.ignore_mapping) {
        try {
            ignoreMappingJson = JSON.stringify(policy.ignore_mapping);
        } catch (error) {
            log.warn("[MainThreadShellExec] Failed to serialize ignore_mapping:", error);
        }
    }

    return {
        type: SandboxType[policy.type],
        networkAccess: policy.networkAccess,
        additionalReadwritePaths: policy.additionalReadwritePaths ?? [],
        additionalReadonlyPaths: policy.additionalReadonlyPaths ?? [],
        blockGitWrites: policy.blockGitWrites,
        ignoreMappingJson: ignoreMappingJson,
        debugOutputDir: policy.debugOutputDir
    };
}
```

## Server Configuration (CursorIgnoreControls)

The server can control ignore behavior via protobuf message:

```javascript
// Lines 276395-276408
class CursorIgnoreControls {
    static typeName = "aiserver.v1.CursorIgnoreControls"
    static fields = [
        { no: 1, name: "hierarchical_enabled", kind: "scalar", T: 8 /* bool */ },
        { no: 2, name: "ignore_symlinks", kind: "scalar", T: 8 /* bool */ }
    ]
}
```

Applied in settings sync:

```javascript
// Lines 306028-306040
const hierarchicalEnabled = serverConfig?.cursorIgnoreControls?.hierarchicalEnabled ?? false;
const ignoreSymlinks = serverConfig?.cursorIgnoreControls?.ignoreSymlinks ?? false;

if (storage.applicationUserPersistentStorage.teamAdminSettings) {
    const settings = storage.applicationUserPersistentStorage.teamAdminSettings;
    const updated = {
        ...settings,
        cursorIgnore: {
            ...settings.cursorIgnore,
            hierarchicalEnabled: hierarchicalEnabled,
            ignoreSymlinks: ignoreSymlinks
        }
    };
    storage.setApplicationUserPersistentStorage("teamAdminSettings", updated);
}
```

## Event System

### onDidCursorIgnoreChange

Fired when ignore patterns change:

```javascript
// Line 441733
this._onDidCursorIgnoreChange = this._register(new Emitter());
this.onDidCursorIgnoreChange = this._onDidCursorIgnoreChange.event;

// Cache invalidation on change
this._register(this._onDidCursorIgnoreChange.event(() => {
    this._cache.clear();
}));
```

### Extension Host Notification

```javascript
// Lines 831823-831824
this._register(this.cursorIgnoreService.onDidCursorIgnoreChange(() => {
    this._proxy.$triggerCursorIgnoredFilesChange();
}));
```

## Public API

| Method | Description |
|--------|-------------|
| `shouldIgnoreUri(uri, options)` | Async: checks if URI should be ignored (resolves symlinks) |
| `shouldIgnoreUriSync(uri, options)` | Sync: cached check if URI should be ignored |
| `shouldBlockUriFromReading(uri)` | Returns true if URI should block AI reading |
| `filterCursorIgnoredFiles(files, getUri)` | Filters array, removing ignored files |
| `getSerializableIgnoreMapping()` | Returns patterns for sandbox policy |
| `addOnCursorIgnoreLoadedCallback(cb)` | Register callback for when loading complete |
| `reloadCursorIgnoreForDirectory(uri)` | Reload ignore file for specific directory |
| `listCursorIgnoreFilesByRoot(roots, token)` | List all .cursorignore files under roots |

## Usage Throughout Codebase

The service is used extensively:

1. **File listing operations** (Line 470333):
   ```javascript
   const filtered = await cursorIgnoreService.filterCursorIgnoredFiles(
       children, file => URI.joinPath(baseUri, file.name));
   ```

2. **Context file collection** (Line 476093):
   ```javascript
   const files = await this.cursorIgnoreService.filterCursorIgnoredFiles(
       allFiles, file => file.uri);
   ```

3. **Search results** (Lines 477770, 478096, 478299, 478324, 478373):
   ```javascript
   results = await this.cursorIgnoreService.filterCursorIgnoredFiles(
       results, r => URI.joinPath(root, r.file));
   ```

4. **Repository service** (Line 441788):
   ```javascript
   this.repositoryService.setIsUriCursorIgnored(
       uri => this.shouldBlockUriFromReading(uri));
   ```

5. **File deletion tool** (Line 480465):
   ```javascript
   if (ignoreResult?.type === "adminBlock") {
       throw new Error("Admin blocked file deletion");
   }
   ```

## Worktree Support

Special handling for git worktrees:

```javascript
// Lines 441839-441849
cleanupWorktreeCursorIgnoreEntries(worktreePath) {
    const worktreeUri = URI.file(worktreePath);
    const toRemove = [];

    for (const key of Object.keys(this._ignoreMapping)) {
        const uri = URI.parse(key);
        if (this.uriIdentityService.extUri.isEqualOrParent(uri, worktreeUri)) {
            toRemove.push(key);
        }
    }

    if (toRemove.length > 0) {
        for (const key of toRemove) {
            delete this._ignoreMapping[key];
            delete this._ignorePatternsMapping[key];
        }
        this.logService.info(`[CursorIgnore] Cleaned up ${toRemove.length} entries for worktree at ${worktreePath}`);
        this._onDidCursorIgnoreChange.fire({});
    }
}
```

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `cursor.general.globalCursorIgnoreList` | Global ignore patterns array | `[]` |
| `cursorIgnore.hierarchicalEnabled` | Look for .cursorignore in parent directories | `false` |
| `cursorIgnore.ignoreSymlinks` | Ignore symlinked files during search | `false` |

## Security Considerations

1. **Admin blocklists take priority** - Checked first in `shouldIgnoreUriWithWorkspaceFolders`
2. **Dot files auto-blocked** - Files starting with `.` (except `.cursor`) are blocked by default
3. **Out-of-workspace blocked** - Files outside workspace folders return `outOfWorkspace`
4. **Sandbox integration** - Patterns passed to sandbox layer for enforcement
5. **Real path resolution** - Symlinks are resolved to prevent bypass

## Dependencies

- `fileService` - File reading and watching
- `searchService` - Finding .cursorignore files
- `workspaceContextService` - Workspace folder information
- `configurationService` - Global settings
- `reactiveStorageService` - Team/admin settings
- `gitContextService` - Git repo information for admin blocks
- `uriIdentityService` - Path comparison utilities
- `worktreeManagerService` - Worktree lifecycle events
