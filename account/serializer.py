import logging

from djoser.conf import settings as djoser_settings
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from account.models import User, Invintation, Child
from mobile.models import Visit

logger = logging.getLogger(__name__)


class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = ("id", "name", "age", "sex")


class InvintationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invintation
        fields = ("id", "creator", "value", "used", "visited")


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ("id", "date", "duration", "end", "is_free", "free_reason", "is_active", "staff")


class GetUserSerializer(UserSerializer):
    visits = VisitSerializer(source='visits_user', many=True)
    children = ChildSerializer(many=True, read_only=True)
    used_invintation = InvintationSerializer(read_only=True)
    my_invintations = InvintationSerializer(source='invintation_creator', many=True, read_only=True)

    class Meta:
        model = User
        fields = User.REQUIRED_FIELDS + User.OTHER_FIELDS_TO_SEE + User.COMPUTED + (
            "visits", "children", "used_invintation", "my_invintations",
            # выпилить когда фронт перестанет его использовать
            # ----
            "password", djoser_settings.LOGIN_FIELD, djoser_settings.USER_ID_FIELD,
            "is_superuser", "phone_code", "phone_confirmed", "is_staff", "is_active", "date_joined", "last_login", "groups", "user_permissions"
            # ----
        )
        read_only_fields = fields


class CreateUserSerializer(UserCreateSerializer):
    code = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            djoser_settings.LOGIN_FIELD,
            djoser_settings.USER_ID_FIELD,
            "password", "code"
        )

    def validate(self, attrs):
        # Костыль, чтобы inv_code не попал в User при валидации
        self.invintation_code = attrs.pop('code', None)
        return super(CreateUserSerializer, self).validate(attrs)

    def create(self, validated_data):
        used_invite = None
        logger.info(f'validated_data: {validated_data}')
        if self.invintation_code:
            used_invite = Invintation.objects.filter(value=self.invintation_code, used_by=None).first()
            if used_invite is None:
                logger.info('Пригласительный купон не найден')
                raise ValueError('Пригласительный купон не найден')
        user = super().create({**validated_data, 'used_invintation': used_invite})
        logger.info(f'User created')

        if used_invite:
            used_invite.used_by = user
            used_invite.save()
        return user


class UpdateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')