#!/usr/bin/env python3
"""
Simple Tea Pour Example - Pour hot water for tea.

This example demonstrates pouring water for tea at a lower temperature
without any grinding. Perfect for tea brewing.

Usage:
    XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_tea_pour.py

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
    print("Usage: XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_tea_pour.py")
    print("Find your device with: xbloom scan")
    sys.exit(1)
from xbloom.models.manual import XBloomManualRecipe
from xbloom.models.types import PourStep, PourPattern


async def main():
    """Pour water for tea using XBloomManualRecipe."""

    # Tea pour: lower temperature, single pour, spiral pattern
    recipe = XBloomManualRecipe(
        name="Tea Pour",
        pours=[
            PourStep(
                volume=200,             # 200ml for a cup of tea
                temperature=85,         # Lower temp for green tea (85°C)
                flow_rate=3.0,
                pattern=PourPattern.SPIRAL
            ),
        ]
    )
    
    print(f"\n🍵 {recipe.name}")
    print(f"   Volume: {recipe.total_volume}ml")
    print(f"   Temperature: {recipe.pours[0].temperature}°C")
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
        print("🍵 Enjoy your tea!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted - machine may still be running")
