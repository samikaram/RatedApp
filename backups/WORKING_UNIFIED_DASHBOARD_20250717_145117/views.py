import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db.models import F
from django.db import models, IntegrityError, transaction
import requests
import base64
import time
from .models import ScoringConfiguration, Patient, AgeBracket
from .utils.patient_analyzer import analyze_patient_behavior

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
            
            # Handle weight updates
            else:
                active_config.future_appointments_weight = int(request.POST.get("future_appointments_weight", active_config.future_appointments_weight))
                active_config.age_demographics_weight = int(request.POST.get("age_demographics_weight", active_config.age_demographics_weight))
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
    except ScoringConfiguration.DoesNotExist:
        active_config = None
        age_brackets = []
    
    context = {
        'active_config': active_config,
        'age_brackets': age_brackets,
    }
    
    return render(request, 'patient_rating/unified_dashboard.html', context)
