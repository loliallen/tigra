from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from mobile.serializer import VisitSerializer
from .models import User, Invintation, Child


class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = "__all__"


class InvintationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invintation
        fields = "__all__"

class CreateUserSerializer(UserCreateSerializer):

    visits = VisitSerializer(many=True)
    children = ChildSerializer(many=True)
    used_invintation = InvintationSerializer()
    my_invintations = InvintationSerializer(many=True)

    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        print(validated_data.__dict__)
        code = validated_data.get('inv_code')
        used_invite = None
        print(code)

        if code:
            # TODO rel ref user and created user
            used_invite = Invintation.objects.get(value=code)
            used_invite.used = True
            used_invite.save()


        user = User.objects.create(
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
            device_token=validated_data.get("device_token"),
            phone=validated_data.get('phone'),
            password=make_password(validated_data.get('password')),
            inv_code=validated_data.get('inv_code'),
            used_invintation=used_invite
        )
        # user.children.set(alidated_data.get("children"))
        # send verification code
        sendCode(user.phone, user.phone_code)

        return user
