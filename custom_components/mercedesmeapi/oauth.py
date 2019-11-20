""" OAuth class.
"""

import base64
import hashlib
import json
import logging
import time
from os import urandom

from urllib.parse import parse_qs, urlparse

import requests
import lxml.html

# Set to False for testing with tools like fiddler
# Change to True for production
LOGIN_VERIFY_SSL_CERT = True
URL_LOGIN = "https://login.secure.mercedes-benz.com"
URL_API = "https://api.secure.mercedes-benz.com"

ANDROID_USERAGENT = 'Mozilla/5.0 (Linux; Android 5.1; ' \
    'Google Nexus 5 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) ' \
    'Version/4.0 Chrome/39.0.0.0 Mobile Safari/537.36'

_LOGGER = logging.getLogger(__name__)


def _make_authorization_headers(client_id, client_secret):
    auth_header = base64.b64encode(
        '{}:{}'.format(client_id, client_secret).encode('utf-8'))
    return {'Authorization': 'Bearer %s' % auth_header.decode('ascii')}


def is_token_expired(token_info):
    now = int(time.time())
    return token_info['expires_at'] - now < 60

class MercedesMeOAuth(object):
    '''
    Implements Authorization for Mercedes Benz's OAuth implementation.
    '''
    OAUTH_BASE_URL = 'https://api.secure.mercedes-benz.com/oidc10/auth/oauth/v2'
    OAUTH_AUTHORIZE_URL = '{}{}'.format(OAUTH_BASE_URL, '/authorize')
    OAUTH_TOKEN_URL = '{}{}'.format(OAUTH_BASE_URL, '/token')

    REDIRECT_SERVER = 'https://cgw.meapp.secure.mercedes-benz.com'
    REDIRECT_URI = '{}/endpoint/api/v1/redirect'.format(REDIRECT_SERVER)

    OAUTH_CLIENT_ID = '4390b0db-4be9-40e9-9147-5845df537beb'
    OAUTH_SCOPE = 'mma:backend:all openid ciam-uid profile email'
    OAUTH_API_ID = "MCMAPP.FE_PROD"

    def __init__(self, user_name, password, accept_lang, cache_path):
        '''
            Creates a MercedesMeOAuth object
        '''
        self.user_name = user_name
        self.password = password
        self.accept_lang = accept_lang
        self.cache_path = cache_path
        self.token_info = None

    def get_cached_token(self):
        ''' Gets a cached auth token
        '''
        _LOGGER.debug("start: %s", __name__)
        token_info = None
        if self.cache_path:
            try:
                token_file = open(self.cache_path)
                token_info_string = token_file.read()
                token_file.close()
                token_info = json.loads(token_info_string)

                if self.is_token_expired(token_info):
                    _LOGGER.debug("%s - token expired - start refresh",
                                  __name__)
                    token_info = self.refresh_access_token(
                        token_info['refresh_token'])

            except IOError:
                pass
        self.token_info = token_info
        return token_info

    def _save_token_info(self, token_info):
        _LOGGER.debug("start: _save_token_info to %s", self.cache_path)
        if self.cache_path:
            try:
                token_file = open(self.cache_path, 'w')
                token_file.write(json.dumps(token_info))
                token_file.close()
            except IOError:
                _LOGGER.warning("couldn't write token cache to %s",
                                self.cache_path)

    def is_token_expired(self, token_info):
        return is_token_expired(token_info)

    def refresh_access_token(self, refresh_token):
        """ Gets the new access token
        """
        _LOGGER.debug("access_token_refresh started - refresh_token: %s",
                      refresh_token)

        headers = {'User-Agent': 'okhttp/3.9.0',
                   'Content-Type': 'application/x-www-form-urlencoded'}

        url = '{}?'.format(self.OAUTH_TOKEN_URL) \
              + 'grant_type=refresh_token&' \
              + 'redirect_uri={}&'.format(self.REDIRECT_URI) \
              + 'client_id={}&'.format(self.OAUTH_CLIENT_ID) \
              + 'refresh_token={}'.format(refresh_token)

        response = requests.post(
            url, data=None,
            headers=headers, verify=LOGIN_VERIFY_SSL_CERT)

        if response.status_code != 200:
            _LOGGER.warning('headers %s', headers)
            _LOGGER.warning('request %s', response.url)
            _LOGGER.warning("couldn't refresh token: code:%s reason:%s",
                            response.status_code, response.reason)
            return None
        token_info = response.json()
        token_info = self._add_custom_values_to_token_info(token_info)
        if not 'refresh_token' in token_info:
            token_info['refresh_token'] = refresh_token
        self._save_token_info(token_info)
        self.token_info = token_info
        return token_info

    def _add_custom_values_to_token_info(self, token_info):
        '''
        Store some values that aren't directly provided by a Web API
        response.
        '''
        token_info['expires_at'] = int(time.time()) + token_info['expires_in']
        token_info['scope'] = self.OAUTH_SCOPE
        return token_info

    def request_initial_token(self):
        session = requests.session()
        code_verifier = self._random_string(64)
        code_challenge = self._generate_code_challenge(code_verifier)

        #Start Login Session - Step 1 call API - Result is 302 redirect
        step1_url = "{0}".format(self.OAUTH_AUTHORIZE_URL) \
                    + "?response_type=code&" \
                    + "client_id={0}&".format(self.OAUTH_CLIENT_ID) \
                    + "code_challenge={0}&".format(code_challenge) \
                    + "code_challenge_method=S256&" \
                    + "scope={}&".format(self.OAUTH_SCOPE) \
                    + "redirect_uri={0}".format(self.REDIRECT_URI)

        step1_headers = {
            'Accept-Language': self.accept_lang,
            'X-Requested-With': 'com.daimler.mm.android',
            'Accept': '*/*',
            'User-Agent': ANDROID_USERAGENT
            }

        #session.proxies.update({'https': 'http://localhost:8866' })

        # First we get a 302 redirect to the login server
        login_page = session.get(step1_url,
                                 verify=LOGIN_VERIFY_SSL_CERT,
                                 headers=step1_headers)

        _LOGGER.debug("Step 1 result: %s", login_page.text)

        # Side Step 1.5 - collect additional cookies
        # /wl/third-party-cookie?app-id=MCMAPP.FE_PROD
        # Caution with debug breakpoints here,
        # the cookie life time out of step 1 is short
        sidestep_url = '{0}/wl/third-party-cookie?app-id={1}'.format(
            URL_LOGIN, self.OAUTH_API_ID)
        session.get(sidestep_url, verify=LOGIN_VERIFY_SSL_CERT)

        # Get the hidden elements and put them in our form.
        login_html = lxml.html.fromstring(login_page.text)
        hidden_elements = login_html.xpath('//form//input')
        form = {x.attrib['name']: x.attrib['value'] for x in hidden_elements}
        form['username'] = self.user_name
        form['password'] = self.password

        step_2_headers = {
            'Accept-Language': self.accept_lang,
            'X-Requested-With': 'com.daimler.mm.android',
            'Accept': '*/*',
            'User-Agent': ANDROID_USERAGENT,
            'Referer': login_page.url,
            'Origin' : URL_LOGIN,
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded'
            }
        step_2_url = 'https://login.secure.mercedes-benz.com/wl/login'
        step_2_result = session.post(step_2_url,
                                     data=form,
                                     verify=LOGIN_VERIFY_SSL_CERT,
                                     headers=step_2_headers
                                     )

        # Result should be a Webpage with a form, Javascript auto post the form
        # We rebuild the auto post process in Step 3

        _LOGGER.debug("Step 2 result: %s", step_2_result.text)

        # Get the hidden elements and put them in our form
        step_2_html = lxml.html.fromstring(step_2_result.text)
        step_3_elements = step_2_html.xpath('//form//input')
        step_3_form = {x.attrib['name']: x.attrib['value']
                       for x in step_3_elements}
        step_3_url = "{0}/consent".format(self.OAUTH_AUTHORIZE_URL)
        step_3_headers = {
            'Accept-Language': self.accept_lang,
            'Accept': '*/*',
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin' : URL_LOGIN,
            'Referer': step_2_result.url,
            'User-Agent': ANDROID_USERAGENT,
            'X-Requested-With': 'com.daimler.mm.android'
            }

        # The expected result is a redirect to AUTH_REDIR_URL,
        # we do not want the redirect,
        # we are interesseted in the OAuth code only
        # therefore we set allow_redirect to false
        step_3_result = session.post(step_3_url,
                                     data=step_3_form,
                                     verify=LOGIN_VERIFY_SSL_CERT,
                                     headers=step_3_headers,
                                     allow_redirects=False)

        if step_3_result.status_code == 302:
            location = urlparse(step_3_result.headers['Location'])
            code = parse_qs(location.query).get("code")

            # Step 4 - Time to get the bearer token :-)
            step_4_url = '{0}?'.format(self.OAUTH_TOKEN_URL) \
                         + 'grant_type=authorization_code&' \
                         + 'redirect_uri={0}&'.format(self.REDIRECT_URI) \
                         + 'client_id={0}&'.format(self.OAUTH_CLIENT_ID) \
                         + 'code_verifier={0}&'.format(code_verifier
                                                       .rstrip('=')) \
                         + 'code={0}'.format(code[0])

            step_4_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'okhttp/3.9.0',
                }
            step_4_result = session.post(step_4_url,
                                         verify=LOGIN_VERIFY_SSL_CERT,
                                         headers=step_4_headers,
                                         allow_redirects=False,
                                         cookies=None)
            _LOGGER.debug("Step 4 result: %s", step_4_result.text)

            token_info = step_4_result.json()
            token_info = self._add_custom_values_to_token_info(token_info)
            _LOGGER.debug("Step 4 - before Token safe: %s", token_info)
            self._save_token_info(token_info)
            self.token_info = token_info
            return token_info
        else:
            _LOGGER.debug("Error getting Access-Token. %s",
                          step_3_result.text)



    def _random_string(self, length=64):
        """Generate a random string of fixed length """
        return str(base64.urlsafe_b64encode(urandom(length)),
                   "utf-8").rstrip('=')

    def _generate_code_challenge(self, code):
        """Generate a hash of the given string """
        code_challenge = hashlib.sha256()
        code_challenge.update(code.encode("utf-8"))
        return str(base64.urlsafe_b64encode(
            code_challenge.digest()), "utf-8").rstrip('=')
