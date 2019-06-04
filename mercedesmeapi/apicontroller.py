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

URL_LOGIN = "https://login.secure.mercedes-benz.com"
URL_API = "https://api.secure.mercedes-benz.com"
URL_VHS_API = "https://vhs.meapp.secure.mercedes-benz.com"
URL_USR_API = "https://bff.meapp.secure.mercedes-benz.com"

CLIENT_ID = "4390b0db-4be9-40e9-9147-5845df537beb"
API_ID = "MCMAPP.FE_PROD"
AUTH_REDIR_URL = "https://cgw.meapp.secure.mercedes-benz.com/endpoint/api/v1/redirect"

ME_STATUS_URL = "{0}/api/v2/appdata".format(URL_USR_API)
CAR_STATUS_URL = "{0}/api/v1/vehicles/%s/dynamic?forceRefresh=true".format(URL_VHS_API)
CAR_LOCAT_URL = "{0}/api/v1/vehicles/%s/location".format(URL_VHS_API)
CAR_DETAIL_URL = "{0}/backend/vehicles/%s/converant".format(URL_VHS_API)
CAR_LOCK_URL = "{0}/api/v1/vehicles/%s/doors/lock".format(URL_VHS_API)
CAR_UNLOCK_URL = "{0}/api/v1/vehicles/%s/doors/unlock".format(URL_VHS_API)
CAR_HEAT_ON_URL = "{0}/api/v1/vehicles/%s/auxheat/start".format(URL_VHS_API)
CAR_HEAT_OFF_URL = "{0}/api/v1/vehicles/%s/auxheat/stop".format(URL_VHS_API)
CAR_FEATURE_URL = "{0}/api/v2/dashboarddata/%s/vehicle".format(URL_USR_API)

CONTENT_TYPE_JSON = "application/json;charset=UTF-8"

