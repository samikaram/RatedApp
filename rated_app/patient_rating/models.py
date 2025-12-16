from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils import timezone

# Software Integration Choices
SOFTWARE_CHOICES = [
    ('cliniko', 'Cliniko'),
    ('pracsuite', 'PracSuite'),
    # Future software options can be added here
]

AUTH_TYPES = [
    ('basic', 'Basic Authentication'),
    ('oauth2', 'OAuth 2.0'),
    ('api_key', 'API Key')
]


class BehaviorCategory(models.Model):
    """Configurable behavior categories with sliding scale parameters"""
    BEHAVIOR_TYPES = [
        ('positive', 'Positive Behavior'),
        ('negative', 'Negative Behavior'),
    ]
    
    SCORING_METHODS = [
        ('boolean', 'True/False'),
        ('bracket', 'Bracket-based'),
        ('incremental', 'Accumulative'),
        ('strike', 'Strike System'),
        ('manual_input', 'Manual Input (0-100)'),
    ]
    
    name = models.CharField(max_length=100)
    behavior_type = models.CharField(max_length=10, choices=BEHAVIOR_TYPES)
    scoring_method = models.CharField(max_length=20, choices=SCORING_METHODS)
    max_points = models.IntegerField(validators=[MinValueValidator(-100), MaxValueValidator(100)])
    is_active_for_scoring = models.BooleanField(default=True)
    is_active_for_analytics = models.BooleanField(default=True, help_text="Active for analytics processing")
    description = models.TextField(blank=True)

    # Connectivity Settings
    software_integration = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Software Integration"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="API Key"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_behavior_type_display()})"

class ScoringBracket(models.Model):
    """Configurable brackets for age, spend, referrals, strikes"""
    behavior_category = models.ForeignKey(BehaviorCategory, on_delete=models.CASCADE, related_name='brackets')
    bracket_min = models.DecimalField(max_digits=10, decimal_places=2)
    bracket_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    points_awarded = models.IntegerField()
    bracket_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['bracket_order']
    
    def __str__(self):
        if self.bracket_max:
            return f"{self.behavior_category.name}: {self.bracket_min}-{self.bracket_max} = {self.points_awarded}pts"
        return f"{self.behavior_category.name}: {self.bracket_min}+ = {self.points_awarded}pts"

class Patient(models.Model):
    """Patient data from Cliniko integration"""
    cliniko_patient_id = models.CharField(max_length=50, unique=True)
    patient_name = models.CharField(max_length=200, blank=True)
    total_score = models.IntegerField(default=0)
    calculated_rating = models.CharField(max_length=1, blank=True)
    override_active = models.BooleanField(default=False)
    override_rating = models.CharField(max_length=1, blank=True)
    last_calculated = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Individual patient attributes (manual input, default 0)
    likability = models.IntegerField(default=0, validators=[MinValueValidator(-100), MaxValueValidator(100)], help_text="Patient likability score from -100 (very unlikable) to +100 (very likable)")
    
    def get_letter_grade(self):
        """Convert total score to A+ through F rating"""
        if self.override_active and self.override_rating:
            return self.override_rating
        
        score = self.total_score
        if score > 100:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 40:
            return 'C'
        elif score >= 20:
            return 'D'
        elif score >= 0:
            return 'E'
        else:
            return 'F'
    
    def __str__(self):
        return f"Patient {self.cliniko_patient_id} - {self.get_letter_grade()} ({self.total_score}pts)"

