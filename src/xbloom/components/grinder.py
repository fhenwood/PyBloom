from typing import Optional, TYPE_CHECKING
import asyncio
from xbloom.protocol import XBloomCommand

if TYPE_CHECKING:
    from xbloom.core.client import XBloomClient

class GrinderController:
    """Control the grinder"""
    
    def __init__(self, client: 'XBloomClient'):
        self._client = client
        self._size: int = 50
        self._speed: int = 100
    
    async def enter_mode(self, size: int = None, speed: int = None) -> bool:
        """Enter grinder mode - MUST call before start()!"""
        if size is not None:
            self._size = size
        if speed is not None:
            self._speed = speed
        return await self._client._send_command(
            XBloomCommand.APP_GRINDER_IN, 
            [self._size, self._speed]
        )
    
    async def start(self, size: int = None, speed: int = None, timeout_ms: int = 1000) -> bool:
        """Start the grinder. Automatically enters grinder mode first."""
        if size is not None:
            self._size = size
        if speed is not None:
            self._speed = speed
        
        # Enter grinder mode first - this sets size/speed on the machine
        await self.enter_mode()
        # Wait for burrs to move/adjust settings
        await asyncio.sleep(2.0)
        
        # Then start WITHOUT params - working packet is 580101AC0D0C000000012021
        # Size/speed are already set via GRINDER_IN above
        return await self._client._send_command(XBloomCommand.APP_GRINDER_START)
    
    async def stop(self) -> bool:
        """Stop the grinder"""
        return await self._client._send_command(XBloomCommand.APP_GRINDER_STOP)
    
    async def pause(self) -> bool:
        """Pause the grinder"""
        return await self._client._send_command(XBloomCommand.APP_GRINDER_PAUSE)
    
    async def restart(self) -> bool:
        """Restart the grinder"""
        return await self._client._send_command(XBloomCommand.APP_GRINDER_RESTART)
    
    @property
    def size(self) -> int:
        return self._size
    
    @property
    def speed(self) -> int:
        return self._speed
    
    @property
    def is_running(self) -> bool:
        return self._client.status.grinder.is_running
    
    @property
    def position(self) -> int:
        return self._client.status.grinder.position
