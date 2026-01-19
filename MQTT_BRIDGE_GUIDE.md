# XBloom MQTT Bridge Setup Guide

## 🚀 Quick Start

### 1. Install MQTT Dependencies

```bash
# For bridge functionality
pip install "xbloom-py[mqtt]"

# Or install aiomqtt directly
pip install aiomqtt
```

### 2. Start the Bridge

```bash
# Basic usage with auto-discovery
xbloom bridge --broker homeassistant.local

# With specific device
xbloom bridge --broker 192.168.1.100 --device-address B0:F8:93:DB:B1:C1

# With authentication
xbloom bridge --broker homeassistant.local --username xbloom --password secret123
```

### 3. Test the Bridge

```bash
# Run the test script
python test_mqtt_bridge.py --broker homeassistant.local
```

## 🏗️ Docker Deployment

### Option 1: Docker Compose (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Edit your settings

# 2. Start services
docker-compose up -d

# 3. Check logs
docker-compose logs -f xbloom-bridge
```

### Option 2: Docker Run

```bash
docker build -t xbloom-bridge .

docker run -d \
  --name xbloom-bridge \
  --network host \
  --privileged \
  -v /var/run/dbus:/var/run/dbus:ro \
  -e MQTT_BROKER=homeassistant.local \
  -e MQTT_USERNAME=xbloom \
  -e MQTT_PASSWORD=your_password \
  -e DEVICE_ADDRESS=B0:F8:93:DB:B1:C1 \
  xbloom-bridge \
  xbloom bridge --broker homeassistant.local --username xbloom --password your_password
```

## 🏠 Home Assistant Integration

### 1. MQTT Device Configuration

Add to your `configuration.yaml`:

```yaml
mqtt:
  sensor:
    - name: "XBloom Weight"
      state_topic: "xbloom/xbloom/status/telemetry"
      value_template: "{{ value_json.weight }}"
      unit_of_measurement: "g"
      device_class: "weight"
      
    - name: "XBloom Temperature"
      state_topic: "xbloom/xbloom/status/telemetry"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: "temperature"
      
    - name: "XBloom State"
      state_topic: "xbloom/xbloom/status/telemetry"
      value_template: "{{ value_json.state }}"
      
  binary_sensor:
    - name: "XBloom Online"
      state_topic: "xbloom/xbloom/status/availability"
      payload_on: "online"
      payload_off: "offline"
      device_class: "connectivity"
      
    - name: "XBloom Grinder"
      state_topic: "xbloom/xbloom/status/telemetry"
      value_template: "{{ value_json.grinder_running }}"
      payload_on: true
      payload_off: false
      
    - name: "XBloom Brewer"
      state_topic: "xbloom/xbloom/status/telemetry"
      value_template: "{{ value_json.brewer_running }}"
      payload_on: true
      payload_off: false

  button:
    - name: "XBloom Connect"
      command_topic: "xbloom/xbloom/command/connect"
      payload_press: "{}"
      
    - name: "XBloom Emergency Stop"
      command_topic: "xbloom/xbloom/command/stop_all"
      payload_press: "{}"
      
    - name: "XBloom Vibrate Scale"
      command_topic: "xbloom/xbloom/command/scale/vibrate"
      payload_press: "{}"

  number:
    - name: "XBloom Temperature"
      command_topic: "xbloom/xbloom/command/temperature"
      command_template: '{"celsius": {{ value }}}'
      min: 80
      max: 100
      step: 0.5
      unit_of_measurement: "°C"
      
  select:
    - name: "XBloom Pour Pattern"
      command_topic: "xbloom/xbloom/command/pour"
      command_template: '{"pattern": "{{ value }}"}'
      options:
        - "center"
        - "spiral"
        - "circular"
```

### 2. Automation Examples

```yaml
# Auto-connect on Home Assistant startup
automation:
  - alias: "XBloom Auto Connect"
    trigger:
      platform: homeassistant
      event: start
    action:
      service: mqtt.publish
      data:
        topic: "xbloom/xbloom/command/connect"
        payload: "{}"

  # Morning coffee routine
  - alias: "Morning Coffee"
    trigger:
      platform: time
      at: "07:00:00"
    condition:
      condition: state
      entity_id: binary_sensor.xbloom_online
      state: "on"
    action:
      - service: mqtt.publish
        data:
          topic: "xbloom/xbloom/command/grind"
          payload: '{"size": 50, "speed": 80, "timeout_ms": 5000}'
      - delay: "00:00:10"
      - service: mqtt.publish
        data:
          topic: "xbloom/xbloom/command/temperature"
          payload: '{"celsius": 93.5}'
```

## 🎛️ MQTT Command Reference

### Connection Commands

```bash
# Connect to device
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/connect" -m "{}"

# Disconnect from device  
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/disconnect" -m "{}"
```

### Grinder Commands

```bash
# Start grinder
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/grind" -m '{"size": 50, "speed": 80, "timeout_ms": 5000}'
```

### Brewer Commands

```bash
# Set temperature
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/temperature" -m '{"celsius": 93.5}'

