from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from .views import ConfirmPhone, InvitationsViewSet, UserModelView

inv_list = InvitationsViewSet.as_view({ 'get': 'list'})
inv_create = InvitationsViewSet.as_view({ 'post': 'create'})

router = routers.SimpleRouter()
router.register(r'invite', InvitationsViewSet, basename="invite")
router.register(r'manage', UserModelView, basename="user")

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('confirm/', ConfirmPhone.as_view()),
]
