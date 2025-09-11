from django.urls import path
from . import views

urlpatterns = [
    path('', views.PatientSearchView.as_view(), name='patient_search'),
    path('search/', views.PatientSearchView.as_view(), name='patient_search'),
    path('patients/<int:patient_id>/analyze/', views.PatientAnalysisView.as_view(), name='patient_analysis'),
    path("dashboard/", views.unified_dashboard, name="unified_dashboard"),
    path('patients/update-likability/', views.UpdateLikabilityView.as_view(), name='update_likability'),
    path('patients/update-unlikability/', views.UpdateUnlikabilityView.as_view(), name='update_unlikability'),
]
