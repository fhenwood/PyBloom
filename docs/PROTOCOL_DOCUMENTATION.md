# XBloom Protocol Documentation

Complete reverse-engineered documentation of the XBloom coffee machine BLE protocol.

> **Disclaimer:** This documentation was created through clean-room reverse engineering (BLE traffic analysis and protocol inspection) for interoperability purposes. This project is not affiliated with XBloom.

**Last updated:** January 2026

---

## Table of Contents

1. [Overview](#overview)
2. [BLE Connection](#ble-connection)
3. [Packet Format](#packet-format)
4. [Command Codes](#command-codes)
5. [Response Codes](#response-codes)
6. [Recipe Payload Format](#recipe-payload-format)
7. [NFC Card Format](#nfc-card-format)
8. [Brew Workflow](#brew-workflow)
9. [Key Discoveries](#key-discoveries)
10. [Error Codes](#error-codes)
11. [Examples](#examples)

---

## Overview

The XBloom coffee machine communicates over Bluetooth Low Energy (BLE) using a custom binary protocol. The machine supports:

- **Grinding**: Adjustable grind size (1-100) and RPM
- **Brewing**: Multi-pour recipes with temperature, flow rate, and pattern control
- **Omni Dripper**: Motorized dripper that moves between grinder and brewer positions
- **Scale**: Built-in weight measurement
- **NFC**: Recipe cards with encoded brewing parameters

---

## BLE Connection

### Service and Characteristics

| UUID | Description |
|------|-------------|
| `0000e0ff-3c17-d293-8e48-14fe2e4da212` | Main Service UUID |
| `0000ffe1-0000-1000-8000-00805f9b34fb` | Write Characteristic (commands) |
| `0000ffe2-0000-1000-8000-00805f9b34fb` | Notify Characteristic (responses) |

### Connection Flow

1. Scan for device with service UUID `0000e0ff-3c17-d293-8e48-14fe2e4da212`
2. Connect to device
3. Subscribe to notifications on `0000ffe2`
4. Send commands via write to `0000ffe1`

---

## Packet Format

All packets follow this structure:

```
┌────────┬──────────┬───────────┬─────────┬────────┬─────────┬──────┐
│ Header │ DeviceID │ TypeCode  │ Command │ Length │ Payload │ CRC  │
│ 1 byte │ 1 byte   │ 1 byte    │ 2 bytes │ 4 bytes│ N bytes │2 bytes│
└────────┴──────────┴───────────┴─────────┴────────┴─────────┴──────┘
```

### Field Details

| Field | Size | Description |
|-------|------|-------------|
| Header | 1 byte | `0x58` for outbound commands |
| DeviceID | 1 byte | Device identifier, typically `0x01` for send, `0x07` for receive |
| TypeCode | 1 byte | `0x01` = Standard, `0x02` = Studio mode |
| Command | 2 bytes | Command ID (little-endian) |
| Length | 4 bytes | Total packet length including header (little-endian) |
| Payload | Variable | Command-specific data |
| CRC | 2 bytes | CRC-16 checksum (polynomial 0x8408) |

### CRC-16 Calculation

```python
def calculate_crc16(data: bytes) -> int:
    """CRC-16 with polynomial 0x8408 (reversed 0x1021)"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc ^ 0xFFFF
```

---

## Command Codes

### Recipe Commands

| Code | Name | Description |
|------|------|-------------|
| **8001** | `APP_RECIPE_SEND_AUTO` | Send recipe **with grinding** |
| **8004** | `APP_RECIPE_SEND_MANUAL` | Send recipe **without grinding** |
| **8002** | `APP_RECIPE_EXECUTE` | Execute the sent recipe |
| **40519** | `APP_RECIPE_STOP` | Stop/abort current recipe |

### Setup Commands

| Code | Name | Description |
|------|------|-------------|
| **8102** | `APP_SET_BYPASS` | Set bypass water and **bean dose** |
| **8104** | `APP_SET_CUP` | Set cup weight bounds |
| **4510** | `APP_BREWER_SET_TEMPERATURE` | Set water temperature |

### Control Commands

| Code | Name | Description |
|------|------|-------------|
| 8012 | `APP_GRINDER_QUIT` | Exit grinder mode |
| 8013 | `APP_BREWER_QUIT` | Exit brewer mode |
| 8006 | `APP_GRINDER_IN` | Move dripper to grinder |
| 3500 | `APP_GRINDER_START` | Start grinding |
| 3505 | `APP_GRINDER_STOP` | Stop grinding |
| 4506 | `APP_BREWER_START` | Start brewing |
| 4507 | `APP_BREWER_STOP` | Stop brewing |

### Scale/Movement Commands

| Code | Name | Description |
|------|------|-------------|
| 2500 | `SG_LEFT` | Move dripper left (to grinder) |
| 2501 | `SG_RIGHT` | Move dripper right (to brewer) |
| 2502 | `SG_VIBRATE` | Activate vibration/agitation |
| 2505 | `SG_STOP` | Stop movement |

---

## Response Codes

### Status Responses

| Code | Name | Description |
|------|------|-------------|
| 9000 | `RD_IN_GRINDER` | Dripper arrived at grinder position |
| 9001 | `RD_IN_BREWER` | Dripper arrived at brewer position |
| 9003 | `RD_GRINDER_BEGIN` | Grinding started |
| 9005 | `RD_BREWER_BEGIN` | Brewing/pouring started |
| 40507 | `RD_Grinder_Stop` | Grinding complete |
| 40511 | `RD_Brewer_Stop` | Brewing complete |
| 40510 | `RD_BLOOM` | Bloom phase active |
| 40512 | `RD_ENJOY` | Recipe complete - enjoy your coffee! |
| 40502 | `RD_BREWER_COFFEE_START` | Coffee recipe started |

### Telemetry Responses

| Code | Name | Description |
|------|------|-------------|
| 20501 | `RD_CURRENT_WEIGHT2` | Scale weight (float32 at offset 0) |
| 40523 | `RD_WATER_VOLUME` | Water volume reading |
| 8023 | `RD_MachineActivity` | Machine activity status |
| 40521 | `RD_MachineInfo` | Machine info (serial, model, version) |
| 8108 | `RD_BREWER_TEMPERATURE` | Current brewer temperature |
| 40505 | `RD_GearReport` | Dripper position report |

### Error Responses

| Code | Name | Description |
|------|------|-------------|
| 40517 | `RD_ErrorIdling` | **Empty grinding** - no beans detected |
| 40522 | `RD_ErrorLackOfWater` | Water tank empty |
| 8204 | `RD_AbnormalDoseOrWater` | Invalid dose or water parameters |
| 8203 | `RD_AbnormalGearPosition` | Dripper position error |

---

## Recipe Payload Format

The recipe payload is sent with commands 8001 (with grinding) or 8004 (without grinding).

### Overall Structure

```
┌────────────┬──────────────────────┬────────────┐
│ Length     │ Body                 │ Footer     │
│ 1 byte     │ Variable             │ 2 bytes    │
└────────────┴──────────────────────┴────────────┘
```

| Field | Size | Description |
|-------|------|-------------|
| Length | 1 byte | Size of Body only (not including footer) |
| Body | Variable | Pour data (sub-steps + metadata per pour) |
| Footer | 2 bytes | `[grindSize, totalWater*10]` |

### Body Structure (Per Pour)

Each pour consists of:

1. **Sub-steps** (4 bytes each) - Volume chunks (max 127ml per sub-step)
2. **Metadata** (4 bytes) - Pause, RPM, flow rate

#### Sub-step Format (4 bytes)

```
┌─────────┬─────────────┬─────────┬───────────┐
│ Volume  │ Temperature │ Pattern │ Vibration │
│ 1 byte  │ 1 byte      │ 1 byte  │ 1 byte    │
└─────────┴─────────────┴─────────┴───────────┘
```

| Byte | Field | Description |
|------|-------|-------------|
| 0 | Volume | Pour volume in ml (max 127 per sub-step) |
| 1 | Temperature | Water temperature in Celsius |
| 2 | Pattern | Pour pattern (see below) |
| 3 | Vibration | Vibration/agitation mode (see below) |

**Volume Chunking:** If a pour exceeds 127ml, it's split into multiple sub-steps:
- 200ml pour → 127ml sub-step + 73ml sub-step

#### Metadata Format (4 bytes)

```
┌───────────┬──────────┬─────┬────────────┐
│ PauseByte │ Reserved │ RPM │ FlowRate   │
│ 1 byte    │ 1 byte   │1 byte│ 1 byte    │
└───────────┴──────────┴─────┴────────────┘
```

| Byte | Field | Description |
|------|-------|-------------|
| 0 | PauseByte | `(-pause) & 0xFF` (two's complement) |
| 1 | Reserved | Always `0x00` |
| 2 | RPM | Grinder speed (only for first pour, else 0) |
| 3 | FlowRate | Flow rate × 10 (e.g., 3.5 → 35) |

### Footer Format (2 bytes)

```
┌───────────┬────────────────┐
│ GrindSize │ TotalWater×10  │
│ 1 byte    │ 1 byte         │
└───────────┴────────────────┘
```

| Byte | Field | Description |
|------|-------|-------------|
| 0 | GrindSize | Grinder setting (1-100) |
| 1 | TotalWater×10 | Total water in ml ÷ 10 (e.g., 240ml → 24) |

**⚠️ IMPORTANT:** The footer is exactly 2 bytes. Previous implementations incorrectly used 4 bytes.

### Pattern Values

| Value | Name | Description |
|-------|------|-------------|
| 0 | CENTER | Fixed center pour |
| 1 | CIRCULAR | Circular motion |
| 2 | SPIRAL | Spiral pattern (most common) |

### Vibration Values

| Value | Name | Description |
|-------|------|-------------|
| 0 | NONE | No agitation |
| 1 | BEFORE | Vibrate before pour |
| 2 | AFTER | Vibrate after pour |
| 3 | BOTH | Vibrate before and after |

---

## NFC Card Format

XBloom recipe NFC cards use ISO 15693 tags with 128 bytes of data.

### Overall Structure

```
┌────────┬─────┬──────────┬───────────┬───────────┬──────────┐
│ Hash   │ XID │ Metadata │ Pour Data │ Settings  │ Checksum │
│32 bytes│8 bytes│2 bytes │ Variable  │ 2 bytes   │ 1 byte   │
└────────┴─────┴──────────┴───────────┴───────────┴──────────┘
```

### Field Details

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0-31 | 32 bytes | Hash | Cryptographic hash (read-only) |
| 32-38 | 7 bytes | XID | Recipe ID (ASCII, null-padded) |
| 39 | 1 byte | PodType | `0x00`=overflow on, `0x02`=off |
| 40 | 1 byte | NumPours | Number of pours << 3 |
| 41+ | 8×N bytes | PourData | Pour definitions |
| After pours | 1 byte | GrindSize | Grind size - 40 |
| +1 | 1 byte | Ratio | Water:coffee ratio |
| +2 | 1 byte | Checksum | CRC-8 MAXIM-DOW |

### NFC Pour Format (8 bytes each)

```
┌────────┬──────┬─────────┬───────────┬───────┬──────────┬──────────┬──────────┐
│ Volume │ Temp │ Pattern │ Agitation │ Pause │ Reserved │ Reserved │ FlowRate │
│ 1 byte │1 byte│ 1 byte  │ 1 byte    │1 byte │ 1 byte   │ 1 byte   │ 1 byte   │
└────────┴──────┴─────────┴───────────┴───────┴──────────┴──────────┴──────────┘
```

| Byte | Field | Description |
|------|-------|-------------|
| 0 | Volume | Pour volume in ml |
| 1 | Temperature | Water temperature |
| 2 | Pattern | 0=Center, 1=Circular, 2=Spiral |
| 3 | Agitation | Bitmask: bit0=before, bit1=after |
| 4 | Pause | `256 - pauseSeconds` (or 0 if no pause) |
| 5 | Reserved | `0x00` |
| 6 | Reserved | `0x00` |
| 7 | FlowRate | Raw flow rate (not ×10) |

### NFC vs BLE Differences

| Field | NFC Format | BLE Format |
|-------|------------|------------|
| GrindSize | `grindSize - 40` | Raw grindSize |
| FlowRate | Raw value | Value × 10 |
| Pause | `256 - pause` | `(-pause) & 0xFF` |

---

## Brew Workflow

### Command Sequence

The correct order for a full grind + brew cycle:

```
1. APP_SET_BYPASS (8102)   ─────────────────────────────────────┐
   Payload: [bypassVolume, bypassTemp×10, dose]                 │
   ⚠️ dose = bean weight in grams - REQUIRED for grinding!      │
                                                                │
2. APP_SET_CUP (8104)      ─────────────────────────────────────┤ Setup
   Payload: [cupMaxWeight, cupMinWeight] (as float32 bits)      │
                                                                │
3. APP_RECIPE_SEND_AUTO (8001) ─────────────────────────────────┘
   Payload: Recipe binary (length + body + footer)
   
4. APP_RECIPE_EXECUTE (8002) ───────────────────────────────────── Execute
   Payload: None
```

### Machine Response Sequence

After executing, expect these responses in order:

```
9000  RD_IN_GRINDER      → Dripper moved to grinder
9003  RD_GRINDER_BEGIN   → Grinding started
40507 RD_Grinder_Stop    → Grinding complete
9004  RD_OUT_GRINDER     → Leaving grinder position
9001  RD_IN_BREWER       → Dripper at brewer position
9005  RD_BREWER_BEGIN    → Water pouring started
40510 RD_BLOOM           → Bloom phase (if applicable)
40511 RD_Brewer_Stop     → Pour complete
40512 RD_ENJOY           → Recipe complete!
```

### Bypass Command Details (8102)

**This is the most critical command for grinding to work!**

```
Payload: 3 × 4-byte integers (little-endian)
┌─────────────────┬─────────────────┬─────────────────┐
│ BypassVolume    │ BypassTemp×10   │ Dose            │
│ 4 bytes (float) │ 4 bytes (float) │ 4 bytes (int)   │
└─────────────────┴─────────────────┴─────────────────┘
```

| Field | Description |
|-------|-------------|
| BypassVolume | Bypass water volume (0.0 to disable) |
| BypassTemp×10 | Bypass water temp × 10 (0.0 to disable) |
| **Dose** | **Bean weight in grams - MUST be set for grinding!** |

**⚠️ Critical Discovery:** Even when bypass is disabled (vol=0, temp=0), the `dose` parameter MUST contain the bean weight. Setting dose=0 tells the machine "grind 0 grams" = skip grinding!

### Cup Command Details (8104)

```
Payload: 2 × 4-byte floats (as integer bit patterns)
┌─────────────────┬─────────────────┐
│ CupMaxWeight    │ CupMinWeight    │
│ 4 bytes         │ 4 bytes         │
└─────────────────┴─────────────────┘
```

Default values by cup type:
| Cup Type | theMax | theMin |
|----------|--------|--------|
| XPod (1) | 80.0 | 40.0 |
| XDripper (2) | 90.0 | 40.0 |
| Other (3) | 90.0 | 40.0 |

---

## Key Discoveries

### 1. Bypass Dose is CRITICAL

The `dose` parameter in the bypass command (8102) tells the machine how many grams to grind. This parameter is required even when bypass water is disabled!

```python
# WRONG - dose=0 means "grind nothing"
await client.set_bypass(0.0, 0.0, 0)

# CORRECT - dose=15 means "grind 15 grams"
await client.set_bypass(0.0, 0.0, 15)
```

### 2. Recipe Footer is 2 Bytes

The footer is exactly 2 bytes: `[grindSize, totalWater×10]`

Previous implementations incorrectly used 4 bytes, which corrupted the packet.

### 3. Command Order Matters

Must send in this exact order:
1. Bypass (8102) - includes dose
2. Cup (8104) - weight bounds
3. Recipe (8001) - the actual recipe
4. Execute (8002) - start brewing

### 4. 8001 vs 8004

| Command | Name | When to Use |
|---------|------|-------------|
| 8001 | AUTO | Fresh beans - machine will grind |
| 8004 | MANUAL | Pre-ground coffee - skip grinding |

The command choice depends on whether grinding is needed:
- Use **8001** when `grind_size` is set (fresh beans)
- Use **8004** when using pre-ground coffee

### 5. Pattern Enum is 0-Indexed

```
CENTER  = 0  (not 1!)
CIRCULAR = 1
SPIRAL   = 2
```

### 6. Cleanup Commands Abort Brew

Sending these commands will abort an in-progress brew:
- `APP_RECIPE_STOP` (40519)
- `APP_BREWER_QUIT` (8013)
- `APP_GRINDER_QUIT` (8012)

Be careful with connection disconnect handlers!

---

## Error Codes

| Code | Name | Cause | Solution |
|------|------|-------|----------|
| 40517 | ErrorIdling | Empty grinding - no beans detected | Add beans to hopper |
| 40522 | ErrorLackOfWater | Water tank empty | Fill water tank |
| 8204 | AbnormalDoseOrWater | Invalid dose/water params | Check recipe values |
| 8203 | AbnormalGearPosition | Dripper position error | Reset machine |

---

## Examples

### Complete Brew Example

```python
from xbloom import XBloomClient
from xbloom.models.types import XBloomRecipe, PourStep, PourPattern, CupType

recipe = XBloomRecipe(
    name="Morning Pour Over",
    grind_size=50,          # 1-100
    rpm=80,                 # Grinder speed
    bean_weight=15.0,       # Grams to grind
    total_water=24,         # 240ml (24 × 10)
    cup_type=CupType.X_DRIPPER,
    pours=[
        PourStep(
            volume=50,
            temperature=93,
            pausing=30,         # 30s bloom
            flow_rate=3.0,
            pattern=PourPattern.SPIRAL
        ),
        PourStep(
            volume=95,
            temperature=93,
            pausing=15,
            flow_rate=3.5,
            pattern=PourPattern.SPIRAL
        ),
        PourStep(
            volume=95,
            temperature=93,
            pausing=0,
            flow_rate=3.5,
            pattern=PourPattern.SPIRAL
        ),
    ]
)

async with XBloomClient() as client:
    client._cleanup_on_disconnect = False
    await client.brew(recipe, wait_for_completion=True)
```

### Raw Packet Example

Sending a simple 100ml recipe:

```
Recipe payload breakdown:
  08              Length (8 bytes body)
  64 5C 02 00     Sub-step: 100ml, 92°C, SPIRAL, NONE
  00 00 50 1E     Metadata: pause=0, 0, rpm=80, flow=30
  32 64           Footer: grindSize=50, water=100

Full packet:
  58              Header
  01              DeviceID
  01              TypeCode
  41 1F           Command 8001 (little-endian)
  17 00 00 00     Length 23
  08 64 5C 02 00 00 00 50 1E 32 64  Payload
  XX XX           CRC16
```

---

## Parameter Constraints

### Grind Size
| Model | Range | Resolution |
|-------|-------|------------|
| Studio | 1-80 | 18.75 micrometers per step |
| Original | 1-30 | Larger steps |

### Grinder RPM
Valid values: `{60, 70, 80, 90, 100, 110, 120}`

Setting RPM=0 skips grinding entirely.

### Temperature
| Mode | Range |
|------|-------|
| Copilot | 40-95°C |
| xPod | 40-98°C |
| Freesolo | 40-100°C (BP) |

Precision: ±1°C

### Flow Rate
Valid values: `3.0, 3.1, 3.2, 3.25, 3.3, 3.4, 3.5` ml/s

Note: Sent as integer (×10) in BLE payload.

### Bean Dose
Valid range: 4g-25g (common: 5g-18g)

xPod cards are limited to exactly 15g.

### Pour Volume
Maximum 127ml per sub-step (automatically chunked in payload).

### Pause Duration
Range: 0-255 seconds between pours.

---

## References

- **XBRecipeWriter:** Third-party NFC card writer (TypeScript) - useful for validating NFC card format
- **Bleak:** Python BLE library used for communication

---

*This documentation was created through BLE traffic analysis and clean-room reverse engineering for interoperability purposes.*
