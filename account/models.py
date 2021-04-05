from django.db import models
from django.contrib.auth.models import AbstractUser

from mobile.models import Visit

from string import digits, ascii_uppercase
import random
# Create your models here.

def createCode():
    return ''.join([random.choice(digits + ascii_uppercase) for i in range(6)])

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
    email = models.EmailField()
    username = models.TextField(unique=True)
    phone_code = models.CharField(default=createCode, blank=True, unique=True, max_length=6)
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
        "first_name",
        "last_name",
        "username",
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
    value = models.CharField(default=createCode, blank=True, unique=True, max_length=6)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        default=None,
        null=True
    )
    used = models.BooleanField(blank=True, default=False)
    visited = models.BooleanField(blank=True, default=False)
