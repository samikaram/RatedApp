from django.urls import path
from . import views

urlpatterns = [
    path('', views.PatientSearchView.as_view(), name='patient_search'),
    path('search/', views.PatientSearchView.as_view(), name='patient_search'),
    path('patients/<int:patient_id>/analyze/', views.PatientAnalysisView.as_view(), name='patient_analysis'),
    path("dashboard/", views.unified_dashboard, name="unified_dashboard"),
    path('patients/update-likability/', views.UpdateLikabilityView.as_view(), name='update_likability'),
    path("presets/get/", views.get_presets, name="get_presets"),
    path("presets/get/<int:preset_id>/", views.get_preset_details, name="get_preset_details"),
    path("create_preset/", views.create_preset, name="create_preset"),
# Apply Button - Bracket Bulk Operations
    path('age-brackets/clear/', views.clear_age_brackets, name='clear_age_brackets'),
    path('age-brackets/bulk-insert/', views.bulk_insert_age_brackets, name='bulk_insert_age_brackets'),
    path('spend-brackets/clear/', views.clear_spend_brackets, name='clear_spend_brackets'),
    path('spend-brackets/bulk-insert/', views.bulk_insert_spend_brackets, name='bulk_insert_spend_brackets'),
    path('delete-preset/', views.delete_preset, name='delete_preset'),
    path('patients/<int:patient_id>/dashboard-score/', views.PatientDashboardScoreView.as_view(), name='patient_dashboard_score'),
]
