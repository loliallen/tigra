from rest_framework import serializers

from mobile.serializer import VisitSerializer
from .models import User



class CreateUserSerializer(serializers.ModelSerializer):

    visits = VisitSerializer(many=True)

    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        user = User.objects.create(
            phone=validated_data.get('phone'),
            password=make_password(validated_data.get('password'))
        )
        # send verification code
        sendCode(user.phone, user.code)

        return user
