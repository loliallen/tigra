from django.db import models

from datetime import datetime
import pytz

# Create your models here.

def now():
    return datetime.now()

class Visit(models.Model):
    date = models.DateTimeField(default=now, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    is_free = models.BooleanField(default=False)
