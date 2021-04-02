from django.contrib import admin
from django.urls import path

from .views import VisitsView, VisitListView, NotitficationView

urlpatterns = [
    path('visits/', VisitsView.as_view()),
    path('visits/add/', VisitListView.as_view()),
    path('push/add/', NotitficationView.as_view())
]
