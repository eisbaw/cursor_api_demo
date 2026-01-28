# TASK-121: @vscode/deviceid Package Implementation Analysis

## Overview

The `@vscode/deviceid` npm package (microsoft/vscode-deviceid) is used by Cursor IDE to generate the `devDeviceId` telemetry identifier. Unlike other machine identifiers in VSCode/Cursor that derive from hardware properties, this package generates and persists a random UUID.

## Source References

### Package Import Location (main.js line 64)
```javascript
async function E6(t) {
    try {
        return await (await import("@vscode/deviceid")).getDeviceId();
    } catch (e) {
        return t(e), li();  // Fallback to random UUID
    }
}
```

### Storage Key
- **Key:** `telemetry.devDeviceId`
- **Scope:** Application-level storage

## Package Implementation Details

Based on analysis of the @vscode/deviceid GitHub repository (microsoft/vscode-deviceid):

### Architecture
- **Language Composition:** TypeScript (46.2%), C++ (42.5%), Python (11.3%)
- **Key Feature:** Uses native bindings on Windows, file-based storage on Unix-like systems

### Core Algorithm (devdeviceid.ts)

```typescript
import { v4 as uuidv4 } from "uuid";
import * as storage from "./storage.js";

export async function getDeviceId(): Promise<string> {
    let deviceId: string | undefined;
    try {
        deviceId = await storage.getDeviceId();
    } catch (e) {
        // Regenerate the deviceId if it cannot be read
    }

    if (deviceId) {
        return deviceId;
    } else {
        const newDeviceId = uuidv4().toLowerCase();
        await storage.setDeviceId(newDeviceId);
        return newDeviceId;
    }
}
```

**Key Characteristics:**
1. Does NOT use hardware identifiers
2. Generates a random UUID v4 on first run
3. Persists the ID for subsequent reads
4. Returns lowercase UUID format

### Platform-Specific Storage

| Platform | Storage Location | Method |
|----------|------------------|--------|
| Windows | Windows Registry | Native C++ bindings via `windows.node` |
| macOS | `~/Library/Application Support/Microsoft/DeveloperTools/deviceid` | File-based |
| Linux | `$XDG_CACHE_HOME/Microsoft/DeveloperTools/deviceid` (or `~/.cache/...`) | File-based |

#### Windows Implementation
- Uses native bindings from `../build/Release/windows.node`
- Methods: `windowRegistry.GetDeviceId()`, `windowRegistry.SetDeviceId(deviceId)`
- Registry-based storage (specific key not documented)

#### macOS/Linux Implementation
- Uses `fs-extra` library for file operations
- Creates directories via `fs.ensureDir()`
- Reads/writes UTF-8 encoded string file

## Comparison with Other Machine IDs

| Identifier | Source | Persistence | Platform-Specific |
|------------|--------|-------------|-------------------|
| `machineId` | SHA-256(Platform UUID) | Application storage | Yes (ioreg/registry/machine-id) |
| `macMachineId` | SHA-256(MAC address) | Application storage | No (uses os.networkInterfaces) |
| `sqmId` | Windows SQMClient registry | Application storage | Windows only |
| `devDeviceId` | Random UUID | Dedicated storage file/registry | Yes (different storage paths) |
| `serviceMachineId` | Random UUID | `machineid` file in user data | No |

## Stability Analysis

### devDeviceId Stability

**More stable than:**
- `macMachineId` - survives network adapter changes
- `machineId` on Linux - survives hostname changes

**Less stable than:**
- Hardware-derived `machineId` on Windows/macOS

**Persistence survives:**
- Hardware replacements (network cards, disks)
- OS minor updates
- Application reinstalls (if storage location preserved)

**Persistence does NOT survive:**
- Fresh OS reinstall
- Manual deletion of storage file
- Windows registry reset (on Windows)

### Storage Location Implications

The separation from VSCode's application storage directory means:
1. `devDeviceId` persists independently of Cursor/VSCode uninstallation
2. Multiple VSCode-based editors share the same `devDeviceId`
3. System administrators could deploy a shared device ID across machines

## Telemetry Integration

### Common Properties (workbench.desktop.main.js line 344174)
```javascript
f["common.machineId"] = r;
f["common.macMachineId"] = o;
f["common.sqmId"] = a;
f["common.devDeviceId"] = l;
```

### Telemetry Service Access (workbench.desktop.main.js line 1131071)
```javascript
get devDeviceId() {
    return this.impl.devDeviceId;
}
```

### Configuration Pass-Through (workbench.desktop.main.js line 1114000)
```javascript
get devDeviceId() {
    return this.configuration.devDeviceId;
}
```

## Usage in Cursor-Specific Code

### Header Construction (line 268907)
The `devDeviceId` is NOT directly used in the `x-cursor-checksum` header, which uses only:
- `machineId`
- `macMachineId` (optional)

However, it is sent as part of telemetry common properties.

### IPC Proxy Methods (line 832772)
```javascript
async $getMachineId() {
    return this.abuseService.getMachineId();
}
async $getMacMachineId() {
    return this.abuseService.getMacMachineId();
}
```
Note: No `$getDevDeviceId()` - suggesting it's only accessed via configuration.

## Fallback Mechanism

If the `@vscode/deviceid` package fails:
```javascript
async function E6(t) {
    try {
        return await (await import("@vscode/deviceid")).getDeviceId();
    } catch (e) {
        return t(e), li();  // li() returns crypto.randomUUID()
    }
}
```

The fallback generates a new random UUID without persistence, meaning:
- Device tracking breaks on each session
- Telemetry analytics lose device correlation

## Privacy and Security Considerations

### Positive Aspects
1. No hardware fingerprinting
2. User-deletable storage location
3. Not included in API request headers (unlike machineId)

### Potential Concerns
1. Cross-application tracking (shared Microsoft developer tools directory)
2. Survives application uninstall
3. Could correlate usage across VSCode, Cursor, and other Microsoft dev tools

## Differences from Built-in machineId

| Aspect | machineId | devDeviceId |
|--------|-----------|-------------|
| Generation | Platform-specific command execution | Random UUID v4 |
| Derivation | Hardware identifiers (IOPlatformUUID, MachineGuid, machine-id) | None |
| Processing | SHA-256 hashed | Stored as-is (lowercase) |
| Stability | Tied to hardware/OS | Tied to storage file |
| Portability | Cannot be transferred | File can be copied |

## Related Tasks

- **TASK-47:** Machine ID/Device Fingerprinting Analysis (comprehensive machine ID documentation)
- **TASK-18:** x-cursor-checksum algorithm
- **TASK-76:** Privacy mode implementation

## Future Investigation Avenues

1. **Windows Registry Key:** The specific registry key used by the native Windows binding is not documented - could be investigated by examining the C++ source
2. **Cross-Tool Correlation:** Test whether VSCode, Cursor, and other Microsoft dev tools share the same devDeviceId
3. **Native Binding Analysis:** The `windows.node` native module may contain additional functionality not documented

## Conclusion

The `@vscode/deviceid` package takes a fundamentally different approach from traditional machine ID generation:

1. **Random Generation:** Uses cryptographically random UUIDs instead of hardware fingerprinting
2. **Persistent Storage:** Stores the ID in platform-appropriate locations outside the application
3. **Simple Algorithm:** No hashing or obfuscation - just raw UUID storage
4. **Cross-Application:** Designed to be shared across Microsoft developer tools

This makes `devDeviceId` more privacy-respecting than hardware-derived identifiers, but creates a different tracking surface through shared storage locations.
