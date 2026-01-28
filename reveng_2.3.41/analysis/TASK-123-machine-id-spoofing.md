# TASK-123: Machine ID Spoofing Techniques Analysis

## Overview

This document analyzes the machine ID fingerprinting system in Cursor IDE 2.3.41 and documents potential spoofing vectors for research and testing purposes. Understanding these mechanisms is essential for security research and testing environments where device fingerprint manipulation may be necessary.

**IMPORTANT**: This analysis is for research/testing purposes only. Spoofing machine IDs may violate Cursor's Terms of Service.

## Machine ID Architecture

Cursor uses multiple layered identifiers for device fingerprinting:

| Identifier | Source | Storage | Hash Algorithm | Spoofing Difficulty |
|------------|--------|---------|----------------|---------------------|
| `machineId` | Platform UUID | `storage.serviceMachineId` | SHA-256 | Medium |
| `macMachineId` | MAC Address | Telemetry storage | SHA-256 | Easy |
| `sqmId` | Windows Registry | Telemetry storage | None (raw) | Easy (Windows) |
| `devDeviceId` | @vscode/deviceid | Telemetry storage | Package-specific | Medium |

## Detailed ID Generation Analysis

### 1. machineId Generation

**Source locations:**
- Module: `out-build/vs/base/node/id.js` (in main.js)
- Renderer access: Line 1113991 (`get machineId()`)
- Storage: Line 352912-352927 (`Pft` function)

**Platform-specific commands:**

```javascript
// Platform commands for machine ID retrieval
const commands = {
    darwin: "ioreg -rd1 -c IOPlatformExpertDevice",
    win32: `${systemPath}\\REG.exe QUERY HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid`,
    linux: "( cat /var/lib/dbus/machine-id /etc/machine-id 2> /dev/null || hostname ) | head -n 1 || :",
    freebsd: "kenv -q smbios.system.uuid || sysctl -n kern.hostuuid"
};
```

**Processing flow:**
1. Execute platform command with 5-second timeout
2. Parse output for UUID/GUID value
3. Hash with SHA-256: `crypto.createHash("sha256").update(rawId, "utf8").digest("hex")`
4. Store as 64-character hex string

**Storage persistence:**
- Stored in: `{userDataPath}/machineid` file
- Cached in: `storage.serviceMachineId` (IndexedDB/SQLite)
- Validated using UUID regex: `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i`

### 2. macMachineId Generation

**Source locations:**
- Module: `out-build/vs/base/node/macAddress.js` (in main.js)
- AbuseService access: Line 832775-832776

**Algorithm:**
```javascript
// Invalid MAC addresses that are filtered
const invalidMACs = new Set([
    "00:00:00:00:00:00",  // Null MAC
    "ff:ff:ff:ff:ff:ff",  // Broadcast
    "ac:de:48:00:11:22"   // Docker default
]);

function getMacMachineId() {
    const interfaces = os.networkInterfaces();
    for (const name in interfaces) {
        for (const { mac } of interfaces[name]) {
            const normalized = mac.replace(/-/g, ":").toLowerCase();
            if (!invalidMACs.has(normalized)) {
                return crypto.createHash("sha256").update(mac, "utf8").digest("hex");
            }
        }
    }
    return crypto.randomUUID();  // Fallback
}
```

**Key observations:**
- First valid (non-null, non-broadcast) MAC address is used
- Order depends on OS enumeration of network interfaces
- Falls back to random UUID if no valid MAC found

### 3. sqmId (Windows Only)

**Source:** Windows Registry
```
HKEY_LOCAL_MACHINE\Software\Microsoft\SQMClient\MachineId
```

**Notes:**
- Windows-only identifier
- Not hashed - used directly
- Empty string on non-Windows platforms

### 4. devDeviceId

**Source:** `@vscode/deviceid` npm package

This package uses platform-specific methods that likely include:
- Hardware serial numbers
- Platform-specific unique identifiers
- Fallback to generated UUIDs

**Note:** See TASK-121 for detailed investigation of this package.

## Header Integration: x-cursor-checksum

All machine IDs flow into the `x-cursor-checksum` header (documented in TASK-18):

```javascript
// From Gyh function at line 268885-268917
function setChecksumHeader(req, machineId, macMachineId) {
    const timestamp = Math.floor(Date.now() / 1e6);
    const bytes = new Uint8Array([
        (timestamp >> 40) & 255, (timestamp >> 32) & 255,
        (timestamp >> 24) & 255, (timestamp >> 16) & 255,
        (timestamp >> 8) & 255, timestamp & 255
    ]);
    const obfuscated = Jyh(bytes);  // Rolling XOR cipher with key 165
    const encoded = base64UrlSafe(obfuscated);

    // Header format: {8-char timestamp}{machineId}[/{macMachineId}]
    req.header.set("x-cursor-checksum",
        macMachineId ? `${encoded}${machineId}/${macMachineId}` : `${encoded}${machineId}`
    );
}
```

