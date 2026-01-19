from typing import TYPE_CHECKING
from xbloom.protocol import XBloomCommand

if TYPE_CHECKING:
    from xbloom.core.client import XBloomClient

class ScaleController:
    """Control the scale/tray"""
    
    def __init__(self, client: 'XBloomClient'):
        self._client = client
    
    async def move_left(self) -> bool:
        """Move scale tray left (to Grinder position in this setup)"""
        # Use SG_LEFT_SINGLE (2503) as 2500 might be continuous/ignored
        return await self._client._send_command(XBloomCommand.SG_LEFT_SINGLE)
    
    async def move_right(self) -> bool:
        """Move scale tray right (to Brewer position in this setup)"""
        # Use SG_RIGHT_SINGLE (2504)
        return await self._client._send_command(XBloomCommand.SG_RIGHT_SINGLE)
    
    async def stop(self) -> bool:
        """Stop scale tray movement"""
        return await self._client._send_command(XBloomCommand.SG_STOP)
    
    async def vibrate(self) -> bool:
        """Vibrate the scale (for settling grounds)"""
        return await self._client._send_command(XBloomCommand.SG_VIBRATE)
    
    @property
    def weight(self) -> float:
        return self._client.status.scale.weight
