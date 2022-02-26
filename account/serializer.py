from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from mobile.serializer import VisitSerializer
from .models import User, Invintation, Child

from djoser.conf import settings as djoser_settings


class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = ("id", "name", "age", "sex")


class InvintationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invintation
        fields = ("id", "creator", "value", "used", "visited")


class GetUserSerializer(UserSerializer):
    visits = VisitSerializer(source='visits_user', many=True)
    children = ChildSerializer(many=True, read_only=True)
    used_invintation = InvintationSerializer(read_only=True)
    my_invintations = InvintationSerializer(source='invintation_set', many=True, read_only=True)

    class Meta:
        model = User
        fields = User.REQUIRED_FIELDS + User.OTHER_FIELDS_TO_SEE + User.COMPUTED + (
            "visits", "children", "used_invintation", "my_invintations"
        )
        read_only_fields = fields


class CreateUserSerializer(UserCreateSerializer):
    inv_code = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            djoser_settings.LOGIN_FIELD,
            djoser_settings.USER_ID_FIELD,
            "password", "inv_code"
        )

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
