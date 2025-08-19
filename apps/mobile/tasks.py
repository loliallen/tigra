import logging

from apps.mobile.models import Visit
from server.tasks import app


logger = logging.getLogger(__name__)


@app.task()
def clear_not_confirmed_visits():
    Visit.objects.filter(is_confirmed=False).delete()
