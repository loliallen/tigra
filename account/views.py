from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.hashers import make_password, check_password

from requests.auth import HTTPBasicAuth
import requests


from .models import User, Invintation, Child, ApplicationToReset
from .controller import sendCode
from .serializer import InvintationSerializer, CreateUserSerializer
# Create your views here.

SMS_AERO_API_KEY = "p56Y8j13AhS5mvN1WUXdtDnNeGF"
SMS_AERO_USERNAME = "savrulloevsunrise@gmail.com"
SMS_AERO_URL = "https://email:api_key@gate.smsaero.ru/v2/sms/send"


UPDATE_FIELDS = ['username', 'first_name', 'last_name', 'email']

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


class UserManageView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        userID = request.user.id
        user = User.objects.get(pk=userID)
        user = CreateUserSerializer(user)

        return Response(user.data)

    def put(self, request):
        userID = request.user.id

        data = request.data
        validated_data = {}
        for field in UPDATE_FIELDS:
            if field in data:
                validated_data[field] = data[field]

        user = User.objects.filter(pk=userID)

        user.update(**validated_data)

        if 'old_password' in data and 'password' in data:
            user_data = user.first()
            old_password = data['old_password']
            if check_password(old_password, user_data.password):
                new_password = make_password(data['password'])
                user_data.password = new_password
                user_data.save()

        if 'children' in data:
            children_data = data['children']
            for child in children_data:
                if hasattr(child, 'updates'):
                    child_model = Child.objects.filter(pk=child.id).update(**child.updates)
                if hasattr(child, 'delete'):
                    Child.objects.filter(pk=child.id).delete()
                if hasattr(child, 'add'):
                    user_data = user.first()
                    _child = Child(**child.data)
                    _child.save()
                    user_data.children.add(_child)
                    user_data.save()

        user_data = CreateUserSerializer(user.first())

        return Response(user_data.data)


class ResetPasswordView(APIView):
    def get(self, request):
        params = request.query_params
        code = params['code']
        try:
            atr = ApplicationToReset.objects.get(code=code)
        except:
            return Response({'message': 'Code is invalid'}, status=400)
        return Response({'message': 'Code is valid'}, status=200)


    def post(self, request):
        data = request.data
        phone = data['phone']

        try:
            user = User.objects.get(phone=phone)
        except:
            return Response({'message': 'User with phone {} not found'.format(phone)}, status=400)
        atr = ApplicationToReset(
            user=user,
            field="password"
        )
        atr.save()

        sendCode(phone, atr.code)
        return Response({'message': 'The code was sent to your phone', code: atr.user_code})

    def put(self, request):
        data = request.data
        try:
            atr = ApplicationToReset.objects.get(code=data['code'], user_code=data['usercode'])
        except:
            return Response({'message': 'Not valid codes'}, status=400)

        user = atr.user
        password = data['password']

        user.password = make_password(password)
        user.save()
        return Response({'message': 'New password is set'})


class UserInfo(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        user = User.objects.get(pk=request.user.id)

        data = CreateUserSerializer(user)

        return Response(data.data)
