from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import PanelConfiguration
import json

@login_required
@require_http_methods(["GET", "POST"])
def panel_settings_view(request):
    try:
        panel_config, created = PanelConfiguration.objects.get_or_create(
            user=request.user
        )

        if request.method == 'POST':
            data = json.loads(request.body)
            
            # Update configuration
            panel_config.future_appointments_weight = data.get('future_appointments_weight', panel_config.future_appointments_weight)
            panel_config.age_demographics_weight = data.get('age_demographics_weight', panel_config.age_demographics_weight)
            panel_config.yearly_spend_weight = data.get('yearly_spend_weight', panel_config.yearly_spend_weight)
            panel_config.consecutive_attendance_weight = data.get('consecutive_attendance_weight', panel_config.consecutive_attendance_weight)
            panel_config.referrer_score_weight = data.get('referrer_score_weight', panel_config.referrer_score_weight)
            
            panel_config.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Panel configuration updated'
            })
        
        # GET request: return current configuration
        return JsonResponse({
            'future_appointments_weight': panel_config.future_appointments_weight,
            'age_demographics_weight': panel_config.age_demographics_weight,
            'yearly_spend_weight': panel_config.yearly_spend_weight,
            'consecutive_attendance_weight': panel_config.consecutive_attendance_weight,
            'referrer_score_weight': panel_config.referrer_score_weight
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
