"""
Support for Mercedes cars with Mercedes ME.

For more details about this component, please refer to the documentation at
https://github.com/ReneNulschDE/mbapipy/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from . import (
    DOMAIN,
    CONF_TIRE_WARNING_INDICATOR,
    CONF_CARS,
    CONF_CARS_VIN,
    MercedesMeEntity)
from .const import BINARY_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Setup the sensor platform."""
    if discovery_info is None:
        return

    data = hass.data[DOMAIN].data
    conf = hass.data[DOMAIN].config

    if not data.cars:
        _LOGGER.error("No cars found. Check component log.")
        return

    devices = []
    for car in data.cars:
        
        tire_warning_field = "tirewarninglamp"
        if conf.get(CONF_CARS) is not None:
            for car_conf in conf.get(CONF_CARS):
                if car_conf.get(CONF_CARS_VIN) == car.finorvin:
                    tire_warning_field = car_conf.get(CONF_TIRE_WARNING_INDICATOR)
                    break

        for key, value in sorted(BINARY_SENSORS.items()):
            if key == "tirewarninglamp":
                value[3] = tire_warning_field

            if value[5] is None or getattr(car.features, value[5]) is True:
                device = MercedesMEBinarySensor(
                    data,
                    key,
                    value[0],
                    car.finorvin,
                    value[1],
                    car.licenseplate,
                    value[2],
                    value[3],
                    value[4],
                    value[6],
                )
                if device.device_retrieval_status() == "VALID":
                    devices.append(device)

    async_add_devices(devices, True)


class MercedesMEBinarySensor(MercedesMeEntity, BinarySensorDevice):
    """Representation of a Sensor."""

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        if self._state == "INACTIVE":
            return False
        if self._state == "ACTIVE":
            return True

        return self._state
