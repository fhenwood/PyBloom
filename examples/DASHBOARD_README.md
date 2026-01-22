# XBloom Studio Dashboard Card

A premium custom Lovelace card for Home Assistant that replicates the XBloom Studio mobile app experience.

## ✨ Features

- **Dark Studio Aesthetic** - Deep blacks and subtle borders matching XBloom's design
- **Connection-Aware UI** - Controls automatically disable when machine is disconnected
- **Auto-Discovery** - Finds your XBloom entities automatically
- **All Controls** - Grind, Brew, Sliders, Recipe selection
- **Sensor Panel** - Live weight, status, and error readouts

## 📋 Requirements

- XBloom MQTT custom component installed and configured
- Home Assistant 2024.1 or later

## 🚀 Installation

### Step 1: Copy the Card File

```bash
# Copy to your Home Assistant www folder
cp custom_components/xbloom_mqtt/www/xbloom-studio-card.js /config/www/
```

Or manually copy `xbloom-studio-card.js` to your Home Assistant `/config/www/` directory.

### Step 2: Add as a Lovelace Resource

1. Go to **Settings → Dashboards**
2. Click **⋮** (three dots, top right) → **Resources**
3. Click **Add Resource**
4. Enter:
   - **URL:** `/local/xbloom-studio-card.js`
   - **Type:** JavaScript Module
5. Click **Create**
6. **Refresh your browser** (Ctrl+Shift+R)

### Step 3: Add the Card

1. Edit any dashboard
2. Click **Add Card**
3. Search for "**XBloom Studio**"
4. Click to add

Or add manually via YAML:
```yaml
type: custom:xbloom-studio-card
```

## 🎨 Theme (Optional)

For the full XBloom aesthetic, install the matching theme:

1. Copy `examples/themes/xbloom_studio.yaml` to `/config/themes/`
2. Add to `configuration.yaml` (if not already):
   ```yaml
   frontend:
     themes: !include_dir_merge_named themes
   ```
3. Restart Home Assistant
4. Go to **Settings → General → Theme → XBloom Studio**

## 🎛️ Entity Reference

The card auto-discovers entities matching these patterns:

| UI Element | Entity Pattern |
|------------|----------------|
| Connect | `button.*xbloom*connect` |
| Grind | `button.*xbloom*grind` |
| Pour/Brew | `button.*xbloom*pour` |
| Execute Recipe | `button.*xbloom*execute_recipe` |
| Cancel | `button.*xbloom*cancel` |
| Grind Size | `number.*xbloom*grind_size` |
| RPM | `number.*xbloom*rpm` |
| Temperature | `number.*xbloom*temperature` |
| Volume | `number.*xbloom*volume` |
| Recipe Select | `select.*xbloom*recipe` |
| Status | `sensor.*xbloom*status` |
| Weight | `sensor.*xbloom*weight` |
| Error | `sensor.*xbloom*error` |

## 🔧 Troubleshooting

### Card Not Appearing in Picker

1. Verify file exists at `/config/www/xbloom-studio-card.js`
2. Check resource URL is exactly `/local/xbloom-studio-card.js`
3. Hard refresh browser (Ctrl+Shift+R)
4. Check browser console (F12) for errors

### Entities Show "Unavailable"

This means the XBloom integration isn't connected:

1. Check **Developer Tools → States** and filter by "xbloom"
2. Verify the MQTT bridge is running
3. Try pressing the **Connect** button on the card

### Sliders Not Working

Sliders require the machine to be connected. When disconnected, the UI is disabled (greyed out) by design.

## 📁 Files

```
custom_components/xbloom_mqtt/
├── www/
│   └── xbloom-studio-card.js   # The custom card
├── __init__.py                  # Integration setup
├── button.py                    # Button entities
├── number.py                    # Slider entities
├── sensor.py                    # Sensor entities
└── select.py                    # Recipe selector

examples/
├── themes/
│   └── xbloom_studio.yaml      # Dark theme
└── DASHBOARD_README.md          # This file
```

## 📝 Changelog

### v1.0.0
- Initial release
- Dark theme matching XBloom Studio app
- Auto-discovery of XBloom entities
- Connection-aware disabled state
- All controls: Grind, Brew, Sliders, Recipe, Cancel
