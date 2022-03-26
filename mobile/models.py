from datetime import datetime, timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _


def now():
    return datetime.now()


class FreeReason(models.TextChoices):
    COUNT = 'CNT', _('Count')  # каждое n-ое посещение бесплатно
    INVITE = 'INV', _('Invite')  # за приглашение посещение бесплатно


class Visit(models.Model):
    date = models.DateTimeField(default=now, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True, verbose_name="Продолжительность")  # почему то хранится в секундах _/('_')\_
    is_free = models.BooleanField(default=False, verbose_name="Бесплатный")
    free_reason = models.CharField(max_length=255, choices=FreeReason.choices, null=True,
                                   verbose_name="Причина бесплатного визита")
    is_active = models.BooleanField(default=True)  # deprecated
    user = models.ForeignKey(
        to='account.User',
        related_name='visits_user',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True,
        verbose_name = "Пользователь",
    )
    staff = models.ForeignKey(
        to='account.User',
        related_name='visits_staff',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True,
        verbose_name="Сотрудник",
    )

    @property
    def end(self):
        return (self.date + timedelta(seconds=self.duration or 0)).astimezone() if self.date else None

    def __str__(self):
        return f"{self.date or '~~.~~.~~~~'} - {self.duration and self.duration / 60 or '~~:~~'} mins"

    class Meta:
        verbose_name_plural = "Визиты"
        verbose_name = "визит"
