"""
Support for Mercedes cars with Mercedes ME.

For more details about this component, please refer to the documentation at
https://github.com/ReneNulschDE/mbapipy/
"""
import logging

from custom_components.mercedesmeapi import DOMAIN, MercedesMeEntity
from .const import SENSORS

DEPENDENCIES = ['mercedesmeapi']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Setup the sensor platform."""
    if discovery_info is None:
        return

    data = hass.data[DOMAIN].data

    if not data.cars:
        _LOGGER.info("No Cars found.")
        return

    devices = []
    for car in data.cars:
        for key, value in sorted(SENSORS.items()):
            if value[5] is None or getattr(car.features, value[5]) is True:
                device = MercedesMESensor(data,
                                          key,
                                          value[0],
                                          car.finorvin,
                                          value[1],
                                          car.licenseplate,
                                          value[2],
                                          value[3],
                                          value[4],
                                          value[6])
                if device.device_retrieval_status() == "VALID":
                    devices.append(device)

    async_add_devices(devices, True)


class MercedesMESensor(MercedesMeEntity):
    """Representation of a Sensor."""

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
