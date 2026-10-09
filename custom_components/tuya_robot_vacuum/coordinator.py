"""Collects the data points the Tuya integration throws away."""

from datetime import timedelta
from typing import Any

from tuya_sharing import CustomerDevice, Manager

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, LOGGER, PRODUCTS, PROTOCOL_DEVICE_REPORT, DataPoints

# The Tuya integration replaces its connection now and then, without notice
ATTACH_INTERVAL = timedelta(minutes=1)


def signal_update(device_id: str) -> str:
    """Return the dispatcher signal sent when a robot reports something."""
    return f"{DOMAIN}_update_{device_id}"


class RobotData:
    """Latest data points of each robot, by Tuya device ID.

    Robots push their status, battery and progress as numbered data points.
    The Tuya library only keeps the ones the cloud has a name for, so listen
    to the raw messages next to it.
    """

    def __init__(self, hass: HomeAssistant, tuya_entry_id: str) -> None:
        """Init for the robots the Tuya integration knows."""
        self.hass = hass
        self._tuya_entry_id = tuya_entry_id
        self._attached_mq: Any = None
        self._unsub_interval: CALLBACK_TYPE | None = None
        self.robots: dict[str, DataPoints] = {}
        self.data: dict[str, dict[int, Any]] = {}
        if manager := self.manager:
            for device in manager.device_map.values():
                if points := PRODUCTS.get(device.product_id):
                    self.robots[device.id] = points
                    self.data[device.id] = {}

    @property
    def manager(self) -> Manager | None:
        """Return the Tuya connection, which is replaced when Tuya reloads."""
        tuya_entry = self.hass.config_entries.async_get_entry(self._tuya_entry_id)
        if tuya_entry is None or tuya_entry.state is not ConfigEntryState.LOADED:
            return None
        return tuya_entry.runtime_data.manager

    def device(self, device_id: str) -> CustomerDevice | None:
        """Return the Tuya device of a robot."""
        if (manager := self.manager) is None:
            return None
        return manager.device_map.get(device_id)

    @callback
    def async_start(self) -> None:
        """Start listening, and keep doing so across reconnections."""
        self._async_attach()
        self._unsub_interval = async_track_time_interval(
            self.hass, self._async_attach, ATTACH_INTERVAL
        )

    @callback
    def async_stop(self) -> None:
        """Stop listening."""
        if self._unsub_interval:
            self._unsub_interval()
        if self._attached_mq is not None:
            self._attached_mq.remove_message_listener(self._on_message)
            self._attached_mq = None

    @callback
    def _async_attach(self, *_: Any) -> None:
        """Listen on the current connection, if not already."""
        if (manager := self.manager) is None or manager.mq is None:
            return
        if manager.mq is not self._attached_mq:
            manager.mq.add_message_listener(self._on_message)
            self._attached_mq = manager.mq

    def _on_message(self, message: dict[str, Any]) -> None:
        """Handle a raw message; called from the connection's thread."""
        if message.get("protocol") != PROTOCOL_DEVICE_REPORT:
            return
        data = message.get("data") or {}
        if (points := self.robots.get(data.get("devId"))) is None:
            return
        wanted = {points.status, points.battery, points.clean_time, points.clean_area}
        updates = {
            item["dpId"]: item.get("value")
            for item in data.get("status") or []
            if item.get("dpId") in wanted
        }
        if updates:
            self.hass.loop.call_soon_threadsafe(
                self._async_update, data["devId"], updates
            )

    @callback
    def _async_update(self, device_id: str, updates: dict[int, Any]) -> None:
        """Store what a robot reported and tell its entities."""
        LOGGER.debug("Robot %s reported %s", device_id, updates)
        self.data[device_id].update(updates)
        async_dispatcher_send(self.hass, signal_update(device_id))

    async def async_send_command(self, device_id: str, command: dict[str, Any]) -> None:
        """Send a command to a robot through the Tuya cloud."""
        if (manager := self.manager) is None:
            raise HomeAssistantError("The Tuya integration is not loaded")
        try:
            await self.hass.async_add_executor_job(
                manager.send_commands, device_id, [command]
            )
        except Exception as err:
            # The Tuya library raises a bare Exception when the cloud refuses
            raise HomeAssistantError(f"Tuya rejected {command}: {err}") from err
