"""Vacuum entities for Tuya robots."""

from typing import Any

from tuya_sharing import CustomerDevice

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import RobotVacuumConfigEntry
from .const import (
    COMMAND_LOCATE,
    COMMAND_RETURN,
    COMMAND_START,
    COMMAND_STOP,
    STATUS_ACTIVITY,
)
from .coordinator import RobotData
from .entity import RobotEntity

ATTR_STATUS = "status"
ATTR_BATTERY_LEVEL = "battery_level"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RobotVacuumConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a vacuum entity for each known robot."""
    robot_data = entry.runtime_data
    async_add_entities(
        TuyaRobotVacuum(robot_data, device)
        for device_id in robot_data.robots
        if (device := robot_data.device(device_id)) is not None
    )


class TuyaRobotVacuum(RobotEntity, StateVacuumEntity, RestoreEntity):
    """A robot vacuum whose activity comes from its raw status.

    Robots only report changes, so after a restart the last known activity
    is kept until the robot does something.
    """

    _attr_name = None
    _attr_supported_features = (
        VacuumEntityFeature.STATE
        | VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.LOCATE
    )

    def __init__(self, robot_data: RobotData, device: CustomerDevice) -> None:
        """Init the vacuum."""
        super().__init__(robot_data, device, "vacuum")
        self._restored_activity: VacuumActivity | None = None
        self._restored_attributes: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Restore the last known activity."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if last_state.state in VacuumActivity:
            self._restored_activity = VacuumActivity(last_state.state)
        self._restored_attributes = {
            key: last_state.attributes[key]
            for key in (ATTR_STATUS, ATTR_BATTERY_LEVEL)
            if key in last_state.attributes
        }

    @property
    def activity(self) -> VacuumActivity | None:
        """Return what the robot is doing."""
        if (status := self._reported(self._points.status)) is None:
            return self._restored_activity
        return STATUS_ACTIVITY.get(status)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the raw status, and the battery for cards to show."""
        attributes = dict(self._restored_attributes)
        if (status := self._reported(self._points.status)) is not None:
            attributes[ATTR_STATUS] = status
        if (battery := self._reported(self._points.battery)) is not None:
            attributes[ATTR_BATTERY_LEVEL] = battery
        return attributes

    async def async_start(self) -> None:
        """Start or resume cleaning."""
        await self._robot_data.async_send_command(self._device_id, COMMAND_START)

    async def async_pause(self) -> None:
        """Pause cleaning."""
        await self._robot_data.async_send_command(self._device_id, COMMAND_STOP)

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop cleaning."""
        await self._robot_data.async_send_command(self._device_id, COMMAND_STOP)

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Send the robot to its dock."""
        await self._robot_data.async_send_command(self._device_id, COMMAND_RETURN)

    async def async_locate(self, **kwargs: Any) -> None:
        """Make the robot announce where it is."""
        await self._robot_data.async_send_command(self._device_id, COMMAND_LOCATE)
