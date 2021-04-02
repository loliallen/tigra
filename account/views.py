from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.core.exceptions import ObjectDoesNotExist

from requests.auth import HTTPBasicAuth
import requests


from .models import User, Invintation
from .controller import sendCode
from .serializer import InvintationSerializer, CreateUserSerializer
# Create your views here.

SMS_AERO_API_KEY = "p56Y8j13AhS5mvN1WUXdtDnNeGF"
SMS_AERO_USERNAME = "savrulloevsunrise@gmail.com"
SMS_AERO_URL = "https://email:api_key@gate.smsaero.ru/v2/sms/send"


class ConfirmPhone(APIView):
    def post(self, request):
        data = request.data

        phone = data.get('phone')

        try:
            user = User.objects.get(phone=phone)
        except:
            return Response({'message': 'Not valid phone number'}, status=403)

        if user.confirmed:
            return Response({'message': 'Phone number alrady confirmed'})

        sendCode(user.phone, user.code)

        return Response({'id': user.pk})

    def get(self, request):
        query = request.query_params
        id = query.get('id')
        code = query.get('code')

        try:
            user = User.objects.get(pk=id)
        except:
            return Response({'message': 'Wrong id'}, status=403)


        if code == user.code:
            user.confirmed = True
            user.save()
            return Response({'message': 'Phone number confirmed'})
        return Response({'message': 'Wrong code'}, status=403)


class InvitationsViewSet(ViewSet):
    permission_classes=[IsAuthenticated]
    def list(self, request):
        userId = request.user.id

        user = User.objects.get(pk=userId)

        invintation = InvintationSerializer(user.my_invintations, many=True)

        return Response(invintation.data)

    def create(self, request):
        userId = request.user.id

        user = User.objects.get(pk=userId)

        invintation = InvintationSerializer(data={ "creator": user })
        if not invintation.is_valid():
            return Response(invintation.errors)

        invintation.save()
        user.my_intintations.add(invintation)
        user.save()


        return Response(invintation.data)

class UserModelView(ModelViewSet):
    permission_classes=[IsAuthenticated]
    serializer_class = CreateUserSerializer
    queryset = User.objects.all()

class UserInfo(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user = User.objects.get(pk=request.user.id)

        data = CreateUserSerializer(user)

        return Response(data.data)
