# TASK-122: VM Detection Impact on Cursor Behavior

## Overview

Cursor IDE implements virtual machine detection based on MAC address OUI (Organizationally Unique Identifier) prefixes. This analysis documents the detection mechanism, telemetry integration, and observable behavior impacts.

## VM Detection Implementation

### Source Location
- **Module:** `out-build/vs/base/node/id.js` (in main.js)
- **Renderer:** `workbench.desktop.main.js` lines 1132844-1132851 (isVMLikelyhood)
- **Issue Reporter:** `workbench.desktop.main.js` lines 1162714-1162760 (vmHint display)

### Detected VM OUIs

The code detects the following virtual machine MAC address prefixes using a trie-based lookup:

| OUI Prefix | Hypervisor | Format Variants |
|------------|------------|-----------------|
| `00-50-56` | VMware ESXi/Workstation | Also `00:50:56` |
| `00-0C-29` | VMware Workstation/Player | Also `00:0C:29` |
| `00-05-69` | VMware ESX | Also `00:05:69` |
| `00-03-FF` | Microsoft Hyper-V | Also `00:03:FF` |
| `00-1C-42` | Parallels Desktop | Also `00:1C:42` |
| `00-16-3E` | Xen/AWS EC2 | Also `00:16:3E` |
| `08-00-27` | Oracle VirtualBox | Also `08:00:27` |

### Detection Algorithm

```javascript
// From main.js - out-build/vs/base/node/id.js
class VirtualMachineDetector {
    constructor() {
        this._virtualMachineOUIs = new TrieMap();
        // Register all VM OUI prefixes (both hyphen and colon formats)
        this._virtualMachineOUIs.set("00-50-56", true);  // VMware
        this._virtualMachineOUIs.set("00-0C-29", true);  // VMware
        this._virtualMachineOUIs.set("00-05-69", true);  // VMware
        this._virtualMachineOUIs.set("00-03-FF", true);  // HyperV
        this._virtualMachineOUIs.set("00-1C-42", true);  // Parallels
        this._virtualMachineOUIs.set("00-16-3E", true);  // Xen
        this._virtualMachineOUIs.set("08-00-27", true);  // VirtualBox
        // Also colon variants for compatibility
        this._virtualMachineOUIs.set("00:50:56", true);
        // ... etc
    }

    _isVirtualMachineMacAddress(mac) {
        return !!this._virtualMachineOUIs.findSubstr(mac);
    }

    value() {
        if (this._value === undefined) {
            let vmCount = 0;
            let totalCount = 0;
            const interfaces = os.networkInterfaces();

            for (const name in interfaces) {
                const netInterface = interfaces[name];
                if (netInterface) {
                    for (const { mac, internal } of netInterface) {
                        if (!internal) {  // Exclude loopback
                            totalCount++;
                            if (this._isVirtualMachineMacAddress(mac.toUpperCase())) {
                                vmCount++;
                            }
                        }
                    }
                }
            }

            // Calculate ratio of VM interfaces to total interfaces
            this._value = totalCount > 0 ? vmCount / totalCount : 0;
        }
        return this._value;
    }
}

const yf = new VirtualMachineDetector();
```

### API Integration

The VM hint is exposed via `nativeHostService.getOSVirtualMachineHint()`:

```javascript
// From main.js
async getOSVirtualMachineHint() {
    return yf.value();  // Returns float 0.0 to 1.0
}
```

## Telemetry Integration

### isVMLikelyhood Property

The VM ratio is converted to a percentage (0-100) and included in startup telemetry:

```javascript
// From workbench.desktop.main.js line 1132851
e.isVMLikelyhood = Math.round(s * 100);  // s = getOSVirtualMachineHint()
```

### Startup Metrics Telemetry Event

The `isVMLikelyhood` value is sent as part of the `startupTimeVaried` telemetry event:

```javascript
// From workbench.desktop.main.js line 789142
this._telemetryService.publicLog("startupTimeVaried", e);
// e contains: isVMLikelyhood, platform, arch, totalmem, freemem, cpus, loadavg, etc.
```

### Telemetry Data Schema

The startup metrics object containing VM data:

```typescript
interface StartupMetrics {
    timers: {
        ellapsedAppReady: number;
        ellapsedWindowLoad: number;
        // ... other timing metrics
    };
    platform: string;
    release: string;
    arch: string;
    totalmem: number;
    freemem: number;
    meminfo: {
        workingSetSize: number;
        privateBytes: number;
        sharedBytes: number;
    };
    cpus: {
        count: number;
        speed: number;
        model: string;
    };
    loadavg: number[];
    isVMLikelyhood: number;  // 0-100 percentage
    initialStartup: boolean;
    hasAccessibilitySupport: boolean;
    emptyWorkbench: boolean;
    isARM64Emulated: boolean;
}
```

## UI Display

### Issue Reporter

The VM hint is displayed in the "About" / Issue Reporter dialog:

```javascript
// System info table shows VM status
et("tr", void 0,
    et("td", void 0, "VM"),
    et("td", void 0, n.vmHint)  // Displays the vmHint value
)
```

