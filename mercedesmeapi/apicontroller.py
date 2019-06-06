# -*- coding: utf-8 -*-
""" Simple Mercedes me API.

Attributes:
    username (int): mercedes me username (email)
    password (string): mercedes me password
    update_interval (int): min update intervall in seconds
"""

import base64
import hashlib
import json
import logging
from os import urandom
import random
import string
import time
import uuid

from urllib.parse import urlparse, parse_qs
from multiprocessing import RLock

import requests
import lxml.html

_LOGGER = logging.getLogger(__name__)

URL_VHS_API = "https://vhs.meapp.secure.mercedes-benz.com"
URL_USR_API = "https://bff.meapp.secure.mercedes-benz.com"

CLIENT_ID = "4390b0db-4be9-40e9-9147-5845df537beb"
API_ID = "MCMAPP.FE_PROD"
AUTH_REDIR_URL = "https://cgw.meapp.secure.mercedes-benz.com/endpoint/api/v1/redirect"

ME_STATUS_URL = "{0}/api/v2/appdata".format(URL_USR_API)
CAR_STATUS_URL = "{0}/api/v1/vehicles/%s/dynamic?forceRefresh=true".format(URL_VHS_API)
CAR_LOCAT_URL = "{0}/api/v1/vehicles/%s/location".format(URL_VHS_API)
CAR_LOCK_URL = "{0}/api/v1/vehicles/%s/doors/lock".format(URL_VHS_API)
CAR_UNLOCK_URL = "{0}/api/v1/vehicles/%s/doors/unlock".format(URL_VHS_API)
CAR_HEAT_ON_URL = "{0}/api/v1/vehicles/%s/auxheat/start".format(URL_VHS_API)
CAR_HEAT_OFF_URL = "{0}/api/v1/vehicles/%s/auxheat/stop".format(URL_VHS_API)
CAR_CLIMATE_ON_URL = "{0}/api/v1/vehicles/%s/precond/start".format(URL_VHS_API)
CAR_CLIMATE_OFF_URL = "{0}/api/v1/vehicles/%s/precond/stop".format(URL_VHS_API)
CAR_FEATURE_URL = "{0}/api/v2/dashboarddata/%s/vehicle".format(URL_USR_API)

APP_USER_AGENT = "MercedesMe/2.13.2+639 (Android 5.1)"

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

LOCATION_OPTIONS = ["latitude",
                    "longitude",
                    "heading"]

TIRE_OPTIONS = ["tirepressureRearLeft",
                "tirepressureRearRight",
                "tirepressureFrontRight",
                "tirepressureFrontLeft",
                "tirewarninglamp",
                "tirewarningsrdk",
                "tirewarningsprw"
                "tireMarkerFrontRight",
                "tireMarkerFrontLeft",
                "tireMarkerRearLeft",
                "tireMarkerRearRight",
                "tireWarningRollup",
                "lastTirepressureTimestamp"]

WINDOW_OPTIONS = ["windowstatusrearleft",
                  "windowstatusrearright",
                  "windowstatusfrontright",
                  "windowstatusfrontleft",
                  'windowsClosed']

DOOR_OPTIONS = [
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
    'locked']

ELECTRIC_OPTIONS = [
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
    'electricconsumptionstart']



BINARY_SENSOR_OPTIONS = [
    'warningwashwater',
    'warningenginelight',
    'warningbrakefluid',
    'warningcoolantlevellow',
    'parkbrakestatus',
    'readingLampFrontRight',
    'readingLampFrontLeft',
    'preWarningBrakeLiningWear']

AUX_HEAT_OPTIONS = [
    'auxheatActive',
    'auxheatwarnings',
    'auxheatruntime',
    'auxheatstatus',
    'auxheatwarningsPush',
    'auxheattimeselection',
    'auxheattime1',
    'auxheattime2',
    'auxheattime3']

PRE_COND_OPTIONS = [
    'preconditionState',
    'precondimmediate'
]

# Set to False for testing with tools like fiddler
# Change to True for production
LOGIN_VERIFY_SSL_CERT = True


