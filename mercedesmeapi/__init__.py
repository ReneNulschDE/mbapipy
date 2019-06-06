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

    'warningenginelight': ['Engine Light Warning', None, 'binarysensors', 'warningenginelight', 'value', None, {
        'warningbrakefluid',
        'warningwashwater',
        'warningcoolantlevellow',
        'warninglowbattery'
    }],
    
    'parkbrakestatus': ['Park Brake Status', None, 'binarysensors', 'parkbrakestatus', 'value', None, {
        'preWarningBrakeLiningWear'
    }],
    'windowsClosed': ['Windows Closed', None, 'windows',
                              'windowsClosed', 'value', None, { 
                                "windowstatusrearleft",
                                "windowstatusrearright",
                                "windowstatusfrontright",
                                "windowstatusfrontleft",}],
    'tirewarninglamp': ['Tire Warning', None, 'tires',
                              'tirewarninglamp', 'value', None, { 
                                "tirepressureRearLeft",
                                "tirepressureRearRight",
                                "tirepressureFrontRight",
                                "tirepressureFrontLeft",
                                "tirewarningsrdk",
                                "tirewarningsprw"
                                "tireMarkerFrontRight",
                                "tireMarkerFrontLeft",
                                "tireMarkerRearLeft",
                                "tireMarkerRearRight",
                                "tireWarningRollup",
                                "lastTirepressureTimestamp"}]
}

ODOMETER_OPTIONS = ["odo",
                    "distanceReset",
                    "distanceStart",
                    "averageSpeedReset",
                    "averageSpeedStart",
                    "distanceZEReset",
                    "drivenTimeZEReset",
                    "drivenTimeReset",
                    "drivenTimeStart",
                    "ecoscoretotal",
                    "ecoscorefreewhl",
                    "ecoscorebonusrange",
                    "ecoscoreconst",
                    "ecoscoreaccel",
                    "gasconsumptionstart",
                    "gasconsumptionreset",
                    "gasTankRange",
                    "gasTankLevel",
                    "liquidconsumptionstart",
                    "liquidconsumptionreset",
                    "liquidRangeSkipIndication",
                    "rangeliquid",
                    "serviceintervaldays",
                    "tanklevelpercent",
                    "tankReserveLamp"]

LOCKS = {
    'lock': ['Lock', None, "doors", 'locked', 'value', 'remote_door_lock'],
}

SWITCHES = {
    'aux_heat': ['AUX HEAT', None, "auxheat", 'auxheatActive', 'value', 'aux_heat', None, 'heater'],
    'climate_control': ['CLIMATE CONTROL', None, "precond", 'preconditionState', 'value', 'charging_clima_control', None, 'climate'],
}

SENSORS = {
    'lock': ['Lock', None, "doors", 'locked', 'value', None, {
                    'doorStateFrontLeft',
                    'doorStateFrontRight', 
                    'doorStateRearLeft', 
                    'doorStateRearRight', 
                    'frontLeftDoorLocked', 
                    'frontRightDoorLocked', 
                    'rearLeftDoorLocked', 
                    'rearRightDoorLocked',
                    'frontLeftDoorClosed', 
                    'frontRightDoorClosed', 
                    'rearLeftDoorClosed', 
                    'rearRightDoorClosed', 
                    'rearRightDoorClosed', 
                    'doorsClosed',
                    'trunkStateRollup',
                    'sunroofstatus',
    }],
    'rangeElectricKm' : ['Range electric', 'Km', "electric", 'rangeElectricKm', 'value', 'charging_clima_control', {
                    'rangeelectric',
                    'rangeElectricKm',
                    'criticalStateOfSoc',
                    'maxrange',
                    'stateOfChargeElectricPercent',
                    'endofchargetime',
                    'criticalStateOfDeparturetimesoc',
                    'warninglowbattery',
                    'electricconsumptionreset',
                    'maxStateOfChargeElectricPercent',
                    'supplybatteryvoltage',
                    'electricChargingStatus',
                    'chargingstatus',
                    'soc',
                    'showChargingErrorAndDemand',
                    'electricconsumptionstart'}],

    'auxheatstatus': ['auxheat status', None, "auxheat", 'auxheatstatus', 'value', 'aux_heat', {
                    'auxheatActive',
                    'auxheatwarnings',
                    'auxheatruntime',
                    'auxheatwarningsPush',
                    'auxheattimeselection',
                    'auxheattime1',
                    'auxheattime2',
                    'auxheattime3'
    }],
    'tanklevelpercent': ['Fuel Level', '%', "odometer", 'tanklevelpercent', 'value', None, None],
    'odometer': ['Odometer', 'Km', 'odometer', 'odo', 'value', None, {"distanceReset",
                    "distanceStart",
                    "averageSpeedReset",
                    "averageSpeedStart",
                    "distanceZEReset",
                    "drivenTimeZEReset",
                    "drivenTimeReset",
                    "drivenTimeStart",
                    "ecoscoretotal",
                    "ecoscorefreewhl",
                    "ecoscorebonusrange",
                    "ecoscoreconst",
                    "ecoscoreaccel",
                    "gasconsumptionstart",
                    "gasconsumptionreset",
                    "gasTankRange",
                    "gasTankLevel",
                    "liquidconsumptionstart",
                    "liquidconsumptionreset",
                    "liquidRangeSkipIndication",
                    "rangeliquid",
                    "serviceintervaldays",
                    "tanklevelpercent",
                    "tankReserveLamp"}],
}