# Start brewing
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/brew" -m "{}"

# Manual pour with pattern
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/pour" -m '{"temperature": 94, "pattern": "spiral"}'
```

### Scale Commands

```bash
# Vibrate scale
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/scale/vibrate" -m "{}"

# Move scale tray
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/scale/move" -m '{"direction": "left"}'
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/scale/move" -m '{"direction": "right"}'
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/scale/move" -m '{"direction": "stop"}'
```

### Recipe Commands

```bash
# Execute recipe (full recipe JSON required)
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/recipe/execute" -f recipe.json

# Stop recipe
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/recipe/stop" -m "{}"
```

### Emergency Commands

```bash
# Emergency stop all
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/stop_all" -m "{}"
```

## 📊 Status Topics

### Real-time Telemetry

```bash
# Subscribe to telemetry
mosquitto_sub -h homeassistant.local -t "xbloom/xbloom/status/telemetry"
```

Sample telemetry data:
```json
{
  "timestamp": "2026-01-18T10:30:45.123456",
  "weight": 245.67,
  "temperature": 93.2,
  "grinder_position": 2840,
  "water_level_ok": true,
  "state": "brewing",
  "grinder_running": false,
  "brewer_running": true
}
```

### Device Availability

```bash
# Subscribe to availability
mosquitto_sub -h homeassistant.local -t "xbloom/xbloom/status/availability"
# Returns: "online" or "offline"
```

### Machine Status

```bash
# Subscribe to machine status
mosquitto_sub -h homeassistant.local -t "xbloom/xbloom/status/machine"
```

### Error Messages

```bash
# Subscribe to errors
mosquitto_sub -h homeassistant.local -t "xbloom/xbloom/status/error"
```

## 🔧 Troubleshooting

### BLE Connection Issues

```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# Reset Bluetooth adapter
sudo hciconfig hci0 down
sudo hciconfig hci0 up

# Check device permissions in Docker
docker exec -it xbloom-bridge ls -la /dev/bus/usb/
```

### MQTT Connection Issues

```bash
# Test MQTT broker connectivity
mosquitto_pub -h homeassistant.local -t "test" -m "hello"
mosquitto_sub -h homeassistant.local -t "test"

# Check bridge logs
docker logs xbloom-bridge -f
```

### Debug Mode

```bash
# Run bridge with debug logging
xbloom bridge --broker homeassistant.local --device-address B0:F8:93:DB:B1:C1 2>&1 | tee bridge.log

# Or set environment variable
export LOG_LEVEL=DEBUG
```

## 📋 Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | `localhost` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` | - | MQTT username (optional) |
| `MQTT_PASSWORD` | - | MQTT password (optional) |
| `DEVICE_NAME` | `xbloom` | Device name for MQTT topics |
| `DEVICE_ADDRESS` | - | XBloom BLE address (auto-discover if empty) |
| `SESSION_TIMEOUT` | `60` | BLE session timeout in seconds |
| `TELEMETRY_INTERVAL` | `5` | Telemetry publishing interval in seconds |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### CLI Options

```bash
xbloom bridge --help
```

```
Usage: xbloom bridge [OPTIONS]

Start MQTT bridge for Home Assistant integration.

Options:
  --broker TEXT                   MQTT broker hostname [default: localhost]
  --port INTEGER                  MQTT broker port [default: 1883]
  --username TEXT                 MQTT username
  --password TEXT                 MQTT password
  --device-name TEXT              Device name for MQTT topics [default: xbloom]
  --device-address TEXT           XBloom device address (auto-discover if not specified)
  --session-timeout INTEGER      BLE session timeout in seconds [default: 60]
  --telemetry-interval INTEGER    Telemetry publishing interval in seconds [default: 5]
  --help                          Show this message and exit.
```

## 🔐 Security Considerations

1. **MQTT Authentication**: Always use username/password for production MQTT brokers
2. **Network Security**: Run on isolated IoT network if possible
3. **Container Security**: Bridge runs as non-root user in container
4. **BLE Security**: XBloom uses encrypted BLE communication
5. **Access Control**: Limit MQTT topic access via broker ACLs

## 🚀 Advanced Usage

### Multiple Devices

```bash
# Run multiple bridges for different devices
xbloom bridge --device-name kitchen --device-address B0:F8:93:DB:B1:C1
xbloom bridge --device-name office --device-address A1:E2:84:CA:A2:D2
```

### Custom Topics

Modify the bridge code to use custom topic structures:

```python
# In bridge.py
self.base_topic = f"coffee/xbloom/{config.device_name}"
```

### Recipe Integration

Create recipe files and execute them:

```bash
# Create recipe file
cat > morning_blend.json << EOF
{
  "name": "Morning Blend",
  "grind_size": 50,
  "total_water": 250,
  "pours": [
    {"volume": 60, "temperature": 94, "pattern": 1},
    {"volume": 190, "temperature": 93, "pattern": 2}
  ]
}
EOF

# Execute recipe
mosquitto_pub -h homeassistant.local -t "xbloom/xbloom/command/recipe/execute" -f morning_blend.json
```