class PatientBehaviorScore(models.Model):
    """Individual behavior scores for each patient"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='behavior_scores')
    behavior_category = models.ForeignKey(BehaviorCategory, on_delete=models.CASCADE)
    raw_data_value = models.TextField()  # Store actual data (age, spend amount, etc.)
    calculated_points = models.IntegerField()
    max_possible_points = models.IntegerField()
    calculation_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['patient', 'behavior_category']
    
    def __str__(self):
        return f"{self.patient.cliniko_patient_id} - {self.behavior_category.name}: {self.calculated_points}pts"

class PatientRawData(models.Model):
    """Raw patient data from Cliniko for scoring calculations"""
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='raw_data')
    
    # Positive behaviors
    appointments_booked = models.BooleanField(default=False)
    age = models.PositiveIntegerField(null=True, blank=True)
    yearly_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    referrals_made = models.PositiveIntegerField(default=0)
    consecutive_attendance_count = models.PositiveIntegerField(default=0)
    
    # Negative behaviors
    no_appointments_booked = models.BooleanField(default=False)
    dna_count = models.PositiveIntegerField(default=0)
    cancellation_count = models.PositiveIntegerField(default=0)
    has_unpaid_cancellation_fee = models.BooleanField(default=False)
    unpaid_invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Raw data for {self.patient.cliniko_patient_id}"

class AdminOverride(models.Model):
    """Track admin overrides for audit purposes"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='overrides')
    original_rating = models.CharField(max_length=1)
    override_rating = models.CharField(max_length=1)
    admin_user = models.CharField(max_length=100)
    reason = models.TextField(blank=True)
    override_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Override: {self.patient.cliniko_patient_id} {self.original_rating}→{self.override_rating}"