class Car(object):
    def __init__(self):
        self.licenseplate = None
        self.finorvin = None
        self.salesdesignation = None
        self.nickname = None
        self.modelyear = None
        self.colorname = None
        self.fueltype = None
        self.powerhp = None
        self.powerkw = None
        self.numberofdoors = None
        self.numberofseats = None

        self.vehicleHealthStatus = None
        self.binarysensors = None
        self.tires = None
        self.odometer = None
        self.doors = None
        self.stateofcharge = None
        self.location = None
        self.windows = None
        self.features = None
        self.auxheat = None
        self.precond = None

class StateOfObject(object):
    def __init__(self, unit=None, value=None, retrievalstatus=None, timestamp=None):
        self.unit = None
        self.value = None
        self.timestamp = None
        if unit is not None:
            self.retrievalstatus = None
            self.unit = unit

        if value is not None:
            self.value = value
        if retrievalstatus is not None:
            self.retrievalstatus = retrievalstatus
        if timestamp is not None:
            self.timestamp = timestamp

class Tires(object):
    def __init__(self):
        self.name = "Tires"

class Odometer(object):
    def __init__(self):
        self.name = "Odometer"

class Features(object):
    def __init__(self):
        self.name = "Features"

class Windows(object):
    def __init__(self):
        self.name = "Windows"

class Doors(object):
    def __init__(self):
        self.name = "Features"

class Electric(object):
    def __init__(self):
        self.name = "Electric"

class Auxheat(object):
    def __init__(self):
        self.name = "Auxheat"

class Precond(object):
    def __init__(self):
        self.name = "Precond"

class Binary_Sensors(object):
    def __init__(self):
        self.name = "Binary_Sensors"

class Location(object):
    def __init__(self, latitude=None, longitude=None, heading=None):
        self.name = "Location"
        self.latitude = None
        self.longitude = None
        self.heading = None
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if heading is not None:
            self.heading = heading

class CarAttribute(object):
    def __init__(self, value, retrievalstatus, timestamp):
        self.value = value
        self.retrievalstatus = retrievalstatus
        self.timestamp = timestamp

