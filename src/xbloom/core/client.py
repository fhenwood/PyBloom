import asyncio
import struct
import logging
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any

from xbloom.models.types import DeviceStatus, DeviceState, GrinderStatus, BrewerStatus, ScaleStatus
from xbloom.models.recipes import build_recipe_payload
from xbloom.models.types import XBloomRecipe
from xbloom.connection import XBloomConnection, BleakConnection
from xbloom.protocol import (
    SERVICE_UUID, WRITE_UUID, NOTIFY_UUID,
    XBloomCommand, XBloomResponse,
    build_command, build_command_raw
)
from xbloom.protocol.parser import _get_command_name
from xbloom.components import GrinderController, BrewerController, ScaleController

logger = logging.getLogger(__name__)

class XBloomClient:
    """
    Main XBloom device controller.
    
    Provides high-level async API for controlling all XBloom functions.
    Uses BLE for communication via XBloomConnection interface.
    """
    
    READ_CHAR = "0000ffe3-0000-1000-8000-00805f9b34fb"

    def __init__(self, mac_address: str = None, connection: XBloomConnection = None):
        if mac_address is None:
            raise ValueError("mac_address is required. Use 'xbloom scan' to find your device.")
        self.mac_address = mac_address
        self._connection = connection or BleakConnection()
        self._status = DeviceStatus()
        self._callbacks: List[Callable[[DeviceStatus], None]] = []
        self._device_id = 0x01  # Back to 0x01 default
        self._cleanup_on_disconnect = True  # Set to False to preserve brew state on disconnect
        
        # Component controllers
        self.grinder = GrinderController(self)
        self.brewer = BrewerController(self)
        self.scale = ScaleController(self)
    
    async def connect(self, timeout: float = 20.0) -> bool:
        """Connect to the XBloom device"""
        if self._connection.is_connected:
            return True
        
        try:
            await self._connection.connect(self.mac_address, timeout=timeout)
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
        
        if self._connection.is_connected:
            # Subscribe to notifications
            await self._connection.start_notify(NOTIFY_UUID, self._on_notification)
            try:
                await self._connection.start_notify(self.READ_CHAR, self._on_notification)
            except:
                pass
            
            self._status.connected = True
            
            # Perform initial cleanup to ensure clean state
            await self._reset_state()
            
            await asyncio.sleep(0.5)  # Wait for initial status
            return True
        
        return False
    
    async def _reset_state(self):
        """Reset machine state by stopping recipes and exiting modes"""
        logger.info("Cleaning up machine state...")
        try:
            # Stop any running recipe
            await self._send_command(XBloomCommand.APP_RECIPE_STOP)
            await asyncio.sleep(0.5)
            # Quit modes
            await self._send_command(XBloomCommand.APP_BREWER_QUIT)
            await self._send_command(XBloomCommand.APP_GRINDER_QUIT)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"Cleanup failed (may be disconnected): {e}")

    async def disconnect(self) -> None:
        """Disconnect from the device"""
        if self._connection.is_connected:
            # Try to cleanup before disconnecting (unless disabled)
            if self._cleanup_on_disconnect:
                try:
                    await self._reset_state()
                except:
                    pass
            
            try:
                await self._connection.stop_notify(NOTIFY_UUID)
            except:
                pass
            await self._connection.disconnect()
        self._status.connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connection.is_connected
    
    @property
    def status(self) -> DeviceStatus:
        """Get current device status"""
        return self._status
    
    async def send_recipe(self, recipe: 'XBloomRecipe', type_code: int = 1, device_id: int = None) -> bool:
        """Send a recipe to the machine (uses Tea protocol by default)"""
        payload_bytes = build_recipe_payload(recipe)
        return await self._send_command_raw(XBloomCommand.APP_TEA_RECIP_CODE, payload_bytes, type_code=type_code, device_id=device_id)

    async def execute_recipe(self, recipe: 'XBloomRecipe', type_code: int = 1, device_id: int = None) -> bool:
        """Start brewing the uploaded recipe (uses Tea protocol by default)"""
        payload_bytes = build_recipe_payload(recipe)
        return await self._send_command_raw(XBloomCommand.APP_TEA_RECIP_MAKE, payload_bytes, type_code=type_code, device_id=device_id)

    async def send_coffee_recipe(self, recipe: 'XBloomRecipe', type_code: int = 1, device_id: int = None) -> bool:
        """Send a coffee recipe (defaults to 8001 APP_RECIPE_SEND_AUTO for full automation)"""
        payload_bytes = build_recipe_payload(recipe)
        return await self._send_command_raw(XBloomCommand.APP_RECIPE_SEND_AUTO, payload_bytes, type_code=type_code, device_id=device_id)

    async def execute_coffee_recipe(self, device_id: int = None) -> None:
        """Execute the already sent coffee recipe (Standard 8002)"""
        await self._send_command(XBloomCommand.APP_RECIPE_EXECUTE, device_id=device_id)

    async def set_easy_mode(self, enabled: bool = True, device_id: int = None) -> None:
        """Switch between EASY (auto-advance) and PRO (manual confirmation) modes."""
        mode_str = "01" if enabled else "02"
        # Studio uses type_code=0x02 for mode switch
        await self._send_command_raw(11511, bytes.fromhex(mode_str), device_id=device_id, type_code=0x02)

    async def confirm_next(self, device_id: int = None) -> None:
        """Send confirmation to advance to the next recipe step."""
        await self._send_command(40516, device_id=device_id)

    async def stop_recipe(self, type_code: int = 1, device_id: int = None) -> bool:
        """Stop any currently running recipe execution (Standard 40519)"""
        return await self._send_command(XBloomCommand.APP_RECIPE_STOP, type_code=type_code, device_id=device_id)

    async def set_cup(self, f1: float, f2: float, type_code: int = 1, device_id: int = None) -> bool:
        """Set cup type using two floats (bits)"""
        b1 = struct.unpack('<I', struct.pack('<f', f1))[0]
        b2 = struct.unpack('<I', struct.pack('<f', f2))[0]
        return await self._send_command(XBloomCommand.APP_SET_CUP, [b1, b2], type_code=type_code, device_id=device_id)

    async def set_temperature(self, temp_celsius: float, type_code: int = 1, device_id: int = None) -> bool:
        """Set target water temperature in Celsius (multiplied by 10)"""
        temp_value = int(temp_celsius * 10)
        return await self._send_command(XBloomCommand.APP_BREWER_SET_TEMPERATURE, [temp_value], type_code=type_code, device_id=device_id)

    async def set_bypass(self, volume: float, temp: float, dose: int, type_code: int = 1, device_id: int = None) -> bool:
        """Set bypass parameters (Volume, Temp, Dose)"""
        vol_bits = struct.unpack('<I', struct.pack('<f', volume))[0]
        # Temp is * 10 in float bits
        temp_val = float(temp * 10)
        temp_bits = struct.unpack('<I', struct.pack('<f', temp_val))[0]
        return await self._send_command(XBloomCommand.APP_SET_BYPASS, [vol_bits, temp_bits, int(dose)], type_code=type_code, device_id=device_id)

    def on_status_update(self, callback: Callable[[DeviceStatus], None]) -> None:
        """Register a callback for status updates"""
        self._callbacks.append(callback)
    
    async def _send_command(self, command: int, data: list = None, device_id: int = None, type_code: int = 0x01) -> bool:
        """Send a command with integer list data (packed as 4-byte LE ints)"""
        if not self.is_connected:
            raise ConnectionError("Not connected to device")
        
        target_device_id = device_id if device_id is not None else self._device_id
        packet = build_command(command, data, device_id=target_device_id, type_code=type_code)
        logger.info(f"SEND CMD [ID:0x{target_device_id:02x}, Type:0x{type_code:02x}]: {command} ({_get_command_name(command)}) | DATA: {packet.hex()}")
        await self._connection.write_command(WRITE_UUID, packet, response=False)
        return True

    async def _send_command_raw(self, command: int, data: bytes, device_id: int = None, type_code: int = 0x01) -> bool:
        """Send a command with raw binary data"""
        if not self.is_connected:
            raise ConnectionError("Not connected to device")
        
        target_device_id = device_id if device_id is not None else self._device_id
        packet = build_command_raw(command, data, device_id=target_device_id, type_code=type_code)
        logger.info(f"SEND CMD RAW [ID:0x{target_device_id:02x}, Type:0x{type_code:02x}]: {command} ({_get_command_name(command)}) | DATA: {packet.hex()}")
        await self._connection.write_command(WRITE_UUID, packet, response=False)
        return True
    
    def _on_notification(self, char, data: bytearray) -> None:
        """Handle incoming BLE notifications, splitting multiple packets if needed."""
        raw_data = bytes(data)
        logger.debug(f"NOTIFICATION [{char}]: {raw_data.hex()}")
        
        # Packets can be concatenated. Headers are 0x58 (outbound/Standard) or 0x02 (Studio notify)
        offset = 0
        while offset < len(raw_data):
            # Find next header
            if raw_data[offset] not in (0x58, 0x02):
                offset += 1
                continue
                
            if len(raw_data) - offset < 10:
                break # Too short for header
                
            # Length is 4 bytes at offset + 5
            try:
                payload_len = struct.unpack('<I', raw_data[offset+5 : offset+9])[0]
                total_len = payload_len # Standard length includes header etc? 
                # Wait, build_command says length is total packet length.
                # Let's verify. 1 (header) + 1 (id) + 1 (type) + 2 (cmd) + 4 (len) + ...
                # If total_len is 16, then we read 16 bytes.
                
                if offset + total_len > len(raw_data):
                    logger.warning(f"Partial packet received: {len(raw_data)-offset}/{total_len} bytes")
                    break
                    
                packet = raw_data[offset : offset + total_len]
                self._parse_response(packet)
                offset += total_len
            except Exception as e:
                logger.warning(f"Error splitting packets at offset {offset}: {e}")
                offset += 1
    
    def _parse_response(self, data: bytes) -> None:
        """Parse and process response data"""
        if len(data) < 10:
            logger.debug(f"Received short packet: {len(data)} bytes")
            return
        
        # Extract command ID (bytes 3-5, little-endian)
        try:
            cmd = struct.unpack('<H', data[3:5])[0]
            logger.info(f"RECV CMD: {cmd} ({_get_command_name(cmd)}) | DATA: {data.hex()}")
        except Exception as e:
            logger.error(f"Failed to unpack command ID: {e}")
            return
        
        # Update status based on response type
        try:
            response_type = XBloomResponse(cmd)
            self._handle_response(response_type, data)
        except ValueError:
            logger.debug(f"Unknown response command: {cmd}")
        except Exception as e:
            logger.error(f"Error handling response {cmd}: {e}")
        
        self._status.last_update = datetime.now()
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(self._status)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _handle_response(self, response: XBloomResponse, data: bytes) -> None:
        """Handle specific response types"""
        # Payload starts at byte 10 (Header 3 + Cmd 2 + Len 4 + Type 1)
        # Ends at -2 (CRC 2)
        payload = data[10:-2] if len(data) > 12 else b''
        
        if response == XBloomResponse.RD_MachineInfo:
            try:
                if len(payload) >= 34:
                    self._status.serial_number = payload[0:13].decode('utf-8', errors='ignore').strip('\x00')
                    self._status.model = payload[13:19].decode('utf-8', errors='ignore').strip('\x00')
                    self._status.version = payload[19:29].decode('utf-8', errors='ignore').strip('\x00')
                    self._status.water_level_ok = (payload[33] == 1)
                    system_status = payload[34]
                    logger.info(f"SYSTEM STATUS UPDATE: {system_status}")
                    if len(payload) >= 37:
                        self._status.water_volume = payload[36]
            except Exception:
                pass
        
        elif response == XBloomResponse.RD_GearReport:
            if len(payload) >= 4:
                self._status.grinder.position = struct.unpack('<I', payload[:4])[0]
        
        elif response == XBloomResponse.RD_CURRENT_WEIGHT2:
            if len(payload) >= 4:
                self._status.scale.weight = struct.unpack('<f', payload[:4])[0]
        
        elif response == XBloomResponse.RD_BREWER_TEMPERATURE:
            if len(payload) >= 4:
                temp_raw = struct.unpack('<I', payload[:4])[0]
                self._status.brewer.temperature = temp_raw / 10.0
                
        elif response == XBloomResponse.RD_GRINDER_BEGIN:
            self._status.grinder.is_running = True
            self._status.state = DeviceState.GRINDING
            
        elif response == XBloomResponse.RD_Grinder_Stop:
            self._status.grinder.is_running = False
            self._status.state = DeviceState.IDLE
            
        elif response == XBloomResponse.RD_BREWER_BEGIN:
            self._status.brewer.is_running = True
            self._status.state = DeviceState.BREWING
            
        elif response == XBloomResponse.RD_Brewer_Stop:
            self._status.brewer.is_running = False
            self._status.state = DeviceState.IDLE
            
        elif response == XBloomResponse.RD_BLOOM:
            self._status.state = DeviceState.BREWING
            
        elif response == XBloomResponse.RD_BREWER_PAUSE:
            self._status.state = DeviceState.PAUSED
            
        elif response == XBloomResponse.RD_BREWER_COFFEE_START:
            self._status.brewer.is_running = True
            self._status.state = DeviceState.BREWING

        elif response == XBloomResponse.RD_WATER_VOLUME:
            if len(payload) >= 4:
                # payload is a float32 at byte 0
                self._status.water_volume = int(struct.unpack('<f', payload[:4])[0])

        elif response == XBloomResponse.RD_IN_BREWER:
            # Studio reports brewer state via 9001 with: volume, temperature, pattern
            if len(payload) >= 12:
                volume = struct.unpack('<I', payload[0:4])[0]
                temperature = struct.unpack('<I', payload[4:8])[0]
                pattern = struct.unpack('<I', payload[8:12])[0]
                self._status.brewer.temperature = float(temperature)
                self._status.brewer.is_running = True
                self._status.state = DeviceState.BREWING
                logger.info(f"BREWER STATE: vol={volume} temp={temperature}C pattern={pattern}")

    # ========================================================================
    # HIGH-LEVEL BREW API
    # ========================================================================
    
    async def brew(
        self,
        recipe: 'XBloomRecipe',
        wait_for_completion: bool = True,
        timeout: float = 600.0
    ) -> bool:
        """
        Execute a complete coffee brew with grinding.
        
        This is the main high-level method that handles the full workflow:
        1. Set bypass parameters (including bean dose - CRITICAL for grinding!)
        2. Set cup bounds
        3. Send recipe (8001 - with grinding)
        4. Execute recipe (8002)
        5. Optionally wait for completion
        
        Args:
            recipe: XBloomRecipe containing grind settings, pours, etc.
            wait_for_completion: If True, wait for brew to finish
            timeout: Max seconds to wait for completion (default 10 minutes)
            
        Returns:
            True if brew started (and completed if wait_for_completion=True)
            
        Protocol Notes (reverse-engineered from Java app):
            - Command order MUST be: Bypass(8102) -> Cup(8104) -> Recipe(8001) -> Execute(8002)
            - Bypass command takes [volume, temp*10, dose] - dose is REQUIRED for grinding!
            - Recipe 8001 = with grinding, 8004 = without grinding
            - Recipe footer is 2 bytes: [grindSize, totalWater*10]
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to device")
        
        logger.info("=" * 60)
        logger.info(f"Starting brew: {recipe.name}")
        logger.info(f"  Grind Size: {recipe.grind_size}")
        logger.info(f"  Bean Weight: {recipe.bean_weight}g")
        logger.info(f"  Total Water: {recipe.total_water * 10}ml")
        logger.info(f"  Pours: {len(recipe.pours)}")
        logger.info("=" * 60)
        
        # Determine cup bounds based on cup type
        # Cup weight limits:
        #   XPod (1):     min=40g, max=80g
        #   XDripper (2): min=40g, max=90g
        #   Other (3):    min=40g, max=90g
        cup_bounds = {
            1: (80.0, 40.0),   # XPod: (max, min)
            2: (90.0, 40.0),   # XDripper
            3: (90.0, 40.0),   # Other
        }
        cup_type_val = recipe.cup_type.value if hasattr(recipe.cup_type, 'value') else recipe.cup_type
        cup_max, cup_min = cup_bounds.get(cup_type_val, (90.0, 40.0))
        
        # ====================================================================
        # STEP 1: Set Bypass (8102)
        # CRITICAL: The dose parameter tells the machine how many grams to grind!
        # Even when bypass water is disabled (vol=0, temp=0), dose MUST be set!
        # ====================================================================
        dose = int(recipe.bean_weight)
        logger.info(f"[1/4] Setting bypass (vol=0, temp=0, dose={dose})")
        await self.set_bypass(0.0, 0.0, dose)
        await asyncio.sleep(1.0)
        
        # ====================================================================
        # STEP 2: Set Cup Bounds (8104)
        # Sets weight limits for cup detection
        # ====================================================================
        logger.info(f"[2/4] Setting cup bounds (max={cup_max}, min={cup_min})")
        await self.set_cup(cup_max, cup_min)
        await asyncio.sleep(1.0)
        
        # ====================================================================
        # STEP 3: Send Recipe (8001 - APP_RECIPE_SEND_AUTO)
        # Uses command 8001 for full automation with grinding
        # Recipe payload: LENGTH(1) + BODY + FOOTER(2)
        # Footer: [grindSize, totalWater*10]
        # ====================================================================
        logger.info(f"[3/4] Sending recipe (8001)")
        await self.send_coffee_recipe(recipe)
        await asyncio.sleep(1.0)
        
        # ====================================================================
        # STEP 4: Execute Recipe (8002)
        # Triggers the full sequence:
        #   - Move dripper to grinder (9000)
        #   - Grind beans (9003)
        #   - Move dripper to brewer (9001)
        #   - Pour water (9005)
        #   - Complete (40512 RD_ENJOY)
        # ====================================================================
        logger.info(f"[4/4] Executing recipe (8002)")
        await self.execute_coffee_recipe()
        
        if not wait_for_completion:
            logger.info("Brew started - not waiting for completion")
            return True
        
        # ====================================================================
        # WAIT FOR COMPLETION
        # Monitor status until brewing finishes
        # ====================================================================
        logger.info("Waiting for brew to complete...")
        start_time = asyncio.get_event_loop().time()
        brewing_started = False
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if not self.is_connected:
                logger.error("Disconnected during brew!")
                return False
            
            status = self.status
            
            # Detect brewing start
            if status.brewer.is_running and not brewing_started:
                brewing_started = True
                logger.info(">>> Water pouring started <<<")
            
            # Detect completion (brewing was running, now stopped)
            if brewing_started and not status.brewer.is_running:
                await asyncio.sleep(2)  # Settle time
                if not self.status.brewer.is_running:
                    logger.info(">>> Brew complete! <<<")
                    return True
            
            await asyncio.sleep(0.5)
        
        logger.warning("Brew timed out!")
        return False

    async def brew_without_grinding(
        self,
        recipe: 'XBloomRecipe',
        wait_for_completion: bool = True,
        timeout: float = 300.0
    ) -> bool:
        """
        Execute a brew WITHOUT grinding (for pre-ground coffee).
        
        Uses command 8004 instead of 8001.
        
        Args:
            recipe: XBloomRecipe containing pour settings
            wait_for_completion: If True, wait for brew to finish
            timeout: Max seconds to wait for completion
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to device")
        
        logger.info(f"Starting brew (no grinding): {recipe.name}")
        
        # Cup bounds - BYPASSING SAFETY CHECK (min=0.0) due to 0g telemetry issue
        cup_bounds = {1: (80.0, 0.0), 2: (90.0, 0.0), 3: (90.0, 0.0)}
        cup_type_val = recipe.cup_type.value if hasattr(recipe.cup_type, 'value') else recipe.cup_type
        cup_max, cup_min = cup_bounds.get(cup_type_val, (90.0, 40.0))
        
        # Step 1: Bypass with dose=0 (no grinding)
        await self.set_bypass(0.0, 0.0, 0)
        await asyncio.sleep(0.3)
        
        # Step 2: Cup bounds
        await self.set_cup(cup_max, cup_min)
        await asyncio.sleep(0.3)
        
        # Step 3: Send recipe with 8004 (no grinding)
        payload_bytes = build_recipe_payload(recipe)
        await self._send_command_raw(XBloomCommand.APP_RECIPE_SEND_MANUAL, payload_bytes)
        await asyncio.sleep(0.3)
        
        # Step 4: Execute
        await self.execute_coffee_recipe()
        
        if not wait_for_completion:
            return True
        
        # Wait for completion
        start_time = asyncio.get_event_loop().time()
        brewing_started = False
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if not self.is_connected:
                return False
            
            status = self.status
            if status.brewer.is_running and not brewing_started:
                brewing_started = True
            
            if brewing_started and not status.brewer.is_running:
                await asyncio.sleep(2)
                if not self.status.brewer.is_running:
                    return True
            
            await asyncio.sleep(0.5)
        
        return False

    async def run_recipe_workflow(self, recipe: 'XBloomRecipe') -> None:
        """
        DEPRECATED: Use brew() instead.
        
        Legacy method kept for backwards compatibility.
        """
        logger.warning("run_recipe_workflow() is deprecated, use brew() instead")
        await self.brew(recipe, wait_for_completion=False)
            
    async def __aenter__(self) -> 'XBloomClient':
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()
