import struct
from typing import List
from .constants import XBloomCommand, crc16

def build_command(command: int, data: List[int] = None, type_code: int = 1, device_id: int = 0x01) -> bytes:
    """Build a XBloom protocol command packet"""
    if data is None:
        data = []
    
    data_bytes_len = len(data) * 4
    total_length = 12 + data_bytes_len
    
    packet = bytearray()
    packet.append(0x58)
    packet.append(device_id)
    packet.append(type_code)
    packet.extend(struct.pack('<H', command))
    packet.extend(struct.pack('<I', total_length))
    packet.append(0x01)
    
    for value in data:
        packet.extend(struct.pack('<I', value))
    
    crc = crc16(bytes(packet))
    packet.extend(struct.pack('<H', crc))
    
    return bytes(packet)

def build_command_raw(command: int, data: bytes, type_code: int = 1, device_id: int = 0x01) -> bytes:
    """Build a XBloom protocol command packet with raw bytes data"""
    total_length = 12 + len(data)
    
    packet = bytearray()
    packet.append(0x58)
    packet.append(device_id)
    packet.append(type_code)
    packet.extend(struct.pack('<H', command))
    packet.extend(struct.pack('<I', total_length))
    packet.append(0x01)
    
    packet.extend(data)
    
    crc = crc16(bytes(packet))
    packet.extend(struct.pack('<H', crc))
    
    return bytes(packet)

# Helpers
def cmd_brewer_start() -> bytes: return build_command(XBloomCommand.APP_BREWER_START)
def cmd_brewer_stop() -> bytes: return build_command(XBloomCommand.APP_BREWER_STOP)
def cmd_brewer_pause() -> bytes: return build_command(XBloomCommand.APP_BREWER_PAUSE)
def cmd_brewer_restart() -> bytes: return build_command(XBloomCommand.APP_BREWER_RESTART)
def cmd_set_temperature(temp_c: float) -> bytes:
    return build_command(XBloomCommand.APP_BREWER_SET_TEMPERATURE, [int(temp_c * 10)])
def cmd_brewer_set_pattern(pattern: int) -> bytes:
    return build_command(XBloomCommand.APP_BREWER_SET_PATTERN, [pattern])
def cmd_set_cup_size(cup_type: int) -> bytes:
    return build_command(XBloomCommand.APP_SET_CUP, [cup_type])

def cmd_grinder_in(size: int, speed: int) -> bytes:
    return build_command(XBloomCommand.APP_GRINDER_IN, [size, speed])
def cmd_grinder_start(timeout: int, size: int, speed: int) -> bytes:
    return build_command(XBloomCommand.APP_GRINDER_START, [timeout, size, speed])
def cmd_grinder_stop() -> bytes: return build_command(XBloomCommand.APP_GRINDER_STOP)
def cmd_grinder_pause() -> bytes: return build_command(XBloomCommand.APP_GRINDER_PAUSE)
def cmd_grinder_restart() -> bytes: return build_command(XBloomCommand.APP_GRINDER_RESTART)

def cmd_scale_left() -> bytes: return build_command(XBloomCommand.SG_LEFT)
def cmd_scale_right() -> bytes: return build_command(XBloomCommand.SG_RIGHT)
def cmd_scale_stop() -> bytes: return build_command(XBloomCommand.SG_STOP)
def cmd_scale_vibrate() -> bytes: return build_command(XBloomCommand.SG_VIBRATE)

def cmd_recipe_send(data: bytes) -> bytes: return build_command_raw(XBloomCommand.APP_TEA_RECIP_CODE, data)
def cmd_recipe_execute(data: bytes) -> bytes: return build_command_raw(XBloomCommand.APP_TEA_RECIP_MAKE, data)
def cmd_recipe_stop() -> bytes: return build_command(XBloomCommand.APP_RECIPE_START_QUIT)
