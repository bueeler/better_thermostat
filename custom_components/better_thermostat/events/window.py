import asyncio
import logging

from custom_components.better_thermostat import DOMAIN
from homeassistant.core import callback
from homeassistant.const import STATE_OFF
from homeassistant.helpers import issue_registry as ir

_LOGGER = logging.getLogger(__name__)


@callback
async def trigger_window_change(self, event) -> None:
    """Triggered by window sensor event from HA to check if the window is open.

    Parameters
    ----------
    self :
            self instance of better_thermostat
    event :
            Event object from the eventbus. Contains the new and old state from the window (group).

    Returns
    -------
    None
    """

    new_state = event.data.get("new_state")

    if None in (self.hass.states.get(self.window_id), self.window_id, new_state):
        return

    new_state = new_state.state

    old_window_open = self.window_open

    if new_state in ("on", "unknown", "unavailable"):
        new_window_open = True
        if new_state == "unknown":
            _LOGGER.warning(
                "better_thermostat %s: Window sensor state is unknown, assuming window is open",
                self.device_name,
            )

        # window was opened, disable heating power calculation for this period
        self.heating_start_temp = None
        self.async_write_ha_state()
    elif new_state == "off":
        new_window_open = False
    else:
        _LOGGER.error(
            f"better_thermostat {self.device_name}: New window sensor state '{new_state}' not recognized"
        )
        ir.async_create_issue(
            hass=self.hass,
            domain=DOMAIN,
            issue_id=f"missing_entity_{self.device_name}",
            issue_title=f"better_thermostat {self.device_name} has invalid window sensor state",
            issue_severity="error",
            issue_description=f"better_thermostat {self.device_name} has invalid window sensor state: {new_state}",
            issue_category="config",
            issue_suggested_action="Please check the window sensor",
        )
        return

    # make sure to skip events which do not change the saved window state:
    if new_window_open == old_window_open:
        _LOGGER.debug(
            f"better_thermostat {self.device_name}: Window state did not change, skipping event"
        )
        return
    await self.window_queue_task.put(new_window_open)


async def window_queue(self):
    try:
        while True:
            window_event_to_process = await self.window_queue_task.get()
            try:
                if window_event_to_process is not None:
                    if window_event_to_process:
                        _LOGGER.debug(
                            f"better_thermostat {self.device_name}: Window opened, waiting {self.window_delay} seconds before continuing"
                        )
                        await asyncio.sleep(self.window_delay)
                    else:
                        _LOGGER.debug(
                            f"better_thermostat {self.device_name}: Window closed, waiting {self.window_delay_after} seconds before continuing"
                        )
                        await asyncio.sleep(self.window_delay_after)
                    # remap off on to true false
                    current_window_state = True
                    if self.hass.states.get(self.window_id).state == STATE_OFF:
                        current_window_state = False
                    # make sure the current state is the suggested change state to prevent a false positive:
                    if current_window_state == window_event_to_process:
                        self.window_open = window_event_to_process
                        self.async_write_ha_state()
                        if not self.control_queue_task.empty():
                            empty_queue(self.control_queue_task)
                        await self.control_queue_task.put(self)
            except asyncio.CancelledError:
                raise
            finally:
                self.window_queue_task.task_done()
    except asyncio.CancelledError:
        _LOGGER.debug(
            f"better_thermostat {self.device_name}: Window queue task cancelled"
        )
        raise


def empty_queue(q: asyncio.Queue):
    for _ in range(q.qsize()):
        q.get_nowait()
        q.task_done()
