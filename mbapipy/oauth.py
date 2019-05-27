""" OAuth class.
"""

import base64
import json
import time
import sys
import urllib.parse

import requests

from mbapipy import Exceptions as mbmeExc

# Set to False for testing with tools like fiddler
# Change to True for production
LOGIN_VERIFY_SSL_CERT = True

class MercedesMeAuthError(Exception):
    pass


def _make_authorization_headers(client_id, client_secret):
    auth_header = base64.b64encode(
        '{}:{}'.format(client_id, client_secret).encode('utf-8'))
    return {'Authorization': 'Bearer %s' % auth_header.decode('ascii')}


def is_token_expired(token_info):
    now = int(time.time())
    return token_info['expires_at'] - now < 60


class MercedesMeClientCredentials(object):
    OAUTH_TOKEN_URL = "https://api.secure.mercedes-benz.com/oidc10/auth/oauth/v2/token"

    def __init__(self, client_id, client_secret, redirect_uri):
        """
        You have to provide a client_id and client_secret to the
        constructor
        """

        if not client_id:
            raise MercedesMeAuthError('No client id')

        if not client_secret:
            raise mbmeExc.MercedesMeException('No client secret')

        if not redirect_uri:
            raise mbmeExc.MercedesMeException('No redirect_uri')
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_info = None

    def get_access_token(self):
        """
        If a valid access token is in memory, returns it
        Else feches a new token and returns it
        """
        if self.token_info and not self.is_token_expired(self.token_info):
            return self.token_info['access_token']

        token_info = self._request_access_token()
        token_info = self._add_custom_values_to_token_info(token_info)
        self.token_info = token_info
        return self.token_info['access_token']

    def _request_access_token(self):
        """Gets client credentials access token """
        payload = {'grant_type': 'authorization_code',
                   'code': code,
                   'redirect_uri': self.redirect_uri}

        headers = _make_authorization_headers(self.client_id,
                                              self.client_secret)

        response = requests.post(self.OAUTH_TOKEN_URL, data=payload,
                                 headers=headers,
                                 verify=LOGIN_VERIFY_SSL_CERT)

        if response.status_code is not 200:
            raise MercedesMeAuthError(response.reason)
        token_info = response.json()
        return token_info

    def is_token_expired(self, token_info):
        return is_token_expired(token_info)

    def _add_custom_values_to_token_info(self, token_info):
        """
        Store some values that aren't directly provided by a Web API
        response.
        """
        token_info['expires_at'] = int(time.time()) + token_info['expires_in']
        return token_info


class MercedesMeOAuth(object):
    '''
    Implements Authorization Code Flow for Mercedes Benz's OAuth implementation.
    '''
    OAUTH_BASE_URL = 'https://api.secure.mercedes-benz.com/oidc10/auth/oauth/v2'
    OAUTH_AUTHORIZE_URL = '{}{}'.format(OAUTH_BASE_URL, '/authorize')
    OAUTH_TOKEN_URL = '{}{}'.format(OAUTH_BASE_URL, '/token')

    def __init__(self, client_id, client_secret, redirect_uri,
            scope, cache_path):
        '''
            Creates a MercedesMeOAuth object

            Parameters:
                 - client_id - the client id of your app
                 - client_secret - the client secret of your app
                 - redirect_uri - the redirect URI of your app
                 - scope - the desired scope of the request
                 - cache_path - path to location to save tokens
        '''

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.cache_path = cache_path
        self.scope=scope

    def get_cached_token(self):
        ''' Gets a cached auth token
        '''
        token_info = None
        if self.cache_path:
            try:
                f = open(self.cache_path)
                token_info_string = f.read()
                f.close()
                token_info = json.loads(token_info_string)

                if self.is_token_expired(token_info):
                    token_info = self.refresh_access_token(token_info['refresh_token'])

            except IOError:
                pass
        return token_info

    def _save_token_info(self, token_info):
        if self.cache_path:
            try:
                f = open(self.cache_path, 'w')
                f.write(json.dumps(token_info))
                f.close()
            except IOError:
                self._warn("couldn't write token cache to " + self.cache_path)

    def is_token_expired(self, token_info):
        return is_token_expired(token_info)

    def get_authorize_url(self, state=None):
        """ Gets the URL to use to authorize this app
        """
        payload = {'client_id': self.client_id,
                   'response_type': 'code',
                   'redirect_uri': self.redirect_uri,
                   'scope': self.scope}

        urlparams = urllib.parse.urlencode(payload)

        return "%s?%s" % (self.OAUTH_AUTHORIZE_URL, urlparams)

    def parse_response_code(self, url):
        """ Parse the response code in the given response url

            Parameters:
                - url - the response url
        """

        try:
            return url.split("?code=")[1].split("&")[0]
        except IndexError:
            return None

    def _make_authorization_headers(self):
        return _make_authorization_headers(self.client_id, self.client_secret)

    def get_access_token(self, code):
        """ Gets the access token for the app given the code

            Parameters:
                - code - the response code
        """

        payload = {'redirect_uri': self.redirect_uri,
                   'code': code,
                   'grant_type': 'authorization_code'}

        headers = self._make_authorization_headers()

        response = requests.post(self.OAUTH_TOKEN_URL, data=payload,
            headers=headers, verify=LOGIN_VERIFY_SSL_CERT)
        if response.status_code is not 200:
            raise MercedesMeAuthError(response.reason)
        token_info = response.json()
        token_info = self._add_custom_values_to_token_info(token_info)
        self._save_token_info(token_info)
        return token_info

    def refresh_access_token(self, refresh_token):
        payload = { 'refresh_token': refresh_token,
                   'grant_type': 'refresh_token'}

        headers = self._make_authorization_headers()

        response = requests.post(self.OAUTH_TOKEN_URL, data=payload,
            headers=headers,verify=LOGIN_VERIFY_SSL_CERT)
        if response.status_code != 200:
            print('headers', headers)
            print('request', response.url)
            self._warn("couldn't refresh token: code:%d reason:%s" \
                % (response.status_code, response.reason))
            return None
        token_info = response.json()
        token_info = self._add_custom_values_to_token_info(token_info)
        if not 'refresh_token' in token_info:
            token_info['refresh_token'] = refresh_token
        self._save_token_info(token_info)
        return token_info

    def _add_custom_values_to_token_info(self, token_info):
        '''
        Store some values that aren't directly provided by a Web API
        response.
        '''
        token_info['expires_at'] = int(time.time()) + token_info['expires_in']
        token_info['scope'] = self.scope
        return token_info

    def _warn(self, msg):
        print('warning:' + msg, file=sys.stderr)
