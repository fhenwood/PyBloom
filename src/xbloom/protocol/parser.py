import struct
from typing import Optional, Dict, Any
from .constants import XBloomCommand, XBloomResponse, crc16

def parse_response(data: bytes) -> Optional[Dict[str, Any]]:
    """Parse a XBloom response packet"""
    if len(data) < 12:
        return None
    
    packet_crc = struct.unpack('<H', data[-2:])[0]
    calculated_crc = crc16(data[:-2])
    valid_crc = (packet_crc == calculated_crc)
    
    header = data[0:3]
    command = 0
    if len(data) >= 5:
        command = struct.unpack('<H', data[3:5])[0]
    
    payload = data[8:-2] if len(data) > 10 else b''
    
    return {
        'header': header.hex(),
        'command': command,
        'command_name': _get_command_name(command),
        'data': payload,
        'valid_crc': valid_crc,
    }

def _get_command_name(command: int) -> str:
    try:
        return XBloomCommand(command).name
    except ValueError:
        try:
            return XBloomResponse(command).name
        except ValueError:
            return f"UNKNOWN_{command}"
