from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

from account.models import User, TmpHash
from account.serializer import CreateUserSerializer
from .serializer import VisitSerializer
from .models import Visit, now
import server.firebase as fcm

import qrcode

import hashlib

# Create your views here.

TITLE = "Some notification title"
MSG = "Some msg body lol kek lorem impus"

class VisitListView(APIView):
    permission_classes=[IsAuthenticated]
    """
        Check user info
    """
    def post(self, request):
        data = request.data
        hashStr = data.get('hash')

        try:
            tmpHash = TmpHash.objects.get(hash=hashStr)
        except ObjectDoesNotExist:
            return Response({'message', 'Hash Does Not Exist'}, status=403)
        user = tmpHash.user
        
        responseData = CreateUserSerializer(user)

        return Response(responseData.data)
    
    def put(self, request):
        data = request.data

        userId = data.get('user_id')
        userDuration = data.get('duration')
        try:
            user = User.objects.get(pk=userId)
        except ObjectDoesNotExist:
            return Response({'message', 'User Does Not Exist'}, status=403)

        
        if user.used_invintation != None and len(user.visits.all()) == 0:
            invite = user.used_invintation
            creator = user.used_invintation.creator
            vis = Visit(
                is_free=True,
                date=None
            )
            vis.save()
            invite.visited = True
            invite.save()
            creator.visits.add(vis)
            # send notification
            fcm.sendPush(title=TITLE, msg=MSG, registration_token=[creator.device_token])


        vis = user.visits.last()
        vis_len = len(user.visits.all())

        if vis != None and vis.duration == None and vis.is_free:
            print("A")
            vis.duration = userDuration
            vis.date = now()
            vis.save()  
        else:
            print("C")
            vis = Visit(
                is_free=False,
                duration=userDuration
            )
            vis.save()
            user.visits.add(vis)
        user.save()

        if (vis_len+2) % 5 == 0:
            print("B")
            vis_ = Visit(
                is_free=True,
                date=None
            )
            vis_.save()
            user.visits.add(vis_)

        responseData = VisitSerializer(vis)

        return Response(responseData.data, status=201)
        


class VisitsView(APIView):
    permission_classes=[IsAuthenticated]
    """
        Get visit qr-code
    """
    def get(self, request):
        userId = request.user.id
        userModel = User.objects.get(pk=userId)

        hash_object = hashlib.sha512(str(userId).encode())
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


class NotitficationView(APIView):
    def post(self, request):
        data = request.data

        fcm.sendPush(data.get('title'), data.get('msg'), data.get('tokens'))

        return Response({'message': 'Cloud Message sent...'})