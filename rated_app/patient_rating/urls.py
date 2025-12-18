from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .health import healthz

urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("update-clinic-settings/", views.update_clinic_settings, name="update_clinic_settings"),
    path('validate-cliniko-api-key/', views.validate_cliniko_api_key, name='validate_cliniko_api_key'),
    path('', views.PatientSearchView.as_view(), name='patient_search'),
    path('search/', views.PatientSearchView.as_view(), name='patient_search'),
    path('patients/<int:patient_id>/analyze/', views.PatientAnalysisView.as_view(), name='patient_analysis'),
    path("dashboard/", views.unified_dashboard, name="unified_dashboard"),
    path('patients/update-likability/', views.UpdateLikabilityView.as_view(), name='update_likability'),
    path("presets/get/", views.get_presets, name="get_presets"),
    path("presets/get/<int:preset_id>/", views.get_preset_details, name="get_preset_details"),
    path("create_preset/", views.create_preset, name="create_preset"),
    path('age-brackets/clear/', views.clear_age_brackets, name='clear_age_brackets'),
    path('age-brackets/bulk-insert/', views.bulk_insert_age_brackets, name='bulk_insert_age_brackets'),
    path('spend-brackets/clear/', views.clear_spend_brackets, name='clear_spend_brackets'),
    path('spend-brackets/bulk-insert/', views.bulk_insert_spend_brackets, name='bulk_insert_spend_brackets'),
    path('delete-preset/', views.delete_preset, name='delete_preset'),
    path('patients/<int:patient_id>/dashboard-score/', views.PatientDashboardScoreView.as_view(), name='patient_dashboard_score'),
    path('patients/presets/get/', views.get_presets, name='get_presets'),
    path('analytics/config/', views.analytics_config, name='analytics_config'),
    path('analytics/start/', views.analytics_start, name='analytics_start'),
    path('analytics/cancel/', views.analytics_cancel, name='analytics_cancel'),
    path('analytics/status/', views.analytics_status, name='analytics_status'),
    path('analytics/presets/', views.analytics_presets, name='analytics_presets'),
]