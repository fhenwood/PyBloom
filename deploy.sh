#!/bin/bash
# XBloom MQTT Bridge Deployment Script

set -e

echo "🚀 XBloom MQTT Bridge Deployment Script"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"

# Check if user is in docker group
if ! groups $USER | grep &>/dev/null '\bdocker\b'; then
    echo -e "${YELLOW}⚠️  User $USER is not in docker group${NC}"
    echo "Add user to docker group: sudo usermod -aG docker $USER"
    echo "Then log out and log back in"
    exit 1
fi

# Check Bluetooth
echo -e "${BLUE}🔍 Checking Bluetooth...${NC}"
if ! command_exists bluetoothctl; then
    echo -e "${YELLOW}⚠️  Bluetooth tools not found${NC}"
    echo "Install bluetooth: sudo apt-get install bluetooth bluez"
fi

if ! sudo systemctl is-active --quiet bluetooth; then
    echo -e "${YELLOW}⚠️  Bluetooth service is not running${NC}"
    echo "Start bluetooth: sudo systemctl start bluetooth"
fi

# Check if .env file exists
if [[ ! -f .env ]]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo -e "${BLUE}📝 Creating .env file from template...${NC}"
    
    cat > .env << EOF
# MQTT Broker Settings
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# XBloom Device Settings
DEVICE_NAME=xbloom
DEVICE_ADDRESS=
SESSION_TIMEOUT=60
TELEMETRY_INTERVAL=5

# Logging
LOG_LEVEL=INFO
EOF
    
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}📝 Please edit .env file with your settings${NC}"
    
    read -p "Do you want to edit .env now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo -e "${GREEN}✅ Found .env file${NC}"
fi

# Ask user what to do
echo
echo "What would you like to do?"
echo "1) Build and start the bridge"
echo "2) Stop the bridge"
echo "3) View logs"
echo "4) Test MQTT connection"
echo "5) Scan for XBloom devices"
echo "6) Run MQTT bridge test"

read -p "Enter your choice (1-6): " -n 1 -r
echo

case $REPLY in
    1)
        echo -e "${BLUE}🔨 Building and starting XBloom MQTT Bridge...${NC}"
        docker-compose up --build -d
        echo -e "${GREEN}✅ Bridge started successfully${NC}"
        echo -e "${BLUE}📋 View logs with: docker-compose logs -f xbloom-bridge${NC}"
        ;;
    2)
        echo -e "${BLUE}🛑 Stopping XBloom MQTT Bridge...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Bridge stopped${NC}"
        ;;
    3)
        echo -e "${BLUE}📋 Viewing bridge logs...${NC}"
        docker-compose logs -f xbloom-bridge
        ;;
    4)
        echo -e "${BLUE}🔗 Testing MQTT connection...${NC}"
        source .env
        echo "Testing connection to $MQTT_BROKER:$MQTT_PORT"
        
        if command_exists mosquitto_pub; then
            mosquitto_pub -h $MQTT_BROKER -p $MQTT_PORT -t "test/xbloom" -m "Hello from deployment script"
            echo -e "${GREEN}✅ MQTT publish successful${NC}"
        else
            echo -e "${YELLOW}⚠️  mosquitto clients not installed${NC}"
            echo "Install with: sudo apt-get install mosquitto-clients"
        fi
        ;;
    5)
        echo -e "${BLUE}🔍 Scanning for XBloom devices...${NC}"
        if command_exists python3; then
            python3 -c "
import asyncio
import sys
sys.path.append('src')
from xbloom.scanner import discover_devices

async def scan():
    print('Scanning for XBloom devices (10s)...')
    devices = await discover_devices(timeout=10.0)
    if devices:
        print(f'Found {len(devices)} devices:')
        for d in devices:
            print(f'  - {d.name}: {d.address}')
    else:
        print('No devices found')

asyncio.run(scan())
"
        else
            echo -e "${RED}❌ Python3 not found${NC}"
        fi
        ;;
    6)
        echo -e "${BLUE}🧪 Running MQTT bridge test...${NC}"
        if [[ -f test_mqtt_bridge.py ]]; then
            source .env
            python3 test_mqtt_bridge.py --broker $MQTT_BROKER --device-name $DEVICE_NAME
        else
            echo -e "${RED}❌ test_mqtt_bridge.py not found${NC}"
        fi
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Done!${NC}"