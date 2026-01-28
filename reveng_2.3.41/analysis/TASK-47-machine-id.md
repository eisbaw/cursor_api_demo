# TASK-47: Machine ID/Device Fingerprinting Analysis

## Overview

Cursor IDE uses multiple machine identifiers for telemetry, anti-abuse detection, and device tracking. This analysis documents how `machineId`, `macMachineId`, `sqmId`, and `devDeviceId` are derived from hardware identifiers.

## Source Locations

### Main Process (main.js)
- **Module:** `out-build/vs/base/node/id.js`
- **MAC Address Module:** `out-build/vs/base/node/macAddress.js`
- **Telemetry Storage Keys:** `out-build/vs/platform/telemetry/common/telemetry.js`

### Renderer Process (workbench.desktop.main.js)
- **AbuseService:** Line 831668 (`Byo = on("abuseService")`)
- **Header Injection:** Line 268885 (`Gyh` function)
- **Configuration Access:** Line 1113990 (`get machineId()`)

## Machine ID Types

### 1. machineId (Primary)

**Purpose:** Primary device identifier, stored in telemetry and used in `x-cursor-checksum` header.

**Storage Key:** `telemetry.machineId`

**Generation Algorithm:**

```javascript
// Platform-specific commands (C6 object in main.js)
const commands = {
    darwin: "ioreg -rd1 -c IOPlatformExpertDevice",
    win32: `${systemPath}\\REG.exe QUERY HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid`,
    linux: "( cat /var/lib/dbus/machine-id /etc/machine-id 2> /dev/null || hostname ) | head -n 1 || :",
    freebsd: "kenv -q smbios.system.uuid || sysctl -n kern.hostuuid"
};
```

**Processing:**

1. Execute platform-specific command (5 second timeout)
2. Parse output using `RL` function:
   - **macOS:** Extract value after `IOPlatformUUID`
   - **Windows:** Parse registry output for MachineGuid
   - **Linux:** Use raw output (machine-id or hostname)
3. Hash with SHA-256: `crypto.createHash("sha256").update(rawId, "utf8").digest("hex")`
4. Store as 64-character hex string

**Platform Details:**

| Platform | Source | Format |
|----------|--------|--------|
| macOS | `IOPlatformExpertDevice` registry | UUID |
| Windows | `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid` | GUID |
| Linux | `/var/lib/dbus/machine-id` or `/etc/machine-id` | 32-char hex |
| FreeBSD | SMBIOS UUID or kern.hostuuid | UUID |

### 2. macMachineId (MAC Address Based)

**Purpose:** Secondary identifier based on network interface MAC address.

**Storage Key:** `telemetry.macMachineId`

**Generation Algorithm:**

```javascript
// Invalid MAC addresses to filter (S6/dH set)
const invalidMACs = new Set([
    "00:00:00:00:00:00",  // Null MAC
    "ff:ff:ff:ff:ff:ff",  // Broadcast
    "ac:de:48:00:11:22"   // Docker default
]);

// MAC validation function (CL/hH)
function isValidMAC(mac) {
    const normalized = mac.replace(/\-/g, ":").toLowerCase();
    return !invalidMACs.has(normalized);
}

// MAC retrieval (PL/fH function)
function getMAC() {
    const interfaces = os.networkInterfaces();
    for (const name in interfaces) {
        const netInterface = interfaces[name];
        if (netInterface) {
            for (const { mac } of netInterface) {
                if (isValidMAC(mac)) {
                    return mac;
                }
            }
        }
    }
    throw new Error("Unable to retrieve mac address");
}

// Final hash
function getMacMachineId() {
    try {
        const mac = getMAC();
        return crypto.createHash("sha256").update(mac, "utf8").digest("hex");
    } catch (err) {
        return crypto.randomUUID();  // Fallback to random UUID
    }
}
```

**Characteristics:**
- First valid (non-null, non-broadcast) MAC address found
- SHA-256 hashed
- Falls back to random UUID if no valid MAC found

### 3. sqmId (SQM Client ID - Windows Only)

**Purpose:** Windows Software Quality Metrics identifier.

**Storage Key:** `telemetry.sqmId`

**Source:** Windows Registry
```
HKEY_LOCAL_MACHINE\Software\Microsoft\SQMClient\MachineId
```

**Generation:**
```javascript
async function getSqmId() {
    if (process.platform === 'win32') {
        const registry = await import("@vscode/windows-registry");
        try {
            return registry.GetStringRegKey(
                "HKEY_LOCAL_MACHINE",
                "Software\\Microsoft\\SQMClient",
                "MachineId"
            ) || "";
        } catch (err) {
            return "";
        }
    }
    return "";
}
```

**Notes:**
- Windows-only identifier
- Not hashed (used directly from registry)
- Empty string on non-Windows platforms

### 4. devDeviceId (VSCode Device ID)

**Purpose:** Device ID from `@vscode/deviceid` package.

**Storage Key:** `telemetry.devDeviceId`

