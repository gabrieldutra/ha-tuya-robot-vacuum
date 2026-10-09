"""Base entity for a robot vacuum."""

from typing import Any

from tuya_sharing import CustomerDevice

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, DataPoints
from .coordinator import RobotData, signal_update


class RobotEntity(Entity):
    """An entity fed by the data points of one robot."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, robot_data: RobotData, device: CustomerDevice, key: str) -> None:
        """Init the entity from the Tuya device."""
        self._robot_data = robot_data
        self._device_id = device.id
        self._points: DataPoints = robot_data.robots[device.id]
        self._attr_unique_id = f"{device.id}_{key}"
        # A device of our own: one integration cannot add entities to a device
        # that another integration registered
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            manufacturer="Tuya",
            model=device.product_name,
            name=device.name,
        )

    def _reported(self, data_point: int) -> Any:
        """Return the last value the robot reported for a data point."""
        return self._robot_data.data[self._device_id].get(data_point)

    @property
    def available(self) -> bool:
        """Return if the robot is online."""
        device = self._robot_data.device(self._device_id)
        return device is not None and device.online

    async def async_added_to_hass(self) -> None:
        """Follow what the robot reports."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self._device_id), self.async_write_ha_state
            )
        )
