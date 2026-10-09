"""Constants for the Tuya Robot Vacuum integration."""

from dataclasses import dataclass
import logging

from homeassistant.components.vacuum import VacuumActivity

DOMAIN = "tuya_robot_vacuum"
LOGGER = logging.getLogger(__package__)

TUYA_DOMAIN = "tuya"

# Tuya protocol number of a device reporting its data points
PROTOCOL_DEVICE_REPORT = 4


@dataclass(frozen=True)
class DataPoints:
    """Numbers of the data points a robot reports, which Tuya gives no name."""

    status: int
    battery: int
    clean_time: int
    clean_area: int


# Robots by Tuya product ID. Add a product here once its numbers are known.
PRODUCTS = {
    # "Lds Robot", sold in Brazil as the KaBuM! Smart 900
    "7vx4ulan46paequq": DataPoints(
        status=105, battery=106, clean_time=107, clean_area=108
    ),
}

# Values of the status data point, spelled as the robots send them
STATUS_ACTIVITY = {
    "totaling": VacuumActivity.CLEANING,
    "pointing": VacuumActivity.CLEANING,
    "areaing": VacuumActivity.CLEANING,
    "tocharge": VacuumActivity.RETURNING,
    "chargring": VacuumActivity.DOCKED,
    "fullcharge": VacuumActivity.DOCKED,
    "pause": VacuumActivity.PAUSED,
    "idle": VacuumActivity.IDLE,
    "standby": VacuumActivity.IDLE,
    "sleep": VacuumActivity.IDLE,
    "fault": VacuumActivity.ERROR,
}

# Commands the Tuya cloud does have a name for
COMMAND_START = {"code": "power_go", "value": True}
COMMAND_STOP = {"code": "power_go", "value": False}
COMMAND_RETURN = {"code": "mode", "value": "chargego"}
COMMAND_LOCATE = {"code": "seek", "value": True}