class ScoringConfiguration(models.Model):
    """Store configurable scoring weights for behavioral analysis"""
    
    name = models.CharField(max_length=100, default="Default Configuration")
    description = models.TextField(blank=True)
    
    # Positive Behaviors (0-100 sliders)
    future_appointments_weight = models.IntegerField(default=20, help_text="Weight for future appointments (0-100)")
    age_demographics_weight = models.IntegerField(default=10, help_text="Weight for target age demographic (0-100)")
    yearly_spend_weight = models.IntegerField(default=25, help_text="Weight for yearly spend (0-100)")
    consecutive_attendance_weight = models.IntegerField(default=30, help_text="Weight for attendance streak (0-100)")
    referrer_score_weight = models.IntegerField(default=25, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text='Weight for referrer score behavior (0-100)')
    points_per_consecutive_attendance = models.IntegerField(default=2, help_text="Points awarded per consecutive attendance (1-10)")
    points_per_referral = models.IntegerField(default=5, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text='Points awarded per patient referral (0-100)')
    likability_weight = models.IntegerField(default=20, help_text="Weight for manual likability (0-100)")    
    # Negative Behaviors (0-100 sliders - will be applied as negative)
    cancellations_weight = models.IntegerField(default=20, help_text="Penalty weight per cancellation (0-100)")
    points_per_cancellation = models.IntegerField(default=3, help_text="Points deducted per cancellation (1-10)")
    dna_weight = models.IntegerField(default=50, help_text="Penalty weight per DNA (0-100)")
    points_per_dna = models.IntegerField(default=5, help_text="Points deducted per DNA (1-10)")
    unpaid_invoices_weight = models.IntegerField(default=50, help_text="Penalty weight per unpaid invoice (0-100)")
    points_per_unpaid_invoice = models.IntegerField(default=10, help_text="Points deducted per unpaid invoice (1-100)")
    open_dna_invoice_weight = models.IntegerField(default=100, help_text="Penalty weight for open DNA invoice (0-100)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active_for_behavior = models.BooleanField(default=False, help_text="Active preset for patient behavior scoring")
    is_active_for_analytics = models.BooleanField(default=False, help_text="Active preset for analytics processing")
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        active_status = []
        if self.is_active_for_behavior:
            active_status.append('Behavior')
        if self.is_active_for_analytics:
            active_status.append('Analytics')
        
        if active_status:
            return f"{self.name} (Active for: {', '.join(active_status)})"
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one active configuration for behavior
        if self.is_active_for_behavior:
            ScoringConfiguration.objects.filter(is_active_for_behavior=True).exclude(id=self.id).update(is_active_for_behavior=False)
        # Ensure only one active configuration for analytics
        if self.is_active_for_analytics:
            ScoringConfiguration.objects.filter(is_active_for_analytics=True).exclude(id=self.id).update(is_active_for_analytics=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """Get the currently active scoring configuration for behavior"""
        try:
            return cls.objects.get(is_active_for_behavior=True)
        except cls.DoesNotExist:
            # Create default configuration if none exists
            return cls.objects.create(
                name="Default Configuration",
                description="Standard RatedApp scoring weights",
                is_active_for_behavior=True
            )

class AgeBracket(models.Model):
    config = models.ForeignKey(ScoringConfiguration, on_delete=models.CASCADE, related_name='age_brackets')
    min_age = models.IntegerField()
    max_age = models.IntegerField()
    percentage = models.IntegerField(help_text="Percentage of slider maximum (0-100)")
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['config', 'order']
    
    def __str__(self):
        return f"{self.min_age}-{self.max_age}: {self.percentage}%"

class SpendBracket(models.Model):
    config = models.ForeignKey(ScoringConfiguration, on_delete=models.CASCADE, related_name='spend_brackets')
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum spend amount")
    max_spend = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum spend amount (999999.99 for unlimited)")
    percentage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Percentage of slider value")
    order = models.IntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['order']
        unique_together = ['config', 'order']
    
    def __str__(self):
        if self.max_spend >= 999999.99:
            return f"${self.min_spend:.0f}+ ({self.percentage}%)"
        return f"${self.min_spend:.0f}-${self.max_spend:.0f} ({self.percentage}%)"

class RatedAppSettings(models.Model):

    # Clinic Information
    clinic_name = models.CharField(
        max_length=200, 
        null=False, 
        blank=False, 
        verbose_name="Clinic Name"
    )
    clinic_email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name="Clinic Email",
        help_text="Email address for analytics reports"
    )
    smtp_host = models.CharField(
        max_length=200,
        default='smtp.gmail.com',
        blank=True,
        verbose_name="SMTP Host"
    )
    smtp_port = models.IntegerField(
        default=587,
        verbose_name="SMTP Port"
    )
    smtp_username = models.EmailField(
        max_length=254,
        blank=True,
        verbose_name="SMTP Username"
    )
    smtp_password = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="SMTP Password"
    )
    smtp_use_tls = models.BooleanField(
        default=True,
        verbose_name="Use TLS"
    )
    clinic_location = models.CharField(
        max_length=200,
        null=False,
        blank=False, 
        verbose_name="Clinic Location"
    )
    clinic_timezone = models.CharField(
        max_length=100, 
        default='Australia/Sydney', 
        choices=[
            ('Australia/Sydney', 'Sydney'),
            ('Australia/Melbourne', 'Melbourne'),
            ('Australia/Brisbane', 'Brisbane'),
            ('Australia/Perth', 'Perth'),
            ('Australia/Adelaide', 'Adelaide'),
            ('Australia/Darwin', 'Darwin'),
            ('Australia/Hobart', 'Hobart'),
            ('Australia/Canberra', 'Canberra')
        ],
        verbose_name="Clinic Timezone"
    )

    # Connectivity Settings
    software_integration = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Software Integration"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="API Key"
    )
    # Metadata for tracking

    # NEW SOFTWARE INTEGRATION FIELDS
    software_type = models.CharField(
        max_length=50, 
        choices=SOFTWARE_CHOICES, 
        default='cliniko',
        verbose_name="Software Type"
    )

    base_url = models.URLField(
        max_length=300, 
        default='https://api.au1.cliniko.com/v1/',
        verbose_name="API Base URL"
    )

    auth_type = models.CharField(
        max_length=20, 
        choices=AUTH_TYPES, 
        default='basic',
        verbose_name="Authentication Type"
    )

    additional_config = models.JSONField(
        null=True, 
        blank=True,
        verbose_name="Additional Configuration"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.clinic_name} Settings ({self.software_type})"

    class Meta:
        verbose_name = "RatedApp Clinic Settings"
        verbose_name_plural = "RatedApp Clinic Settings"

    # Analytics Settings (add these fields)
    analytics_enabled = models.BooleanField(
        default=False,
        help_text="Whether analytics processing is enabled"
    )
    analytics_preset = models.ForeignKey(
        ScoringConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_settings',
        help_text="Active preset for analytics processing"
    )
    analytics_last_job = models.ForeignKey(
        'AnalyticsJob',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text="Reference to the current/last analytics job"
    )

