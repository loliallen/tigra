from rest_framework import serializers
from account.serializer import GetUserSerializer
from .models import Visit


class CustomVisitSerializer(serializers.ModelSerializer):
    visiter = GetUserSerializer(source='user')

    class Meta:
        model = Visit
        fields = "__all__"

    # костыль для обратной совместимости c админским приложением,
    # потому что раньше отношение было ManyToMany
    def to_representation(self, instance):
        data = super(CustomVisitSerializer, self).to_representation(instance)
        data['visiter'] = [data['visiter']]
        return data
