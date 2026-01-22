#!/usr/bin/env python3
"""
Simple Pour Example - Pour water without grinding.

This example demonstrates pouring a specific amount of water at a set temperature
using XBloomManualRecipe. Supports multiple pour steps with pauses.

Usage:
    XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_pour.py

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
    print("Usage: XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_pour.py")
    print("Find your device with: xbloom scan")
    sys.exit(1)
from xbloom.models.manual import XBloomManualRecipe
from xbloom.models.types import PourStep, PourPattern


async def main():
    """Pour water without grinding using XBloomManualRecipe."""
    
    # Option 1: Simple single pour
    # recipe = XBloomManualRecipe.pour_only(
    #     volume=100,         # 100ml of water
    #     temperature=85      # At 85°C
    # )
    
    # Option 2: Multiple pours with bloom (uncomment to use)
    recipe = XBloomManualRecipe(
        name="V60 Manual Pour",
        pours=[
            PourStep(volume=50, temperature=93, pausing=30, pattern=PourPattern.SPIRAL),  # Bloom
            PourStep(volume=100, temperature=93, pausing=15),
            PourStep(volume=100, temperature=93),  # Final pour
        ]
    )
    
    print(f"\n💧 {recipe.name}")
    print(f"   Total volume: {recipe.total_volume}ml")
    print(f"   Pour steps: {len(recipe.pours)}")
    print("=" * 40)
    
    async with XBloomClient(mac_address=DEVICE_MAC) as client:
        if not client.is_connected:
            print("❌ Failed to connect to XBloom!")
            return
        
        # Keep connection alive after script exits
        client._cleanup_on_disconnect = False
        
        # Execute the recipe
        total_poured = await recipe.execute(client)
        
        print("=" * 40)
        print(f"✅ Complete: {total_poured:.1f}g poured")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted - machine may still be running")
