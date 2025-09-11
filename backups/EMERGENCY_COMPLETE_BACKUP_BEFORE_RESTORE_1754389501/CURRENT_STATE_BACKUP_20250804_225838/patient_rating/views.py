import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db.models import F
from django.db import models, IntegrityError, transaction
import requests
import base64
import time
from .models import ScoringConfiguration, Patient, AgeBracket, SpendBracket
from .utils.patient_analyzer import analyze_patient_behavior
from django.views.decorators.csrf import csrf_exempt

# Cliniko API Configuration
RAW_API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
ENCODED_API_KEY = base64.b64encode(f"{RAW_API_KEY}:".encode()).decode()
BASE_URL = "https://api.au1.cliniko.com/v1"
HEADERS = {
    'Authorization': f'Basic {ENCODED_API_KEY}',
    'Accept': 'application/json',
    'User-Agent': 'RatedApp Patient Search'
}

class HomeView(View):
    def get(self, request):
        return render(request, 'patient_rating/home.html')

class PatientSearchView(View):
    def get(self, request):
        return render(request, 'patient_rating/patient_search.html')
    
    def post(self, request):
        search_type = request.POST.get('search_type', 'name')
        search_value = request.POST.get('search_value', '').strip()
        
        if not search_value:
            return render(request, 'patient_rating/patient_search.html', {
                'error': 'Please enter a search value'
            })
        
        try:
            if search_type == 'name':
                patients = self.search_by_name(search_value)
            elif search_type == 'id':
                patients = self.search_by_id(search_value)
            else:
                patients = []
            
            return render(request, 'patient_rating/patient_search.html', {
                'patients': patients,
                'search_value': search_value,
                'search_type': search_type
            })
        except Exception as e:
            return render(request, 'patient_rating/patient_search.html', {
                'error': f'Search failed: {str(e)}'
            })
    
    def get_phone_numbers(self, patient):
        phone_numbers = patient.get('patient_phone_numbers', [])
        if not phone_numbers:
            return "Not provided"
        formatted_phones = []
        for phone in phone_numbers:
            number = phone.get('number', '')
            phone_type = phone.get('phone_type', '')
            if number:
                formatted_phones.append(f"{number} ({phone_type})")
        return " | ".join(formatted_phones) if formatted_phones else "Not provided"
    
    def search_by_name(self, name):
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        url = f"{BASE_URL}/patients"
        params = {'q[]': f'first_name:={first_name}'}
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        patients = data.get('patients', [])
        formatted_patients = []
        for patient in patients:
            phone = self.get_phone_numbers(patient)
            formatted_patients.append({
                'id': patient.get('id'),
                'first_name': patient.get('first_name'),
                'last_name': patient.get('last_name'),
                'email': patient.get('email'),
                'phone': phone,
                'date_of_birth': patient.get('date_of_birth'),
                'full_name': f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            })
        return formatted_patients
    
    def search_by_id(self, patient_id):
        url = f"{BASE_URL}/patients/{patient_id}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        patient = response.json()
        phone = self.get_phone_numbers(patient)
        return [{
            'id': patient.get('id'),
            'first_name': patient.get('first_name'),
            'last_name': patient.get('last_name'),
            'email': patient.get('email'),
            'phone': phone,
            'date_of_birth': patient.get('date_of_birth'),
            'full_name': f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        }]

class PatientAnalysisView(View):
    def get(self, request, patient_id):
        return render(request, 'patient_rating/patient_analysis.html', {
            'patient_id': patient_id
        })
    
    def post(self, request, patient_id):
        try:
            # Get active scoring configuration for dynamic weights
            config = ScoringConfiguration.get_active_config()
            analysis = analyze_patient_behavior(patient_id, config)
            
            if analysis:
                return JsonResponse({
                    'status': 'success',
                    'analysis': analysis
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Analysis failed'
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

class UpdateLikabilityView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            patient_id = data.get('patient_id')
            likability_value = int(data.get('likability', 0))
            
            # Get or create patient record
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'patient_name': f'Patient {patient_id}'}
            )
            
            # Update likability value
            patient.likability = likability_value
            patient.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class UpdateUnlikabilityView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            patient_id = data.get('patient_id')
            unlikability_value = int(data.get('unlikability', 0))
            
            # Get or create patient record
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'patient_name': f'Patient {patient_id}'}
            )
            
            # Update unlikability value
            patient.unlikability = unlikability_value
            patient.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