ANDROID_USER_AGENT = 'Mozilla/5.0 (Linux; Android 5.1; ' \
                        'Google Nexus 5 Build/LMY47D) AppleWebKit/537.36 ' \
                        '(KHTML, like Gecko) Version/4.0 ' \
                        'Chrome/39.0.0.0 Mobile Safari/537.36'
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
                 excluded_cars, save_car_details):

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
        self.session = requests.session()
        
        _LOGGER.debug("Controller init complete. Start _get_cars")
        self._get_cars()

    def update(self):
        _LOGGER.debug("Update start")
        self._update_cars()

    def lock(self, car_id):
        _LOGGER.debug("lock for %s called", car_id)
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": "Bearer {}".format(self.auth_handler.token_info["access_token"]),
            "country_code": "DE",
            "User-Agent": APP_USER_AGENT
            }
        _LOGGER.debug(self._retrieve_json_at_url(CAR_LOCK_URL % car_id, me_status_header, "post"))
        return True
    
    def unlock(self, car_id, pin):
        _LOGGER.debug("unlock for %s called", car_id)
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": "Bearer {}".format(self.auth_handler.token_info["access_token"]),
            "country_code": "DE",
            "User-Agent": "MercedesMe/2.13.2+639 (Android 5.1)",
            "x-pin": pin
            }
        _LOGGER.debug(self._retrieve_json_at_url(CAR_UNLOCK_URL % car_id, me_status_header, "post"))
        return True

    def heater_on(self, car_id):
        _LOGGER.debug("lock for %s called", car_id)
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": "Bearer {}".format(self.auth_handler.token_info["access_token"]),
            "country_code": "DE",
            "User-Agent": APP_USER_AGENT
            }
        _LOGGER.debug(self._retrieve_json_at_url(CAR_HEAT_ON_URL % car_id, me_status_header, "post"))
        return True

    def heater_off(self, car_id):
        _LOGGER.debug("lock for %s called", car_id)
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": "Bearer {}".format(self.auth_handler.token_info["access_token"]),
            "country_code": "DE",
            "User-Agent": APP_USER_AGENT
            }
        _LOGGER.debug(self._retrieve_json_at_url(CAR_HEAT_OFF_URL % car_id, me_status_header, "post"))
        return True

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
            with open('{0}/feat_{1}.json'.format('/config',car_id), 'w') as outfile:
                json.dump(features, outfile)

        for feature in features.get("metadata").get("featureEnablements"):
            setattr(car_features, 
                    feature.get("name").lower(),
                    feature.get("enablement") == "ACTIVATED")
        
        return car_features

    def _get_initial_tokens(self, username, password):
        session = requests.session()
        code_verifier = self._random_string(64)
        code_challenge = self._generate_code_challenge(code_verifier)

        #Start Login Session - Step 1 call API - Result is 302 redirect to html form
        url_step1 = "{0}/oidc10/auth/oauth/v2/authorize".format(URL_API)
        url_step1 += "?response_type=code&"
        url_step1 += "client_id={0}&".format(CLIENT_ID)
        url_step1 += "code_challenge={0}&".format(code_challenge)
        url_step1 += "code_challenge_method=S256&"
        url_step1 += "scope=mma:backend:all openid ciam-uid profile email&"
        url_step1 += "redirect_uri={0}".format(AUTH_REDIR_URL)

        mb_headers = {'Accept-Language': 'en-US',
                      'X-Requested-With': 'com.daimler.mm.android',
                      'Accept': '*/*',
                      'User-Agent': ANDROID_USER_AGENT
                      }

        session.proxies.update({'https': 'http://localhost:8866' })

        # First we get a 302 redirect to the login server
        login_page = session.get(url_step1, verify=LOGIN_VERIFY_SSL_CERT, headers=mb_headers)

        # Side Step 1.5 - collect additional cookies
        # /wl/third-party-cookie?app-id=MCMAPP.FE_PROD
        # Caution with debug breakpoints here, the cookie life time out of step 1 is short
        sidestep_url = '{0}/wl/third-party-cookie?app-id={1}'.format(URL_LOGIN, API_ID)
        session.get(sidestep_url, verify=LOGIN_VERIFY_SSL_CERT)

        # Get the hidden elements and put them in our form.
        login_html = lxml.html.fromstring(login_page.text)
        hidden_elements = login_html.xpath('//form//input')
        form = {x.attrib['name']: x.attrib['value'] for x in hidden_elements}

        # "Fill out" the form.
        form['username'] = username
        form['password'] = password


        mb_headers = {
            'Accept-Language': 'en-US',
            'X-Requested-With': 'com.daimler.mm.android',
            'Accept': '*/*',
            'User-Agent': ANDROID_USER_AGENT,
            'Referer': login_page.url,
            'Origin' : URL_LOGIN,
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded'
            }

        step_2_url = 'https://login.secure.mercedes-benz.com/wl/login'

        step_2_result = session.post(step_2_url,
                                     data=form,
                                     verify=LOGIN_VERIFY_SSL_CERT,
                                     headers=mb_headers
                                    )

        # Result should be a Webpage with a form, Javascript auto post the form
        # We rebuild the auto post process in Step 3

        # Get the hidden elements and put them in our form.s
        step_2_html = lxml.html.fromstring(step_2_result.text)
        step_3_elements = step_2_html.xpath('//form//input')
        step_3_form = {x.attrib['name']: x.attrib['value'] for x in step_3_elements}
        step_3_url = "{0}/oidc10/auth/oauth/v2/authorize/consent".format(URL_API)

        mb_headers = {
            'Accept-Language': 'en-US', 
            'Accept': '*/*', 
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin' : URL_LOGIN,
            'Referer': step_2_result.url,
            'User-Agent': ANDROID_USER_AGENT,
            'X-Requested-With': 'com.daimler.mm.android'
            }

        # The expected result is a redirect to AUTH_REDIR_URL, 
        # we do not want the redirect, 
        # we are interesseted in the OAuth code only
        # therefore we set allow_redirect to false
        step_3_result = session.post(step_3_url,
                                     data=step_3_form,
                                     verify=LOGIN_VERIFY_SSL_CERT,
                                     headers=mb_headers,
                                     allow_redirects=False)

        if step_3_result.status_code == 302:
            location = urlparse(step_3_result.headers['Location'])
            code = parse_qs(location.query).get("code")

        print(code)

        # Step 4 - Time to get the bearer token :-)
        step_4_url = '{0}/oidc10/auth/oauth/v2/token?'.format(URL_API)
        step_4_url += 'grant_type=authorization_code&'
        step_4_url += 'redirect_uri={0}&'.format(AUTH_REDIR_URL)
        step_4_url += 'client_id={0}&'.format(CLIENT_ID)
        step_4_url += 'code_verifier={0}&'.format(code_verifier.rstrip('='))
        step_4_url += 'code={0}'.format(code[0])

        mb_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'okhttp/3.9.0',
            }


        step_4_result = session.post(step_4_url, 
                                     verify=LOGIN_VERIFY_SSL_CERT, 
                                     headers=mb_headers,
                                     allow_redirects=False,
                                     cookies=None)

        print(step_4_result.text)

    def _retrieve_car_details(self, fin):
        me_status_header = {
            "Accept-Language": self.accept_lang,
            "Authorization": self._get_bearer_token(),
            "country_code": "DE",
            "User-Agent": "MercedesMe/2.13.2+639 (Android 5.1)"
            }

        result = self._retrieve_json_at_url(CAR_STATUS_URL % fin, me_status_header, "get")
        
        if self.save_car_details:
            with open('{0}/state_{1}.json'.format('/config',fin), 'w') as outfile:
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
        if res.status_code != 200 and res.status_code != 403:
            _LOGGER.exception(
                "Connection failed with http code %s", res.status_code)
            return
        if res.status_code == 403:
            _LOGGER.info(
                "Session invalid, will try to relogin, http code %s",
                res.status_code)
            self.is_valid_session = False
            self.session = None
            self.session = requests.session()
            #login
            return
        #_LOGGER.debug("Connect to URL %s Status Code: %s Content: %s", str(url),
        #              str(res.status_code), res.text)
        return res.json()

    def _get_bearer_token(self):
        return "Bearer {}".format(self.auth_handler.token_info["access_token"])

    def _random_string(self, length=64):
        """Generate a random string of fixed length """
        return str(base64.urlsafe_b64encode(urandom(length)), 
                   "utf-8").rstrip('=')

    def _generate_code_challenge(self, code):
        """Generate a hash of the given string """
        m = hashlib.sha256()
        m.update(code.encode("utf-8"))
        return str(base64.urlsafe_b64encode(m.digest()), "utf-8").rstrip('=')
