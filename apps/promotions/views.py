from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PromoBanner


class PromoBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoBanner
        fields = ("name", "image", "link", "hyperlink",)


class BannersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PromoBannerSerializer(PromoBanner.objects.filter(is_active=True), many=True)
        return Response(serializer.data)