class Controller(object):
    """ Simple Mercedes me API.
    """
    def __init__(self, auth_handler, update_interval, accept_lang, country_code,
                 excluded_cars, save_car_details, save_path):

        self.__lock = RLock()
        self.accept_lang = accept_lang
        self.country_code = country_code
        self.auth_handler = auth_handler
        self.cars = []
        self.update_interval = update_interval
        self.excluded_cars = excluded_cars
        self.is_valid_session = False
        self.last_update_time = 0
        self.save_car_details = save_car_details
        self.save_path = save_path
        self.session = requests.session()
        
        _LOGGER.debug("Controller init complete. Start _get_cars")
        self._get_cars()

    def update(self):
        _LOGGER.debug("Update start")
        self._update_cars()

    def lock(self, car_id):
        return self._execute_car_action(CAR_LOCK_URL, car_id, 'car unlock', None)

    def unlock(self, car_id, pin):
        return self._execute_car_action(CAR_UNLOCK_URL, car_id, 'car unlock', pin)

    def switch_car_feature(self, action = None, car_id = None):
        function_list = {
            'heater_on': self.heater_on,
            'heater_off': self.heater_off,
            'climate_on': self.climate_on,
            'climate_off': self.climate_off
        }
        parameters = {
            'car_id': car_id
        }

        return function_list[action](parameters)

    def heater_on(self, car_id):
        return self._execute_car_action(CAR_HEAT_ON_URL, car_id.get('car_id'), 'heater_on', None)

    def heater_off(self, car_id):
        return self._execute_car_action(CAR_HEAT_OFF_URL, car_id.get('car_id'), 'heater_off', None)

    def climate_on(self, car_id):
        return self._execute_car_action(CAR_CLIMATE_ON_URL, car_id.get('car_id'), 'climate_on', None)

    def climate_off(self, car_id):
        return self._execute_car_action(CAR_CLIMATE_OFF_URL, car_id.get('car_id'), 'climate_off', None)

    def _execute_car_action(self, url, car_id, action, pin):
        _LOGGER.debug("%s for %s called", action, car_id)
        self._check_access_token()
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": "Bearer {}".format(self.auth_handler.token_info["access_token"]),
            "country_code": self.country_code,
            "User-Agent": "MercedesMe/2.13.2+639 (Android 5.1)",
            "x-pin": pin
            }
        if pin is not None:
            me_status_header['x-pin'] = pin

        result = self._retrieve_json_at_url(url % car_id, me_status_header, "post")
        _LOGGER.debug(result)
        if result.get("status") == 'PENDING':
            wait_counter = 0
            while wait_counter < 30:
                result = self._retrieve_json_at_url(url % car_id, me_status_header, "get")
                _LOGGER.debug(result)
                if result.get('status') == 'PENDING':
                    wait_counter = wait_counter + 1
                    time.sleep(1)
                else:
                    break
        self.update()
        if result.get('status') == 'SUCCESS':
            return True
        else:
            return False


    def _update_cars(self):
        cur_time = time.time()
        with self.__lock:
            if self.auth_handler.is_token_expired(self.auth_handler.token_info):
                self.auth_handler.refresh_access_token(self.auth_handler.token_info['refresh_token'])
            if cur_time - self.last_update_time > self.update_interval:
                for car in self.cars:

                    api_result = self._retrieve_car_details(car.finorvin).get("dynamic")

                    car.odometer = self._get_car_values(api_result, car.finorvin, Odometer(), ODOMETER_OPTIONS)
                    car.tires = self._get_car_values(api_result, car.finorvin, Tires(), TIRE_OPTIONS)
                    car.doors = self._get_car_values(api_result, car.finorvin, Doors(), DOOR_OPTIONS)
                    car.location = self._get_location(car.finorvin)
                    car.binarysensors = self._get_car_values(api_result, car.finorvin, Binary_Sensors(), BINARY_SENSOR_OPTIONS)
                    car.windows = self._get_car_values(api_result, car.finorvin, Windows(), WINDOW_OPTIONS)
                    if car.features.charging_clima_control:
                        car.electric = self._get_car_values(api_result, car.finorvin, Electric(), ELECTRIC_OPTIONS)
                    if car.features.aux_heat:
                        car.auxheat = self._get_car_values(api_result, car.finorvin, Auxheat(), AUX_HEAT_OPTIONS)
                    if car.features.charging_clima_control:
                        car.precond = self._get_car_values(api_result, car.finorvin, Precond(), PRE_COND_OPTIONS)

                self.last_update_time = time.time()

    def _get_cars(self):

        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": "Bearer {}".format(self.auth_handler.token_info["access_token"])
        }
        response = self.session.get(ME_STATUS_URL, headers=me_status_header,
                                    verify=LOGIN_VERIFY_SSL_CERT)

        _LOGGER.debug("Me_status_response: %s", response.text)
        
        cars = json.loads(
            response.content.decode('utf8'))['vehicles']

        for c in cars:
            
            if c.get("fin") in self.excluded_cars:
                continue

            car = Car()
            car.finorvin = c.get("fin")
            car.licenseplate = c.get("licensePlate")
            car.features = self._get_car_features(car.finorvin)

            api_result = self._retrieve_car_details(car.finorvin).get("dynamic")

            # car.salesdesignation = detail.get("salesDesignation")

            car.odometer = self._get_car_values(api_result, car.finorvin, Odometer(), ODOMETER_OPTIONS)
            car.tires = self._get_car_values(api_result, car.finorvin, Tires(), TIRE_OPTIONS)
            car.doors = self._get_car_values(api_result, car.finorvin, Doors(), DOOR_OPTIONS)
            car.location = self._get_location(car.finorvin)
            car.binarysensors = self._get_car_values(api_result, car.finorvin, Binary_Sensors(), BINARY_SENSOR_OPTIONS)
            car.windows = self._get_car_values(api_result, car.finorvin, Windows(), WINDOW_OPTIONS)
            if car.features.charging_clima_control:
                car.electric = self._get_car_values(api_result, car.finorvin, Electric(), ELECTRIC_OPTIONS)
            if car.features.aux_heat:
                car.auxheat = self._get_car_values(api_result, car.finorvin, Auxheat(), AUX_HEAT_OPTIONS)
            if car.features.charging_clima_control:
                car.precond = self._get_car_values(api_result, car.finorvin, Precond(), PRE_COND_OPTIONS)

            self.cars.append(car)

    def _get_car_attribute(self, c, attribute_name, fin):
        _LOGGER.debug("get_car_attribute %s for %s called",
                      attribute_name,
                      fin)
        _LOGGER.info(c.get(attribute_name))
        option_status = CarAttribute(c.get(attribute_name).get("value"),
                                     c.get(attribute_name).get("status"),
                                     0#,c.get(attribute_name).get("ts")
                                     )
        return option_status

    def _get_location(self, car_id):
        """ get refreshed location information."""
        _LOGGER.debug("get_location for %s called", car_id)

        api_result = self._retrieve_location_details(car_id)

        _LOGGER.debug("get_location result: %s", api_result)

        location = Location()

        for loc_option in LOCATION_OPTIONS:
            if api_result is not None:
                curr_loc_option = api_result.get(loc_option)
                value = CarAttribute(
                    curr_loc_option,
                    None,
                    None)
                setattr(location, loc_option, value)
            else:
                setattr(location, loc_option, CarAttribute(-1, -1, None))

        return location

    def _get_car_values(self, car_detail, car_id, classInstance, options):
        _LOGGER.debug("get_car_values %s for %s called", classInstance.name, car_id)

        for option in options:
            if car_detail is not None:
                curr = car_detail.get(option)
                if curr is not None:
                    curr_status = CarAttribute(
                        curr.get("value"),
                        curr.get("status"),
                        car_detail.get("vtime")
                    )
                else:
                    curr_status = CarAttribute(0, 4, 0)
                setattr(classInstance, option, curr_status)
            else:
                setattr(classInstance, option, CarAttribute(-1, -1, None))

        return classInstance

    def _get_car_features(self, car_id):
        _LOGGER.debug("_get_car_features for %s called", car_id)
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": "Bearer {}".format(self.auth_handler.token_info["access_token"]),
            "country_code": "DE",
            "User-Agent": APP_USER_AGENT
            }
        features = self._retrieve_json_at_url(CAR_FEATURE_URL % car_id, me_status_header, "get")

        car_features = Features()

        if self.save_car_details:
            with open('{0}feat_{1}.json'.format(self.save_path, car_id), 'w') as outfile:
                json.dump(features, outfile)

        for feature in features.get("metadata").get("featureEnablements"):
            setattr(car_features, 
                    feature.get("name").lower(),
                    feature.get("enablement") == "ACTIVATED")
        
        return car_features

    def _retrieve_car_details(self, fin):
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": self._get_bearer_token(),
            "country_code": "DE",
            "User-Agent": "MercedesMe/2.13.2+639 (Android 5.1)"
            }

        result = self._retrieve_json_at_url(CAR_STATUS_URL % fin, me_status_header, "get")
        
        if self.save_car_details:
            with open('{0}state_{1}.json'.format(self.save_path, fin), 'w') as outfile:
                json.dump(result, outfile)

        return result

    def _retrieve_location_details(self, car_id):
        _LOGGER.debug("get location for %s called", car_id)
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": self._get_bearer_token(),
            "country_code": "DE",
            "User-Agent": "MercedesMe/2.13.2+639 (Android 5.1)",
            "lat": "1",
            "lon": "1"
            }

        res = self._retrieve_json_at_url(CAR_LOCAT_URL % car_id, 
                                         me_status_header, "get")
        return res

    def _retrieve_json_at_url(self, url, headers, type):
        try:
            _LOGGER.debug("Connect to URL %s %s", type, str(url))

            if type == "get":
                res = self.session.get(url,
                                       verify=LOGIN_VERIFY_SSL_CERT,
                                       headers=headers)
            else:
                res = self.session.post(url,
                                        verify=LOGIN_VERIFY_SSL_CERT,
                                        headers=headers)
        except requests.exceptions.Timeout:
            _LOGGER.exception(
                "Connection to the api timed out at URL %s", url)
            return
        if res.status_code != 200:
            _LOGGER.exception(
                "Connection failed with http code %s", res.status_code)
            return

        return res.json()

    def _get_bearer_token(self):
        return "Bearer {}".format(self.auth_handler.token_info["access_token"])

    def _check_access_token(self):
        if self.auth_handler.is_token_expired(self.auth_handler.token_info):
            self.auth_handler.refresh_access_token(self.auth_handler.token_info['refresh_token'])
