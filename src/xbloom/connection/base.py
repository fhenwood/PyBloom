from abc import ABC, abstractmethod
from typing import Callable

class XBloomConnection(ABC):
    """Abstract interface for XBloom device communication"""
    
    @abstractmethod
    async def connect(self, address: str, timeout: float = 20.0) -> bool:
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        pass
        
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass
        
    @abstractmethod
    async def write_command(self, char_uuid: str, data: bytes, response: bool = False) -> None:
        pass
        
    @abstractmethod
    async def start_notify(self, char_uuid: str, callback: Callable[[int, bytearray], None]) -> None:
        pass
        
    @abstractmethod
    async def stop_notify(self, char_uuid: str) -> None:
        pass
