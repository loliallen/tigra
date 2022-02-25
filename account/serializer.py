from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from mobile.serializer import VisitSerializer
from .models import User, Invintation, Child

from djoser.conf import settings as djoser_settings


class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = "__all__"


class InvintationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invintation
        fields = "__all__"


class GetUserSerializer(UserSerializer):
    visits = serializers.ListField(source='visits_user', child=VisitSerializer(many=True))


class CreateUserSerializer(UserCreateSerializer):

    visits = VisitSerializer(source='visits_user', many=True, read_only=True)
    children = ChildSerializer(many=True, read_only=True)
    used_invintation = InvintationSerializer(read_only=True)
    my_invintations = InvintationSerializer(source='invintation_set', many=True, read_only=True)
    inv_code = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        READ_ONLY = ("visits", "children", "used_invintation", "my_invintations")
        fields = tuple(User.REQUIRED_FIELDS) + (
            djoser_settings.LOGIN_FIELD,
            djoser_settings.USER_ID_FIELD,
            "password", "inv_code"
        ) + READ_ONLY

    def validate(self, attrs):
        # Костыль, чтобы inv_code не попал в User при валидации
        self.invintation_code = attrs.pop('inv_code', None)
        return super(CreateUserSerializer, self).validate(attrs)

    def create(self, validated_data):
        used_invite = None

        if self.invintation_code:
            used_invite = Invintation.objects.get(value=self.invintation_code)
            used_invite.used = True
            used_invite.save()

        password = make_password(validated_data.pop('password'))
        user = User.objects.create(
            **validated_data,
            password=password,
            used_invintation=used_invite
        )
        return user
