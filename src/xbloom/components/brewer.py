from typing import TYPE_CHECKING
import struct
from xbloom.protocol import XBloomCommand

if TYPE_CHECKING:
    from xbloom.core.client import XBloomClient

class BrewerController:
    """Control the brewer/water system"""
    
    def __init__(self, client: 'XBloomClient'):
        self._client = client
    
    async def start(
        self,
        volume: float = 100.0,
        temperature: float = 93.0,
        flow_rate: float = 3.0,
        pattern: int = 2,  # 0=Center, 1=Circular, 2=Spiral
        water_source: int = 0
    ) -> bool:
        """
        Start pouring water with specified parameters.
        
        The Java app sends: CodeModule(APP_BREWER_START, "启动打水",
            floatToIntBits(flowRate*10),
            floatToIntBits(volume*10), 
            floatToIntBits(temp*10),
            waterFeed,
            pattern)
        
        Args:
            volume: Water volume in ml
            temperature: Water temperature in Celsius
            flow_rate: Flow rate (typically 3.0-3.5)
            pattern: Pour pattern (0=Center, 1=Circular, 2=Spiral)
            water_source: Water source/feed setting (default 0)
        """
        # Convert to Java float bits format (value * 10), using little-endian like rest of protocol
        flow_bits = struct.unpack('<I', struct.pack('<f', flow_rate * 10))[0]
        volume_bits = struct.unpack('<I', struct.pack('<f', volume * 10))[0]
        temp_bits = struct.unpack('<I', struct.pack('<f', temperature * 10))[0]
        
        # Pack as 5 32-bit integers (little-endian)
        payload = struct.pack('<5I', flow_bits, volume_bits, temp_bits, water_source, pattern)
        
        return await self._client._send_command_raw(XBloomCommand.APP_BREWER_START, payload)
    
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

