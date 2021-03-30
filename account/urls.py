from django.contrib import admin
from django.urls import path, include
from .views import ConfirmPhone


urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('confirm/', ConfirmPhone.as_view()),
]
