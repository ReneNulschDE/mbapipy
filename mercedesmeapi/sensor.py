"""
Support for Mercedes cars with Mercedes ME.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/sensor.mercedesme/
"""
import logging
import datetime

from custom_components.mercedesmebeta import (
    DATA_MME, DOMAIN, FEATURE_NOT_AVAILABLE, MercedesMeEntity, SENSORS)

DEPENDENCIES = ['mercedesmebeta']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the sensor platform."""
    if discovery_info is None:
        return

    data = hass.data[DATA_MME].data
    
    if not data.cars:
        return

    devices = []
    for car in data.cars:
        for key, value in sorted(SENSORS.items()):
            devices.append(
                MercedesMESensor(
                    data, 
                    key, 
                    value[0], 
                    car.finorvin, 
                    value[1], 
                    car.licenseplate,
                    value[2],
                    value[3],
                    value[4]))

    async_add_devices(devices, True)


class MercedesMESensor(MercedesMeEntity):
    """Representation of a Sensor."""

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Get the latest data and updates the states."""
        _LOGGER.info("Updating %s", self._internal_name)

        self._car = next(
            car for car in self._data.cars if car.finorvin == self._vin)

        self._state = self.get_car_value(self._feature_name, 
                                    self._object_name, 
                                    self._attrib_name,
                                    'error')

    @property
    def device_state_attributes(self):
        """Return the state attributes."""

        return {
            "car": self._car.licenseplate,
            "retrievalstatus": self.get_car_value(self._feature_name, 
                                             self._object_name, 
                                             'retrievalstatus',
                                             'error')
        }

    def get_car_value(self, feature, object_name, attrib_name, default_value):
        
        value = None

        if object_name:
            if not feature:
                value = getattr(
                                getattr(self._car, object_name, default_value), 
                                attrib_name, default_value)
            else:
                value = getattr(
                            getattr(
                                getattr(self._car, feature, default_value), 
                                object_name, default_value),
                            attrib_name, default_value)
                
        else:
            value = getattr(self._car, attrib_name, default_value)

        return value
