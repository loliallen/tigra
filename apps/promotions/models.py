from django.db import models


class PromoBanner(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField()
    is_active = models.BooleanField(default=False)
    link = models.URLField()
    hyperlink = models.CharField(max_length=255)
