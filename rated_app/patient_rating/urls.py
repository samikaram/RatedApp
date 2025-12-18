from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import path
from . import views
from .health import healthz

def home(request):
    return redirect("unified_dashboard")

urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("update-clinic-settings/", login_required(views.update_clinic_settings), name="update_clinic_settings"),
    path("validate-cliniko-api-key/", login_required(views.validate_cliniko_api_key), name="validate_cliniko_api_key"),

    path("", login_required(home), name="home"),
    path("search/", login_required(views.PatientSearchView.as_view()), name="patient_search"),
    path("patients/<int:patient_id>/analyze/", login_required(views.PatientAnalysisView.as_view()), name="patient_analysis"),

    path("dashboard/", login_required(views.unified_dashboard), name="unified_dashboard"),
    path("patients/update-likability/", login_required(views.UpdateLikabilityView.as_view()), name="update_likability"),

    path("presets/get/", login_required(views.get_presets), name="get_presets"),
    path("presets/get/<int:preset_id>/", login_required(views.get_preset_details), name="get_preset_details"),
    path("create_preset/", login_required(views.create_preset), name="create_preset"),

    path("age-brackets/clear/", login_required(views.clear_age_brackets), name="clear_age_brackets"),
    path("age-brackets/bulk-insert/", login_required(views.bulk_insert_age_brackets), name="bulk_insert_age_brackets"),
    path("spend-brackets/clear/", login_required(views.clear_spend_brackets), name="clear_spend_brackets"),
    path("spend-brackets/bulk-insert/", login_required(views.bulk_insert_spend_brackets), name="bulk_insert_spend_brackets"),

    path("delete-preset/", login_required(views.delete_preset), name="delete_preset"),
    path("patients/<int:patient_id>/dashboard-score/", login_required(views.PatientDashboardScoreView.as_view()), name="patient_dashboard_score"),
    path("patients/presets/get/", login_required(views.get_presets), name="get_presets"),

    path("analytics/config/", login_required(views.analytics_config), name="analytics_config"),
    path("analytics/start/", login_required(views.analytics_start), name="analytics_start"),
    path("analytics/cancel/", login_required(views.analytics_cancel), name="analytics_cancel"),
    path("analytics/status/", login_required(views.analytics_status), name="analytics_status"),
    path("analytics/presets/", login_required(views.analytics_presets), name="analytics_presets"),
]
