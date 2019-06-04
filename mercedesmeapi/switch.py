"""
Support for Mercedes cars with Mercedes ME.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/sensor.mercedesme/
"""
import logging
import datetime

from homeassistant.components.switch import SwitchDevice
from homeassistant.const import STATE_OFF, STATE_ON

from custom_components.mercedesmeapi import (
    DATA_MME, DOMAIN, FEATURE_NOT_AVAILABLE, MercedesMeEntity, SWITCHES)

DEPENDENCIES = ['mercedesmeapi']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the sensor platform."""
    if discovery_info is None:
        return

    data = hass.data[DATA_MME].data
    
    if not data.cars:
        _LOGGER.info("No Cars found.")
        return

    devices = []
    for car in data.cars:
        for key, value in sorted(SWITCHES.items()):
            if value[5] is None or getattr(car.features, value[5]) == True:
                devices.append(
                    MercedesMESwitch(
                        data, 
                        key, 
                        value[0], 
                        car.finorvin, 
                        value[1], 
                        car.licenseplate,
                        value[2],
                        value[3],
                        value[4],
                        None))

    async_add_devices(devices, True)


class MercedesMESwitch(MercedesMeEntity, SwitchDevice):
    """Representation of a Sensor."""

    @property
    def is_on(self):
        """Get whether the lock is in locked state."""
        return self._state
    
    def turn_off(self, **kwargs):
        """Send the lock command."""
        _LOGGER.debug("turn off for: %s", self._name)
        self._data.heater_off(self._vin)

    def turn_on(self, **kwargs):
        """Send the unlock command."""
        _LOGGER.debug("turn on doors for: %s", self._name)
        self._data.heater_on(self._vin)

    @property
    def state(self):
        """Return the state of the sensor."""
        return STATE_ON if self._state else STATE_OFF
