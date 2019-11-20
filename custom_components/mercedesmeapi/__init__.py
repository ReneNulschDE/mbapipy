"""
Support for MercedesME System.

For more details about this component, please refer to the documentation at
https://github.com/ReneNulschDE/mbapipy/
"""
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.const import (CONF_SCAN_INTERVAL,
                                 CONF_USERNAME, CONF_PASSWORD, CONF_NAME)
from homeassistant.helpers import discovery, config_validation as cv
from homeassistant.helpers import aiohttp_client, device_registry as dr
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval
from homeassistant.util import slugify

from .apicontroller import Controller
from .oauth import MercedesMeOAuth
from .const import MERCEDESME_COMPONENTS

_LOGGER = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = ".mercedesme-token-cache"

CONF_COUNTRY_CODE = "country_code"
CONF_ACCEPT_LANG = "accept_lang"
CONF_PIN = "pin"
CONF_EXCLUDED_CARS = "excluded_cars"
CONF_SAVE_CAR_DETAILS = "save_car_details"
CONF_TIRE_WARNING_INDICATOR = "tire_warning"
CONF_CARS = "cars"
CONF_CARS_VIN = "vin"

DEFAULT_NAME = "Mercedes ME"
DOMAIN = "mercedesmeapi"

SIGNAL_UPDATE_MERCEDESME = "mercedesmeapi_update"

CARS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CARS_VIN): cv.string,
        vol.Optional(CONF_TIRE_WARNING_INDICATOR,
                     default="tirewarninglamp"): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=30):
            vol.All(cv.positive_int, vol.Clamp(min=60)),
        vol.Optional(CONF_COUNTRY_CODE, default="DE"): cv.string,
        vol.Optional(CONF_ACCEPT_LANG, default="en_DE"): cv.string,
        vol.Optional(CONF_EXCLUDED_CARS, default=[]):
            vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_PIN): cv.string,
        vol.Optional(CONF_SAVE_CAR_DETAILS, default=False): cv.boolean,
        vol.Optional(CONF_CARS): [CARS_SCHEMA],
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up MercedesMe System."""

    conf = config[DOMAIN]

    scan_interval = conf.get(CONF_SCAN_INTERVAL)

    cache = hass.config.path(DEFAULT_CACHE_PATH)

    auth_handler = MercedesMeOAuth(conf.get(CONF_USERNAME),
                                   conf.get(CONF_PASSWORD),
                                   conf.get(CONF_ACCEPT_LANG),
                                   cache)

    token_info = auth_handler.get_cached_token()

    if not token_info:
        _LOGGER.debug("no token; requesting authorization")
        token_info = auth_handler.request_initial_token()
    else:
        _LOGGER.debug("cached token found")

    if not token_info:
        _LOGGER.warning("no token; authorization failed; check debug log")
        return

    mercedesme_api = Controller(auth_handler,
                                scan_interval,
                                conf.get(CONF_ACCEPT_LANG),
                                conf.get(CONF_COUNTRY_CODE),
                                conf.get(CONF_EXCLUDED_CARS),
                                conf.get(CONF_SAVE_CAR_DETAILS),
                                conf.get(CONF_PIN),
                                hass.config.path(""))

    hass.data[DOMAIN] = MercedesMeHub(mercedesme_api, conf)

    for component in MERCEDESME_COMPONENTS:
        hass.async_create_task(
            discovery.async_load_platform(hass, component, DOMAIN, {}, config)
        )

    def hub_refresh(event_time):
        """Call Mercedes me API to refresh information."""
        _LOGGER.info("Updating Mercedes me component.")
        hass.data[DOMAIN].data.update()
        dispatcher_send(hass, SIGNAL_UPDATE_MERCEDESME)

    track_time_interval(
        hass,
        hub_refresh,
        timedelta(seconds=scan_interval))

    return True


class MercedesMeHub(object):
    """Representation of a base MercedesMe device."""

    def __init__(self, data, config):
        """Initialize the entity."""
        self.data = data
        self.config = config


class MercedesMeEntity(Entity):
    """Entity class for MercedesMe devices."""

    def __init__(self, data, internal_name, sensor_name, vin,
                 unit, licenseplate, feature_name, object_name, attrib_name,
                 extended_attributes, **kwargs):
        """Initialize the MercedesMe entity."""
        self._data = data
        self._state = False
        self._name = licenseplate + " " + sensor_name
        self._internal_name = internal_name
        self._unit = unit
        self._vin = vin
        self._feature_name = feature_name
        self._object_name = object_name
        self._attrib_name = attrib_name
        self._licenseplate = licenseplate
        self._extended_attributes = extended_attributes
        self._kwargs = kwargs
        self._unique_id = slugify(f"{self._vin}_{self._internal_name}")
        self._car = next(
            car for car in self._data.cars if car.finorvin == self._vin)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        return self._unique_id

    def device_retrieval_status(self):
        return self.get_car_value(self._feature_name,
                                  self._object_name,
                                  "retrievalstatus",
                                  "error")

    def update(self):
        """Get the latest data and updates the states."""
        _LOGGER.debug("Updating %s", self._internal_name)

        self._car = next(
            car for car in self._data.cars if car.finorvin == self._vin)

        self._state = self.get_car_value(self._feature_name,
                                         self._object_name,
                                         self._attrib_name,
                                         "error")

        _LOGGER.debug("Updated %s %s", self._internal_name, self._state)

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

    @property
    def device_state_attributes(self):
        """Return the state attributes."""

        state = {
            "car": self._licenseplate,
            "retrievalstatus": self.get_car_value(self._feature_name,
                                                  self._object_name,
                                                  "retrievalstatus",
                                                  "error")
        }
        if self._extended_attributes is not None:
            for attrib in self._extended_attributes:
                if self.get_car_value(
                        self._feature_name, attrib,
                        "retrievalstatus", "error") == "VALID":
                    state[attrib] = self.get_car_value(self._feature_name,
                                                       attrib,
                                                       "value",
                                                       "error")
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit
