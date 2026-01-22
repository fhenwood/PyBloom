"""Button entities for XBloom MQTT."""
import json
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, MQTT_COMMAND_TOPIC, DEFAULT_VOLUME, DEFAULT_TEMPERATURE, DEFAULT_GRIND_SIZE, DEFAULT_RPM

_LOGGER = logging.getLogger(__name__)


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return device info for XBloom."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="XBloom Coffee Machine",
        manufacturer="XBloom",
        model="Studio",
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up XBloom buttons."""
    async_add_entities([
        XBloomConnectButton(hass, entry),
        XBloomPourButton(hass, entry),
        XBloomGrindButton(hass, entry),
        XBloomExecuteRecipeButton(hass, entry),
        XBloomCancelButton(hass, entry),
    ])


class XBloomConnectButton(ButtonEntity):
    """Button to connect/disconnect XBloom."""
    
    _attr_name = "Connect"
    _attr_unique_id = "xbloom_connect"
    _attr_icon = "mdi:bluetooth-connect"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    async def async_press(self):
        """Handle button press - toggle connection."""
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        if entry_data.get("connected", False):
            await mqtt.async_publish(self.hass, f"{MQTT_COMMAND_TOPIC}/disconnect", "{}")
        else:
            await mqtt.async_publish(self.hass, f"{MQTT_COMMAND_TOPIC}/connect", "{}")


class XBloomPourButton(ButtonEntity):
    """Button to pour water."""
    
    _attr_name = "Pour"
    _attr_unique_id = "xbloom_pour"
    _attr_icon = "mdi:water"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    async def async_press(self):
        """Pour water using current settings."""
        volume = self.hass.states.get("number.xbloom_coffee_machine_volume")
        temp = self.hass.states.get("number.xbloom_coffee_machine_temperature")
        
        payload = {
            "volume": int(float(volume.state)) if volume and volume.state not in ("unknown", "unavailable") else DEFAULT_VOLUME,
            "temperature": int(float(temp.state)) if temp and temp.state not in ("unknown", "unavailable") else DEFAULT_TEMPERATURE,
        }
        
        _LOGGER.info(f"Pouring: {payload}")
        await mqtt.async_publish(self.hass, f"{MQTT_COMMAND_TOPIC}/pour", json.dumps(payload))


class XBloomGrindButton(ButtonEntity):
    """Button to grind coffee."""
    
    _attr_name = "Grind"
    _attr_unique_id = "xbloom_grind"
    _attr_icon = "mdi:coffee"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    async def async_press(self):
        """Grind using current settings."""
        grind_size = self.hass.states.get("number.xbloom_coffee_machine_grind_size")
        rpm = self.hass.states.get("number.xbloom_coffee_machine_rpm")
        
        payload = {
            "grind_size": int(float(grind_size.state)) if grind_size and grind_size.state not in ("unknown", "unavailable") else DEFAULT_GRIND_SIZE,
            "rpm": int(float(rpm.state)) if rpm and rpm.state not in ("unknown", "unavailable") else DEFAULT_RPM,
        }
        
        _LOGGER.info(f"Grinding: {payload}")
        await mqtt.async_publish(self.hass, f"{MQTT_COMMAND_TOPIC}/grind", json.dumps(payload))


class XBloomExecuteRecipeButton(ButtonEntity):
    """Button to execute selected recipe."""
    
    _attr_name = "Execute Recipe"
    _attr_unique_id = "xbloom_execute_recipe"
    _attr_icon = "mdi:play"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    async def async_press(self):
        """Execute the currently selected recipe."""
        recipe_select = self.hass.states.get("select.xbloom_coffee_machine_recipe")
        if not recipe_select or recipe_select.state in ("unknown", "unavailable"):
            _LOGGER.warning("No recipe selected")
            return
        
        recipe_name = recipe_select.state
        recipes = self.hass.data[DOMAIN].get("yaml_recipes", {})
        
        if recipe_name not in recipes:
            _LOGGER.error(f"Recipe '{recipe_name}' not found")
            return
        
        recipe = recipes[recipe_name]
        _LOGGER.info(f"Executing recipe: {recipe_name}")
        await mqtt.async_publish(self.hass, f"{MQTT_COMMAND_TOPIC}/recipe/execute", json.dumps(recipe))


class XBloomCancelButton(ButtonEntity):
    """Button to cancel/stop all operations."""
    
    _attr_name = "Cancel"
    _attr_unique_id = "xbloom_cancel"
    _attr_icon = "mdi:stop"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    async def async_press(self):
        """Stop all operations."""
        _LOGGER.info("Cancelling all operations")
        await mqtt.async_publish(self.hass, f"{MQTT_COMMAND_TOPIC}/stop_all", "{}")
