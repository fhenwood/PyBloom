"""XBloom MQTT Integration - Simple Home Assistant component."""
import logging
import json
import os
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.components import mqtt

from .const import DOMAIN, MQTT_BASE_TOPIC, MQTT_STATUS_TOPIC, CONF_RECIPES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BUTTON, Platform.NUMBER, Platform.SELECT, Platform.SENSOR]

# Frontend card URL
CARD_URL = "/xbloom_mqtt/xbloom-studio-card.js"
CARD_NAME = "xbloom-studio-card"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the XBloom MQTT component from YAML."""
    hass.data.setdefault(DOMAIN, {})
    
    # Load recipes from configuration.yaml
    if DOMAIN in config and CONF_RECIPES in config[DOMAIN]:
        recipes = config[DOMAIN][CONF_RECIPES]
        hass.data[DOMAIN]["yaml_recipes"] = {r["name"]: r for r in recipes}
        _LOGGER.info(f"Loaded {len(recipes)} recipes from YAML")
    else:
        hass.data[DOMAIN]["yaml_recipes"] = {}
    
    return True


async def _register_frontend(hass: HomeAssistant):
    """Register the XBloom Studio custom card with the frontend."""
    try:
        from homeassistant.components.http import StaticPathConfig
        
        card_path = os.path.join(os.path.dirname(__file__), "www", "xbloom-studio-card.js")
        
        if os.path.exists(card_path) and hass.http:
            # Register static path for the card JS file
            await hass.http.async_register_static_paths([
                StaticPathConfig(CARD_URL, card_path, cache_headers=False)
            ])
            _LOGGER.info("XBloom Studio card registered at %s", CARD_URL)
        else:
            _LOGGER.debug("XBloom Studio card not registered - file or http not available")
    except Exception as e:
        _LOGGER.warning("Could not register XBloom Studio card: %s", e)



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XBloom MQTT from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "connected": False,
        "error": None,
        "weight": 0.0,
        "temperature": 0.0,
        "status": "disconnected",
        "bridge_status": "offline",
    }
    
    # Subscribe to status updates from device
    async def status_callback(msg):
        """Handle status messages from bridge."""
        try:
            topic = msg.topic
            payload = msg.payload.decode() if isinstance(msg.payload, bytes) else str(msg.payload)
            entry_data = hass.data[DOMAIN][entry.entry_id]
            
            # Handle telemetry
            if topic.endswith("/status/telemetry"):
                data = json.loads(payload)
                if "weight" in data:
                    entry_data["weight"] = data["weight"]
                if "temperature" in data:
                    entry_data["temperature"] = data["temperature"]
                # Assume connected if receiving telemetry
                entry_data["connected"] = True
                entry_data["status"] = "connected"

            # Handle availability (online/offline string)
            elif topic.endswith("/status/availability"):
                entry_data["connected"] = (payload == "online")
                entry_data["status"] = "connected" if entry_data["connected"] else "disconnected"

            # Handle machine events
            elif topic.endswith("/status/machine"):
                # Can process other events here if needed
                pass

            # Handle errors
            elif topic.endswith("/status/error"):
                data = json.loads(payload)
                if "error" in data:
                    entry_data["error"] = data["error"]
                
        except Exception as e:
            _LOGGER.error(f"Error parsing status topic {msg.topic}: {e}")
    
    # Subscribe to bridge status (online/offline)
    async def bridge_status_callback(msg):
        """Handle bridge status messages."""
        try:
            entry_data = hass.data[DOMAIN][entry.entry_id]
            status = msg.payload.decode() if isinstance(msg.payload, bytes) else str(msg.payload)
            entry_data["bridge_status"] = status
            _LOGGER.info(f"Bridge status: {status}")
        except Exception as e:
            _LOGGER.error(f"Error parsing bridge status: {e}")
    
    await mqtt.async_subscribe(hass, f"{MQTT_STATUS_TOPIC}/#", status_callback)
    await mqtt.async_subscribe(hass, f"{MQTT_BASE_TOPIC}/bridge/status", bridge_status_callback)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
