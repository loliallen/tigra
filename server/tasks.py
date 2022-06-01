import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

broker = os.environ.get('CELERY_RABBIT_ADDRESS', default='pyamqp://rabbitmq:rabbitmq@127.0.0.1:5672//')
app = Celery('tigra', broker=broker)

app.config_from_object('django.conf:settings')
app.autodiscover_tasks()



