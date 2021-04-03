from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from .views import ConfirmPhone, InvitationsViewSet, UserManageView, UserInfo, ResetPasswordView, DeviceTokenView

router = routers.SimpleRouter()
router.register(r'invite', InvitationsViewSet, basename="invite")

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('confirm/', ConfirmPhone.as_view()),
    path('manage/', UserManageView.as_view()),
    path('about/me/', UserInfo.as_view()),
    path('reset_password/', ResetPasswordView.as_view()),
    path('device/', DeviceTokenView.as_view()),
]