## Spoofing Vectors

### Vector 1: Modify machineId at Source

#### Linux

**Option A: Modify /etc/machine-id**
```bash
# Backup original
sudo cp /etc/machine-id /etc/machine-id.bak

# Generate new ID
uuidgen | tr -d '-' | sudo tee /etc/machine-id
# OR use specific value:
echo "aaaabbbbccccdddd1111222233334444" | sudo tee /etc/machine-id

# Restart Cursor to pick up new ID
```

**Option B: Modify /var/lib/dbus/machine-id**
```bash
sudo rm /var/lib/dbus/machine-id
sudo ln -s /etc/machine-id /var/lib/dbus/machine-id
```

**Impact:** machineId will be SHA-256 hash of the new value

#### Windows

**Registry modification:**
```powershell
# Backup original
$backup = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Cryptography").MachineGuid
$backup | Out-File "$env:USERPROFILE\machine-guid-backup.txt"

# Set new GUID (requires admin)
$newGuid = [guid]::NewGuid().ToString()
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name "MachineGuid" -Value $newGuid
```

**Warning:** This affects ALL applications that use MachineGuid, not just Cursor.

#### macOS

**Method:** The IOPlatformUUID is read from IOKit and cannot be modified without hardware changes. However, you can:

1. Use a VM with custom platform UUID
2. Intercept the `ioreg` command output

### Vector 2: Spoof macMachineId via MAC Address

This is the easiest vector as MAC addresses can be changed at the OS level.

#### Linux
```bash
# Using ip command
sudo ip link set eth0 down
sudo ip link set eth0 address 00:11:22:33:44:55
sudo ip link set eth0 up

# Using macchanger
sudo apt install macchanger
sudo macchanger -m 00:11:22:33:44:55 eth0
```

#### macOS
```bash
# Disconnect from network first
sudo ifconfig en0 ether 00:11:22:33:44:55
```

#### Windows
```powershell
# Via Device Manager or registry
Set-NetAdapter -Name "Ethernet" -MacAddress "00-11-22-33-44-55"

# Or via registry (requires reboot)
$adapter = Get-NetAdapter | Where-Object {$_.Name -eq "Ethernet"}
$path = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002bE10318}\$($adapter.DevicePath.Split('\')[-1])"
Set-ItemProperty -Path $path -Name "NetworkAddress" -Value "001122334455"
```

**Impact:** macMachineId will be SHA-256 hash of the new MAC

### Vector 3: Modify Cursor Storage Directly

#### Storage Location
```
# Linux
~/.config/Cursor/machineid
~/.config/Cursor/User/globalStorage/storage.json

# macOS
~/Library/Application Support/Cursor/machineid
~/Library/Application Support/Cursor/User/globalStorage/storage.json

# Windows
%APPDATA%\Cursor\machineid
%APPDATA%\Cursor\User\globalStorage\storage.json
```

#### Direct File Modification
```bash
# Linux/macOS
echo "your-custom-machine-id-uuid-format" > ~/.config/Cursor/machineid

# Also clear the cached storage value
# (Cursor will regenerate from the file on next start)
rm -rf ~/.config/Cursor/User/globalStorage/storage.json
```

**Note:** The machineid file must contain a valid UUID format string.

### Vector 4: Environment Interception

For more complete spoofing, intercept at the process level:

#### Using LD_PRELOAD (Linux)
```c
// spoof_machineid.c
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>

// Intercept fopen for /etc/machine-id
FILE *fopen(const char *path, const char *mode) {
    static FILE *(*real_fopen)(const char *, const char *) = NULL;
    if (!real_fopen) real_fopen = dlsym(RTLD_NEXT, "fopen");

    if (strcmp(path, "/etc/machine-id") == 0 ||
        strcmp(path, "/var/lib/dbus/machine-id") == 0) {
        // Return file with spoofed content
        return fmemopen("aaaabbbbccccdddd1111222233334444\n", 33, "r");
    }
    return real_fopen(path, mode);
}
```

```bash
gcc -shared -fPIC -o spoof_machineid.so spoof_machineid.c -ldl
LD_PRELOAD=./spoof_machineid.so cursor
```

### Vector 5: Virtual Machine with Custom IDs

The cleanest spoofing approach is running Cursor in a VM with custom:
- Platform UUID
- MAC address
- Any other hardware identifiers

#### QEMU/KVM
```bash
# Set custom machine UUID
qemu-system-x86_64 -uuid aaaabbbb-cccc-dddd-eeee-ffffffffffff \
    -net nic,macaddr=00:11:22:33:44:55 ...
```

#### VirtualBox
```bash
VBoxManage modifyvm "CursorVM" --hardwareuuid "aaaabbbb-cccc-dddd-eeee-ffffffffffff"
VBoxManage modifyvm "CursorVM" --macaddress1 001122334455
```

