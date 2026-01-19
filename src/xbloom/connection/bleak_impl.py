from typing import Callable, Optional
import logging
from bleak import BleakClient
from .base import XBloomConnection

logger = logging.getLogger(__name__)

class BleakConnection(XBloomConnection):
    """Concrete implementation using Bleak"""
    
    def __init__(self):
        self._client: Optional[BleakClient] = None
        
    async def connect(self, address: str, timeout: float = 20.0) -> bool:
        logger.info(f"Connecting to {address} (timeout={timeout})...")
        self._client = BleakClient(address, timeout=timeout)
        try:
            await self._client.connect()
            logger.info(f"Connected: {self._client.is_connected}")
            return self._client.is_connected
        except Exception as e:
            logger.error(f"Bleak connect failed: {e}")
            raise

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
            
    @property
    def is_connected(self) -> bool:
        connected = self._client is not None and self._client.is_connected
        if not connected:
            logger.debug(f"BleakConnection status: client={self._client is not None}, connected={self._client.is_connected if self._client else 'N/A'}")
        return connected
        
    async def write_command(self, char_uuid: str, data: bytes, response: bool = False) -> None:
        if not self.is_connected:
            raise ConnectionError("Not connected")
        await self._client.write_gatt_char(char_uuid, data, response=response)
        
    async def start_notify(self, char_uuid: str, callback: Callable[[int, bytearray], None]) -> None:
        if not self.is_connected:
            raise ConnectionError("Not connected")
        await self._client.start_notify(char_uuid, callback)
        
    async def stop_notify(self, char_uuid: str) -> None:
        if self.is_connected:
            try:
                await self._client.stop_notify(char_uuid)
            except Exception as e:
                logger.warning(f"Failed to stop notify: {e}")
