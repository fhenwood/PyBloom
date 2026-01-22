#!/usr/bin/env python3
"""
Simple XBloom Brew Example

Demonstrates the clean high-level API for brewing coffee with the XBloom machine.
This script will grind beans and pour water using a simple recipe.

Usage:
    XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_brew.py

Find your device MAC address with: xbloom scan
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xbloom import XBloomClient

# Get MAC address from environment variable
DEVICE_MAC = os.environ.get('XBLOOM_MAC')
if not DEVICE_MAC:
    print("Error: XBLOOM_MAC environment variable not set")
    print("Usage: XBLOOM_MAC=XX:XX:XX:XX:XX:XX python examples/simple_brew.py")
    print("Find your device with: xbloom scan")
    sys.exit(1)
from xbloom.models.types import XBloomRecipe, PourStep, PourPattern, CupType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


async def main():
    """Brew a simple coffee recipe."""
    
    # Define a simple recipe
    recipe = XBloomRecipe(
        name="Simple Pour Over",
        grind_size=50,          # Grinder setting (1-100)
        rpm=80,                 # Grinder motor speed
        bean_weight=15.0,       # Grams of beans to grind
        total_water=24,         # 24 * 10 = 240ml total water
        cup_type=CupType.OMNI_DRIPPER,
        pours=[
            # Bloom pour
            PourStep(
                volume=50,
                temperature=93,
                pausing=30,             # 30 second bloom
                flow_rate=3.0,
                pattern=PourPattern.SPIRAL
            ),
            # Main pour 1
            PourStep(
                volume=95,
                temperature=93,
                pausing=15,
                flow_rate=3.5,
                pattern=PourPattern.SPIRAL
            ),
            # Main pour 2
            PourStep(
                volume=95,
                temperature=93,
                pausing=0,              # No pause after final pour
                flow_rate=3.5,
                pattern=PourPattern.SPIRAL
            ),
        ]
    )
    
    # Connect and brew
    async with XBloomClient(mac_address=DEVICE_MAC) as client:
        if not client.is_connected:
            print("Failed to connect to XBloom!")
            return
        
        # Disable cleanup so brew continues even if script exits
        client._cleanup_on_disconnect = False
        
        print(f"\n☕ Starting brew: {recipe.name}")
        print(f"   Grinding {recipe.bean_weight}g at size {recipe.grind_size}")
        print(f"   Pouring {recipe.total_water * 10}ml in {len(recipe.pours)} pours\n")
        
        # This single method handles everything:
        # - Sets bypass with bean dose (critical for grinding!)
        # - Sets cup bounds
        # - Sends recipe
        # - Executes and waits for completion
        success = await client.brew(recipe, wait_for_completion=True, timeout=600.0)
        
        if success:
            print("\n✅ Brew complete! Enjoy your coffee!")
        else:
            print("\n❌ Brew failed or timed out")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBrew interrupted - machine may still be running")
