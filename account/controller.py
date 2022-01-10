import os

import requests
from requests.auth import HTTPBasicAuth

SMS_AERO_API_KEY = os.environ.get("SMS_AERO_API_KEY")
SMS_AERO_USERNAME = os.environ.get("SMS_AERO_USERNAME")
SMS_AERO_URL = "https://email:api_key@gate.smsaero.ru/v2/sms/send"


def sendCode(phone, code):
    # for pathing in tests
    _send_code(phone, code)


def _send_code(phone, code):
    print('sendCode called')
    custom_params = {
        "number": phone,
        "text":"Your one time code is: {}".format(code),
        "sign":"SMS Aero"
    }
    res = requests.get(
        url = SMS_AERO_URL,
        params=custom_params,
        auth=HTTPBasicAuth(SMS_AERO_USERNAME,SMS_AERO_API_KEY)
    ) #same as Http Basic auth
    print(res.status_code)
