from rest_framework import fields, serializers
from django.core import serializers as django_serializers 

from .models import Visit

class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = "__all__"