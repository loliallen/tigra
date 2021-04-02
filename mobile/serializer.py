from rest_framework import fields, serializers
from django.core import serializers as django_serializers

from account.models import User
from .models import Visit





class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = "__all__"



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"



class CustomVisitSerializer(serializers.ModelSerializer):
    visiter = UserSerializer(many=True)
    class Meta:
        model = Visit
        fields = "__all__"
