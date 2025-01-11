import logging

from .generic import (
    set_temperature as generic_set_temperature,
    set_hvac_mode as generic_set_hvac_mode,
)

_LOGGER = logging.getLogger(__name__)

# see "Application Work Group Z-Wave Specifications, Release 2024A",
# chapter "2.2.25 Climate Control Schedule Command Class, version 1"
CLIMATE_CONTROL_SCHEDULE_CC_ID = 70

MAX_SETBACK = 12.0
MIN_SETBACK = -12.8


async def get_info(self, entity_id):
    """Get info from TRV."""
    support_offset = False
    support_valve = False
    # enable offset calibration for supported model
    for trv in self.trv_bundle:
        if trv["model"] == "MT02650":
            support_offset = True
            break
    return {"support_offset": support_offset, "support_valve": support_valve}


async def init(self, entity_id):
    return None


async def set_temperature(self, entity_id, temperature):
    """Set new target temperature."""
    return await generic_set_temperature(self, entity_id, temperature)


async def set_hvac_mode(self, entity_id, hvac_mode):
    """Set new target hvac mode."""
    return await generic_set_hvac_mode(self, entity_id, hvac_mode)


async def get_current_offset(self, entity_id):
    """Get current offset."""
    # TBD - need to find other way to get offset, as zwave_js.invoke_cc_api cannot return response
    # override = await self.hass.services.async_call(
    #         "zwave_js",
    #         "invoke_cc_api",
    #         {"entity_id": entity_id, "command_class": CLIMATE_CONTROL_SCHEDULE_CC_ID, "method_name": "getOverride", "parameters": []},
    #         blocking=True,
    #         return_response=True,
    #     )
    
    # _LOGGER.debug(
    #     "better_thermostat get_current_offset: override is %s for trv %s",
    #     override,
    #     entity_id,
    # )
    return 0


async def get_offset_step(self, entity_id):
    """Get offset step."""
    return float(0.1)


async def get_min_offset(self, entity_id):
    """Get min offset."""
    return -MAX_SETBACK


async def get_max_offset(self, entity_id):
    """Get max offset."""
    return -MIN_SETBACK


async def set_offset(self, entity_id, offset):
    """Set new schedule state."""
    setback = -offset
    if setback >= MAX_SETBACK:
        setback = MAX_SETBACK
    if setback <= MIN_SETBACK:
        setback = MIN_SETBACK

    if setback == 0:
        await self.hass.services.async_call(
            "zwave_js",
            "invoke_cc_api",
            {"entity_id": entity_id, "command_class": CLIMATE_CONTROL_SCHEDULE_CC_ID, "method_name": "setOverride", "parameters": [0, 0]},
            blocking=True,
            context=self.context,
        )
    else:
        await self.hass.services.async_call(
            "zwave_js",
            "invoke_cc_api",
            {"entity_id": entity_id, "command_class": CLIMATE_CONTROL_SCHEDULE_CC_ID, "method_name": "setOverride", "parameters": [2, setback]},
            blocking=True,
            context=self.context,
        )
    self.real_trvs[entity_id]["last_calibration"] = offset


async def set_valve(self, entity_id, valve):
    """Set new target valve."""
    return None
