from django.contrib import admin
from .models import PanelConfiguration

@admin.register(PanelConfiguration)
class PanelConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'future_appointments_weight', 
        'age_demographics_weight', 
        'yearly_spend_weight', 
        'consecutive_attendance_weight', 
        'referrer_score_weight', 
        'created_at', 
        'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')
