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
    visiter = UserSerializer(source='user')

    class Meta:
        model = Visit
        fields = "__all__"

    # костыль для обратной совместимости c админским приложением,
    # потому что раньше отношение было ManyToMany
    def to_representation(self, instance):
        data = super(CustomVisitSerializer, self).to_representation(instance)
        data['visiter'] = [data['visiter']]
        return data
