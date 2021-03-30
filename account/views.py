from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

from requests.auth import HTTPBasicAuth
import requests


from .models import User
from .controller import sendCode
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
    


