"""
Support for Mercedes cars with Mercedes ME.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/sensor.mercedesme/
"""
import logging
import datetime

from homeassistant.components.lock import ENTITY_ID_FORMAT, LockDevice
from homeassistant.const import STATE_LOCKED, STATE_UNLOCKED

from custom_components.mercedesmeapi import (
    DATA_MME, DOMAIN, FEATURE_NOT_AVAILABLE, MercedesMeEntity, LOCKS)

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
        for key, value in sorted(LOCKS.items()):
            if value[5] is None or getattr(car.features, value[5]) == True:
                devices.append(
                    MercedesMELock(
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


class MercedesMELock(MercedesMeEntity, LockDevice):
    """Representation of a Sensor."""

    @property
    def is_locked(self):
        """Get whether the lock is in locked state."""
        return True if self._state == STATE_LOCKED \
            else False
    
    def lock(self, **kwargs):
        """Send the lock command."""
        _LOGGER.debug("Locking doors for: %s", self._name)
        self._data.lock(self._vin)

    def unlock(self, **kwargs):
        """Send the unlock command."""
        _LOGGER.debug("Unlocking doors for: %s", self._name)
        self._data.unlock(self._vin)

    @property
    def state(self):
        """Return the state of the sensor."""
        return STATE_LOCKED if self._state else STATE_UNLOCKED
