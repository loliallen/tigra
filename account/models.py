import datetime
import enum
import logging
import random
from string import digits, ascii_uppercase
from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import signals

import server.firebase as fcm
from mobile.models import Visit, FreeReason, now
from mobile.visits_logic import count_to_free_visit as cnt_to_free_visit_logic
from account import tasks

logger = logging.getLogger(__name__)

def createCode():
    return ''.join([random.choice(digits + ascii_uppercase) for i in range(6)])

def createCodeDigits6():
    return ''.join([random.choice(digits) for i in range(6)])

def createCodeDigits4():
    return ''.join([random.choice(digits) for i in range(4)])

SEX_CHOICES = (
    ('F', 'female'),
    ('M', 'male'),
)

class Child(models.Model):
    name = models.TextField()
    age = models.IntegerField()
    sex = models.TextField(choices=SEX_CHOICES)
    birth_date = models.DateField(null=True, blank=True)
    my_parent = models.ForeignKey(
        to='account.User',
        related_name='children',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Дети"
        verbose_name = "ребенок"

class User(AbstractUser):
    phone = models.CharField(max_length=12, unique=True)
    username = models.TextField(default="username", blank=False)
    phone_code = models.CharField(default=createCodeDigits6, blank=True, unique=True, max_length=6, verbose_name='проверочный код телефона')
    phone_confirmed = models.BooleanField(default=False, blank=True, verbose_name='телефон подтвержден')
    device_token = models.TextField(default="", verbose_name="токен устройства для отправки пушей")
    used_invintation = models.ForeignKey(
        to='account.Invintation',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True,
        verbose_name="использованный код приглашения",
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = (
        "username",
        "first_name",
        "last_name",
        "device_token",
    )
    OTHER_FIELDS_TO_SEE = (
        "phone",
        "email",
    )
    COMPUTED = (
        "id",
        "phone_confirmed",
        "device_token",
        "phone_code",
        "count_to_free_visit",
        "free_reason",
    )

    @property
    def count_to_free_visit(self) -> int:
        return cnt_to_free_visit_logic(self)[0]

    @property
    def free_reason(self) -> Optional[FreeReason]:
        return cnt_to_free_visit_logic(self)[1]


    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.phone})"


class TmpHash(models.Model):
    LIFETIME = 600  # 10 минут

    hash = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=now)

    def check_lifetime(self):
        return self.created_at > now().astimezone(datetime.timezone.utc) - datetime.timedelta(seconds=TmpHash.LIFETIME)


class ApplicationToReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.CharField(max_length=60)
    code = models.CharField(default=createCode, blank=True, unique=True, max_length=6)
    user_code = models.CharField(default=createCode, blank=True, unique=True, max_length=6)


class Invintation(models.Model):
    value = models.CharField(default=createCodeDigits6, blank=True, unique=True, max_length=6, verbose_name='код')
    creator = models.ForeignKey(
        User,
        related_name='invintation_creator',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )
    used_by = models.ForeignKey(
        User,
        related_name='invintation_used_by',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )
    is_used_by_creator = models.BooleanField(blank=True, default=False, verbose_name='использован создателем')

    @property
    def used(self) -> bool:
        return self.used_by is not None

    @property
    def visited(self) -> bool:
        return bool(self.used_by and self.used_by.visits_user.count() > 0)

    def __str__(self):
        return f"{self.value} ({self.creator.username})"

    class Meta:
        verbose_name_plural = "Пригласительные купоны"
        verbose_name = "пригласительный купон"


class Notification(models.Model):
    title = models.TextField()
    body = models.TextField()
    date_creation = models.DateTimeField(default=datetime.datetime.utcnow)
    to_users = models.ManyToManyField(
        to=User,
        related_name="notifications",
        default=[],
        blank=True
    )
    scheduler = models.ForeignKey('SchedulerNotify', null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = "Уведомления"
        verbose_name = "уведомление"


VARIABLE_CHOICES = (
    ('visit.duration', 'visit duration'),
    ('visit.is_free', 'visit is free'),
)

VARIABLE_TYPE_MAP = {
    'visit.duration': int,
    'visit.is_free': bool,
}


COMPARATOR_CHOICES = (
    ('==', '=='),
    ('>=', '>='),
    ('<=', '<='),
    ('>', '>'),
    ('<', '<'),
)


class Condition(models.Model):
    variable = models.TextField(choices=VARIABLE_CHOICES, null=False, blank=False)
    comparator = models.TextField(choices=COMPARATOR_CHOICES, null=False, blank=False)
    value = models.CharField(null=False, blank=False, max_length=100)
    scheduled_notify = models.ForeignKey(to='account.SchedulerNotify',
                                         related_name="conditions",
                                         on_delete=models.PROTECT,
                                         blank=False,
                                         null=False)

    def compare(self, visit):
        return eval(f'{self.variable} {self.comparator} {self.value}')


class TriggerEnum(enum.Enum):
    ON_START = 'start'
    ON_END = 'end'


SCHEDULER_NOTIFY_CHOICES = (
    ('start', 'on_visit_start'),
    ('end', 'on_visit_end'),
)


class SchedulerNotify(models.Model):
    trigger = models.TextField(choices=SCHEDULER_NOTIFY_CHOICES, null=False, blank=False)
    minute_offset = models.IntegerField(default=0)
    title = models.TextField(null=False, blank=False, default='-')
    body = models.TextField(null=False, blank=False, default='-')

    def check_conditions(self, visit):
        return all(condition.compare(visit) for condition in self.conditions.all())

    @classmethod
    def send_push_for_visit(cls, visit: Visit):
        for scheduled_notify in SchedulerNotify.objects.prefetch_related('conditions').all():
            if scheduled_notify.trigger == TriggerEnum.ON_START.value \
                    and scheduled_notify.check_conditions(visit):
                tasks.send_push.apply_async(
                    args=([visit.user.id], scheduled_notify.title, scheduled_notify.body),
                    countdown=scheduled_notify.minute_offset*60
                )
            if scheduled_notify.trigger == TriggerEnum.ON_END.value \
                    and scheduled_notify.check_conditions(visit):
                tasks.send_push.apply_async(
                    args=([visit.user.id], scheduled_notify.title, scheduled_notify.body),
                    countdown=scheduled_notify.minute_offset * 60 + visit.duration
                )

# callbacks


def create_notification(sender, instance, action, **kwargs):
    if action == "post_add":
        logger.info('create_notification')
        logger.info(f'sender {sender}, instance {instance}, '
                    f'instance.to_users {instance.to_users.all()}, kwargs {kwargs}')
        users = instance.to_users.all()
        tokens = []
        for v in users:
            if len(v.device_token) > 5:
                tokens.append(v.device_token)

        fcm.sendPush(instance.title, instance.body, tokens)
# signals

signals.m2m_changed.connect(receiver=create_notification, sender=Notification.to_users.through)
