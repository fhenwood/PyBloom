#!/usr/bin/env python3
"""
Simple Grind Example - Grind beans without brewing.

This example demonstrates using the grinder with specific size and speed
using XBloomManualRecipe. No water is poured.

Usage:
    XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_grind.py

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
    print("Usage: XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_grind.py")
    print("Find your device with: xbloom scan")
    sys.exit(1)
from xbloom.models.manual import XBloomManualRecipe


async def main():
    """Grind beans without brewing using XBloomManualRecipe."""
    
    # Create grind-only recipe
    recipe = XBloomManualRecipe.grind_only(
        grind_size=50,          # Medium grind (1-100)
        grind_speed_rpm=80      # Medium speed (60-100)
    )
    
    print(f"\n⚙️  {recipe.name}")
    print(f"   Grind size: {recipe.grind_size}")
    print(f"   Speed: {recipe.grind_speed_rpm} RPM")
    print("=" * 40)
    
    async with XBloomClient(mac_address=DEVICE_MAC) as client:
        if not client.is_connected:
            print("❌ Failed to connect to XBloom!")
            return
        
        # Keep connection alive after script exits
        client._cleanup_on_disconnect = False
        
        # Execute the recipe
        total_ground = await recipe.execute(client)
        
        print("=" * 40)
        print(f"✅ Complete: {total_ground:.1f}g of coffee ground")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted - stopping grinder...")
