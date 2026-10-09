"""Battery and progress sensors for Tuya robots."""

from collections.abc import Callable
from dataclasses import dataclass

from tuya_sharing import CustomerDevice

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfArea, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RobotVacuumConfigEntry
from .const import DataPoints
from .coordinator import RobotData
from .entity import RobotEntity


@dataclass(frozen=True, kw_only=True)
class RobotSensorDescription(SensorEntityDescription):
    """A sensor and the data point it reads."""

    data_point: Callable[[DataPoints], int]


SENSORS = (
    RobotSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_point=lambda points: points.battery,
    ),
    RobotSensorDescription(
        key="clean_time",
        translation_key="clean_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        data_point=lambda points: points.clean_time,
    ),
    RobotSensorDescription(
        key="clean_area",
        translation_key="clean_area",
        device_class=SensorDeviceClass.AREA,
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        suggested_display_precision=0,
        data_point=lambda points: points.clean_area,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RobotVacuumConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors of each known robot."""
    robot_data = entry.runtime_data
    async_add_entities(
        TuyaRobotSensor(robot_data, device, description)
        for device_id in robot_data.robots
        if (device := robot_data.device(device_id)) is not None
        for description in SENSORS
    )


class TuyaRobotSensor(RobotEntity, RestoreSensor):
    """A number a robot reports; kept across restarts until it reports again."""

    entity_description: RobotSensorDescription

    def __init__(
        self,
        robot_data: RobotData,
        device: CustomerDevice,
        description: RobotSensorDescription,
    ) -> None:
        """Init the sensor."""
        super().__init__(robot_data, device, description.key)
        self.entity_description = description
        self._restored_value: float | None = None

    async def async_added_to_hass(self) -> None:
        """Restore the last reported value."""
        await super().async_added_to_hass()
        if (last_data := await self.async_get_last_sensor_data()) is not None:
            self._restored_value = last_data.native_value

    @property
    def native_value(self) -> float | None:
        """Return the last value the robot reported."""
        value = self._reported(self.entity_description.data_point(self._points))
        return self._restored_value if value is None else value