Example display values:
- `0%` - Not a VM
- `50%` - Half of network interfaces are VM-like
- `100%` - All network interfaces are VM-like

## Behavior Impact Analysis

### What VM Detection DOES Affect

1. **Telemetry**: The `isVMLikelyhood` value is sent to Microsoft/Cursor telemetry servers as part of startup metrics
2. **Issue Reporting**: VM status is included in bug reports to help diagnose environment-specific issues
3. **Server-Side Analytics**: Cursor can analyze usage patterns from VM environments

### What VM Detection DOES NOT Appear to Affect (Client-Side)

Based on code analysis, there is **no evidence** of the following behaviors being tied to VM detection:

1. **Rate Limiting**: Rate limiting is based on user tier (free/pro), not VM status
2. **Feature Restrictions**: No feature gates reference VM status
3. **Service Degradation**: No client-side code modifies behavior based on isVMLikelyhood
4. **Authentication**: x-cursor-checksum uses machineId/macMachineId but not vmRatio
5. **Local Functionality**: No local features are disabled in VM environments

### Server-Side Behavior (Unknown)

The VM ratio data is transmitted to Cursor's telemetry servers. Server-side behavior cannot be determined from client code, but possibilities include:

1. **Abuse Detection Signals**: High VM ratio could be weighted in fraud detection models
2. **Rate Limit Adjustments**: Server could apply stricter limits to suspected VM users
3. **Account Verification**: Could trigger additional verification for new accounts from VMs
4. **Usage Pattern Analysis**: Could flag accounts with unusual VM usage patterns

## How VM Ratio is Calculated

The ratio represents the proportion of network interfaces with VM MAC prefixes:

| Scenario | VM Interfaces | Total Interfaces | isVMLikelyhood |
|----------|---------------|------------------|----------------|
| Physical host | 0 | 2 | 0% |
| VM with bridged network | 1 | 1 | 100% |
| VM with host + guest adapters | 1 | 2 | 50% |
| Physical with USB WiFi adapter on VM | 1 | 3 | 33% |

## VM Detection Bypass Methods

### Method 1: MAC Address Spoofing

Change the VM's MAC address to a non-VM OUI:

**VMware:**
```
# In VMX file
ethernet0.addressType = "static"
ethernet0.address = "00:11:22:33:44:55"
```

**VirtualBox:**
```bash
VBoxManage modifyvm "VMName" --macaddress1 001122334455
```

**Hyper-V:**
```powershell
Set-VMNetworkAdapter -VMName "VMName" -StaticMacAddress "001122334455"
```

### Method 2: Add Physical USB Network Adapter

Pass through a physical USB WiFi adapter to the VM. This adds a non-VM MAC address to the interface list, reducing the ratio.

### Method 3: Network Isolation

If the VM has no external network adapters, the ratio may be undefined (0/0 = 0).

## Integration with Other Systems

### Relationship to machineId

VM detection is **separate** from the machineId fingerprinting system:

- `machineId`: SHA-256 hash of platform UUID (used in x-cursor-checksum)
- `macMachineId`: SHA-256 hash of first valid MAC address (also in checksum)
- `isVMLikelyhood`: Ratio of VM interfaces (telemetry only, not in checksum)

### Relationship to AbuseService

The AbuseService provides `getMachineId()` and `getMacMachineId()` for anti-abuse purposes, but does **not** expose VM ratio. VM data flows through telemetry service instead.

## Limitations

1. **Only Detects Known OUIs**: Does not detect:
   - QEMU with custom MAC
   - Docker/container environments (unless using VM networking)
   - Cloud instances with custom MAC policies
   - WSL2 (uses its own networking stack)

2. **Spoofing Vulnerable**: MAC address spoofing trivially bypasses detection

3. **False Positives**: Physical NICs with VM-like OUIs would trigger detection

## Source Code References

| File | Line | Description |
|------|------|-------------|
| main.js | Module jl | Virtual machine OUI detection class |
| workbench.desktop.main.js | 1132844 | getOSVirtualMachineHint API call |
| workbench.desktop.main.js | 1132851 | isVMLikelyhood calculation |
| workbench.desktop.main.js | 789142 | startupTimeVaried telemetry event |
| workbench.desktop.main.js | 789207 | isVMLikelyhood in metrics schema |
| workbench.desktop.main.js | 1162715 | vmHint display in issue reporter |
| workbench.desktop.main.js | 1163721 | vmHint in system info table |

## Conclusions

1. **Detection Mechanism**: Standard MAC OUI prefix matching for common hypervisors
2. **Data Collection**: VM ratio is collected and transmitted via telemetry
3. **Client Impact**: No observable client-side behavior changes based on VM detection
4. **Server Impact**: Unknown - data may be used for server-side decisions
5. **Bypass**: Trivially bypassed via MAC address spoofing

## Recommendations for Further Investigation

1. Monitor network traffic to see if isVMLikelyhood correlates with server responses
2. Test rate limiting behavior in VM vs physical environments
3. Check if new account creation from VMs triggers additional verification
4. Compare API responses for identical requests from VM vs physical machines
