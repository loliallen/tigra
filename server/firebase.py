# import time
# from datetime import timedelta
# from uuid import uuid4

import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("/home/loliallen/Documents/Projects/tigra/server/creds.json")
app = firebase_admin.initialize_app(cred)


def sendPush(title, msg, registration_token, dataObject = None):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        data=dataObject,
        tokens=registration_token
    )

    response = messaging.send_multicast(message)
    print('Messages sent', response)