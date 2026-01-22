"""Sensor entities for XBloom MQTT."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

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
    """Set up XBloom sensor entities."""
    async_add_entities([
        XBloomBridgeSensor(hass, entry),
        XBloomStatusSensor(hass, entry),
        XBloomWeightSensor(hass, entry),
        XBloomErrorSensor(hass, entry),
    ])


class XBloomBridgeSensor(SensorEntity):
    """Sensor showing MQTT bridge connection status."""
    
    _attr_name = "Bridge"
    _attr_unique_id = "xbloom_bridge"
    _attr_icon = "mdi:server-network"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self):
        """Return bridge status."""
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        return entry_data.get("bridge_status", "offline")

    @property
    def icon(self):
        """Return icon based on bridge status."""
        if self.native_value == "online":
            return "mdi:server-network"
        return "mdi:server-network-off"


class XBloomStatusSensor(SensorEntity):
    """Sensor showing connection status."""
    
    _attr_name = "Status"
    _attr_unique_id = "xbloom_status"
    _attr_icon = "mdi:connection"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self):
        """Return current status."""
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        return entry_data.get("status", "disconnected")

    @property
    def icon(self):
        """Return icon based on status."""
        if self.native_value == "connected":
            return "mdi:bluetooth-connect"
        return "mdi:bluetooth-off"


class XBloomWeightSensor(SensorEntity):
    """Sensor showing current scale weight."""
    
    _attr_name = "Weight"
    _attr_unique_id = "xbloom_weight"
    _attr_icon = "mdi:scale"
    _attr_native_unit_of_measurement = "g"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self):
        """Return current weight."""
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        return entry_data.get("weight", 0.0)


class XBloomErrorSensor(SensorEntity):
    """Sensor showing last error."""
    
    _attr_name = "Error"
    _attr_unique_id = "xbloom_error"
    _attr_icon = "mdi:alert-circle"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_device_info = get_device_info(entry)

    @property
    def native_value(self):
        """Return last error or None."""
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        return entry_data.get("error") or "No errors"

    @property
    def icon(self):
        """Return icon based on error state."""
        if self.native_value == "No errors":
            return "mdi:check-circle"
        return "mdi:alert-circle"
