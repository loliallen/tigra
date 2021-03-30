from django.db import models
from django.contrib.auth.models import AbstractUser

from mobile.models import Visit
# Create your models here.

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
    email = models.TextField(unique=True)
    username = models.TextField(unique=True)
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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

class TmpHash(models.Model):
    hash = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)