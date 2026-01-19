from typing import TYPE_CHECKING
from xbloom.protocol import XBloomCommand

if TYPE_CHECKING:
    from xbloom.core.client import XBloomClient

class BrewerController:
    """Control the brewer/water system"""
    
    def __init__(self, client: 'XBloomClient'):
        self._client = client
    
    async def start(self) -> bool:
        """Start brewing/pouring water"""
        return await self._client._send_command(XBloomCommand.APP_BREWER_START)
    
    async def stop(self) -> bool:
        """Stop brewing"""
        return await self._client._send_command(XBloomCommand.APP_BREWER_STOP)
    
    async def pause(self) -> bool:
        """Pause brewing"""
        return await self._client._send_command(XBloomCommand.APP_BREWER_PAUSE)
    
    async def restart(self) -> bool:
        """Restart brewing"""
        return await self._client._send_command(XBloomCommand.APP_BREWER_RESTART)
    
    async def set_temperature(self, temp_celsius: float) -> bool:
        """Set target water temperature in Celsius"""
        return await self._client.set_temperature(temp_celsius)

    async def set_cup(self, f1: float, f2: float) -> bool:
        """Set cup type (discovery: [1.0, 0.0] for standard)"""
        return await self._client.set_cup(f1, f2)
    
    async def set_pattern(self, pattern: int) -> bool:
        """Set pour pattern (0=Center, 1=Spiral, 2=Circle)"""
        return await self._client._send_command(XBloomCommand.APP_BREWER_SET_PATTERN, [pattern])
    
    @property
    def temperature(self) -> float:
        return self._client.status.brewer.temperature
    
    @property
    def is_running(self) -> bool:
        return self._client.status.brewer.is_running
