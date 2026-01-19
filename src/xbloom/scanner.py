import asyncio
from typing import List, Optional
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from .protocol import SERVICE_UUID

async def discover_devices(timeout: float = 5.0) -> List[BLEDevice]:
    """
    Discover XBloom devices in the area.
    
    Tries to find devices by Service UUID first. 
    If none found, scans for devices with 'XBLOOM' in the name.
    
    Args:
        timeout: Scan duration in seconds
        
    Returns:
        List of BLEDevice objects found
    """
    # Try discovering by Service UUID to filter efficiently
    devices = await BleakScanner.discover(timeout=timeout, service_uuids=[SERVICE_UUID])
    
    if not devices:
        # Fallback: Scan everything and filter by name
        # Some devices might not advertise the custom service UUID in the main packet
        all_devices = await BleakScanner.discover(timeout=timeout)
        devices = [d for d in all_devices if d.name and "XBLOOM" in d.name.upper()]
        
    return devices
