import struct
import asyncio
from unittest.mock import MagicMock
from typing import Callable, Any
from xbloom.protocol import crc16, XBloomCommand, XBloomResponse
from xbloom.connection import XBloomConnection

# UUIDs
CHARACTERISTIC_WRITE_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb" # Placeholder/Example?
CHARACTERISTIC_NOTIFY_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb" 
# Note: Real UUIDs should be used if strict. Assuming BleXBloom uses correct ones.

class MockXBloomDevice:
    def __init__(self):
        self.connected = False
        self.state = "IDLE"
        self.recipe = None
        self.notification_callback = None
        self.logs = []
        
    def connect(self):
        self.connected = True
        self.logs.append("CONNECTED")
        
    def disconnect(self):
        self.connected = False
        self.logs.append("DISCONNECTED")
        
    def write_gatt_char(self, char_specifier, data, response=False):
        # Validate Packet
        if data[0] != 0x58:
            self.logs.append("INVALID_HEADER")
            return
            
        # Check CRC
        pkt_crc = struct.unpack('<H', data[-2:])[0]
        calc_crc = crc16(data[:-2])
        if pkt_crc != calc_crc:
            self.logs.append(f"INVALID_CRC Expected={calc_crc} Got={pkt_crc}")
            return
            
        # Parse Command
        # Format: 58 01 01 [CMD_LO] [CMD_HI] ...
        cmd_id = struct.unpack('<H', data[3:5])[0]
        self.logs.append(f"CMD_RECEIVED: {cmd_id}")
        
        self.handle_command(cmd_id, data)
        
    def handle_command(self, cmd_id, data):
        if cmd_id == XBloomCommand.APP_TEA_RECIP_CODE:
            # Payload extract
            payload = data[10:-2]
            self.recipe = payload
            self.logs.append(f"RECIPE_STORED Len={len(payload)}")
            
        elif cmd_id == XBloomCommand.APP_TEA_RECIP_MAKE:
            if self.recipe:
                self.state = "BREWING"
                self.logs.append("STATE: BREWING")
                
        elif cmd_id == XBloomCommand.APP_BREWER_STOP:
            self.state = "IDLE"
            self.logs.append("STATE: IDLE")
            
        elif cmd_id == XBloomCommand.APP_BREWER_PAUSE:
            self.state = "PAUSED"
            self.logs.append("STATE: PAUSED")
            
        elif cmd_id == XBloomCommand.APP_GRINDER_START:
            self.state = "GRINDING"
            self.logs.append("STATE: GRINDING")

    def simulate_knob_click(self, times=1):
        self.logs.append(f"KNOB_CLICKED {times}x")
        if times == 3:
             self.state = "IDLE" # Emergency Stop
             self.logs.append("STATE: IDLE (Emergency Stop)")
             
    def simulate_nfc_scan(self, valid=True):
        if valid:
            self.logs.append("NFC_SCANNED_VALID")
            self.recipe = b'dummy_recipe_data'
        else:
            self.logs.append("NFC_SCANNED_INVALID")
            
    def simulate_weight_change(self, weight):
        # Emit RD_CURRENT_WEIGHT2 (20501)
        # Manually build packet: 
        # Header(58 01 02) + Cmd(2) + Len(4) + Type(1) + Data(4) + CRC(2)
        # Note: using type_code=2 for notifications usually
        
        pkt = bytearray([0x58, 0x01, 0x02])
        pkt.extend(struct.pack('<H', 20501))
        pkt.extend(struct.pack('<I', 16)) # 12 + 4
        pkt.append(0x01)
        pkt.extend(struct.pack('<f', weight)) # Float
        
        # CRC
        calc = crc16(pkt)
        pkt.extend(struct.pack('<H', calc))
        
        self.emit_notification(pkt)
             
    def simulate_machine_info(self):
        # Emit RD_MachineInfo (40521 = 0x9E49)
        # Payload Format (from Client logic):
        # 0-13: Serial
        # 13-19: Model
        # 19-29: Version
        # ...
        
        serial = b"SN1234567890\x00" # 13 bytes
        model = b"ModelA\x00"        # 6+ bytes? Logic says 13:19 (6 bytes)
        # Assuming fixed width or null Terminated?
        # Client: payload[0:13], payload[13:19].
        
        # Safe construction:
        pl = bytearray(40) # Ensure enough size
        pl[0:12] = b"SN1234567890" # 12 chars + null?
        pl[13:18] = b"Model" 
        pl[19:24] = b"v1.0.0"
        pl[33] = 1 # Water Level OK
        
        pkt = bytearray([0x58, 0x01, 0x02])
        pkt.extend(struct.pack('<H', 40521))
        pkt.extend(struct.pack('<I', 12 + len(pl)))
        pkt.append(0x01)
        pkt.extend(pl)
        
        calc = crc16(pkt)
        pkt.extend(struct.pack('<H', calc))
        
        self.emit_notification(pkt)
        
    def start_notify(self, char_specifier, callback: Callable[[int, bytearray], None]):
        self.notification_callback = callback
        self.logs.append("NOTIFY_STARTED")

    def stop_notify(self, char_specifier):
        self.notification_callback = None
        
    def emit_notification(self, data: bytes):
        if self.notification_callback:
            self.notification_callback(0, bytearray(data))

class MockConnection(XBloomConnection):
    """Mock connection for testing without Bleak"""
    
    def __init__(self, device: MockXBloomDevice):
        self._device = device
        
    async def connect(self, address: str, timeout: float = 20.0) -> bool:
        self._device.connect()
        return True
        
    async def disconnect(self) -> None:
        self._device.disconnect()
        
    @property
    def is_connected(self) -> bool:
        return self._device.connected
        
    async def write_command(self, char_uuid: str, data: bytes, response: bool = False) -> None:
        self._device.write_gatt_char(char_uuid, data, response)
        
    async def start_notify(self, char_uuid: str, callback: Callable[[int, bytearray], None]) -> None:
        self._device.start_notify(char_uuid, callback)
        
    async def stop_notify(self, char_uuid: str) -> None:
        self._device.stop_notify(char_uuid)
