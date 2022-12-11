from django.urls import path

from .views import BannersView

urlpatterns = [
    path('banner/', BannersView.as_view()),
]
