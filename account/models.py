from django.db import models
from django.db.models import signals
from django.contrib.auth.models import AbstractUser

from mobile.models import Visit

from string import digits, ascii_uppercase
import random
# Create your models here.

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



class User(AbstractUser):
    phone = models.CharField(max_length=12, unique=True)
    username = models.TextField(default="username", blank=False)
    phone_code = models.CharField(default=createCodeDigits6, blank=True, unique=True, max_length=6)
    phone_confirmed = models.BooleanField(default=False, blank=True)
    device_token = models.TextField(default="")
    used_invintation = models.ForeignKey(
        to='account.Invintation',
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )
    my_invintations = models.ManyToManyField(
        to='account.Invintation',
        related_name="creator_user",
        default=[],
        blank=True
    )
    children = models.ManyToManyField(
        to=Child,
        related_name="parent",
        default=[],
        blank=True
    )
    visits = models.ManyToManyField(
        to=Visit,
        related_name="visiter",
        default=[],
        blank=True
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = (
        "username",
        "first_name",
        "last_name",
        "device_token",
    )

class TmpHash(models.Model):
    hash = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class ApplicationToReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.CharField(max_length=60)
    code = models.CharField(default=createCode, blank=True, unique=True, max_length=6)
    user_code = models.CharField(default=createCode, blank=True, unique=True, max_length=6)

class Invintation(models.Model):
    value = models.CharField(default=createCodeDigits6, blank=True, unique=True, max_length=6)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )
    used = models.BooleanField(blank=True, default=False)
    visited = models.BooleanField(blank=True, default=False)

class Notification(models.Model):
    title = models.TextField()
    body = models.TextField()
    to_users = models.ManyToManyField(
        to=User,
        related_name="notifications",
        default=[],
        blank=True
    )

# callbacks

def create_notification(sender, instance, action, **kwargs):
    if action == "post_add":
        print('sender', sender)
        print('instance', instance)
        print('instance.to_users', instance.to_users.all())
        print('kwargs', kwargs)
        title = instance.title
        body = instance.body
        users = instance.to_users.all()
        tokens = []
        for k, v in users.items():
            tokens.append(v.device_token)

        fcm.sendPush(title, body, tokens)
# signals

signals.m2m_changed.connect(receiver=create_notification, sender=Notification.to_users.through)