**Generation:**
```javascript
async function getDevDeviceId() {
    try {
        const { getDeviceId } = await import("@vscode/deviceid");
        return await getDeviceId();
    } catch (err) {
        return crypto.randomUUID();  // Fallback
    }
}
```

**Notes:**
- Uses VSCode's official device ID package
- Platform-specific implementation in the package
- Falls back to random UUID on error

## Virtual Machine Detection

The code includes detection for virtual machine MAC addresses:

```javascript
// Virtual Machine OUI (Organizationally Unique Identifier) prefixes
const vmOUIs = {
    "00-50-56": true,  // VMware
    "00-0C-29": true,  // VMware
    "00-05-69": true,  // VMware
    "00-03-FF": true,  // HyperV
    "00-1C-42": true,  // Parallels
    "00-16-3E": true,  // Xen
    "08-00-27": true   // VirtualBox
};

// Also supports colon-separated format
// "00:50:56", "00:0C:29", etc.
```

This data is used to calculate a "virtual machine ratio" for telemetry purposes:
```javascript
// Calculate VM ratio from network interfaces
let vmCount = 0;
let totalCount = 0;
const interfaces = os.networkInterfaces();
for (const name in interfaces) {
    for (const { mac, internal } of interfaces[name]) {
        if (!internal) {
            totalCount++;
            if (isVirtualMachineMacAddress(mac.toUpperCase())) {
                vmCount++;
            }
        }
    }
}
const vmRatio = totalCount > 0 ? vmCount / totalCount : 0;
```

## AbuseService Integration

The `AbuseService` in the renderer process provides access to machine IDs:

```javascript
// From workbench.desktop.main.js line 1098225
class CursorAuthenticationService {
    constructor() {
        // Async initialization of machine IDs
        this.abuseService.getMachineId()
            .then(id => this._machineId = id)
            .catch(() => {});
        this.abuseService.getMacMachineId()
            .then(id => this._macMachineId = id)
            .catch(() => {});
    }
}

// IPC proxy methods (line 832772)
async $getMachineId() {
    return this.abuseService.getMachineId();
}

async $getMacMachineId() {
    return this.abuseService.getMacMachineId();
}
```

## x-cursor-checksum Header Usage

The machine IDs are combined in the `x-cursor-checksum` header:

```javascript
// From Gyh function at line 268885
function setChecksumHeader(req, machineId, macMachineId, base64Fn) {
    const timestamp = Math.floor(Date.now() / 1e6);
    const bytes = new Uint8Array([
        (timestamp >> 40) & 255,
        (timestamp >> 32) & 255,
        (timestamp >> 24) & 255,
        (timestamp >> 16) & 255,
        (timestamp >> 8) & 255,
        timestamp & 255
    ]);
    const obfuscated = Jyh(bytes);  // Rolling XOR cipher
    const encoded = base64Fn(obfuscated);

    // Header format: {8-char timestamp}{machineId}[/{macMachineId}]
    const checksum = macMachineId === undefined
        ? `${encoded}${machineId}`
        : `${encoded}${machineId}/${macMachineId}`;

    req.header.set("x-cursor-checksum", checksum);
}
```

## Telemetry Common Properties

All machine IDs are included in telemetry common properties:

```javascript
// From Z2m function (line 344174)
commonProperties["common.machineId"] = machineId;
commonProperties["common.macMachineId"] = macMachineId;
commonProperties["common.sqmId"] = sqmId;
commonProperties["common.devDeviceId"] = devDeviceId;
```

## Storage Locations

| Key | Scope | Description |
|-----|-------|-------------|
| `telemetry.machineId` | Application | SHA-256 of platform UUID |
| `telemetry.macMachineId` | Application | SHA-256 of MAC address |
| `telemetry.sqmId` | Application | Windows SQM Client ID |
| `telemetry.devDeviceId` | Application | VSCode device ID |
| `telemetry.firstSessionDate` | Application | First launch timestamp |
| `telemetry.lastSessionDate` | Application | Last launch timestamp |
| `telemetry.currentSessionDate` | Application | Current session timestamp |

## Privacy Considerations

1. **Hashing:** `machineId` and `macMachineId` are SHA-256 hashed before storage/transmission
2. **Persistence:** IDs are stored persistently in application storage
3. **Tracking:** Same device will have consistent IDs across sessions
4. **Cross-Platform:** Different algorithms per platform may affect ID consistency

## Security Implications

1. **Device Fingerprinting:** Combination of multiple IDs creates strong device fingerprint
2. **Anti-Abuse:** IDs used to detect rate limiting evasion and multi-accounting
3. **VM Detection:** Virtual machine detection may affect service behavior
4. **Spoofing Risk:** IDs derived from modifiable system properties (MAC, hostname)

## Related Tasks

- TASK-18: x-cursor-checksum algorithm (uses these IDs)
- TASK-76: Privacy mode implementation
- TASK-29: Auth schemas (includes device identification)
