import datetime
import enum
import logging
import random
import typing
from string import digits, ascii_uppercase
from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import signals
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

import server.firebase as fcm
from apps.mobile.models import Visit, FreeReason, now
from apps.mobile.visits_logic import count_to_free_visit as cnt_to_free_visit_logic
from apps.account import tasks

logger = logging.getLogger(__name__)

def createCode():
    return ''.join([random.choice(digits + ascii_uppercase) for i in range(6)])

def createCodeDigits6():
    return ''.join([random.choice(digits) for i in range(6)])

def createCodeDigits4():
    return ''.join([random.choice(digits) for i in range(4)])

SEX_CHOICES = (
    ('F', 'Женский'),
    ('M', 'Мужской'),
)

class Child(models.Model):
    class Meta:
        verbose_name = 'Ребенок'
        verbose_name_plural = 'Дети'

    name = models.TextField(verbose_name='Имя')
    age = models.IntegerField(verbose_name='Возраст (вводится в приложении)')
    sex = models.TextField(choices=SEX_CHOICES, verbose_name='Пол')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения (заполняется сотрудником)')
    my_parent = models.ForeignKey(
        to='account.User',
        related_name='children',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )

    def __str__(self):
        return f"{self.name} ({self.my_parent.last_name} {self.my_parent.first_name})"

    def years(self) -> typing.Optional[int]:
        if self.birth_date is None:
            if self.age is None:
                return None
            return self.age
        today = localtime().date()
        age = today.year - self.birth_date.year -(
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
        return age

    def age_str(self):
        years = self.years()
        if years % 10 == 1:
            return f'{years} год'
        elif years % 10 in [2, 3, 4]:
            return f'{years} года'
        else:
            return f'{years} лет'

    def is_today_birthday(self) -> bool:
        try:
            today = localtime().date()
            return self.birth_date.day == today.day and  self.birth_date.month == today.month
        except:
            return False

    def admin_str(self):
        return (
            f"{self.name} {self.birth_date} "
            f"({self.age_str()})"
            f"{' Cегодня день рождение 🎉' if self.is_today_birthday() else ''}"
        )

    class Meta:
        verbose_name_plural = "Дети"
        verbose_name = "ребенок"


class User(AbstractUser):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        permissions = (
            ('can_change_email', _('Show email field')),
            ('can_change_password', _('Show password field')),
            ('can_see_events', _('Show events sectinos')),
            ('can_change_permissions', _('Show permissions')),
        )

    phone = models.CharField(max_length=12, unique=True, verbose_name='Номер телефона')
    username = models.TextField(default="username", blank=False)
    phone_code = models.CharField(default=createCodeDigits6, blank=True, unique=True, max_length=6, verbose_name='проверочный код телефона')
    phone_confirmed = models.BooleanField(default=False, blank=True, verbose_name='телефон подтвержден')
    device_token = models.TextField(default="", verbose_name="токен устройства для отправки пушей")
    last_mobile_app_visit_date = models.DateField(
        blank=True, null=True, verbose_name='Дата последнего визита в приложение'
    )
    agree_for_video = models.BooleanField(verbose_name="Согласие на видеозапись", default=True)
    agree_for_sms_notifications = models.BooleanField(verbose_name="Согласие смс уведомления", default=True)
    comment_from_staff = models.TextField(verbose_name="Комментарий сотрудника", blank=True, null=True)
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


class AccountDocuments(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='documents')
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    file = models.FileField(verbose_name="Файл", upload_to='user_files/')
    added_by = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, related_name='added_documents')

    class Meta:
        verbose_name_plural = "Документы"
        verbose_name = "Документ"


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
    class Meta:
        verbose_name = "Пуш"
        verbose_name_plural = "Пуши"

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


VARIABLE_CHOICES = (
    ('visit.duration', 'Продолжительность посещения'),
    ('visit.is_free', 'Визит бесплатный?'),
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
    class Meta:
        verbose_name = 'Условие'
        verbose_name_plural = 'Условия'

    variable = models.TextField(choices=VARIABLE_CHOICES, null=False, blank=False, verbose_name='Переменная')
    comparator = models.TextField(choices=COMPARATOR_CHOICES, null=False, blank=False, verbose_name='Тип сравнения')
    value = models.CharField(null=False, blank=False, max_length=100, verbose_name='Значение')
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
    ('start', 'Начало посещения'),
    ('end', 'Конец посещение'),
)


class SchedulerNotify(models.Model):
    class Meta:
        verbose_name = 'Периодический пуш'
        verbose_name_plural = 'Периодические пуши'

    trigger = models.TextField(choices=SCHEDULER_NOTIFY_CHOICES, null=False, blank=False, verbose_name='Событие активации')
    minute_offset = models.IntegerField(default=0, verbose_name='Через сколько минут после события срабатывает')
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
