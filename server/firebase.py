import logging
import os
import firebase_admin
from firebase_admin import credentials, messaging


logger = logging.getLogger(__name__)

cred_abs_path = os.environ.get('FIREBASE_CRED', "creds.json")
if not os.path.exists(cred_abs_path):
    logger.warning('creds for firebase isn\'t exists')
else:
    cred = credentials.Certificate(cred_abs_path)
    app = firebase_admin.initialize_app(cred)


def sendPush(title, msg, registration_tokens, dataObject = None):
    logger.info(f'trying to send push {title}: {msg},  {registration_tokens},  {dataObject}')
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=msg
        ),
        data=dataObject,
        tokens=registration_tokens
    )
    response = messaging.send_multicast(message)
    data = [{attr: getattr(item, attr, None) for attr in ['success', '_exception', 'message_id']} for item in response.responses]
    logger.info(f'data {data}')
