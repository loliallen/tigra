from django.contrib import admin
from django.urls import path

from .views import VisitsView, VisitListView

urlpatterns = [
    path('visits/', VisitsView.as_view()),
    path('visits/add/', VisitListView.as_view()),
]
