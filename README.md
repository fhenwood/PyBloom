# PyBloom 🌸☕

An open-source Python library for automating XBloom coffee machines via Bluetooth Low Energy.

> **Disclaimer:** This project is not affiliated with, endorsed by, or connected to XBloom in any way. It was created through clean-room reverse engineering for personal automation and interoperability purposes.

## ✨ Features

- **Full Brew Automation** - Grind beans, pour water, complete recipes
- **Real-Time Monitoring** - Weight, temperature, water level, grinder status
- **Recipe Support** - Multi-pour recipes with temperature, flow rate, and pattern control
- **Async API** - Modern Python async/await patterns
- **Cross-Platform** - Works on Linux, macOS, Windows

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/fhenwood/PyBloom.git
cd pybloom

# Install in development mode
pip install -e .
```

### Requirements
- Python 3.9+
- Bluetooth adapter with BLE support
- XBloom Studio coffee machine

## 🚀 Quick Start

```python
import asyncio
from xbloom import XBloomClient
from xbloom.models.types import XBloomRecipe, PourStep, PourPattern, CupType

async def brew_coffee():
    recipe = XBloomRecipe(
        name="Morning Pour Over",
        grind_size=50,          # 1-100
        rpm=80,                 # Grinder speed
        bean_weight=15.0,       # Grams to grind
        total_water=24,         # 24 * 10 = 240ml
        cup_type=CupType.X_DRIPPER,
        pours=[
            # Bloom
            PourStep(
                volume=50,
                temperature=93,
                pausing=30,         # 30 second bloom
                flow_rate=3.0,
                pattern=PourPattern.SPIRAL
            ),
            # Main pour
            PourStep(
                volume=190,
                temperature=93,
                pausing=0,
                flow_rate=3.5,
                pattern=PourPattern.SPIRAL
            ),
        ]
    )
    
    async with XBloomClient() as client:
        if client.is_connected:
            # This handles everything: bypass, cup, recipe, execute
            await client.brew(recipe, wait_for_completion=True)
            print("☕ Enjoy your coffee!")

asyncio.run(brew_coffee())
```

## 📖 API Reference

### XBloomClient

The main client for controlling the machine.

```python
async with XBloomClient(mac_address="B0:F8:93:DB:B1:C1") as client:
    # High-level brewing
    await client.brew(recipe)                    # Full automated brew
    await client.brew_without_grinding(recipe)   # Skip grinding (pre-ground)
    
    # Low-level control
    await client.set_bypass(volume, temp, dose)  # Set bypass parameters
    await client.set_cup(max_weight, min_weight) # Set cup bounds
    await client.send_coffee_recipe(recipe)      # Send recipe data
    await client.execute_coffee_recipe()         # Start execution
    
    # Monitoring
    status = client.status                       # Current device status
    status.scale.weight                          # Current weight (grams)
    status.brewer.temperature                    # Current temperature (°C)
    status.grinder.is_running                    # Grinder active?
    status.brewer.is_running                     # Brewer active?
```

### Recipe Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| `grind_size` | 1-100 | Grind fineness (1=finest) |
| `rpm` | 60-100 | Grinder motor speed |
| `bean_weight` | 5-30g | Grams of beans to grind |
| `total_water` | 1-50 | Total water ÷ 10 (e.g., 24 = 240ml) |
| `temperature` | 80-100°C | Pour temperature |
| `flow_rate` | 1.0-5.0 | Water flow speed |
| `pausing` | 0-255s | Pause after pour (bloom time) |

### Pour Patterns

```python
PourPattern.CENTER   # 0 - Center only
PourPattern.CIRCULAR # 1 - Circular motion
PourPattern.SPIRAL   # 2 - Spiral outward
```

## 🔧 CLI Usage

```bash
# Scan for devices
xbloom scan

# Monitor device status
xbloom monitor B0:F8:93:DB:B1:C1
```

## 📁 Project Structure

```
pybloom/
├── src/xbloom/
│   ├── core/client.py      # Main XBloomClient
│   ├── models/
│   │   ├── types.py        # Recipe, PourStep, etc.
│   │   └── recipes.py      # Recipe payload builder
│   ├── protocol/
│   │   ├── constants.py    # Command codes
│   │   ├── packet.py       # Packet building
│   │   └── parser.py       # Response parsing
│   └── connection/         # BLE connection handling
├── examples/
│   └── simple_brew.py      # Example usage
├── tests/                  # Unit tests
├── PROTOCOL_DOCUMENTATION.md
└── README.md
```

## 📚 Documentation

- [Protocol Documentation](PROTOCOL_DOCUMENTATION.md) - Complete BLE protocol reference

## ⚠️ Important Notes

1. **Disconnect Cleanup**: By default, disconnecting sends abort commands. Set `client._cleanup_on_disconnect = False` to let brews continue after script exit.

2. **Timing**: Commands need ~1 second delay between them for reliable operation.

3. **Bean Detection**: The machine will prompt for more beans if the hopper is empty.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Protocol documentation created through BLE traffic analysis and clean-room reverse engineering
- Inspired by the need for home automation integration
- Thanks to the open-source community for BLE tools like [Bleak](https://github.com/hbldh/bleak)

---

*Made with ☕ by coffee enthusiasts, for coffee enthusiasts.*
