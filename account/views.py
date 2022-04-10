import json

from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from account.controller import sendCode
from account.models import User, Invintation, Child, ApplicationToReset
from account.serializer import InvintationSerializer, CreateUserSerializer, GetUserSerializer, UpdateUserSerializer

UPDATE_FIELDS = ['username', 'first_name', 'last_name', 'email']


class ConfirmPhone(APIView):

    def post(self, request):
        data = request.data
        phone = data.get('phone')
        user = User.objects.filter(phone=phone).first()
        if user is None:
            return Response({'message': 'Not valid phone number'}, status=403)
        if user.phone_confirmed:
            return Response({'message': 'Phone number already confirmed'})
        # TODO: тут надо записывать послднее время отправки, чтобы не спамить и себе деньги на смс не тратить
        sendCode(user.phone, user.phone_code)
        return Response({'id': user.pk})

    def get(self, request):
        query = request.query_params
        id = query.get('id')
        code = query.get('code')
        user = User.objects.filter(id=id).first()
        if user is None:
            return Response({'message': 'Wrong id'}, status=403)
        if code == user.phone_code:
            user.phone_confirmed = True
            user.save()
            return Response({'message': 'Phone number confirmed'})
        return Response({'message': 'Wrong code'}, status=403)


class InvitationsViewSet(ViewSet):
    permission_classes=[IsAuthenticated]

    def list(self, request):
        invintation = InvintationSerializer(request.user.invintation_creator, many=True)
        return Response(invintation.data)

    def create(self, request):
        user = request.user
        invintation = InvintationSerializer(data={"creator": user.id})
        if not invintation.is_valid():
            return Response(invintation.errors)
        invintation.save()
        return Response(invintation.data)


class UserManageView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        user = CreateUserSerializer(request.user)
        return Response(user.data)

    def put(self, request):
        children = request.data.get('children')
        user_serializer = UpdateUserSerializer(data=request.data)
        user = request.user
        user_serializer.instance = user
        if user_serializer.is_valid():
            if children:
                if isinstance(children, str):
                    children = json.loads(children)
                for child in children:
                    if 'updates' in child:
                        user.children.filter(pk=child['id']).update(**child['updates'])
                    elif 'delete' in child:
                        user.children.filter(pk=child['id']).delete()
                    elif 'add' in child:
                        Child(**child['data'], my_parent=user).save()
            user_serializer.save()
            user = GetUserSerializer(user)
            return Response(user.data)
        return Response({'message': user_serializer.errors})


class ResetPasswordView(APIView):
    def get(self, request):
        if ApplicationToReset.objects.filter(code=request.query_params['code']).first() is not None:
            return Response({'message': 'Code is valid'}, status=200)
        return Response({'message': 'Code is invalid'}, status=400)

    def post(self, request):
        phone = request.data['phone']
        user = User.objects.filter(phone=phone).first()
        if user is None:
            return Response({'message': 'User with phone {} not found'.format(phone)}, status=400)
        atr = ApplicationToReset(
            user=user,
            field="password"
        )
        atr.save()
        # TODO: писать время последей отправленной смс чтобы не спамить слишком часто
        sendCode(user.phone, atr.code)
        return Response({'message': 'The code was sent to your phone', "code": atr.user_code})

    def put(self, request):
        data = request.data
        atr = ApplicationToReset.objects.filter(code=data['code'], user_code=data['user_code']).first()
        if atr is None:
            return Response({'message': 'Not valid codes'}, status=400)
        user = atr.user
        password = data['password']
        user.password = make_password(password)
        user.save()
        atr.delete()
        return Response({'message': 'New password is set'})


class UserInfo(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        data = GetUserSerializer(request.user)
        return Response(data.data)

class DeviceTokenView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request):
        user = request.user
        user.device_token = request.data['token']
        user.save()
        return Response({'message': "Token updated"})


class UseInvintation(APIView):
    permission_classes=[]

    def put(self, request):
        # TODO: удалить этот метод когда фронт перестанет его использовать
        req_data = request.data
        try:
            invintation = Invintation.objects.get(value=req_data.get('code'), used_by=None)
        except:
            return Response({'message': 'Code already used or doesn\'t exsits'}, status=403)
        data = InvintationSerializer(invintation)
        return Response(data.data)

    def post(self, request):
        # TODO: удалить этот метод когда фронт перестанет его использовать
        req_data = request.data
        try:
            invintation = Invintation.objects.get(value=req_data.get('code')) #, used_by__isnull=False)
        except:
            return Response({'message': 'Code already used of doesn\'t exsits'}, status=403)
        data = InvintationSerializer(invintation)
        return Response(data.data)
