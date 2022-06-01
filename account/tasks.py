import logging
from typing import List

from server.tasks import app
from server import firebase as fcm


logger = logging.getLogger(__name__)


@app.task(max_retries=3)
def send_push(users_id: List[int], title, body):
    from account.models import User
    logger.info(f'users_id: {users_id}, title {title}, body {body}')
    users = User.objects.filter(id__in=users_id)
    tokens = []
    for v in users:
        if len(v.device_token) > 5:
            tokens.append(v.device_token)
    if len(tokens) > 0:
        fcm.sendPush(title, body, tokens)
    else:
        logger.info('no any token for send push notify')