class AnalyticsJob(models.Model):
    """Manages scheduled analytics processing jobs"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('manual', 'Manual'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Analysing...'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('partial', 'Partial Completion'),
    ]
    
    DATE_RANGE_CHOICES = [
        ('1d', '1 day'),
        ('3', '3 months'),
        ('6', '6 months'),
        ('1y', '1 year'),
        ('2y', '2 years'),
        ('5y', '5 years'),
        ('10y', '10 years'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    # Configuration
    date_range = models.CharField(
        max_length=10, 
        choices=DATE_RANGE_CHOICES,
        help_text="Date range for patient selection"
    )
    preset = models.ForeignKey(
        ScoringConfiguration, 
        on_delete=models.PROTECT,
        related_name='analytics_jobs',
        help_text="Scoring configuration used for analysis"
    )
    frequency = models.CharField(
        max_length=10, 
        choices=FREQUENCY_CHOICES,
        default='manual'
    )
    scheduled_time = models.TimeField(
        help_text="Time to run the job (in clinic timezone)"
    )
    scheduled_day = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        null=True, 
        blank=True,
        help_text="Day of week for weekly jobs"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )

    is_test_mode = models.BooleanField(
        default=False,
        help_text="Test mode - processes but doesn't update Cliniko"
    )
    test_results = models.JSONField(
        default=dict,
        blank=True,
        help_text="Results from test mode runs"
    )
    last_run_started = models.DateTimeField(null=True, blank=True)
    last_run_completed = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    total_patients = models.IntegerField(default=0)
    patients_processed = models.IntegerField(default=0)
    patients_failed = models.IntegerField(default=0)
    
    # Processing state (for resumability)
    processed_patient_ids = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of successfully processed patient IDs"
    )
    failed_patient_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of failed patient IDs with error messages"
    )
    
    # Error tracking
    error_log = models.TextField(
        blank=True,
        help_text="Detailed error messages"
    )
    
    # Cancellation flag
    cancel_requested = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Analytics Job"
        verbose_name_plural = "Analytics Jobs"
    
    def __str__(self):
        return f"Analytics Job - {self.get_status_display()} - {self.created_at}"
    
    def calculate_next_run(self):
        """Calculate next run time based on frequency and schedule"""
        from datetime import datetime, timedelta
        import pytz
        
        settings = RatedAppSettings.objects.first()
        clinic_tz = pytz.timezone(settings.clinic_timezone or 'Australia/Sydney')
        now = datetime.now(clinic_tz)
        
        # Create scheduled datetime for today
        scheduled = now.replace(
            hour=self.scheduled_time.hour,
            minute=self.scheduled_time.minute,
            second=0,
            microsecond=0
        )
        
        if self.frequency == 'daily':
            # If scheduled time has passed today, schedule for tomorrow
            if scheduled <= now:
                scheduled += timedelta(days=1)
                
        elif self.frequency == 'weekly':
            # Find next occurrence of scheduled day
            days_ahead = self.scheduled_day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            scheduled += timedelta(days=days_ahead)
            
        self.next_run = scheduled
        return scheduled
    
    def calculate_next_run(self):
        """Calculate next run time based on frequency and schedule"""
        from datetime import datetime, timedelta
        import pytz
        
        settings = RatedAppSettings.objects.first()
        clinic_tz = pytz.timezone(settings.clinic_timezone or 'Australia/Sydney')
        now = datetime.now(clinic_tz)
        
        # Create scheduled datetime for today
        scheduled = now.replace(
            hour=self.scheduled_time.hour,
            minute=self.scheduled_time.minute,
            second=0,
            microsecond=0
        )
        
        if self.frequency == 'daily':
            # If scheduled time has passed today, schedule for tomorrow
            if scheduled <= now:
                scheduled += timedelta(days=1)
                
        elif self.frequency == 'weekly':
            # Find next occurrence of scheduled day
            days_ahead = self.scheduled_day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            scheduled += timedelta(days=days_ahead)
            
        self.next_run = scheduled
        return scheduled
    
    def calculate_next_run(self):
        """Calculate next run time based on frequency and schedule"""
        from datetime import datetime, timedelta
        import pytz
        
        settings = RatedAppSettings.objects.first()
        clinic_tz = pytz.timezone(settings.clinic_timezone or 'Australia/Sydney')
        now = datetime.now(clinic_tz)
        
        # Create scheduled datetime for today
        scheduled = now.replace(
            hour=self.scheduled_time.hour,
            minute=self.scheduled_time.minute,
            second=0,
            microsecond=0
        )
        
        if self.frequency == 'daily':
            # If scheduled time has passed today, schedule for tomorrow
            if scheduled <= now:
                scheduled += timedelta(days=1)
                
        elif self.frequency == 'weekly':
            # Find next occurrence of scheduled day
            days_ahead = self.scheduled_day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            scheduled += timedelta(days=days_ahead)
            
        self.next_run = scheduled
        return scheduled
    
    def get_date_range_dates(self):
        """Get actual start and end dates based on date_range setting"""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        import pytz
        
        settings = RatedAppSettings.objects.first()
        clinic_tz = pytz.timezone(settings.clinic_timezone or 'Australia/Sydney')
        
        end_date = datetime.now(clinic_tz)
        
        # Handle different date range formats
        if self.date_range == '1d':
            # Exactly 1 day (24 hours) back
            start_date = end_date - timedelta(days=1)
        elif self.date_range.endswith('m'):
            # Months - use relativedelta for accurate month calculation
            months = int(self.date_range[:-1])
            start_date = end_date - relativedelta(months=months)
        elif self.date_range.endswith('y'):
            # Years - use relativedelta for accurate year calculation
            years = int(self.date_range[:-1])
            start_date = end_date - relativedelta(years=years)
        
        return start_date, end_date
    
    def mark_completed(self):
        """Mark job as completed and calculate next run"""
        self.status = 'completed'
        self.last_run_completed = datetime.now()
        
        if self.frequency in ['daily', 'weekly']:
            self.calculate_next_run()
            self.status = 'pending'  # Ready for next run
            
        self.save()
    
    def mark_failed(self, error_message):
        """Mark job as failed with error message"""
        self.status = 'failed'
        self.error_log = f"{self.error_log}\n{datetime.now()}: {error_message}".strip()
        self.save()
    
    def mark_completed(self):
        """Mark job as completed and calculate next run"""
        self.status = 'completed'
        self.last_run_completed = datetime.now()
        
        if self.frequency in ['daily', 'weekly']:
            self.calculate_next_run()
            self.status = 'pending'  # Ready for next run
            
        self.save()
    
    def mark_failed(self, error_message):
        """Mark job as failed with error message"""
        self.status = 'failed'
        self.error_log = f"{self.error_log}\n{datetime.now()}: {error_message}".strip()
        self.save()
    
    def mark_completed(self):
        """Mark job as completed and calculate next run"""
        self.status = 'completed'
        self.last_run_completed = datetime.now()
        
        if self.frequency in ['daily', 'weekly']:
            self.calculate_next_run()
            self.status = 'pending'  # Ready for next run
            
        self.save()
    
    def mark_failed(self, error_message):
        """Mark job as failed with error message"""
        self.status = 'failed'
        self.error_log = f"{self.error_log}\n{datetime.now()}: {error_message}".strip()
        self.save()
    
    def should_run_now(self):
        """Check if job should run based on schedule"""
        from datetime import datetime
        import pytz
        
        if self.status != 'pending':
            return False
            
        if self.frequency == 'manual':
            return False
            
        settings = RatedAppSettings.objects.first()
        clinic_tz = pytz.timezone(settings.clinic_timezone or 'Australia/Sydney')
        now = datetime.now(clinic_tz)
        
        if self.next_run and now >= self.next_run:
            return True
            
        return False

