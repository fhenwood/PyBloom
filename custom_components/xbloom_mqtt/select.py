"""Select entity for XBloom recipe dropdown."""
import logging
from homeassistant.components.select import SelectEntity
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
    """Set up XBloom select entities."""
    async_add_entities([XBloomRecipeSelect(hass, entry)])


class XBloomRecipeSelect(SelectEntity):
    """Select entity for choosing a recipe."""
    
    _attr_name = "Recipe"
    _attr_unique_id = "xbloom_recipe"
    _attr_icon = "mdi:coffee-maker"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self._entry = entry
        self._attr_current_option = None
        self._attr_device_info = get_device_info(entry)

    @property
    def options(self) -> list[str]:
        """Return list of available recipes."""
        recipes = self.hass.data[DOMAIN].get("yaml_recipes", {})
        return list(recipes.keys()) if recipes else ["No recipes configured"]

    async def async_select_option(self, option: str):
        """Select a recipe."""
        self._attr_current_option = option
        self.async_write_ha_state()
        _LOGGER.info(f"Selected recipe: {option}")