DEFAULT_CACHE_PATH = '.mercedesme-token-cache'

CONF_COUNTRY_CODE = 'country_code'
CONF_ACCEPT_LANG = 'accept_lang'
CONF_PIN = 'pin'
CONF_EXCLUDED_CARS = 'excluded_cars'
CONF_SAVE_CAR_DETAILS = 'save_car_details'

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
        vol.Optional(CONF_ACCEPT_LANG, default='en_DE'): cv.string,
        vol.Optional(CONF_EXCLUDED_CARS, default=[]):
                vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_PIN): cv.string,
        vol.Optional(CONF_SAVE_CAR_DETAILS, default=False): cv.boolean,
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up MercedesMe System."""

    from custom_components.mercedesmeapi.oauth import MercedesMeOAuth
    from custom_components.mercedesmeapi.apicontroller import Controller

    conf = config[DOMAIN]

    scan_interval = conf.get(CONF_SCAN_INTERVAL)

    cache = hass.config.path(DEFAULT_CACHE_PATH)

    auth_handler = MercedesMeOAuth(conf.get(CONF_USERNAME),
                                   conf.get(CONF_PASSWORD),
                                   conf.get(CONF_ACCEPT_LANG),
                                   cache)

    token_info = auth_handler.get_cached_token()

    if not token_info:
        _LOGGER.info("no token; requesting authorization")
        token_info = auth_handler.request_initial_token()
    else:
        _LOGGER.info("cached token found")

    if not token_info:
        _LOGGER.info("no token; authorization failed; check debug log")
        return

    mercedesme_api = Controller(auth_handler,
                                scan_interval,
                                conf.get(CONF_ACCEPT_LANG),
                                conf.get(CONF_COUNTRY_CODE),
                                conf.get(CONF_EXCLUDED_CARS),
                                conf.get(CONF_SAVE_CAR_DETAILS),
                                hass.config.path(''))

    hass.data[DATA_MME] = MercedesMeHub(mercedesme_api)

    discovery.load_platform(hass, 'sensor', DOMAIN, {}, config)
    discovery.load_platform(hass, 'lock', DOMAIN, {}, config)
    discovery.load_platform(hass, 'device_tracker', DOMAIN, {}, config)
    discovery.load_platform(hass, 'switch', DOMAIN, {}, config)
    discovery.load_platform(hass, 'binary_sensor', DOMAIN, {}, config )

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
                 unit, licenseplate, feature_name, object_name, attrib_name,
                 extended_attributes, **kwargs):
        """Initialize the MercedesMe entity."""
        self._data = data
        self._state = False
        self._name = licenseplate + ' ' + sensor_name
        self._internal_name = internal_name
        self._unit = unit
        self._vin = vin
        self._feature_name = feature_name
        self._object_name = object_name
        self._attrib_name = attrib_name
        self._licenseplate = licenseplate
        self._extended_attributes = extended_attributes
        self._kwargs = kwargs
        self._car = next(
            car for car in self._data.cars if car.finorvin == self._vin)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def device_retrieval_status(self):
        return self.get_car_value(self._feature_name, 
                                  self._object_name, 
                                  'retrievalstatus',
                                  'error')

    def update(self):
        """Get the latest data and updates the states."""
        _LOGGER.debug("Updating %s", self._internal_name)

        self._car = next(
            car for car in self._data.cars if car.finorvin == self._vin)

        self._state = self.get_car_value(self._feature_name, 
                                    self._object_name, 
                                    self._attrib_name,
                                    'error')
        
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
                                             'retrievalstatus',
                                             'error')
        }
        if self._extended_attributes is not None:
            for attrib in self._extended_attributes:
                if self.get_car_value(self._feature_name, attrib, 'retrievalstatus','error') == 'VALID':
                    state[attrib] = self.get_car_value(self._feature_name, 
                                                attrib, 
                                                'value',
                                                'error')
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit
