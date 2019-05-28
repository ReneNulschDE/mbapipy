"""
Support for MercedesME System.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/mercedesme/
"""
import logging
from datetime import timedelta
import urllib.parse
import base64
import time

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.components.http import HomeAssistantView
from homeassistant.const import (
    CONF_SCAN_INTERVAL, LENGTH_KILOMETERS,
    CONF_EXCLUDE, CONF_USERNAME, CONF_PASSWORD)
from homeassistant.helpers import discovery
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect, dispatcher_send)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval

DEPENDENCIES = ['http']

_LOGGER = logging.getLogger(__name__)

BINARY_SENSORS = {
#    'doorsClosed': ['Doors closed'],
#    'windowsClosed': ['Windows closed'],
#    'locked': ['Doors locked'],
#    'tireWarningLight': ['Tire Warning'],
#    'warningWashWater': ['Wash Water Warning'],
#    'warningBrakeFluid': ['Brake Fluid Warning'],
#    'warningEngineLight': ['Engine Light Waring'],
#    'trunkClosed': ['Trunk closed'],
#    'trunkLocked': ['Trunk locked'],
#    'fuelLidClosed': ['Fuel Lid closed'],
#    'warningBrakeLineWear': ['Brake Line Wear Warning'],
#    'warningCoolantLevelLow': ['Coolant Level Low Warning'],
#    'parkingBrakeStatus': ['Parking Brake'],
#    'tankReserveLamp': ['Tank Reserve Lamp']
}

SENSORS = {
    #'fuellevelpercent': ['Fuel Level', '%', 'fuellevelpercent'],
    #'fuelRangeKm': ['Fuel Range', LENGTH_KILOMETERS],
    'licenseplate': ['licenseplate', None, None, None, 'licenseplate'],
    'colorname': ['colorname', None, None, None, 'colorname'],
    'odometer': ['Odometer', 'Km', 'odometer', 'odometer', 'value'],
    'distancesincereset': ['Distance since reset', 'Km', 'odometer',
                           'distancesincereset', 'value'],
    'distancesincestart': ['Distance since start', 'Km', 'odometer',
                           'distancesincestart', 'value'],
    #'serviceIntervalDays': ['Next Service', 'days'],
    #'electricRangeKm': ['Electric Range Km', LENGTH_KILOMETERS],
    'stateofcharge_value': ['Electric Charge', '%', None,
                            'stateofcharge', 'value'],
    #'electricChargingStatus': ['ElectricChargingStatus', None],
    #'electricConsumptionReset': ['Electric Consumption Reset', None],
    #'electricConsumptionStart': ['Electric Consumption Start', None],
    #'distanceElectricalStart': ['Distance Electrical Start', None],
    #'distanceElectricalReset': ['Distance Electrical Reset', None],
    #'lightSwitchPosition': ['Light Switch Position', None],
    'doorstatusfrontleft': ['Door Front Left', None, 'doors',
                            'doorstatusfrontleft', 'value'],
    'doorstatusfrontright': ['Door Front Right', None, 'doors',
                             'doorstatusfrontright', 'value'],
    'doorstatusrearleft': ['Door Rear Left', None, 'doors',
                           'doorstatusrearleft', 'value'],
    'doorstatusrearright': ['Door Rear Right', None, 'doors',
                            'doorstatusrearright', 'value'],
    'doorlockstatusfrontleft': ['Door Lock Front Left', None, 'doors',
                                'doorlockstatusfrontleft', 'value'],
    'doorlockstatusfrontright': ['Door Lock Front Right', None, 'doors',
                                 'doorlockstatusfrontright', 'value'],
    'doorlockstatusrearleft': ['Door Lock Front Left', None, 'doors',
                               'doorlockstatusrearleft', 'value'],
    'doorlockstatusrearright': ['Door Lock Front Right', None, 'doors',
                                'doorlockstatusrearright', 'value'],
    'doorlockstatusdecklid': ['Door Lock Decklid', None, 'doors',
                              'doorlockstatusdecklid', 'value'],
    'doorlockstatusgas': ['Door Lock Gas', None, 'doors',
                          'doorlockstatusgas', 'value'],
    'doorlockstatusvehicle': ['Door Lock Vehicle', None, 'doors',
                              'doorlockstatusvehicle', 'value'],
    'tirepressurefrontleft': ['Tire Pressure Front Left', 'Kp', 'tires',
                              'tirepressurefrontleft', 'value'],
    'tirepressurefrontright': ['Tire Pressure Front Right', 'Kp', 'tires',
                               'tirepressurefrontright', 'value'],
    'tirepressurerearleft': ['Tire Pressure Rear Left', 'Kp', 'tires',
                             'tirepressurerearleft', 'value'],
    'tirepressurerearright': ['Tire Pressure Rear Right', 'Kp', 'tires',
                              'tirepressurerearright', 'value']
    }


