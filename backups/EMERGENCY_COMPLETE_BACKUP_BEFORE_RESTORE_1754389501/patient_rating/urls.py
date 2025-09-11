from django.urls import path
from . import views

app_name = 'patient_rating'

urlpatterns = [
    path('dashboard/', views.unified_dashboard, name='unified_dashboard'),
]