def unified_dashboard(request):
    # Canonical URL redirect - always use /patients/dashboard/
    if request.path == "/dashboard/":
        return HttpResponseRedirect("/patients/dashboard/")

    if request.method == "POST":
        try:
            active_config = ScoringConfiguration.objects.get(is_active=True)
            action = request.POST.get('action')
            
            # Handle age bracket operations
            if action == 'delete_age_bracket':
                bracket_id = request.POST.get('bracket_id')
                if bracket_id:
                    bracket = get_object_or_404(AgeBracket, id=bracket_id)
                    bracket.delete()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True})
            
            elif action == 'add_age_bracket':
                print("DEBUG: add_age_bracket action triggered")
                min_age = request.POST.get('min_age')
                max_age = request.POST.get('max_age')
                percentage = request.POST.get('percentage')
                
                if min_age and max_age and percentage:
                    try:
                        new_min_age = int(min_age)
                        new_max_age = int(max_age)
                        new_percentage = int(percentage)
                        
                        print(f"DEBUG: Values - min_age: {new_min_age}, max_age: {new_max_age}, percentage: {new_percentage}")
                        
                        # Simple approach: just add with next available order
                        max_order = AgeBracket.objects.filter(
                            config=active_config
                        ).aggregate(max_order=models.Max('order'))['max_order'] or 0
                        
                        print(f"DEBUG: Creating bracket with order {max_order + 1}")
                        
                        # Create new bracket
                        AgeBracket.objects.create(
                            config=active_config,
                            min_age=new_min_age,
                            max_age=new_max_age,
                            percentage=new_percentage,
                            order=max_order + 1
                        )
                        
                        print("DEBUG: Bracket created successfully")
                        
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": True})
                            
                    except Exception as e:
                        print(f"DEBUG: Error creating bracket: {e}")
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": str(e)})

            # Handle spend bracket operations
            elif action == 'delete_spend_bracket':
                bracket_id = request.POST.get('bracket_id')
                if bracket_id:
                    bracket = get_object_or_404(SpendBracket, id=bracket_id)
                    bracket.delete()
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"success": True})
            
            elif action == 'add_spend_bracket':
                print("DEBUG: add_spend_bracket action triggered")
                min_spend = request.POST.get('min_spend')
                max_spend = request.POST.get('max_spend')
                percentage = request.POST.get('percentage')
                
                if min_spend and max_spend and percentage:
                    try:
                        new_min_spend = float(min_spend)
                        new_max_spend = float(max_spend)
                        new_percentage = int(percentage)
                        
                        print(f"DEBUG: Values - min_spend: {new_min_spend}, max_spend: {new_max_spend}, percentage: {new_percentage}")
                        
                        # Simple approach: just add with next available order
                        max_order = SpendBracket.objects.filter(
                            config=active_config
                        ).aggregate(max_order=models.Max('order'))['max_order'] or 0
                        
                        print(f"DEBUG: Creating spend bracket with order {max_order + 1}")
                        
                        # Create new bracket
                        SpendBracket.objects.create(
                            config=active_config,
                            min_spend=new_min_spend,
                            max_spend=new_max_spend,
                            percentage=new_percentage,
                            order=max_order + 1
                        )
                        
                        print("DEBUG: Spend bracket created successfully")
                        
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": True})
                            
                    except Exception as e:
                        print(f"DEBUG: Error creating spend bracket: {e}")
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": str(e)})
            
            # Handle weight updates

            # Handle Unpaid Invoices points update

            # Bulk bracket operations for preset application
            elif action == "clear_age_brackets":
                try:
                    active_config = ScoringConfiguration.objects.get(is_active=True)
                    AgeBracket.objects.filter(config=active_config).delete()
                    return JsonResponse({"success": True, "message": "Age brackets cleared"})
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})

            elif action == "clear_spend_brackets":
                try:
                    active_config = ScoringConfiguration.objects.get(is_active=True)
                    SpendBracket.objects.filter(config=active_config).delete()
                    return JsonResponse({"success": True, "message": "Spend brackets cleared"})
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})

            elif action == "insert_age_brackets":
                try:
                    import json
                    active_config = ScoringConfiguration.objects.get(is_active=True)
                    brackets_data = json.loads(request.POST.get("brackets_data", "[]"))
                    
                    for bracket_data in brackets_data:
                        AgeBracket.objects.create(
                            config=active_config,
                            min_age=bracket_data["min_age"],
                            max_age=bracket_data["max_age"],
                            percentage=bracket_data["percentage"],
                            order=bracket_data["order"]
                        )
                    return JsonResponse({"success": True, "message": f"Inserted {len(brackets_data)} age brackets"})
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})

            elif action == "insert_spend_brackets":
                try:
                    import json
                    active_config = ScoringConfiguration.objects.get(is_active=True)
                    brackets_data = json.loads(request.POST.get("brackets_data", "[]"))
                    
                    for bracket_data in brackets_data:
                        SpendBracket.objects.create(
                            config=active_config,
                            min_spend=bracket_data["min_spend"],
                            max_spend=bracket_data["max_spend"],
                            percentage=bracket_data["percentage"],
                            order=bracket_data["order"]
                        )
                    return JsonResponse({"success": True, "message": f"Inserted {len(brackets_data)} spend brackets"})
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            elif action == 'update_unpaid_invoices_points':
                points_value = request.POST.get('points_per_unpaid_invoice')
                if points_value:
                    try:
                        points_int = int(points_value)
                        if 1 <= points_int <= 100:
                            active_config.points_per_unpaid_invoice = points_int
                            active_config.save()
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": True})
                        else:
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": False, "error": "Points must be between 1 and 100"})
                    except ValueError:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": "Invalid points value"})
                    except Exception as e:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": str(e)})


            # Handle DNA points update
            elif action == 'update_dna_points':
                points_value = request.POST.get('points_per_dna')
                if points_value:
                    try:
                        points_int = int(points_value)
                        if 1 <= points_int <= 100:
                            active_config.points_per_dna = points_int
                            active_config.save()
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": True})
                        else:
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": False, "error": "Points must be between 1 and 100"})
                    except ValueError:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": "Invalid points value"})
                    except Exception as e:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": str(e)})


            # Handle cancellations points update
            elif action == 'update_cancellations_points':
                points_value = request.POST.get('points_per_cancellation')
                if points_value:
                    try:
                        points_int = int(points_value)
                        if 1 <= points_int <= 100:
                            active_config.points_per_cancellation = points_int
                            active_config.save()
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": True})
                        else:
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": False, "error": "Points must be between 1 and 100"})
                    except ValueError:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": "Invalid points value"})
                    except Exception as e:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": str(e)})


            # Handle consecutive attendance points update
            elif action == 'update_consecutive_points':
                points_value = request.POST.get('points_per_consecutive_attendance')
                if points_value:
                    try:
                        points_int = int(points_value)
                        if 1 <= points_int <= 100:
                            active_config.points_per_consecutive_attendance = points_int
                            active_config.save()
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": True})
                        else:
                            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                                return JsonResponse({"success": False, "error": "Points must be between 1 and 100"})
                    except ValueError:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": "Invalid points value"})
                    except Exception as e:
                        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "error": str(e)})
            elif action == "delete_preset":
                preset_id = request.POST.get("preset_id")
                if not preset_id:
                    return JsonResponse({"success": False, "error": "No preset ID provided"})
                
                try:
                    # Check if this is the only preset
                    total_presets = ScoringConfiguration.objects.count()
                    if total_presets <= 1:
                        return JsonResponse({"success": False, "error": "Cannot delete the last remaining preset"})
                    
                    # Get and delete the preset
                    preset = ScoringConfiguration.objects.get(id=preset_id)
                    preset_name = preset.name
                    preset.delete()
                    
                    return JsonResponse({
                        "success": True, 
                        "message": f"Preset {preset_name} deleted successfully"
                    })
                except ScoringConfiguration.DoesNotExist:
                    return JsonResponse({"success": False, "error": "Preset not found"})
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})


            else:
                active_config.future_appointments_weight = int(request.POST.get("future_appointments_weight", active_config.future_appointments_weight))
                active_config.age_demographics_weight = int(request.POST.get("age_demographics_weight", active_config.age_demographics_weight))
                active_config.yearly_spend_weight = int(request.POST.get("yearly_spend_weight", active_config.yearly_spend_weight))
                active_config.consecutive_attendance_weight = int(request.POST.get("consecutive_attendance_weight", active_config.consecutive_attendance_weight))
                active_config.cancellations_weight = int(request.POST.get("cancellations_weight", active_config.cancellations_weight))
                active_config.dna_weight = int(request.POST.get("dna_weight", active_config.dna_weight))
                active_config.unpaid_invoices_weight = int(request.POST.get("unpaid_invoices_weight", active_config.unpaid_invoices_weight))
                active_config.open_dna_invoice_weight = int(request.POST.get("open_dna_invoice_weight", active_config.open_dna_invoice_weight))

                # Save points values from form data
                active_config.points_per_consecutive_attendance = int(request.POST.get("points_per_consecutive_attendance", active_config.points_per_consecutive_attendance))
                active_config.points_per_cancellation = int(request.POST.get("points_per_cancellation", active_config.points_per_cancellation))
                active_config.points_per_dna = int(request.POST.get("points_per_dna", active_config.points_per_dna))
                active_config.points_per_unpaid_invoice = int(request.POST.get("points_per_unpaid_invoice", active_config.points_per_unpaid_invoice))
                active_config.save()
                
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"success": True})
                    
                return HttpResponseRedirect(reverse("unified_dashboard"))
                
        except Exception as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": str(e)})

            pass
    
    # GET request - display the dashboard
    try:
        active_config = ScoringConfiguration.objects.get(is_active=True)
        age_brackets = AgeBracket.objects.filter(config=active_config).order_by('min_age')
        spend_brackets = SpendBracket.objects.filter(config=active_config).order_by('min_spend')
    except ScoringConfiguration.DoesNotExist:
        active_config = None
        age_brackets = []
        spend_brackets = []
    
    context = {
        'active_config': active_config,
        'age_brackets': age_brackets,
        'spend_brackets': spend_brackets,
    }
    
    return render(request, 'patient_rating/unified_dashboard.html', context)


