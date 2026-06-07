MIN_OFFSET = -0.5
MAX_OFFSET = 0.8


def fix_local_calibration(self, entity_id, offset):
    ## limit offset
    if offset < MIN_OFFSET:
        offset = MIN_OFFSET
    elif offset > MAX_OFFSET:
        offset = MAX_OFFSET
    return offset


def fix_target_temperature_calibration(self, entity_id, temperature):
    return temperature


async def override_set_hvac_mode(self, entity_id, hvac_mode):
    return False


async def override_set_temperature(self, entity_id, temperature):
    return False
