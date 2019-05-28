import base64
import hashlib
import json
import logging
import random
import string
import time
import uuid
from os import urandom

from urllib.parse import urlparse, parse_qs
from multiprocessing import RLock

import requests
import lxml.html

_LOGGER = logging.getLogger(__name__)

URL_LOGIN = "https://login.secure.mercedes-benz.com"
URL_API = "https://api.secure.mercedes-benz.com"
URL_VHS_API = "https://vhs.meapp.secure.mercedes-benz.com"
URL_USR_API = "https://usr.meapp.secure.mercedes-benz.com"

CLIENT_ID = "4390b0db-4be9-40e9-9147-5845df537beb"
API_ID = "MCMAPP.FE_PROD"

AUTH_REDIR_URL = "https://cgw.meapp.secure.mercedes-benz.com/endpoint/api/v1/redirect"

LOGIN_VERIFY_SSL_CERT = False

CONTENT_TYPE_JSON = "application/json;charset=UTF-8"


def _randomString(length=64):
    """Generate a random string of fixed length """
    return str(base64.urlsafe_b64encode(urandom(length)), "utf-8").rstrip('=')

def _generate_code_challenge(code):
    """Generate a hash of the given string """
    m = hashlib.sha256()
    m.update(code.encode("utf-8"))
    return str(base64.urlsafe_b64encode(m.digest()), "utf-8").rstrip('=')


username = "mb@nulsch.de"
password = "Mercedes.1587"

session = requests.session()
code_verifier = _randomString(64)
code_challenge = _generate_code_challenge(code_verifier)


#Start Login Session - Step 1 call API - Result is 302 redirect to html form
url_step1 = "{0}/oidc10/auth/oauth/v2/authorize".format(URL_API) \
            + "?response_type=code&" \
            + "client_id={0}&".format(CLIENT_ID) \
            + "code_challenge={0}&".format(code_challenge) \
            + "code_challenge_method=S256&" \
            + "scope=mma:backend:all openid ciam-uid profile email&" \
            + "redirect_uri={0}".format(AUTH_REDIR_URL)



mb_headers = {'Accept-Language': 'en-US', 'X-Requested-With': 'com.daimler.mm.android', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1; Google Nexus 5 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.0.0.0 Mobile Safari/537.36'}

#session.proxies.update({'https': 'http://localhost:8866' })

# First we get a 302 redirect to the login server
login_page = session.get(url_step1, verify=LOGIN_VERIFY_SSL_CERT, headers=mb_headers)

# Side Step 1.5 - collect additional cookies
# /wl/third-party-cookie?app-id=MCMAPP.FE_PROD
# Caution with debug breakpoints here, the cookie life time out of step 1 is short
sidestep_url = '{0}/wl/third-party-cookie?app-id={1}'.format(URL_LOGIN, API_ID)
side_step_result = session.get(sidestep_url, verify=LOGIN_VERIFY_SSL_CERT)

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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 
    'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1; Google Nexus 5 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.0.0.0 Mobile Safari/537.36',
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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 
    'Cache-Control': 'max-age=0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin' : URL_LOGIN,
    'Referer': step_2_result.url,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1; Google Nexus 5 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.0.0.0 Mobile Safari/537.36',
    'X-Requested-With': 'com.daimler.mm.android'
    }

# The expected result is a redirect to AUTH_REDIR_URL, 
# we do not want the redirect, we are interesseted in the OAuth code only
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


tokenSession = requests.session()
#tokenSession.proxies.update({'https': 'http://localhost:8866' })


step_4_result = tokenSession.post(step_4_url, 
                             verify=LOGIN_VERIFY_SSL_CERT, 
                             headers=mb_headers,
                             allow_redirects=False,
                             cookies=None)

print(step_4_result.text)