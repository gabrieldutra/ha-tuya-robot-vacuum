"""Status, battery and progress for robot vacuums on Tuya.

The Tuya integration shows these robots as "unknown": they report their
state as numbered data points the cloud has no name for. This integration
reuses its connection and reads those data points.
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import TUYA_DOMAIN
from .coordinator import RobotData

PLATFORMS = [Platform.SENSOR, Platform.VACUUM]

type RobotVacuumConfigEntry = ConfigEntry[RobotData]


async def async_setup_entry(hass: HomeAssistant, entry: RobotVacuumConfigEntry) -> bool:
    """Start listening to the robots once the Tuya integration is connected."""
    if not (tuya_entries := hass.config_entries.async_loaded_entries(TUYA_DOMAIN)):
        raise ConfigEntryNotReady("The Tuya integration is not loaded")

    entry.runtime_data = RobotData(hass, tuya_entries[0].entry_id)
    entry.runtime_data.async_start()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RobotVacuumConfigEntry) -> bool:
    """Stop listening and unload the entities."""
    entry.runtime_data.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
