import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

try:
    import aiomqtt
except ImportError:
    aiomqtt = None

from .core.client import XBloomClient
from .scanner import discover_devices
from .models.types import XBloomRecipe, PourStep, PourPattern, VibrationPattern, DeviceState
from .models.recipes import parse_recipe_json

logger = logging.getLogger(__name__)

@dataclass 
class BridgeConfig:
    """Configuration for the MQTT Bridge"""
    broker_host: str = "localhost"
    broker_port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    device_name: str = "xbloom"
    device_address: Optional[str] = None
    session_timeout: int = 60  # seconds
    telemetry_interval: int = 5  # seconds
    reconnect_delay: int = 5  # seconds
    auto_discover: bool = True

class XBloomMQTTBridge:
    """
    MQTT Bridge for XBloom Coffee Machine
    
    Provides session-based BLE connection management with MQTT control.
    Connects to machine only when needed, disconnects after timeout.
    """
    
    def __init__(self, config: BridgeConfig):
        if aiomqtt is None:
            raise ImportError("aiomqtt is required. Install with: pip install aiomqtt")
            
        self.config = config
        self.client: Optional[XBloomClient] = None
        self.mqtt_client: Optional[aiomqtt.Client] = None
        
        # Session management
        self._last_activity = datetime.now()
        self._session_lock = asyncio.Lock()
        self._running = False
        self._telemetry_task: Optional[asyncio.Task] = None
        
        # Topic structure
        self.base_topic = f"xbloom/{config.device_name}"
        
        # Last known values for change detection
        self._last_telemetry = {}
        
    async def start(self):
        """Start the MQTT bridge"""
        logger.info(f"Starting XBloom MQTT Bridge for device: {self.config.device_name}")
        
        if self.config.auto_discover and not self.config.device_address:
            logger.info("Auto-discovering XBloom devices...")
            devices = await discover_devices(timeout=10.0)
            if devices:
                self.config.device_address = devices[0].address
                logger.info(f"Found device: {self.config.device_address}")
            else:
                logger.error("No XBloom devices found. Please specify device address.")
                return
                
        self._running = True
        
        # Start MQTT connection
        mqtt_config = {
            "hostname": self.config.broker_host,
            "port": self.config.broker_port,
        }
        if self.config.username:
            mqtt_config["username"] = self.config.username
        if self.config.password:
            mqtt_config["password"] = self.config.password
            
        try:
            async with aiomqtt.Client(**mqtt_config) as mqtt_client:
                self.mqtt_client = mqtt_client
                
                # Subscribe to command topics
                await self._subscribe_to_commands()
                
                # Publish initial status
                await self._publish_bridge_status("online")
                await self._publish_availability("offline")
                
                # Start background tasks
                session_task = asyncio.create_task(self._session_manager())
                telemetry_task = asyncio.create_task(self._telemetry_publisher())
                
                logger.info("MQTT Bridge started successfully")
                
                # Main message loop
                async for message in mqtt_client.messages:
                    await self._handle_mqtt_message(message)
                    
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            await self._publish_error(f"MQTT connection failed: {e}")
        finally:
            self._running = False
            if session_task:
                session_task.cancel()
            if telemetry_task:
                telemetry_task.cancel()
            await self._cleanup()
    
    async def _subscribe_to_commands(self):
        """Subscribe to all command topics"""
        command_topics = [
            f"{self.base_topic}/command/connect",
            f"{self.base_topic}/command/disconnect", 
            f"{self.base_topic}/command/grind",
            f"{self.base_topic}/command/brew",
            f"{self.base_topic}/command/pour",
            f"{self.base_topic}/command/scale/tare",
            f"{self.base_topic}/command/scale/vibrate",
            f"{self.base_topic}/command/scale/move",
            f"{self.base_topic}/command/temperature",
            f"{self.base_topic}/command/recipe/execute",
            f"{self.base_topic}/command/recipe/stop",
            f"{self.base_topic}/command/stop_all",
        ]
        
        for topic in command_topics:
            await self.mqtt_client.subscribe(topic)
            logger.debug(f"Subscribed to {topic}")
    
    async def _handle_mqtt_message(self, message: aiomqtt.Message):
        """Handle incoming MQTT messages"""
        try:
            topic = str(message.topic)
            payload_str = message.payload.decode() if message.payload else "{}"
            
            # Parse JSON payload if not empty
            try:
                payload = json.loads(payload_str) if payload_str.strip() else {}
            except json.JSONDecodeError:
                payload = {"raw": payload_str}
                
            logger.info(f"Received MQTT: {topic} -> {payload}")
            
            # Update activity timestamp
            self._last_activity = datetime.now()
            
            # Route to appropriate handler
            await self._route_command(topic, payload)
            
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
            await self._publish_error(f"Command error: {e}")
    
    async def _route_command(self, topic: str, payload: Dict[str, Any]):
        """Route MQTT commands to appropriate handlers"""
        topic_suffix = topic.replace(f"{self.base_topic}/command/", "")
        
        handlers = {
            "connect": self._handle_connect,
            "disconnect": self._handle_disconnect,
            "grind": self._handle_grind,
            "brew": self._handle_brew,
            "pour": self._handle_pour,
            "scale/tare": self._handle_scale_tare,
            "scale/vibrate": self._handle_scale_vibrate,
            "scale/move": self._handle_scale_move,
            "temperature": self._handle_temperature,
            "recipe/execute": self._handle_recipe_execute,
            "recipe/stop": self._handle_recipe_stop,
            "stop_all": self._handle_stop_all,
        }
        
        handler = handlers.get(topic_suffix)
        if handler:
            await handler(payload)
        else:
            logger.warning(f"Unknown command topic: {topic}")
            await self._publish_error(f"Unknown command: {topic_suffix}")
    
    async def _ensure_connected(self) -> bool:
        """Ensure BLE connection is active"""
        async with self._session_lock:
            if self.client and self.client.is_connected:
                return True
                
            logger.info("Establishing BLE connection...")
            
            try:
                self.client = XBloomClient(self.config.device_address)
                
                # Register status callback
                self.client.on_status_update(self._on_device_status_update)
                
                connected = await self.client.connect(timeout=20.0)
                if connected:
                    logger.info("BLE connection established")
                    await self._publish_availability("online")
                    return True
                else:
                    logger.error("Failed to establish BLE connection")
                    await self._publish_error("BLE connection failed")
                    return False
                    
            except Exception as e:
                logger.error(f"BLE connection error: {e}")
                await self._publish_error(f"BLE error: {e}")
                return False
    
    async def _disconnect_ble(self):
        """Disconnect from BLE device"""
        async with self._session_lock:
            if self.client and self.client.is_connected:
                logger.info("Disconnecting from BLE device")
                await self.client.disconnect()
                await self._publish_availability("offline")
    
    # Command Handlers
    async def _handle_connect(self, payload: Dict[str, Any]):
        """Handle manual connection request"""
        await self._ensure_connected()
    
    async def _handle_disconnect(self, payload: Dict[str, Any]):
        """Handle manual disconnection request"""
        await self._disconnect_ble()
    
    async def _handle_grind(self, payload: Dict[str, Any]):
        """Handle grind command"""
        if not await self._ensure_connected():
            return
            
        size = payload.get("size", 50)
        speed = payload.get("speed", 80)
        timeout_ms = payload.get("timeout_ms", 5000)
        
        try:
            success = await self.client.grinder.start(
                size=size,
                speed=speed,
                timeout_ms=timeout_ms
            )
            
            if success:
                await self._publish_status({"grinder": {"active": True, "size": size, "speed": speed}})
            else:
                await self._publish_error("Grinder start failed")
                
        except Exception as e:
            logger.error(f"Grinder error: {e}")
            await self._publish_error(f"Grinder error: {e}")
    
    async def _handle_brew(self, payload: Dict[str, Any]):
        """Handle brew start command"""
        if not await self._ensure_connected():
            return
            
        try:
            success = await self.client.brewer.start()
            if success:
                await self._publish_status({"brewer": {"active": True}})
            else:
                await self._publish_error("Brewer start failed")
                
        except Exception as e:
            await self._publish_error(f"Brewer error: {e}")
    
    async def _handle_pour(self, payload: Dict[str, Any]):
        """Handle manual pour command (immediate brew with temp)"""
        if not await self._ensure_connected():
            return
            
        temp = payload.get("temperature", 93.0)
        pattern = payload.get("pattern", "center")
        
        # Map pattern names to enum values
        pattern_map = {
            "center": PourPattern.CENTER,
            "spiral": PourPattern.SPIRAL, 
            "circular": PourPattern.CIRCULAR,
            "circle": PourPattern.CIRCULAR
        }
        
        try:
            # Set temperature first
            await self.client.brewer.set_temperature(temp)
            
            # Set pattern if supported
            if pattern in pattern_map:
                await self.client.brewer.set_pattern(int(pattern_map[pattern]))
            
            # Start brewing
            await self.client.brewer.start()
            
            await self._publish_status({
                "brewer": {
                    "active": True, 
                    "temperature": temp,
                    "pattern": pattern
                }
            })
            
        except Exception as e:
            await self._publish_error(f"Pour error: {e}")
    
    async def _handle_scale_tare(self, payload: Dict[str, Any]):
        """Handle scale tare (zero) - Note: Not directly available in API"""
        await self._publish_error("Scale tare not implemented in XBloom API")
    
    async def _handle_scale_vibrate(self, payload: Dict[str, Any]):
        """Handle scale vibration"""
        if not await self._ensure_connected():
            return
            
        try:
            success = await self.client.scale.vibrate()
            if success:
                await self._publish_status({"scale": {"vibrating": True}})
                
        except Exception as e:
            await self._publish_error(f"Scale vibrate error: {e}")
    
    async def _handle_scale_move(self, payload: Dict[str, Any]):
        """Handle scale tray movement"""
        if not await self._ensure_connected():
            return
            
        direction = payload.get("direction", "left")  # left, right, stop
        
        try:
            if direction == "left":
                success = await self.client.scale.move_left()
            elif direction == "right":  
                success = await self.client.scale.move_right()
            elif direction == "stop":
                success = await self.client.scale.stop()
            else:
                await self._publish_error(f"Invalid scale direction: {direction}")
                return
                
            if success:
                await self._publish_status({"scale": {"moving": direction}})
                
        except Exception as e:
            await self._publish_error(f"Scale move error: {e}")
    
    async def _handle_temperature(self, payload: Dict[str, Any]):
        """Handle temperature setting"""
        if not await self._ensure_connected():
            return
            
        temp = payload.get("celsius", 93.0)
        
        try:
            success = await self.client.brewer.set_temperature(temp)
            if success:
                await self._publish_status({"brewer": {"target_temperature": temp}})
                
        except Exception as e:
            await self._publish_error(f"Temperature error: {e}")
    
    async def _handle_recipe_execute(self, payload: Dict[str, Any]):
        """Handle recipe execution"""
        if not await self._ensure_connected():
            return
            
        try:
            # Parse recipe from payload
            recipe = parse_recipe_json(payload)
            
            # Send and execute recipe
            await self.client.send_recipe(recipe)
            await asyncio.sleep(1)  # Brief pause
            await self.client.execute_recipe(recipe)
            
            await self._publish_status({
                "recipe": {
                    "active": True,
                    "name": recipe.name,
                    "steps": len(recipe.pours)
                }
            })
            
        except Exception as e:
            await self._publish_error(f"Recipe error: {e}")
    
    async def _handle_recipe_stop(self, payload: Dict[str, Any]):
        """Handle recipe stop"""
        if not await self._ensure_connected():
            return
            
        try:
            success = await self.client.stop_recipe()
            if success:
                await self._publish_status({"recipe": {"active": False}})
                
        except Exception as e:
            await self._publish_error(f"Recipe stop error: {e}")
    
    async def _handle_stop_all(self, payload: Dict[str, Any]):
        """Emergency stop all operations"""
        if not await self._ensure_connected():
            return
            
        try:
            # Stop all components
            await self.client.grinder.stop()
            await self.client.brewer.stop()
            await self.client.scale.stop()
            await self.client.stop_recipe()
            
            await self._publish_status({
                "emergency_stop": True,
                "grinder": {"active": False},
                "brewer": {"active": False},
                "recipe": {"active": False}
            })
            
        except Exception as e:
            await self._publish_error(f"Emergency stop error: {e}")
    
    def _on_device_status_update(self, status):
        """Callback for device status updates"""
        # This will trigger telemetry updates
        pass
    
    async def _session_manager(self):
        """Manage BLE session timeouts"""
        while self._running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if self.client and self.client.is_connected:
                    timeout = timedelta(seconds=self.config.session_timeout)
                    if datetime.now() - self._last_activity > timeout:
                        logger.info("Session timeout reached, disconnecting BLE")
                        await self._disconnect_ble()
                        
            except Exception as e:
                logger.error(f"Session manager error: {e}")
    
    async def _telemetry_publisher(self):
        """Publish device telemetry periodically"""
        while self._running:
            try:
                await asyncio.sleep(self.config.telemetry_interval)
                
                if self.client and self.client.is_connected:
                    await self._publish_telemetry()
                    
            except Exception as e:
                logger.error(f"Telemetry publisher error: {e}")
    
    async def _publish_telemetry(self):
        """Publish current device telemetry"""
        if not self.client:
            return
            
        status = self.client.status
        
        # Create telemetry data
        telemetry = {
            "timestamp": datetime.now().isoformat(),
            "weight": round(status.scale.weight, 2),
            "temperature": round(status.brewer.temperature, 1),
            "grinder_position": status.grinder.position,
            "water_level_ok": status.water_level_ok,
            "state": status.state.value if hasattr(status.state, 'value') else str(status.state),
            "grinder_running": status.grinder.is_running,
            "brewer_running": status.brewer.is_running,
        }
        
        # Only publish if values changed significantly
        if self._telemetry_changed(telemetry):
            await self.mqtt_client.publish(
                f"{self.base_topic}/status/telemetry",
                json.dumps(telemetry)
            )
            self._last_telemetry = telemetry.copy()
    
    def _telemetry_changed(self, new_data: Dict[str, Any]) -> bool:
        """Check if telemetry has changed significantly"""
        if not self._last_telemetry:
            return True
            
        # Check for significant weight change (>0.5g)
        weight_delta = abs(new_data.get("weight", 0) - self._last_telemetry.get("weight", 0))
        if weight_delta > 0.5:
            return True
            
        # Check for temperature change (>0.5°C)
        temp_delta = abs(new_data.get("temperature", 0) - self._last_telemetry.get("temperature", 0))
        if temp_delta > 0.5:
            return True
            
        # Check for state changes
        state_changed = new_data.get("state") != self._last_telemetry.get("state")
        grinder_changed = new_data.get("grinder_running") != self._last_telemetry.get("grinder_running")
        brewer_changed = new_data.get("brewer_running") != self._last_telemetry.get("brewer_running")
        
        return state_changed or grinder_changed or brewer_changed
    
    # Status Publishing Methods
    async def _publish_availability(self, status: str):
        """Publish device availability"""
        await self.mqtt_client.publish(
            f"{self.base_topic}/status/availability", 
            status
        )
    
    async def _publish_bridge_status(self, status: str):
        """Publish bridge status"""
        await self.mqtt_client.publish(
            f"{self.base_topic}/bridge/status",
            status
        )
    
    async def _publish_status(self, status_data: Dict[str, Any]):
        """Publish general status update"""
        status_data["timestamp"] = datetime.now().isoformat()
        await self.mqtt_client.publish(
            f"{self.base_topic}/status/machine",
            json.dumps(status_data)
        )
    
    async def _publish_error(self, error_msg: str):
        """Publish error message"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error": error_msg
        }
        await self.mqtt_client.publish(
            f"{self.base_topic}/status/error",
            json.dumps(error_data)
        )
        logger.error(f"Published error: {error_msg}")
    
    async def _cleanup(self):
        """Cleanup resources"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        
        if self.mqtt_client:
            await self._publish_bridge_status("offline")