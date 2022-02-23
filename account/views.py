import json

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.hashers import make_password, check_password

from .models import User, Invintation, Child, ApplicationToReset
from .controller import sendCode
from .serializer import InvintationSerializer, CreateUserSerializer
# Create your views here.


UPDATE_FIELDS = ['username', 'first_name', 'last_name', 'email']

class ConfirmPhone(APIView):
    def post(self, request):
        data = request.data

        phone = data.get('phone')

        try:
            user = User.objects.get(phone=phone)
        except:
            return Response({'message': 'Not valid phone number'}, status=403)

        if user.phone_confirmed:
            return Response({'message': 'Phone number alrady confirmed'})

        sendCode(user.phone, user.phone_code)

        return Response({'id': user.pk})

    def get(self, request):
        query = request.query_params
        id = query.get('id')
        code = query.get('code')

        try:
            user = User.objects.get(pk=id)
        except:
            return Response({'message': 'Wrong id'}, status=403)


        if code == user.phone_code:
            user.phone_confirmed = True
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

        invintation = InvintationSerializer(data={ "creator": user.pk })
        if not invintation.is_valid():
            return Response(invintation.errors)

        invintation.save()
        user.my_invintations.add(invintation.data['id'])
        user.save()


        return Response(invintation.data)

    @action(detail=False, methods=['post'])
    def use(self, request):
        code = request.data.get('code')

        try:
            invintation = Invintation.objects.get(value=code, used=False)
        except:
            return Response({'message': 'Code already used of doesn\'t exsits'})

        user = User.objects.get(pk=request.user.id)
        user.used_invintation = invintation
        user.save()
        invintation.used = True
        invintation.save()
        data = InvintationSerializer(invintation)
        return Response(data.data)


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
            user_data = user.first()
            children_data = data['children']
            if isinstance(children_data, str):
                children_data = json.loads(children_data)
            print(children_data)
            for child in children_data:
                print(child)
                if 'updates' in child:
                    child_model = user_data.children.filter(pk=child['id']).update(**child['updates'])
                elif 'delete' in child:
                    user_data.children.filter(pk=child['id']).delete()
                elif 'add' in child:
                    print("hasattr add")
                    _child = Child(**child['data'])
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

        sendCode(user.phone, atr.code)
        return Response({'message': 'The code was sent to your phone', "code": atr.user_code})

    def put(self, request):
        data = request.data
        try:
            atr = ApplicationToReset.objects.get(code=data['code'], user_code=data['user_code'])
        except:
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
        user = User.objects.get(pk=request.user.id)

        data = CreateUserSerializer(user)

        return Response(data.data)

class DeviceTokenView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        data = request.data

        userID = request.user.id
        try:
            user = User.objects.get(pk=userID)
        except:
            return Response({'message': 'User not found, please provide token'}, status=403)
        user.device_token = data['token']
        user.save()

        return Response({'message': "Token updated"})

class UseInvintation(APIView):
    permission_classes=[IsAuthenticated]
    def put(self, request):
        req_data = request.data
        try:
            invintation = Invintation.objects.get(value=req_data.get('code'), used=False)
        except:
            return Response({'message': 'Code already used of doesn\'t exsits'}, status=403)
        data = InvintationSerializer(invintation)
        return Response(data.data)

    def post(self, request):
        req_data = request.data
        userId = request.user.id
        try:
            invintation = Invintation.objects.get(value=req_data.get('code'), used=False)
        except:
            return Response({'message': 'Code already used of doesn\'t exsits'}, status=403)

        user = User.objects.get(pk=userId)
        user.used_invintation = invintation
        user.save()

        invintation.used=True
        invintation.save()
        data = InvintationSerializer(invintation)
        return Response(data.data)