DEFAULT_CACHE_PATH = '.mercedesme-token-cache'

CONF_COUNTRY_CODE = 'country_code'
CONF_ACCEPT_LANG = 'accept_lang'

DATA_MME = 'mercedesmeapi'
DEFAULT_NAME = 'Mercedes ME'
DOMAIN = 'mercedesmeapi'

FEATURE_NOT_AVAILABLE = "The feature %s is not available for your car %s"

NOTIFICATION_ID = 'mercedesmeapi_integration_notification'
NOTIFICATION_TITLE = 'Mercedes me integration setup'

SIGNAL_UPDATE_MERCEDESME = "mercedesmeapi_update"


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=30):
            vol.All(cv.positive_int, vol.Clamp(min=60)),
        vol.Optional(CONF_COUNTRY_CODE, default='DE'): cv.string,
        vol.Optional(CONF_ACCEPT_LANG, default='de-DE'): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up MercedesMe System."""

    from mercedesmeapi.oauth import MercedesMeOAuth
    from mercedesmeapi.apicontroller import Controller

    conf = config[DOMAIN]

    scan_interval = conf.get(CONF_SCAN_INTERVAL)

    cache = config.get(hass.config.path(DEFAULT_CACHE_PATH))

    auth_handler = MercedesMeOAuth(conf.get(CONF_USERNAME),
                                   conf.get(CONF_PASSWORD),
                                   conf.get(CONF_ACCEPT_LANG),
                                   cache)

    token_info = auth_handler.get_cached_token()

    if not token_info:
        _LOGGER.info("no token; requesting authorization")

        return True

    mercedesme_api = Controller(auth_handler, scan_interval)
    hass.data[DATA_MME] = MercedesMeHub(mercedesme_api)

    discovery.load_platform(hass, 'sensor', DOMAIN, {}, config)
    discovery.load_platform(hass, 'device_tracker', DOMAIN, {}, config)
    #discovery.load_platform(hass, 'binary_sensor', DOMAIN, {}, config )

    def hub_refresh(event_time):
        """Call Mercedes me API to refresh information."""
        _LOGGER.info("Updating Mercedes me component.")
        hass.data[DATA_MME].data.update()
        dispatcher_send(hass, SIGNAL_UPDATE_MERCEDESME)

    track_time_interval(
        hass,
        hub_refresh,
        timedelta(seconds=scan_interval))

    return True

class MercedesMeHub(object):
    """Representation of a base MercedesMe device."""

    def __init__(self, data):
        """Initialize the entity."""
        self.data = data

class MercedesMeEntity(Entity):
    """Entity class for MercedesMe devices."""

    def __init__(self, data, internal_name, sensor_name, vin,
                 unit, licenseplate, feature_name, object_name, attrib_name):
        """Initialize the MercedesMe entity."""
        self._car = None
        self._data = data
        self._state = False
        self._name = licenseplate + ' ' + sensor_name
        self._internal_name = internal_name
        self._unit = unit
        self._vin = vin
        self._feature_name = feature_name
        self._object_name = object_name
        self._attrib_name = attrib_name

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit
