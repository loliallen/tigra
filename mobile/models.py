from django.db import models

from datetime import datetime


def now():
    return datetime.now()


class Visit(models.Model):
    date = models.DateTimeField(default=now, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    end = models.DateTimeField(default=None, blank=True, null=True)
    is_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(
        to='account.User',
        related_name='visits_user',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )

    staff = models.ForeignKey(
        to='account.User',
        related_name='visits_staff',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )

    def __str__(self):
        date = "~~.~~.~~~~"
        if self.date != None:
            date = self.date
        duration = "~~:~~"
        if self.duration != None:
            duration = self.duration / 60
        return "{} - {} mins".format(date, duration)
