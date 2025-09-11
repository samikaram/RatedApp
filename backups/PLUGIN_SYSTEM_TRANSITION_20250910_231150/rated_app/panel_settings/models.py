from django.db import models
from django.contrib.auth.models import User

class PanelConfiguration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    future_appointments_weight = models.FloatField(default=20)
    age_demographics_weight = models.FloatField(default=15)
    yearly_spend_weight = models.FloatField(default=25)
    consecutive_attendance_weight = models.FloatField(default=20)
    referrer_score_weight = models.FloatField(default=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Panel Config for {self.user.username}"
