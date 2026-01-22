#!/usr/bin/env python3
"""
Simple Weight Example - Read weight from the scale.

This example demonstrates reading the current weight from the XBloom scale.
Useful for testing connectivity and monitoring.

Usage:
    XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_weight.py

Find your device MAC address with: xbloom scan
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xbloom import XBloomClient

# Get MAC address from environment variable
DEVICE_MAC = os.environ.get('XBLOOM_MAC')
if not DEVICE_MAC:
    print("Error: XBLOOM_MAC environment variable not set")
    print("Usage: XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_weight.py")
    print("Find your device with: xbloom scan")
    sys.exit(1)


async def main():
    """Read weight from the scale."""
    
    print("\n⚖️  Simple Weight Monitor")
    print("=" * 40)
    
    async with XBloomClient(mac_address=DEVICE_MAC) as client:
        if not client.is_connected:
            print("❌ Failed to connect to XBloom!")
            return
        
        print("✅ Connected to XBloom")
        print("📊 Reading weight (press Ctrl+C to stop)...\n")
        
        try:
            while True:
                # Get current weight from status
                weight = client.status.scale.weight
                
                # Also get other useful info
                temp = client.status.brewer.temperature
                grinder_running = client.status.grinder.is_running
                brewer_running = client.status.brewer.is_running
                
                # Display status
                print(f"   Weight: {weight:7.1f}g  |  "
                      f"Temp: {temp:5.1f}°C  |  "
                      f"Grinder: {'ON' if grinder_running else 'OFF'}  |  "
                      f"Brewer: {'ON' if brewer_running else 'OFF'}", 
                      end='\r')
                
                await asyncio.sleep(0.2)
                
        except asyncio.CancelledError:
            pass
        
        print("\n" + "=" * 40)
        print("✅ Monitoring stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Monitoring stopped by user")
