from django.db import models

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
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
    likability = models.IntegerField(default=0, help_text="Manual likability score (0-100)")
    unlikability = models.IntegerField(default=0, help_text="Manual unlikability score (0-100)")
    
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
    points_per_consecutive_attendance = models.IntegerField(default=2, help_text="Points awarded per consecutive attendance (1-10)")
    likability_weight = models.IntegerField(default=20, help_text="Weight for manual likability (0-100)")    
    # Negative Behaviors (0-100 sliders - will be applied as negative)
    cancellations_weight = models.IntegerField(default=20, help_text="Penalty weight per cancellation (0-100)")
    points_per_cancellation = models.IntegerField(default=3, help_text="Points deducted per cancellation (1-10)")
    dna_weight = models.IntegerField(default=50, help_text="Penalty weight per DNA (0-100)")
    points_per_dna = models.IntegerField(default=5, help_text="Points deducted per DNA (1-10)")
    unpaid_invoices_weight = models.IntegerField(default=50, help_text="Penalty weight per unpaid invoice (0-100)")
    points_per_unpaid_invoice = models.IntegerField(default=10, help_text="Points deducted per unpaid invoice (1-100)")
    open_dna_invoice_weight = models.IntegerField(default=100, help_text="Penalty weight for open DNA invoice (0-100)")
    unlikability_weight = models.IntegerField(default=20, help_text="Weight for manual unlikability (0-100)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False, help_text="Currently active configuration")
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} {'(Active)' if self.is_active else ''}"
    
    def save(self, *args, **kwargs):
        # Ensure only one active configuration
        if self.is_active:
            ScoringConfiguration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """Get the currently active scoring configuration"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            # Create default configuration if none exists
            return cls.objects.create(
                name="Default Configuration",
                description="Standard RatedApp scoring weights",
                is_active=True
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
