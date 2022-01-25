# import time
# from datetime import timedelta
# from uuid import uuid4
import logging
import os
import firebase_admin
from firebase_admin import credentials, messaging


logger = logging.getLogger(__name__)

cred_abs_path = os.environ.get('FIREBASE_CRED', "creds.json")
cred = credentials.Certificate(cred_abs_path)
app = firebase_admin.initialize_app(cred)


def sendPush(title, msg, registration_token, dataObject = None):
    logger.info('trying to send push')
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        data=dataObject,
        tokens=registration_token
    )
    response = messaging.send_multicast(message)
    data = [{attr: getattr(item, attr, None) for attr in ['success', '_exception', 'message_id']} for item in response.responses]
    logger.info(f'data {data}')
    # logger.info(f'push server response {i.sucess}')
