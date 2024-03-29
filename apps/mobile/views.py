import hashlib
from time import time

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.account.models import User, TmpHash, SchedulerNotify
from apps.account.serializer import VisitSerializer, GetUserSerializer
from .models import Visit
from .serializer import CustomVisitSerializer
from .visits_logic import set_visit_if_free


class VisitListView(APIView):
    permission_classes=[IsAuthenticated, IsAdminUser]

    def get(self, request):
        visits = Visit.objects.filter(staff=request.user, date__gte=timezone.now().date())
        data = CustomVisitSerializer(visits, many=True)
        return Response(data.data)

    def post(self, request):
        data = request.data
        hashStr = data.get('hash')
        try:
            tmpHash = TmpHash.objects.get(hash=hashStr)
        except ObjectDoesNotExist:
            return Response({'message', 'Hash Does Not Exist'}, status=403)
        if not tmpHash.check_lifetime():
            return Response({'message', 'Hash is expired'}, status=403)
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
        SchedulerNotify.send_push_for_visit(visit_obj)
        responseData = VisitSerializer(visit_obj)
        return Response(responseData.data, status=201)



class VisitsView(APIView):
    permission_classes=[IsAuthenticated]
    """
        Get visit qr-code
    """
    def get(self, request):
        tmpHash = TmpHash.objects.filter(user=request.user).first()
        if tmpHash and not tmpHash.check_lifetime():
            tmpHash.delete()
            tmpHash = None
        if tmpHash is None:
            tmpHash = TmpHash(
                user=request.user,
                hash=hashlib.sha512((str(request.user.id) + str(int(time()))).encode()).hexdigest()
            )
            tmpHash.save()
        return Response({'hash': tmpHash.hash})