#### VMware
```
# In .vmx file
uuid.bios = "aaaabbbb-cccc-dddd-eeee-ffffffffffff"
ethernet0.address = "00:11:22:33:44:55"
```

**Bonus:** Using a non-VM MAC prefix avoids VM detection (see TASK-122).

## Server-Side Validation

Based on code analysis, the server receives:

1. **x-cursor-checksum header**: Contains obfuscated timestamp + machineId + optional macMachineId
2. **Telemetry data**: Contains all four IDs in common properties

### Potential Server-Side Checks

The server likely performs:

1. **Timestamp validation**: Reject requests with timestamps too far from server time
2. **ID consistency**: Track if machineId/macMachineId change frequently
3. **Pattern detection**: Flag accounts using identical machine IDs
4. **Rate limiting by ID**: Apply limits per machine, not just per account
5. **VM ratio tracking**: `isVMLikelyhood` telemetry may influence server decisions

### What We Cannot Determine

Client-side analysis cannot reveal:
- Exact server validation logic
- Whether ID changes trigger account flags
- If server maintains ID blacklists
- Rate limit quotas per machine ID

## Risks and Detection

### Detection Signals

Changing machine IDs may trigger server-side detection if:

1. **Frequent ID changes**: Same account with rapidly changing IDs
2. **ID collision**: Multiple accounts using identical spoofed IDs
3. **Impossible changes**: machineId change without macMachineId change (platform UUID change is rare)
4. **Pattern matching**: Using obviously fake IDs (all zeros, sequential, etc.)

### Mitigation Strategies

For research/testing with reduced detection risk:

1. **Use realistic values**: Generate proper UUIDs, use valid OUI prefixes for MACs
2. **Be consistent**: If spoofing, keep IDs stable within a session
3. **Match the platform**: If on Linux, don't use Windows registry IDs
4. **Avoid VM detection**: Use non-VM MAC prefixes (see TASK-122)

## Rate Limiting Impact

From TASK-80 analysis, rate limiting is primarily based on:

1. User tier (free/pro/enterprise)
2. Per-user quotas
3. API key limits (for BYOK users)

Machine ID likely contributes to:
- Abuse detection signals
- Multi-account detection
- Device-based rate limiting (unconfirmed)

## Legal and Ethical Considerations

**IMPORTANT DISCLAIMERS:**

1. **Terms of Service**: Spoofing machine IDs likely violates Cursor's ToS
2. **Fraud Prevention**: These techniques could be used for abuse; use responsibly
3. **Research Only**: This analysis is for security research and authorized testing
4. **No Warranty**: Techniques may break, be detected, or result in account action

## Recommended Investigation Paths

1. **TASK-121**: Investigate @vscode/deviceid package for devDeviceId details
2. **Server correlation testing**: Compare API behavior with different machine IDs
3. **Rate limit testing**: Measure if machine ID affects rate limiting
4. **Account creation testing**: Check if new accounts from spoofed IDs get flagged

## Related Tasks

- TASK-47: Machine ID fingerprinting analysis (foundational research)
- TASK-18: x-cursor-checksum algorithm (header format)
- TASK-80: Rate limiting schemas (usage impact)
- TASK-121: @vscode/deviceid package investigation
- TASK-122: VM detection impact analysis

## Source Code References

| Description | File | Line |
|-------------|------|------|
| AbuseService definition | workbench.desktop.main.js | 831668 |
| getMachineId IPC | workbench.desktop.main.js | 832772-832773 |
| getMacMachineId IPC | workbench.desktop.main.js | 832775-832776 |
| Machine ID storage | workbench.desktop.main.js | 352912-352927 |
| serviceMachineIdResource | workbench.desktop.main.js | 412737-412738 |
| x-cursor-checksum header | workbench.desktop.main.js | 268885-268917 |
| Jyh cipher | workbench.desktop.main.js | 268879-268882 |
| Telemetry common properties | workbench.desktop.main.js | 344172-344192 |
| UUID validation regex | workbench.desktop.main.js | 33034-33040 |
| Configuration machineId getter | workbench.desktop.main.js | 1113990-1113991 |

## Summary

Machine ID spoofing in Cursor is technically straightforward but carries risks:

| Approach | Difficulty | Persistence | Detection Risk |
|----------|------------|-------------|----------------|
| MAC address change | Easy | Until reboot | Low |
| Linux machine-id | Medium | Permanent | Medium |
| Windows MachineGuid | Medium | Permanent | Medium |
| Direct storage edit | Easy | Until reinstall | Low-Medium |
| VM with custom IDs | Medium | Per VM | Low |
| LD_PRELOAD intercept | Hard | Per session | Very Low |

The most practical approach for testing is using VMs with custom UUIDs and MAC addresses, as this:
- Isolates spoofing from the host system
- Provides clean, reproducible environments
- Avoids VM detection when using non-VM MAC prefixes
- Allows easy reset by reverting to snapshot
