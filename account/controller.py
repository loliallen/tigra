import logging
import os

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

SMS_AERO_API_KEY = os.environ.get("SMS_AERO_API_KEY")
SMS_AERO_USERNAME = os.environ.get("SMS_AERO_USERNAME")
SMS_AERO_URL = "https://email:api_key@gate.smsaero.ru/v2/sms/send"


def sendCode(phone, code):
    # for pathing in tests
    _send_code(phone, code)


def _send_code(phone, code):
    custom_params = {
        "number": phone,
        "text":"Your one time code is: {}".format(code),
        "sign": "SMS Aero"
    }
    logger.info(f"send code {code} to {phone}")
    res = requests.get(
        url = SMS_AERO_URL,
        params=custom_params,
        auth=HTTPBasicAuth(SMS_AERO_USERNAME,SMS_AERO_API_KEY)
    )
    body = None
    try:
        body = res.json()
    except:
        pass
    logger.info(f"code sended ({code} to {phone}), response status:{res.status_code}, body:{body}")