def get_presets(request):
    """Return JSON list of all saved presets for dropdown population"""
    if request.method == 'GET':
        try:
            presets = ScoringConfiguration.objects.all().order_by('name')
            preset_list = []
            for preset in presets:
                preset_data = {
                    'id': preset.id,
                    'name': preset.name,
                    'description': preset.description or '',
                    'is_active': preset.is_active,
                    'created_at': preset.created_at.isoformat() if preset.created_at else None,
                    'updated_at': preset.updated_at.isoformat() if preset.updated_at else None
                }
                preset_list.append(preset_data)
            
            return JsonResponse({
                'success': True,
                'presets': preset_list,
                'count': len(preset_list)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

def get_preset_details(request, preset_id):
    """Get detailed preset data including all slider values and brackets"""
    try:
        preset = ScoringConfiguration.objects.get(id=preset_id)
        
        # Get age brackets for this preset
        age_brackets = []
        for bracket in preset.age_brackets.all().order_by('order'):
            age_brackets.append({
                'id': bracket.id,
                'min_age': bracket.min_age,
                'max_age': bracket.max_age,
                'percentage': bracket.percentage,
                'order': bracket.order
            })
        
        # Get spend brackets for this preset
        spend_brackets = []
        for bracket in preset.spend_brackets.all().order_by('order'):
            spend_brackets.append({
                'id': bracket.id,
                'min_spend': float(bracket.min_spend),
                'max_spend': float(bracket.max_spend) if bracket.max_spend else None,
                'percentage': bracket.percentage,
                'order': bracket.order
            })
        
        preset_data = {
            'id': preset.id,
            'name': preset.name,
            'description': preset.description,
            'is_active': preset.is_active,
            'created_at': preset.created_at.isoformat(),
            'updated_at': preset.updated_at.isoformat(),
            'slider_values': {
                # Positive behaviors - EXACT FIELD NAMES FROM INVESTIGATION
                'future_appointments_weight': preset.future_appointments_weight,
                'age_demographics_weight': preset.age_demographics_weight,
                'yearly_spend_weight': preset.yearly_spend_weight,
                'consecutive_attendance_weight': preset.consecutive_attendance_weight,
                'points_per_consecutive_attendance': preset.points_per_consecutive_attendance,
                
                # Negative behaviors - EXACT FIELD NAMES FROM INVESTIGATION
                'cancellations_weight': preset.cancellations_weight,
                'points_per_cancellation': preset.points_per_cancellation,
                'dna_weight': preset.dna_weight,
                'points_per_dna': preset.points_per_dna,
                'unpaid_invoices_weight': preset.unpaid_invoices_weight,
                'points_per_unpaid_invoice': preset.points_per_unpaid_invoice,
                'open_dna_invoice_weight': preset.open_dna_invoice_weight,
                
                # Metadata fields
                'likability_weight': preset.likability_weight,
                'unlikability_weight': preset.unlikability_weight,
            },
            'age_brackets': age_brackets,
            'spend_brackets': spend_brackets
        }
        
        return JsonResponse({
            'success': True,
            'preset': preset_data
        })
        
    except ScoringConfiguration.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Preset not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# Apply Button - Bracket Bulk Operations
def clear_age_brackets(request):
    """Clear all age brackets for the active configuration"""
    if request.method == 'POST':
        try:
            from .models import ScoringConfiguration, AgeBracket
            
            # Get active configuration
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            # Clear all age brackets for this configuration
            deleted_count = AgeBracket.objects.filter(config=active_config).delete()[0]
            
            return JsonResponse({
                'success': True, 
                'message': f'Cleared {deleted_count} age brackets',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def bulk_insert_age_brackets(request):
    """Bulk insert age brackets for the active configuration"""
    if request.method == 'POST':
        try:
            import json
            from .models import ScoringConfiguration, AgeBracket
            
            # Get active configuration
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            # Parse brackets data from request
            data = json.loads(request.body)
            brackets_data = data.get('brackets', [])
            
            # Create AgeBracket objects for bulk insert
            age_brackets = []
            for i, bracket in enumerate(brackets_data):
                age_brackets.append(AgeBracket(
                    config=active_config,
                    min_age=bracket.get('min_age', 0),
                    max_age=bracket.get('max_age', 100),
                    percentage=bracket.get('percentage', 0),
                    order=i + 1
                ))
            
            # Bulk insert
            AgeBracket.objects.bulk_create(age_brackets)
            
            return JsonResponse({
                'success': True,
                'message': f'Inserted {len(age_brackets)} age brackets',
                'inserted_count': len(age_brackets)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def clear_spend_brackets(request):
    """Clear all spend brackets for the active configuration"""
    if request.method == 'POST':
        try:
            from .models import ScoringConfiguration, SpendBracket
            
            # Get active configuration
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            # Clear all spend brackets for this configuration
            deleted_count = SpendBracket.objects.filter(config=active_config).delete()[0]
            
            return JsonResponse({
                'success': True,
                'message': f'Cleared {deleted_count} spend brackets',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def bulk_insert_spend_brackets(request):
    """Bulk insert spend brackets for the active configuration"""
    if request.method == 'POST':
        try:
            import json
            from .models import ScoringConfiguration, SpendBracket
            
            # Get active configuration
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            # Parse brackets data from request
            data = json.loads(request.body)
            brackets_data = data.get('brackets', [])
            
            # Create SpendBracket objects for bulk insert
            spend_brackets = []
            for i, bracket in enumerate(brackets_data):
                spend_brackets.append(SpendBracket(
                    config=active_config,
                    min_spend=bracket.get('min_spend', 0),
                    max_spend=bracket.get('max_spend', 10000),
                    percentage=bracket.get('percentage', 0),
                    order=i + 1
                ))
            
            # Bulk insert
            SpendBracket.objects.bulk_create(spend_brackets)
            
            return JsonResponse({
                'success': True,
                'message': f'Inserted {len(spend_brackets)} spend brackets',
                'inserted_count': len(spend_brackets)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@require_POST
def delete_preset(request):
    """
    Delete a scoring preset with protection logic.
    Prevents deletion if only 1 preset remains.
    Handles active preset switching if needed.
    """
    try:
        # Get preset ID from POST data
        preset_id = request.POST.get('preset_id')
        
        if not preset_id:
            return JsonResponse({
                'success': False,
                'error': 'No preset ID provided'
            })
        
        # Check if preset exists
        try:
            preset_to_delete = ScoringConfiguration.objects.get(id=preset_id)
        except ScoringConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Preset not found'
            })
        
        # PROTECTION: Check if this is the last preset
        total_presets = ScoringConfiguration.objects.count()
        if total_presets <= 1:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete the last remaining preset'
            })
        
        # Check if we're deleting the currently active preset
        is_active_preset = preset_to_delete.is_active
        
        # If deleting active preset, switch to another one first
        if is_active_preset:
            # Find another preset to make active
            next_preset = ScoringConfiguration.objects.exclude(id=preset_id).first()
            if next_preset:
                # Deactivate all presets first
                ScoringConfiguration.objects.update(is_active=False)
                # Activate the next preset
                next_preset.is_active = True
                next_preset.save()
        
        # Delete the preset (CASCADE will handle related objects)
        preset_name = preset_to_delete.name
        preset_to_delete.delete()
        
        # Get updated preset list for dropdown
        remaining_presets = list(ScoringConfiguration.objects.values('id', 'name', 'is_active'))
        
        # Find the currently active preset
        active_preset = ScoringConfiguration.objects.filter(is_active=True).first()
        active_preset_id = active_preset.id if active_preset else None
        
        return JsonResponse({
            'success': True,
            'message': f'Preset "{preset_name}" deleted successfully',
            'deleted_preset_id': int(preset_id),
            'remaining_presets': remaining_presets,
            'active_preset_id': active_preset_id,
            'total_remaining': len(remaining_presets)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting preset: {str(e)}'
        })


# =============================================================================
# CREATE PRESET WORKFLOW VIEWS
# =============================================================================

@csrf_exempt
@csrf_exempt
@csrf_exempt
@csrf_exempt
def updateScoringWeights(request):
    """
    Auto-saves current slider values to the active configuration.
    Called before creating a new preset to ensure database reflects screen state.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get the active configuration
            active_config = ScoringConfiguration.objects.get(is_active=True)
            
            # Update all weight fields from slider values
            active_config.future_appointments_weight = int(data.get('future_appointments_weight', active_config.future_appointments_weight))
            active_config.age_demographics_weight = int(data.get('age_demographics_weight', active_config.age_demographics_weight))
            active_config.yearly_spend_weight = int(data.get('yearly_spend_weight', active_config.yearly_spend_weight))
            active_config.consecutive_attendance_weight = int(data.get('consecutive_attendance_weight', active_config.consecutive_attendance_weight))
            active_config.cancellations_weight = int(data.get('cancellations_weight', active_config.cancellations_weight))
            active_config.dna_weight = int(data.get('dna_weight', active_config.dna_weight))
            active_config.unpaid_invoices_weight = int(data.get('unpaid_invoices_weight', active_config.unpaid_invoices_weight))
            active_config.open_dna_invoice_weight = int(data.get('open_dna_invoice_weight', active_config.open_dna_invoice_weight))
            active_config.likability_weight = int(data.get('likability_weight', active_config.likability_weight))
            active_config.unlikability_weight = int(data.get('unlikability_weight', active_config.unlikability_weight))
            
            # Update points fields from input boxes
            active_config.points_per_consecutive_attendance = int(data.get('points_per_consecutive_attendance', active_config.points_per_consecutive_attendance))
            active_config.points_per_cancellation = int(data.get('points_per_cancellation', active_config.points_per_cancellation))
            active_config.points_per_dna = int(data.get('points_per_dna', active_config.points_per_dna))
            active_config.points_per_unpaid_invoice = int(data.get('points_per_unpaid_invoice', active_config.points_per_unpaid_invoice))
            
            # Save the updated configuration
            active_config.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Scoring weights updated successfully',
                'active_config_id': active_config.id
            })
            
        except ScoringConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No active configuration found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error updating scoring weights: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@csrf_exempt
@csrf_exempt
@csrf_exempt
def create_preset(request):
    """
    Creates a new preset by copying all values from the active configuration.
    The active configuration should be updated with current slider values before calling this.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            name = data.get('name', '').strip()
            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'Preset name is required'
                })
            
            description = data.get('description', '').strip()
            
            # Check for duplicate names
            if ScoringConfiguration.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'A preset with the name "{name}" already exists'
                })
            
            # Get the active configuration (source for copying)
            active_config = ScoringConfiguration.objects.get(is_active=True)
            
            # Create new preset by copying all values from active config
            new_preset = ScoringConfiguration.objects.create(
                name=name,
                description=description,
                is_active=False,  # New presets are not active by default
                
                # Copy all weight fields
                future_appointments_weight=active_config.future_appointments_weight,
                age_demographics_weight=active_config.age_demographics_weight,
                yearly_spend_weight=active_config.yearly_spend_weight,
                consecutive_attendance_weight=active_config.consecutive_attendance_weight,
                cancellations_weight=active_config.cancellations_weight,
                dna_weight=active_config.dna_weight,
                unpaid_invoices_weight=active_config.unpaid_invoices_weight,
                open_dna_invoice_weight=active_config.open_dna_invoice_weight,
                likability_weight=active_config.likability_weight,
                unlikability_weight=active_config.unlikability_weight,
                
                # Copy all points fields
                points_per_consecutive_attendance=active_config.points_per_consecutive_attendance,
                points_per_cancellation=active_config.points_per_cancellation,
                points_per_dna=active_config.points_per_dna,
                points_per_unpaid_invoice=active_config.points_per_unpaid_invoice,
            )
            
            # Copy age brackets
            for bracket in active_config.age_brackets.all():
                AgeBracket.objects.create(
                    config=new_preset,
                    min_age=bracket.min_age,
                    max_age=bracket.max_age,
                    percentage=bracket.percentage,
                    order=bracket.order
                )
            
            # Copy spend brackets
            for bracket in active_config.spend_brackets.all():
                SpendBracket.objects.create(
                    config=new_preset,
                    min_spend=bracket.min_spend,
                    max_spend=bracket.max_spend,
                    percentage=bracket.percentage,
                    order=bracket.order
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Preset "{name}" created successfully',
                'preset_id': new_preset.id,
                'preset_name': new_preset.name,
                'age_brackets_copied': active_config.age_brackets.count(),
                'spend_brackets_copied': active_config.spend_brackets.count()
            })
            
        except ScoringConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No active configuration found to copy from'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error creating preset: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
