def sendCode(phone, code):
    custom_params = {
        "number": phone,
        "text":"Your one time code is: {}".format(code),
        "sign":"SMS Aero"
    }
    requests.get(
        url = SMS_AERO_URL,
        params=custom_params,
        auth=HTTPBasicAuth(SMS_AERO_USERNAME,SMS_AERO_API_KEY)
    ) #same as Http Basic auth
