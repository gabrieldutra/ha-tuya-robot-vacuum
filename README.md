# Tuya Robot Vacuum

Status, battery and cleaning progress in Home Assistant for Tuya / Smart Life
robot vacuums that the official integration shows as "Unknown", without a
Tuya developer account.

Some robots report their state as numbered data points that the Tuya cloud
has no name for. The library behind the official
[Tuya integration](https://www.home-assistant.io/integrations/tuya) receives
them and drops them, so the vacuum entity has no state and no battery. This
integration listens to the same messages on the same connection and keeps
those data points.

## What you get

For each supported robot:

- A `vacuum` entity with a real activity (cleaning, returning, docked,
  paused, idle, error) and start, pause, stop, return to base and locate.
- Sensors for battery, the current run's cleaning time and cleaned area.
- The robot's raw status word and battery level as attributes of the vacuum
  entity.

## Supported robots

| Product | Tuya product ID |
|---|---|
| Lds Robot | `7vx4ulan46paequq` |

Robots are matched by product ID, because the data point numbers differ
between products. See [Adding a robot](#adding-a-robot).

## Requirements

- Home Assistant 2026.8 or newer. It is only tested on 2026.8.
- The official Tuya integration, set up and working, with the robot on it.

## Installation

### HACS

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/gabrieldutra/ha-tuya-robot-vacuum` with type
   **Integration**.
3. Install **Tuya Robot Vacuum** and restart Home Assistant.

### Manual

Copy `custom_components/tuya_robot_vacuum` into the `custom_components`
folder of your Home Assistant configuration and restart.

### Setup

Go to **Settings > Devices & services > Add integration** and add **Tuya
Robot Vacuum**. There is nothing to configure.

The official integration keeps its own vacuum entity for the robot, the one
that reads "Unknown". Disable it, or rename it first if you want the new
entity to take over its entity ID.

## Limitations

- **State starts empty.** A robot only reports changes, and an idle robot on
  its dock reports nothing. Entities read "Unknown" until the robot first
  does something; after that the last known state is kept across restarts.
- **Not every status is known.** Cleaning, idle, returning and charging have
  been seen on a real robot. Paused, fully charged, sleeping and fault are
  mapped by guess. An unmapped status shows as "Unknown", with the robot's
  own word in the `status` attribute; please open an issue with it.
- **Pause and stop are the same command.**
- **It needs the cloud**, like the rest of the official integration.
- **It relies on internals.** It reads the official integration's connection
  object and the `tuya-device-sharing-sdk` library. A Home Assistant update
  can break it until it is patched.
- **Each robot shows as two devices,** the official one and the one holding
  these entities. An integration cannot add entities to another integration's
  device.

## Adding a robot

1. Turn on debug logging for the Tuya integration (**Settings > Devices &
   services > Tuya > Enable debug logging**).
2. Start the robot, let it run a minute, send it back to its dock.
3. In the log, look at the `payload->` lines for the robot's device ID. Each
   carries items such as `{"dpId":106,"value":98}`. Work out which number is
   the status word, the battery, the run's time in seconds and its area.
4. Add the product ID and those four numbers to `PRODUCTS` in
   [`const.py`](custom_components/tuya_robot_vacuum/const.py), and any new
   status words to `STATUS_ACTIVITY`.

Pull requests with new products are welcome.

## Disclaimer

This project is not affiliated with Tuya or Home Assistant.
