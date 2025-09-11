from .models import ScoringConfiguration
from django.contrib import admin
from .models import (
    BehaviorCategory,
    ScoringBracket,
    Patient,
    PatientBehaviorScore,
    PatientRawData,
    AdminOverride
)

class ScoringBracketInline(admin.TabularInline):
    """Inline editing for scoring brackets (age, spend, strikes, etc.)"""
    model = ScoringBracket
    extra = 1
    fields = ['bracket_min', 'bracket_max', 'points_awarded', 'bracket_order']
    ordering = ['bracket_order']

@admin.register(BehaviorCategory)
class BehaviorCategoryAdmin(admin.ModelAdmin):
    """Configure all behavior categories with sliding scales"""
    list_display = ['name', 'behavior_type', 'scoring_method', 'max_points', 'is_active']
    list_filter = ['behavior_type', 'scoring_method', 'is_active']
    search_fields = ['name', 'description']
    inlines = [ScoringBracketInline]

    fieldsets = (
        ('Basic Configuration', {
            'fields': ('name', 'behavior_type', 'scoring_method', 'is_active')
        }),
        ('Scoring Parameters', {
            'fields': ('max_points', 'description'),
            'description': 'Configure sliding scale values. Max points can be positive or negative.'
        }),
    )

@admin.register(ScoringBracket)
class ScoringBracketAdmin(admin.ModelAdmin):
    """Manage individual scoring brackets"""
    list_display = ['behavior_category', 'bracket_min', 'bracket_max', 'points_awarded', 'bracket_order']
    list_filter = ['behavior_category__behavior_type', 'behavior_category']
    ordering = ['behavior_category', 'bracket_order']

class PatientBehaviorScoreInline(admin.TabularInline):
    """Show individual behavior scores for each patient"""
    model = PatientBehaviorScore
    extra = 0
    readonly_fields = ['calculation_date']
    fields = ['behavior_category', 'raw_data_value', 'calculated_points', 'max_possible_points', 'calculation_date']

class PatientRawDataInline(admin.StackedInline):
    """Edit raw patient data from Cliniko"""
    model = PatientRawData
    fields = (
        ('appointments_booked', 'no_appointments_booked'),
        ('age', 'yearly_spend'),
        ('referrals_made', 'consecutive_attendance_count'),
        ('dna_count', 'cancellation_count'),
        ('has_unpaid_cancellation_fee', 'unpaid_invoice_amount'),
        'last_updated'
    )
    readonly_fields = ['last_updated']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Patient management with A-F rating system"""
    list_display = ['cliniko_patient_id', 'patient_name', 'total_score', 'calculated_rating', 'get_letter_grade', 'override_active', 'last_calculated']
    list_filter = ['calculated_rating', 'override_active', 'last_calculated']
    search_fields = ['cliniko_patient_id', 'patient_name']
    inlines = [PatientRawDataInline, PatientBehaviorScoreInline]

    fieldsets = (
        ('Patient Information', {
            'fields': ('cliniko_patient_id', 'patient_name')
        }),
        ('Scoring Results', {
            'fields': ('total_score', 'calculated_rating', 'last_calculated'),
            'description': 'Calculated scores and ratings'
        }),
        ('Admin Override (Components 24-26)', {
            'fields': ('override_active', 'override_rating'),
            'description': 'Manual rating override - when active, this rating is sent to Cliniko instead of calculated rating'
        }),
    )

    readonly_fields = ['last_calculated']

    def get_letter_grade(self, obj):
        """Display current letter grade"""
        return obj.get_letter_grade()
    get_letter_grade.short_description = 'Current Grade'

@admin.register(AdminOverride)
class AdminOverrideAdmin(admin.ModelAdmin):
    """Track all admin overrides for audit purposes"""
    list_display = ['patient', 'original_rating', 'override_rating', 'admin_user', 'override_date', 'is_active']
    list_filter = ['original_rating', 'override_rating', 'is_active', 'override_date']
    search_fields = ['patient__cliniko_patient_id', 'admin_user', 'reason']
    readonly_fields = ['override_date']

# Custom admin site header
admin.site.site_header = "Patient Behavior Rating App"
admin.site.site_title = "RatedApp Admin"
admin.site.index_title = "Configure Patient Scoring Parameters"



# Register ScoringConfiguration model
@admin.register(ScoringConfiguration)
class ScoringConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Configuration Info', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Positive Behaviors (0-100)', {
            'fields': (
                'future_appointments_weight',
                'age_demographics_weight',
                'yearly_spend_weight',
                'consecutive_attendance_weight',
                'likability_weight'
            )
        }),
        ('Negative Behaviors (0-100)', {
            'fields': (
                'cancellations_weight',
                'dna_weight',
                'unpaid_invoices_weight',
                'open_dna_invoice_weight',
            )
        }),
        ('Configurable Points', {
            'fields': (
                'points_per_cancellation',
                'points_per_unpaid_invoice',                'points_per_dna',
                'points_per_consecutive_attendance'
            ),
            'description': 'Configure points per occurrence (1-10 range)'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

from django.contrib import admin
from .models import RatedAppSettings

@admin.register(RatedAppSettings)
class RatedAppSettingsAdmin(admin.ModelAdmin):
    list_display = ('clinic_name', 'clinic_location', 'clinic_timezone', 'created_at', 'updated_at')
    search_fields = ('clinic_name', 'clinic_location')
    list_filter = ('clinic_timezone',)
