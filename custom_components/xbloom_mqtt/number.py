"""Number entities for XBloom MQTT."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, DEFAULT_VOLUME, DEFAULT_TEMPERATURE, DEFAULT_GRIND_SIZE, DEFAULT_RPM


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return device info for XBloom."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="XBloom Coffee Machine",
        manufacturer="XBloom",
        model="Studio",
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up XBloom number entities."""
    async_add_entities([
        XBloomVolumeNumber(hass, entry),
        XBloomTemperatureNumber(hass, entry),
        XBloomGrindSizeNumber(hass, entry),
        XBloomRPMNumber(hass, entry),
    ])


class XBloomVolumeNumber(NumberEntity):
    """Number entity for pour volume."""
    
    _attr_name = "Volume"
    _attr_unique_id = "xbloom_volume"
    _attr_icon = "mdi:cup-water"
    _attr_native_min_value = 10
    _attr_native_max_value = 500
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "ml"
    _attr_mode = NumberMode.SLIDER
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_native_value = DEFAULT_VOLUME
        self._attr_device_info = get_device_info(entry)

    async def async_set_native_value(self, value: float):
        """Set the volume."""
        self._attr_native_value = value
        self.async_write_ha_state()


class XBloomTemperatureNumber(NumberEntity):
    """Number entity for water temperature."""
    
    _attr_name = "Temperature"
    _attr_unique_id = "xbloom_temperature"
    _attr_icon = "mdi:thermometer"
    _attr_native_min_value = 40
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "°C"
    _attr_mode = NumberMode.SLIDER
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_native_value = DEFAULT_TEMPERATURE
        self._attr_device_info = get_device_info(entry)

    async def async_set_native_value(self, value: float):
        """Set the temperature."""
        self._attr_native_value = value
        self.async_write_ha_state()


class XBloomGrindSizeNumber(NumberEntity):
    """Number entity for grind size."""
    
    _attr_name = "Grind Size"
    _attr_unique_id = "xbloom_grind_size"
    _attr_icon = "mdi:grain"
    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_native_value = DEFAULT_GRIND_SIZE
        self._attr_device_info = get_device_info(entry)

    async def async_set_native_value(self, value: float):
        """Set the grind size."""
        self._attr_native_value = value
        self.async_write_ha_state()


class XBloomRPMNumber(NumberEntity):
    """Number entity for grinder RPM."""
    
    _attr_name = "RPM"
    _attr_unique_id = "xbloom_rpm"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 60
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_native_value = DEFAULT_RPM
        self._attr_device_info = get_device_info(entry)

    async def async_set_native_value(self, value: float):
        """Set the RPM."""
        self._attr_native_value = value
        self.async_write_ha_state()
