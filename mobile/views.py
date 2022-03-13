import hashlib
from time import time

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

import server.firebase as fcm
from account.models import User, TmpHash
from account.serializer import CreateUserSerializer, VisitSerializer, GetUserSerializer
from .models import Visit
from .serializer import CustomVisitSerializer
from .visits_logic import set_visit_if_free

TITLE = "Some notification title"
MSG = "Some msg body lol kek lorem impus"


def dateNowSec():
    return time()

class VisitListView(APIView):
    permission_classes=[IsAuthenticated, IsAdminUser]
    """
        Check user info
    """
    def get(self, request):
        userId = request.user.id
        visits = Visit.objects.filter(staff=userId)
        data = CustomVisitSerializer(visits, many=True)
        return Response(data.data)

    def post(self, request):
        data = request.data
        hashStr = data.get('hash')

        try:
            tmpHash = TmpHash.objects.get(hash=hashStr)
        except ObjectDoesNotExist:
            return Response({'message', 'Hash Does Not Exist'}, status=403)
        user = tmpHash.user
        tmpHash.delete()
        responseData = GetUserSerializer(user)

        return Response(responseData.data)

    def put(self, request):
        data = request.data
        staff = request.user

        userId = data.get('user_id')
        userDuration = int(data.get('duration'))
        try:
            user = User.objects.get(pk=userId)
        except ObjectDoesNotExist:
            return Response({'message', 'User Does Not Exist'}, status=403)

        visit_obj = Visit(
            duration=userDuration,
            staff=staff,
            user=user,
        )
        set_visit_if_free(visit_obj)
        visit_obj.save()
        responseData = VisitSerializer(visit_obj)
        return Response(responseData.data, status=201)



class VisitsView(APIView):
    permission_classes=[IsAuthenticated]
    """
        Get visit qr-code
    """
    def get(self, request):
        userId = request.user.id
        userModel = User.objects.get(pk=userId)
        ts = int(time())
        hash_object = hashlib.sha512((str(userId) + str(ts)).encode())
        hash_str = hash_object.hexdigest()
        tmpHash = None

        tmpHash = TmpHash(
            user=userModel,
            hash=hash_str
        )
        tmpHash.save()

        # img = qrcode.make(hash_str)
        # response = Response(
        #     content_type="image/png",
        # )
        # img.save(response, "PNG")

        return Response({'hash': hash_str})

    def post(self, request):
        userId = request.user.id
        user = None
        try:
            user = User.objects.get(pk=userId, is_staff=True)
        except:
            return Response({'message', 'Staff user not found'}, status=404)

        data = request.data
        forRemove = data.get('forRemove')
        ok = []
        for i in forRemove:
            try:
                visit = Visit.objects.get(pk=i)
                visit.active = False
                visit.save()
                ok.append(str(i))
            except:
                pass
        return Response({'ok', ', '.join(ok)})

class NotitficationView(APIView):
    def post(self, request):
        data = request.data

        fcm.sendPush(data.get('title'), data.get('msg'), data.get('tokens'), data.get('data'))

        return Response({'message': 'Cloud Message sent...'})
