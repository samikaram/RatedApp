import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import RatedAppSettings
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_http_methods
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db.models import F
from django.db import models, IntegrityError, transaction
import requests
import base64
import time
from .models import ScoringConfiguration, Patient, AgeBracket, SpendBracket, RatedAppSettings
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


import requests
import base64
import re
from django.conf import settings

def get_referrer_count(patient_id):
    """
    Get the number of patients referred by a specific patient using Cliniko API.
    Uses Paula's new referrer_id filter from August 2025.
    
    Args:
        patient_id (str): The Cliniko patient ID
        
    Returns:
        int: Number of patients referred by this patient
    """
    try:
        # Use the working API key
        api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
        encoded_key = base64.b64encode(f"{api_key}:".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_key}',
            'Accept': 'application/json'
        }
        
        # Use Paula's new referrer_id filter
        url = f"https://api.au1.cliniko.com/v1/referral_sources?q[]=referrer_id:={patient_id}"
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            referral_sources = data.get('referral_sources', [])
            return len(referral_sources)
        else:
            print(f"❌ Cliniko API error for patient {patient_id}: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"❌ Error getting referrer count for patient {patient_id}: {e}")
        return 0

def calculate_referrer_score(patient_id, points_per_referral, max_points):
    """
    Calculate referrer score with points cap logic.
    
    Args:
        patient_id (str): The Cliniko patient ID
        points_per_referral (int): Points awarded per referral
        max_points (int): Maximum points cap (from slider)
        
    Returns:
        int: Final referrer score (capped)
    """
    referral_count = get_referrer_count(patient_id)
    raw_score = referral_count * points_per_referral
    final_score = min(raw_score, max_points)
    
    print(f"🔗 Referrer score for patient {patient_id}: {referral_count} referrals × {points_per_referral} points = {raw_score}, capped at {max_points} = {final_score}")
    
    return final_score


def safe_int(value, default=0):
    """
    Safely convert a value to integer, returning default if conversion fails.
    Handles None, empty strings, and invalid values gracefully.
    """
    if value is None or value == '':
        return default
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return default

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

    def get_open_dna_invoices(self, patient_id):
        """Extract and count open DNA (Did Not Arrive) invoices for a patient"""
        try:
            # Get patient's invoices from Cliniko
            url = f"{BASE_URL}/invoices"
            params = {'q[]': f'patient_id:={patient_id}'}
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            
            invoices = data.get('invoices', [])
            open_dna_count = 0
            
            # Filter for unpaid DNA invoices
            for invoice in invoices:
                # Check if invoice is for DNA (Did Not Arrive) and unpaid
                if (invoice.get('status') == 'unpaid' and 
                    ('DNA' in str(invoice.get('description', '')).upper() or
                     'DID NOT ARRIVE' in str(invoice.get('description', '')).upper())):
                    open_dna_count += 1
            
            return {
                'count': open_dna_count,
                'has_open_dna': open_dna_count > 0,
                'description': f"{open_dna_count} open DNA invoices" if open_dna_count != 1 else "1 open DNA invoice"
            }
            
        except Exception as e:
            print(f"❌ Error getting DNA invoices for patient {patient_id}: {e}")
            return {
                'count': 0,
                'has_open_dna': False,
                'description': "Error loading DNA invoices"
            }

    def get_likability_data(self, patient_id):
        """Get or create likability data for a patient"""
        try:
            from .models import Patient
            
            # Get or create patient record
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'likability': 0}  # Default to neutral
            )
            
            # Determine likability status
            if patient.likability > 0:
                status = 'positive'
                description = f'Likable: +{patient.likability}'
            elif patient.likability < 0:
                status = 'negative'
                description = f'Unlikable: {patient.likability}'
            else:
                status = 'neutral'
                description = 'Neutral: 0'
            
            return {
                'likability_score': patient.likability,
                'description': description,
                'status': status,
                'is_positive': patient.likability > 0,
                'is_negative': patient.likability < 0,
                'is_neutral': patient.likability == 0
            }
            
        except Exception as e:
            print(f"❌ Error getting likability for patient {patient_id}: {e}")
            return {
                'likability_score': 0,
                'description': 'Error loading likability',
                'status': 'neutral',
                'is_positive': False,
                'is_negative': False,
                'is_neutral': True
            }

class PatientAnalysisView(View):
    def get(self, request, patient_id):
        return render(request, 'patient_rating/patient_analysis.html', {
            'patient_id': patient_id
        })
    
    def post(self, request, patient_id):
        action = request.POST.get('action')
        if action == 'update_likability':
            try:
                patient_id = request.POST.get('patient_id')
                likability = int(request.POST.get('likability', 0))
                
                # Validate likability value
                if not (-100 <= likability <= 100):
                    return JsonResponse({'success': False, 'error': 'Likability must be between 0 and 100'})
                
                # Get or create patient
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'patient_name': f'Patient {patient_id}'}
                )
                
                # Update likability
                patient.likability = likability
                patient.save()
                
                return JsonResponse({'success': True, 'likability': likability})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
            try:
                patient_id = request.POST.get('patient_id')
                # unlikability removed - was: unlikability = int(request.POST.get('unlikability', 0))
                
                if False:  # unlikability validation removed
                    return JsonResponse({'success': False, 'error': 'Feature removed'})
                
                # Get or create patient
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'patient_name': f'Patient {patient_id}'}
                )
                
                # patient.unlikability removed
                patient.save()
                
                return JsonResponse({'success': True})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Continue with existing POST logic if no action matched
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
            # Use form data instead of JSON
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

    def post(self, request):
        try:
            # Use form data instead of JSON
            patient_id = data.get('patient_id')
            # unlikability removed - was: unlikability_value = int(data.get('unlikability', 0))
            
            # Get or create patient record
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'patient_name': f'Patient {patient_id}'}
            )
            
            # patient.unlikability removed
            patient.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

def unified_dashboard(request):
    print("=== UNIFIED DASHBOARD REQUEST DEBUG ===")
    print(f"Method: {request.method}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    print(f"POST data: {dict(request.POST)}")
    print("=" * 50)

    # ==========================================
    # PATIENT CARDS AJAX HANDLERS - SIMPLE TEST
    # ==========================================
    
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        action = request.POST.get("action")
        print(f"🔍 AJAX ACTION RECEIVED: {action}")
        
        if action == "search_patients":
            search_term = request.POST.get("search_term", "").strip()
            print(f"🔍 SEARCH REQUEST: '{search_term}'")
            
            if len(search_term) < 2:
                print("❌ Search term too short")
                return JsonResponse({"success": False, "error": "Search term too short"})
            
            # Use real Cliniko API
            try:
                search_view = PatientSearchView()
                patients_data = search_view.search_by_name(search_term)
                
                test_patients = []
                for patient in patients_data:
                    test_patients.append({
                        "id": patient['id'],
                        "name": patient['full_name']
                    })
                    
                if not test_patients:
                    test_patients = [{"id": 0, "name": "No patients found"}]
                    
            except Exception as e:
                print(f"❌ API Error: {e}")
                test_patients = [{"id": 0, "name": f"Search error: {str(e)}"}]
            
            print(f"✅ Returning {len(test_patients)} test patients")
            
            return JsonResponse({
                "success": True,
                "patients": test_patients
            })
        
        
        elif action == 'update_likability':
            try:
                patient_id = request.POST.get('patient_id')
                likability = int(request.POST.get('likability', 0))
                
                # Validate likability value (-100 to +100 for unified dashboard)
                if not (-100 <= likability <= 100):
                    return JsonResponse({'success': False, 'error': 'Likability must be between -100 and 100'})
                
                # Import Patient model
                from patient_rating.models import Patient
                
                # Get or create patient
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'patient_name': f'Patient {patient_id}'}
                )
                
                # Update likability
                patient.likability = likability
                patient.save()
                
                print(f"✅ SAVED LIKABILITY: Patient {patient_id} = {likability}")
                return JsonResponse({'success': True, 'likability': likability})
                
            except Exception as e:
                print(f"❌ LIKABILITY ERROR: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'update_weights':
            try:
                # Create/get temporary working config (don't modify presets)
                config, created = ScoringConfiguration.objects.get_or_create(
                    name="Weights Updated",
                    defaults={"description": "Temporary working configuration", "is_active": False}
                )
                
                # Deactivate all other configs (preserve presets)
                ScoringConfiguration.objects.exclude(id=config.id).update(is_active=False)
                config.is_active = True
                
                # Update all weight values
                config.future_appointments_weight = int(request.POST.get("future_appointments_weight", 0))
                config.age_demographics_weight = int(request.POST.get("age_demographics_weight", 0))
                config.yearly_spend_weight = int(request.POST.get("yearly_spend_weight", 0))
                config.consecutive_attendance_weight = int(request.POST.get("consecutive_attendance_weight", 0))
                config.referrer_score_weight = int(request.POST.get("referrer_score_weight", 0))
                config.cancellations_weight = int(request.POST.get("cancellations_weight", 0))
                config.dna_weight = int(request.POST.get("dna_weight", 0))
                config.unpaid_invoices_weight = int(request.POST.get("unpaid_invoices_weight", 0))
                config.open_dna_invoice_weight = int(request.POST.get("open_dna_invoice_weight", 0))
                
                # Update all points values
                config.points_per_consecutive_attendance = int(request.POST.get("points_per_consecutive_attendance", 0))
                config.points_per_cancellation = int(request.POST.get("points_per_cancellation", 0))
                config.points_per_dna = int(request.POST.get("points_per_dna", 0))
                config.points_per_unpaid_invoice = int(request.POST.get("points_per_unpaid_invoice", 0))
                config.points_per_referral = int(request.POST.get("points_per_referral", 0))
                
                # Save the configuration
                config.save()
                
                return JsonResponse({
                    "success": True,
                    "message": "Weights updated successfully"
                })
                
            except Exception as e:
                print(f"❌ Error updating weights: {e}")
                return JsonResponse({"success": False, "error": str(e)})
        elif action == 'update_preset':
            try:
                import json

                
                preset_name = request.POST.get('preset_name')
                if not preset_name:
                    return JsonResponse({"success": False, "error": "Preset name required"})
                
                print(f"🔍 UPDATE PRESET: {preset_name}")
                
                # Find the preset to update
                try:
                    preset_config = ScoringConfiguration.objects.get(name=preset_name)
                    print(f"✅ Found preset to update: {preset_config.id}")
                except ScoringConfiguration.DoesNotExist:
                    return JsonResponse({"success": False, "error": f"Preset '{preset_name}' not found"})
                
                # Update all weight values from captured screen state
                preset_config.future_appointments_weight = int(request.POST.get("future_appointments_weight", 0))
                preset_config.age_demographics_weight = int(request.POST.get("age_demographics_weight", 0))
                preset_config.yearly_spend_weight = int(request.POST.get("yearly_spend_weight", 0))
                preset_config.consecutive_attendance_weight = int(request.POST.get("consecutive_attendance_weight", 0))
                preset_config.referrer_score_weight = int(request.POST.get("referrer_score_weight", 0))
                preset_config.cancellations_weight = int(request.POST.get("cancellations_weight", 0))
                preset_config.dna_weight = int(request.POST.get("dna_weight", 0))
                preset_config.unpaid_invoices_weight = int(request.POST.get("unpaid_invoices_weight", 0))
                preset_config.open_dna_invoice_weight = int(request.POST.get("open_dna_invoice_weight", 0))
                
                # Update all points values from captured screen state
                preset_config.points_per_consecutive_attendance = int(request.POST.get("points_per_consecutive_attendance", 0))
                preset_config.points_per_cancellation = int(request.POST.get("points_per_cancellation", 0))
                preset_config.points_per_dna = int(request.POST.get("points_per_dna", 0))
                preset_config.points_per_unpaid_invoice = int(request.POST.get("points_per_unpaid_invoice", 0))
                preset_config.points_per_referral = int(request.POST.get("points_per_referral", 0))
                
                # Save the updated configuration
                preset_config.save()
                print(f"✅ Updated preset configuration: {preset_name}")
                
                # Process captured age brackets data
                age_brackets_data = request.POST.get('age_brackets_data')
                if age_brackets_data:
                    try:
                        age_brackets = json.loads(age_brackets_data)
                        print(f"✅ Received {len(age_brackets)} age brackets from screen")
                        
                        # Delete existing age brackets for this preset
                        AgeBracket.objects.filter(config=preset_config).delete()
                        print(f"✅ Deleted existing age brackets for preset")
                        
                        # Create new age brackets from captured screen data
                        new_age_brackets = []
                        for bracket_data in age_brackets:
                            new_age_brackets.append(AgeBracket(
                                config=preset_config,
                                min_age=bracket_data['min_age'],
                                max_age=bracket_data['max_age'],
                                percentage=bracket_data['percentage'],
                                order=bracket_data['order']
                            ))
                        
                        AgeBracket.objects.bulk_create(new_age_brackets)
                        print(f"✅ Created {len(new_age_brackets)} new age brackets from screen state")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parsing age brackets JSON: {e}")
                    except Exception as e:
                        print(f"❌ Error processing age brackets: {e}")
                
                # Process captured spend brackets data
                spend_brackets_data = request.POST.get('spend_brackets_data')
                if spend_brackets_data:
                    try:
                        spend_brackets = json.loads(spend_brackets_data)
                        print(f"✅ Received {len(spend_brackets)} spend brackets from screen")
                        
                        # Delete existing spend brackets for this preset
                        SpendBracket.objects.filter(config=preset_config).delete()
                        print(f"✅ Deleted existing spend brackets for preset")
                        
                        # Create new spend brackets from captured screen data
                        new_spend_brackets = []
                        for bracket_data in spend_brackets:
                            new_spend_brackets.append(SpendBracket(
                                config=preset_config,
                                min_spend=bracket_data['min_spend'],
                                max_spend=bracket_data['max_spend'],
                                percentage=bracket_data['percentage'],
                                order=bracket_data['order']
                            ))
                        
                        SpendBracket.objects.bulk_create(new_spend_brackets)
                        print(f"✅ Created {len(new_spend_brackets)} new spend brackets from screen state")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parsing spend brackets JSON: {e}")
                    except Exception as e:
                        print(f"❌ Error processing spend brackets: {e}")
                
                return JsonResponse({
                    "success": True,
                    "message": f"Preset '{preset_name}' updated successfully with screen state"
                })
                
            except Exception as e:
                print(f"❌ Error updating preset: {e}")
                return JsonResponse({"success": False, "error": str(e)})

        elif action == "update_likability":
            patient_id = request.POST.get("patient_id")
            likability = request.POST.get("likability")
            print(f"💚 UPDATE LIKABILITY: Patient {patient_id} = {likability}")
            
            return JsonResponse({"success": True})

        elif action == "update_referrer_points":
            try:
                points_per_referral = int(request.POST.get('points_per_referral', 0))
                if 0 <= points_per_referral <= 100:
                    active_config.points_per_referral = points_per_referral
                    active_config.save()
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Points must be between 0 and 100'})
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid points value'})


        elif action == 'load_patient_behavior':
            """
            Load comprehensive patient behavior data for unified dashboard behavior cards
            Uses our complete 10-behavior system with proper data structure
            """
            try:
                patient_id = request.POST.get('patient_id')
                if not patient_id:
                    return JsonResponse({'success': False, 'error': 'Patient ID required'})
                
                print(f'🔍 Loading comprehensive behavior data for patient {patient_id}')
                
                # Get active scoring configuration
                try:
                    config, created = ScoringConfiguration.objects.get_or_create(name="Weights Updated", defaults={"description": "Working configuration", "is_active": True})
                    if not config:
                        return JsonResponse({'success': False, 'error': 'No active scoring configuration found'})
                except Exception as e:
                    print(f"❌ Error getting active config: {e}")
                    return JsonResponse({'success': False, 'error': 'Configuration error'})
                
                # Extract comprehensive behavior data using our helper functions
                behavior_data = extract_patient_behavior_data(patient_id, config)
                
                # Calculate total score and letter grade
                total_score = calculate_total_score(behavior_data)
                letter_grade = calculate_letter_grade(total_score)
                
                print(f'✅ Comprehensive behavior data loaded: {total_score} points, grade {letter_grade}')
                print(f'📊 Behaviors loaded: {len(behavior_data)} categories')
                
                # Transform comprehensive behavior data to match update function expectations
                formatted_data = {}
                
                # Process each behavior from our comprehensive system
                for behavior_name, behavior_info in behavior_data.items():
                    if isinstance(behavior_info, dict):
                        # Extract key information and format for update functions
                        points = behavior_info.get('points', 0)
                        count = behavior_info.get('count', 0)
                        
                        # Create description based on behavior type and data
                        if behavior_name == 'open_dna_invoice':
                            has_open = behavior_info.get('has_penalty', False)
                            description = f"{'Has' if has_open else 'No'} open DNA invoice"
                        elif behavior_name == 'unpaid_invoices':
                            description = f"{count} unpaid invoice{'s' if count != 1 else ''}"
                        elif behavior_name == 'dna':
                            description = f"{count} DNA occurrence{'s' if count != 1 else ''}"
                        elif behavior_name == 'cancellations':
                            description = f"{count} cancellation{'s' if count != 1 else ''}"
                        elif behavior_name == 'consecutive_attendance':
                            description = f"{count} consecutive attendance{'s' if count != 1 else ''}"
                        elif behavior_name == 'referrer_score':
                            description = f"{count} referral{'s' if count != 1 else ''}"
                        elif behavior_name == 'future_appointments':
                            has_future = behavior_info.get('has_future', False)
                            description = f"{'Has' if has_future else 'No'} future appointments"
                        elif behavior_name == 'age_demographics':
                            age = behavior_info.get('age', 0)
                            description = f"Age: {age} years"
                        elif behavior_name == 'yearly_spend':
                            spend = behavior_info.get('spend', 0)
                            description = f"Yearly spend: ${spend:.2f}"
                        elif behavior_name == 'likability':
                            description = f"Likability score: {points}"
                        else:
                            description = f"{behavior_name}: {points} points"
                        
                        # Format for update functions
                        formatted_data[behavior_name] = {
                            'description': description,
                            'points': points,
                            'count': count,
                            'has_penalty': points < 0
                        }
                    else:
                        # Handle simple numeric values
                        formatted_data[behavior_name] = {
                            'description': f"{behavior_name}: {behavior_info}",
                            'points': behavior_info,
                            'count': 0,
                            'has_penalty': behavior_info < 0
                        }
                
                print(f'✅ Formatted {len(formatted_data)} behaviors for update functions')
                
                return JsonResponse({
                    'success': True,
                    'behavior_data': formatted_data,
                    'total_score': total_score,
                    'letter_grade': letter_grade,
                    'patient_id': patient_id
                })
                
            except Exception as e:
                print(f"❌ Error loading comprehensive patient behavior: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({'success': False, 'error': str(e)})
        elif action == 'save_preset':
            try:
                print("🔧 SAVE PRESET: Reading screen values directly")
                
                # Get preset details from form
                preset_name = request.POST.get('preset_name', '').strip()
                preset_description = request.POST.get('preset_description', '').strip()
                
                if not preset_name:
                    return JsonResponse({'success': False, 'error': 'Preset name is required'})
                
                print(f"📋 Creating preset: '{preset_name}'")
                
                # Read current screen values directly from AJAX request
                config_data = {
                    'name': preset_name,
                    'description': preset_description,
                    'is_active': False,  # New presets are NOT active (not applied)
                    
                    # Slider weights - read directly from screen
                    'future_appointments_weight': int(request.POST.get('future_appointments_weight', 20)),
                    'age_demographics_weight': int(request.POST.get('age_demographics_weight', 20)),
                    'yearly_spend_weight': int(request.POST.get('yearly_spend_weight', 30)),
                    'consecutive_attendance_weight': int(request.POST.get('consecutive_attendance_weight', 20)),
                    'referrer_score_weight': int(request.POST.get('referrer_score_weight', 100)),
                    'cancellations_weight': int(request.POST.get('cancellations_weight', 20)),
                    'dna_weight': int(request.POST.get('dna_weight', 30)),
                    'unpaid_invoices_weight': int(request.POST.get('unpaid_invoices_weight', 60)),
                    'open_dna_invoice_weight': int(request.POST.get('open_dna_invoice_weight', 100)),
                    
                    # Points per occurrence - read directly from screen
                    'points_per_consecutive_attendance': int(request.POST.get('points_per_consecutive_attendance', 3)),
                    'points_per_referral': int(request.POST.get('points_per_referral', 10)),
                    'points_per_cancellation': int(request.POST.get('points_per_cancellation', 3)),
                    'points_per_dna': int(request.POST.get('points_per_dna', 8)),
                    'points_per_unpaid_invoice': int(request.POST.get('points_per_unpaid_invoice', 20)),
                }
                
                print(f"📊 Screen values captured: {len(config_data)} fields")
                
                # Create new preset with screen values (does NOT change active config)
                new_preset = ScoringConfiguration.objects.create(**config_data)
                
                # Handle age brackets from screen
                age_brackets_data = request.POST.get('age_brackets_data')
                if age_brackets_data:
                    import json
                    age_brackets = json.loads(age_brackets_data)
                    for index, bracket in enumerate(age_brackets):
                        AgeBracket.objects.create(
                            config=new_preset,
                            min_age=bracket['min_age'],
                            max_age=bracket['max_age'],
                            percentage=bracket['percentage'],
                            order=index + 1  # Sequential order: 1, 2, 3, 4, 5, 6
                        )
                    print(f"📊 Age brackets added: {len(age_brackets)}")
                
                # Handle spend brackets from screen
                spend_brackets_data = request.POST.get('spend_brackets_data')
                if spend_brackets_data:
                    spend_brackets = json.loads(spend_brackets_data)
                    for index, bracket in enumerate(spend_brackets):
                        SpendBracket.objects.create(
                            config=new_preset,
                            min_spend=bracket['min_spend'],
                            max_spend=bracket['max_spend'],
                            percentage=bracket['percentage'],
                            order=index + 1  # Sequential order: 1, 2, 3
                        )
                    print(f"📊 Spend brackets added: {len(spend_brackets)}")
                
                print(f"✅ PRESET CREATED: '{preset_name}' (ID: {new_preset.id}) - NOT APPLIED")
                print(f"✅ Active config unchanged - new preset available in dropdown")
                
                return JsonResponse({
                    'success': True,
                    'preset_id': new_preset.id,
                    'preset_name': preset_name,
                    'message': f"Preset '{preset_name}' created successfully"
                })
                
            except Exception as e:
                print(f"❌ SAVE PRESET ERROR: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'load_patient_data':
            patient_id = request.POST.get('patient_id')
            
            if not patient_id:
                return JsonResponse({'success': False, 'error': 'No patient ID provided'})
            
            try:
                # Get or create patient record
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'likability': 0}
                )
                
                return JsonResponse({
                    'success': True,
                    'likability': patient.likability
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Update Likability Handler
        elif action == 'update_likability':
            patient_id = request.POST.get('patient_id')
            likability = request.POST.get('likability')
            
            if not patient_id or likability is None:
                return JsonResponse({'success': False, 'error': 'Missing parameters'})
            
            try:
                likability = int(likability)
                if not (-100 <= likability <= 100):
                    return JsonResponse({'success': False, 'error': 'Invalid likability value'})
                
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'likability': likability}
                )
                
                patient.likability = likability
                patient.save()
                
                return JsonResponse({'success': True})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        

        # Referrer Score AJAX Handler
        elif action == 'update_referrer_points':
            try:
                points_per_referral = int(request.POST.get('points_per_referral', 0))
                if 0 <= points_per_referral <= 100:
                    config.points_per_referral = points_per_referral
                    config.save()
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Points must be between 0 and 100'})
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid points value'})
        elif action == "apply_preset":
            try:
                # Add a print statement at the very beginning
                print("DEBUG: Entering apply_preset action")
                
                preset_id = request.POST.get("preset_id")
                if not preset_id:
                    print("DEBUG: No preset ID provided")
                    return JsonResponse({"success": False, "error": "No preset ID provided"})
                
                try:
                    # Get the preset to apply
                    preset = ScoringConfiguration.objects.get(id=preset_id)
                    
                    print(f"DEBUG: Found preset {preset.name} (ID: {preset.id})")
                    
                    # CRITICAL: Deactivate ALL other presets
                    ScoringConfiguration.objects.all().update(is_active=False)
                    
                    # Activate ONLY the selected preset
                    preset.is_active = True
                    preset.save()
                    
                    print(f"DEBUG: Preset {preset.name} activated successfully")
                    
                    # Return success with preset data
                    preset_data = {
                        "id": preset.id,
                        "name": preset.name,
                        "description": preset.description,
                        "future_appointments_weight": preset.future_appointments_weight,
                        "age_demographics_weight": preset.age_demographics_weight,
                        "yearly_spend_weight": preset.yearly_spend_weight,
                        "consecutive_attendance_weight": preset.consecutive_attendance_weight,
                        "referrer_score_weight": preset.referrer_score_weight,
                        "cancellations_weight": preset.cancellations_weight,
                        "dna_weight": preset.dna_weight,
                        "unpaid_invoices_weight": preset.unpaid_invoices_weight,
                        "open_dna_invoice_weight": preset.open_dna_invoice_weight,
                        "points_per_consecutive_attendance": preset.points_per_consecutive_attendance,
                        "points_per_cancellation": preset.points_per_cancellation,
                        "points_per_dna": preset.points_per_dna,
                        "points_per_unpaid_invoice": preset.points_per_unpaid_invoice,
                        "points_per_referral": preset.points_per_referral,
                        "age_brackets": [
                            {
                                "id": bracket.id,
                                "min_age": bracket.min_age,
                                "max_age": bracket.max_age,
                                "percentage": bracket.percentage,
                                "order": bracket.order
                            } for bracket in preset.age_brackets.all().order_by("order")
                        ],
                        "spend_brackets": [
                            {
                                "id": bracket.id,
                                "min_spend": float(bracket.min_spend),
                                "max_spend": float(bracket.max_spend),
                                "percentage": bracket.percentage,
                                "order": bracket.order
                            } for bracket in preset.spend_brackets.all().order_by("order")
                        ]
                    }
                    
                    return JsonResponse({
                        "success": True,
                        "message": f"Preset '{preset.name}' applied successfully",
                        "preset": preset_data
                    })
                    
                except ScoringConfiguration.DoesNotExist:
                    print(f"DEBUG: Preset with ID {preset_id} does not exist")
                    return JsonResponse({"success": False, "error": f"Preset with ID {preset_id} not found"})
                
            except Exception as e:
                # Capture and print full traceback
                import traceback
                print("DEBUG: Unexpected error in apply_preset:")
                traceback.print_exc()
                
                # Return a JSON response with the error
                return JsonResponse({
                    "success": False, 
                    "error": str(e)
                }, status=500)

    # Handle update_weights action
    if request.method == "POST" and request.POST.get("action") == "update_weights":
        try:
            # Get the active configuration
            config, created = ScoringConfiguration.objects.get_or_create(name="Weights Updated", defaults={"description": "Working configuration", "is_active": True})
            if not config:
                return JsonResponse({"success": False, "error": "No active configuration found"})
            
            # Update all weight values
            config.future_appointments_weight = int(request.POST.get("future_appointments_weight", 0))
            config.age_demographics_weight = int(request.POST.get("age_demographics_weight", 0))
            config.yearly_spend_weight = int(request.POST.get("yearly_spend_weight", 0))
            config.consecutive_attendance_weight = int(request.POST.get("consecutive_attendance_weight", 0))
            config.referrer_score_weight = int(request.POST.get("referrer_score_weight", 0))
            config.cancellations_weight = int(request.POST.get("cancellations_weight", 0))
            config.dna_weight = int(request.POST.get("dna_weight", 0))
            config.unpaid_invoices_weight = int(request.POST.get("unpaid_invoices_weight", 0))
            config.open_dna_invoice_weight = int(request.POST.get("open_dna_invoice_weight", 0))
            
            # Update all points values
            config.points_per_consecutive_attendance = int(request.POST.get("points_per_consecutive_attendance", 0))
            config.points_per_cancellation = int(request.POST.get("points_per_cancellation", 0))
            config.points_per_dna = int(request.POST.get("points_per_dna", 0))
            config.points_per_unpaid_invoice = int(request.POST.get("points_per_unpaid_invoice", 0))
            config.points_per_referral = int(request.POST.get("points_per_referral", 0))
            
            # Save the configuration
            config.save()
            
            return JsonResponse({
                "success": True,
                "message": "Weights updated successfully"
            })
            
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # Handle update_preset action
    if request.method == "POST" and request.POST.get("action") == "update_preset":
        try:
            preset_name = request.POST.get("preset_name")
            if not preset_name:
                return JsonResponse({"success": False, "error": "Preset name is required"})
            
            # Find the existing preset to update
            preset = ScoringConfiguration.objects.filter(name=preset_name).first()
            if not preset:
                return JsonResponse({"success": False, "error": f"Preset '{preset_name}' not found"})
            
            # Update the preset with current screen values
            preset.future_appointments_weight = int(request.POST.get("future_appointments_weight", 0))
            preset.age_demographics_weight = int(request.POST.get("age_demographics_weight", 0))
            preset.yearly_spend_weight = int(request.POST.get("yearly_spend_weight", 0))
            preset.consecutive_attendance_weight = int(request.POST.get("consecutive_attendance_weight", 0))
            preset.referrer_score_weight = int(request.POST.get("referrer_score_weight", 0))
            preset.cancellations_weight = int(request.POST.get("cancellations_weight", 0))
            preset.dna_weight = int(request.POST.get("dna_weight", 0))
            preset.unpaid_invoices_weight = int(request.POST.get("unpaid_invoices_weight", 0))
            preset.open_dna_invoice_weight = int(request.POST.get("open_dna_invoice_weight", 0))
            
            # Update points values
            preset.points_per_consecutive_attendance = int(request.POST.get("points_per_consecutive_attendance", 0))
            preset.points_per_cancellation = int(request.POST.get("points_per_cancellation", 0))
            preset.points_per_dna = int(request.POST.get("points_per_dna", 0))
            preset.points_per_unpaid_invoice = int(request.POST.get("points_per_unpaid_invoice", 0))
            preset.points_per_referral = int(request.POST.get("points_per_referral", 0))
            
            # Save the updated preset
            preset.save()
            
            return JsonResponse({
                "success": True,
                "message": f"Preset '{preset_name}' updated successfully"
            })
            
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


            patient_id = request.POST.get('patient_id')
            # unlikability removed - was: unlikability = request.POST.get('unlikability')
            
            if not patient_id:  # unlikability check removed
                return JsonResponse({'success': False, 'error': 'Missing parameters'})
            
            try:
                # unlikability removed - was: unlikability = int(unlikability)
                if False:  # unlikability validation removed
                    return JsonResponse({'success': False, 'error': 'Feature removed'})
                
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'likability': 0}
                )
                
                # patient.unlikability removed
                patient.save()
                
                return JsonResponse({'success': True})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    # ==========================================
    # END PATIENT CARDS AJAX HANDLERS
    # ==========================================


    # Handle AJAX request for loading patient behavior data
    if request.method == 'POST' and request.POST.get('action') == 'load_patient_behavior':
        patient_id = request.POST.get('patient_id')
        if not patient_id:
            return JsonResponse({'success': False, 'error': 'Patient ID required'})
        
        try:
            # Use PatientSearchView to get DNA invoice data
            search_view = PatientSearchView()
            dna_data = search_view.get_open_dna_invoices(patient_id)
            likability_data = search_view.get_likability_data(patient_id)
            
            # Get active configuration for points calculation
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            
            # Calculate Open DNA Invoice points
            if dna_data['has_open_dna'] and active_config:
                # Apply penalty if patient has open DNA invoices
                dna_points = -active_config.open_dna_invoice_weight
            else:
                dna_points = 0
            
            behavior_data = {
                'open_dna_invoice': {
                    'count': dna_data['count'],
                    'description': dna_data['description'],
                    'points': dna_points,
                    'has_penalty': dna_data['has_open_dna']
                },
                'likability': {
                    'score': likability_data['likability_score'],
                    'description': likability_data['description'],
                    'status': likability_data['status'],
                    'is_positive': likability_data['is_positive'],
                    'is_negative': likability_data['is_negative'],
                    'is_neutral': likability_data['is_neutral']
                }
            }
            
            return JsonResponse({
                'success': True,
                'behavior_data': behavior_data
            })
            
        except Exception as e:
            print(f'❌ Error loading patient behavior: {e}')
            return JsonResponse({
                'success': False,
                'error': f'Failed to load behavior data: {str(e)}'})

    # Prepare context for template rendering
    try:
        active_config = ScoringConfiguration.objects.filter(is_active=True).first()
        if not active_config:
            # Create default configuration if none exists
            active_config = ScoringConfiguration.objects.create(
                name="Default Configuration",
                description="Auto-created default configuration",
                is_active=True
            )
    except Exception as e:
        print(f"Error getting active config: {e}")
        active_config = None

    # Add this block for GET request handling
    if request.method == 'GET':
        # Initialize empty lists
        age_brackets = []
        spend_brackets = []

        if active_config:
            try:
                age_brackets = AgeBracket.objects.filter(config=active_config).order_by('order')
                spend_brackets = SpendBracket.objects.filter(config=active_config).order_by('order')
                print(f"✅ Loaded {len(age_brackets)} age brackets and {len(spend_brackets)} spend brackets")
            except Exception as e:
                print(f"❌ Error loading brackets: {e}")
                age_brackets = []
                spend_brackets = []

        clinic_settings = RatedAppSettings.objects.first()
        return render(request, 'patient_rating/unified_dashboard.html', {
            "clinic_settings": clinic_settings,
            "active_config": active_config,
            "age_brackets": age_brackets,
            "spend_brackets": spend_brackets
        })


def get_presets(request):
    """Return JSON list of all saved presets for dropdown population"""
    if request.method == 'GET':
        try:
            presets = ScoringConfiguration.objects.exclude(name="Weights Updated").order_by('name')
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
            
            # CRITICAL FIX: Flatten slider values to root level for frontend compatibility
            # Positive behaviors
            'future_appointments_weight': preset.future_appointments_weight,
            'age_demographics_weight': preset.age_demographics_weight,
            'yearly_spend_weight': preset.yearly_spend_weight,
            'consecutive_attendance_weight': preset.consecutive_attendance_weight,
            'points_per_consecutive_attendance': preset.points_per_consecutive_attendance,
            'referrer_score_weight': preset.referrer_score_weight,
            'points_per_referral': preset.points_per_referral,
            
            # Negative behaviors
            'cancellations_weight': preset.cancellations_weight,
            'points_per_cancellation': preset.points_per_cancellation,
            'dna_weight': preset.dna_weight,
            'points_per_dna': preset.points_per_dna,
            'unpaid_invoices_weight': preset.unpaid_invoices_weight,
            'points_per_unpaid_invoice': preset.points_per_unpaid_invoice,
            'open_dna_invoice_weight': preset.open_dna_invoice_weight,
            
            # Metadata fields
            'likability_weight': preset.likability_weight,
            # unlikability_weight removed,
            
            # Brackets (unchanged)
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
        # Safe integer conversion (copied from working functions)
        def safe_int(value, default=0):
            if value is None or value == "":
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        try:

            
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
        # Safe integer conversion (copied from working functions)
        def safe_int(value, default=0):
            if value is None or value == "":
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        try:
            import json

            
            # Get active configuration
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            # Parse brackets data from request
            # Use form data instead of JSON
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
        # Safe integer conversion (copied from working functions)
        def safe_int(value, default=0):
            if value is None or value == "":
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        try:

            
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
        # Safe integer conversion (copied from working functions)
        def safe_int(value, default=0):
            if value is None or value == "":
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        try:
            import json

            
            # Get active configuration
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            # Parse brackets data from request
            # Use form data instead of JSON
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
# @transaction.atomic
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
            # Priority 1: Always try Factory Settings first
            try:
                next_preset = ScoringConfiguration.objects.get(name='Factory Settings')
                if next_preset.id == preset_id:
                    # If deleting Factory Settings itself, get next available
                    next_preset = ScoringConfiguration.objects.exclude(id=preset_id).first()
            except ScoringConfiguration.DoesNotExist:
                # If Factory Settings doesn't exist, get next available
                next_preset = ScoringConfiguration.objects.exclude(id=preset_id).first()
            if next_preset:
                # Deactivate all presets first
                # Activate the next preset
                next_preset.is_active = True
                next_preset.save()
        
        # Delete the preset (CASCADE will handle related objects)
        preset_name = preset_to_delete.name
        preset_to_delete.delete()
        
        # Verify deletion succeeded
        try:
            # Check if preset still exists (should raise DoesNotExist)
            ScoringConfiguration.objects.get(id=preset_id)
            # If we reach here, deletion failed
            return JsonResponse({
                'success': False,
                'error': f'Deletion failed - preset {preset_name} still exists'
            })
        except ScoringConfiguration.DoesNotExist:
            # This is expected - deletion succeeded
            print(f"DEBUG: Deletion verified - preset {preset_name} (ID: {preset_id}) successfully removed")
            pass
        
        
        # Get updated preset list for dropdown
        remaining_presets = list(ScoringConfiguration.objects.values('id', 'name', 'is_active'))
        
        # Find the currently active preset
        active_preset = ScoringConfiguration.objects.filter(is_active=True).first()
        # DEBUG: Log fallback preset info
        if active_preset:
            print(f"DEBUG: Fallback preset found - ID: {active_preset.id}, Name: {active_preset.name}")
        else:
            print("DEBUG: No active preset found after deletion")
            print(f"DEBUG: Total presets after deletion: {ScoringConfiguration.objects.count()}")
            print(f"DEBUG: is_active_preset was: {is_active_preset}")
            if is_active_preset:
                print("DEBUG: Should have switched to fallback preset, investigating...")
                all_presets = ScoringConfiguration.objects.all()
                for p in all_presets:
                    print(f"DEBUG: Preset {p.id} ({p.name}) - is_active: {p.is_active}")
        print(f"DEBUG: was_active_preset_deleted will be: {is_active_preset}")
        active_preset_id = active_preset.id if active_preset else None
        
        return JsonResponse({
            'success': True,
            'message': f'Preset "{preset_name}" deleted successfully',
            'was_active_preset_deleted': is_active_preset,
            'deleted_preset_id': int(preset_id),
            'fallback_preset': {
                'id': next_preset.id if next_preset else None,
                'name': next_preset.name if next_preset else None
            } if is_active_preset and next_preset else None,
            'remaining_presets': remaining_presets,
            'active_preset_id': active_preset_id,
            'total_remaining': len(remaining_presets)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting preset: {str(e)}'
        })



@csrf_exempt
@csrf_exempt
@csrf_exempt
@csrf_exempt
def create_preset(request):
    """Create a new preset - FIXED: Read screen values from form data"""
    if request.method == 'POST':
        try:
            # Get form data
            preset_name = request.POST.get('preset_name', '').strip()
            preset_description = request.POST.get('preset_description', '').strip()
            
            # Validation
            if not preset_name:
                return JsonResponse({'success': False, 'error': 'Preset name is required'})
            
            if len(preset_name) > 50:
                return JsonResponse({'success': False, 'error': 'Preset name must be 50 characters or less'})
            
            if len(preset_description) > 200:
                return JsonResponse({'success': False, 'error': 'Description must be 200 characters or less'})
            
            # Check for duplicate names
            if ScoringConfiguration.objects.filter(name=preset_name).exists():
                return JsonResponse({'success': False, 'error': f'Preset name "{preset_name}" already exists'})
            
            # Get active configuration for fallback values only
            active_config = ScoringConfiguration.objects.filter(is_active=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            # Safe integer conversion
            def safe_int(value, fallback):
                try:
                    return int(value) if value else fallback
                except (ValueError, TypeError):
                    return fallback
            
            # CRITICAL FIX: Read values from form data (screen values), fallback to active config
            new_preset = ScoringConfiguration.objects.create(
                name=preset_name,
                description=preset_description,
                is_active=False,
                # Read weight values from form data (sent by saveNewPreset)
                future_appointments_weight=safe_int(request.POST.get('future_appointments_weight'), active_config.future_appointments_weight),
                age_demographics_weight=safe_int(request.POST.get('age_demographics_weight'), active_config.age_demographics_weight),
                yearly_spend_weight=safe_int(request.POST.get('yearly_spend_weight'), active_config.yearly_spend_weight),
                consecutive_attendance_weight=safe_int(request.POST.get('consecutive_attendance_weight'), active_config.consecutive_attendance_weight),
                referrer_score_weight=safe_int(request.POST.get('referrer_score_weight'), active_config.referrer_score_weight),
                cancellations_weight=safe_int(request.POST.get('cancellations_weight'), active_config.cancellations_weight),
                dna_weight=safe_int(request.POST.get('dna_weight'), active_config.dna_weight),
                unpaid_invoices_weight=safe_int(request.POST.get('unpaid_invoices_weight'), active_config.unpaid_invoices_weight),
                open_dna_invoice_weight=safe_int(request.POST.get('open_dna_invoice_weight'), active_config.open_dna_invoice_weight),
                # Read points values from form data (sent by saveNewPreset)
                points_per_consecutive_attendance=safe_int(request.POST.get('points_per_consecutive_attendance'), active_config.points_per_consecutive_attendance),
                points_per_referral=safe_int(request.POST.get('points_per_referral'), active_config.points_per_referral),
                points_per_cancellation=safe_int(request.POST.get('points_per_cancellation'), active_config.points_per_cancellation),
                points_per_dna=safe_int(request.POST.get('points_per_dna'), active_config.points_per_dna),
                points_per_unpaid_invoice=safe_int(request.POST.get('points_per_unpaid_invoice'), active_config.points_per_unpaid_invoice)
            )
            
            # Handle screen bracket data (sent by saveNewPreset)
            age_brackets_copied = 0
            spend_brackets_copied = 0
            
            # Try to use screen bracket data first
            screen_age_brackets = request.POST.get('screen_age_brackets')
            if screen_age_brackets:
                try:
                    import json
                    age_brackets_data = json.loads(screen_age_brackets)
                    for bracket_data in age_brackets_data:
                        AgeBracket.objects.create(
                            config=new_preset,
                            min_age=bracket_data['min_age'],
                            max_age=bracket_data['max_age'],
                            percentage=bracket_data['percentage'],
                            order=bracket_data['order']
                        )
                        age_brackets_copied += 1
                except (json.JSONDecodeError, KeyError) as e:
                    # Fallback to copying from active config
                    for bracket in active_config.age_brackets.all():
                        AgeBracket.objects.create(
                            config=new_preset,
                            min_age=bracket.min_age,
                            max_age=bracket.max_age,
                            percentage=bracket.percentage,
                            order=bracket.order
                        )
                        age_brackets_copied += 1
            else:
                # Fallback: Copy from active config
                for bracket in active_config.age_brackets.all():
                    AgeBracket.objects.create(
                        config=new_preset,
                        min_age=bracket.min_age,
                        max_age=bracket.max_age,
                        percentage=bracket.percentage,
                        order=bracket.order
                    )
                    age_brackets_copied += 1
            
            # Try to use screen spend bracket data
            screen_spend_brackets = request.POST.get('screen_spend_brackets')
            if screen_spend_brackets:
                try:
                    spend_brackets_data = json.loads(screen_spend_brackets)
                    for bracket_data in spend_brackets_data:
                        SpendBracket.objects.create(
                            config=new_preset,
                            min_spend=bracket_data['min_spend'],
                            max_spend=bracket_data['max_spend'],
                            percentage=bracket_data['percentage'],
                            order=bracket_data['order']
                        )
                        spend_brackets_copied += 1
                except (json.JSONDecodeError, KeyError) as e:
                    # Fallback to copying from active config
                    for bracket in active_config.spend_brackets.all():
                        SpendBracket.objects.create(
                            config=new_preset,
                            min_spend=bracket.min_spend,
                            max_spend=bracket.max_spend,
                            percentage=bracket.percentage,
                            order=bracket.order
                        )
                        spend_brackets_copied += 1
            else:
                # Fallback: Copy from active config
                for bracket in active_config.spend_brackets.all():
                    SpendBracket.objects.create(
                        config=new_preset,
                        min_spend=bracket.min_spend,
                        max_spend=bracket.max_spend,
                        percentage=bracket.percentage,
                        order=bracket.order
                    )
                    spend_brackets_copied += 1
            
            return JsonResponse({
                'success': True,
                'preset_id': new_preset.id,
                'preset_name': new_preset.name,
                'age_brackets_copied': age_brackets_copied,
                'spend_brackets_copied': spend_brackets_copied,
                'message': f'Preset "{preset_name}" created successfully with current screen values: {age_brackets_copied} age brackets and {spend_brackets_copied} spend brackets'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Database error: {str(e)}'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def update_likability(request):
    """Update patient likability score"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            patient_id = data.get('patient_id')
            likability = int(data.get('likability', 0))
            
            # Validate likability value
            if not (-100 <= likability <= 100):
                return JsonResponse({'success': False, 'error': 'Likability must be between 0 and 100'})
            
            # Get or create patient
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'patient_name': f'Patient {patient_id}'}
            )
            
            # Update likability
            patient.likability = likability
            patient.save()
            
            return JsonResponse({'success': True, 'likability': likability})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

class PatientDashboardScoreView(View):
    """
    Dedicated endpoint for unified dashboard to get patient scores AND behavior data.
    Uses the working analyzer with config parameter like PatientAnalysisView.
    """
    def get(self, request, patient_id):
        try:
            # Get active scoring configuration (same as PatientAnalysisView)
            config = ScoringConfiguration.get_active_config()
            
            # Use the working analyzer function WITH config
            analysis_result = analyze_patient_behavior(patient_id, config)
            
            if analysis_result and 'behavior_data' in analysis_result:
                return JsonResponse({
                    'success': True,
                    'score': analysis_result.get('total_score', 0),
                    'grade': analysis_result.get('letter_grade', 'F'),
                    'patient_id': patient_id,
                    'behavior_data': analysis_result['behavior_data'],  # Include behavior data for cards
                    'patient_name': analysis_result.get('patient_name', f'Patient {patient_id}')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to calculate patient score or extract behavior data',
                    'patient_id': patient_id
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Score calculation error: {str(e)}',
                'patient_id': patient_id
            })
# ==========================================
# PATIENT BEHAVIOR DATA HELPER FUNCTIONS
# ==========================================

def extract_patient_behavior_data(patient_id, config):
    """Extract comprehensive patient behavior data from Cliniko API - PHASE 1: Real Data Test"""
    try:
        print(f"🔍 PHASE 1: Extracting REAL behavior data for patient {patient_id}")
        
        # Initialize behavior data structure
        behavior_data = {}
        
        # Get the search view instance for API calls
        search_view = PatientSearchView()
        
        # 1. FUTURE APPOINTMENTS - Real API call
        try:
            future_data = search_view.get_future_appointments(patient_id)
            behavior_data['future_appointments'] = {
                'count': future_data['count'],
                'description': future_data['description'],
                'points': 0,  # Phase 1: Show raw data, no scoring yet
                'has_appointments': future_data['has_appointments']
            }
            print(f"✅ Future appointments: {future_data['count']}")
        except Exception as e:
            print(f"❌ Future appointments error: {e}")
            behavior_data['future_appointments'] = {'count': 0, 'description': 'Error loading', 'points': 0, 'has_appointments': False}
        
        # 2. AGE DEMOGRAPHICS - Real API call
        try:
            age_data = search_view.get_patient_age(patient_id)
            behavior_data['age_demographics'] = {
                'age': age_data['age'],
                'description': f"Age: {age_data['age']} years",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ Patient age: {age_data['age']}")
        except Exception as e:
            print(f"❌ Age demographics error: {e}")
            behavior_data['age_demographics'] = {'age': 0, 'description': 'Age: Unknown', 'points': 0}
        
        # 3. YEARLY SPEND - Real API call
        try:
            spend_data = search_view.get_yearly_spend(patient_id)
            behavior_data['yearly_spend'] = {
                'amount': spend_data['amount'],
                'description': f"Yearly spend: ${spend_data['amount']:.2f}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ Yearly spend: ${spend_data['amount']:.2f}")
        except Exception as e:
            print(f"❌ Yearly spend error: {e}")
            behavior_data['yearly_spend'] = {'amount': 0, 'description': 'Yearly spend: $0.00', 'points': 0}
        
        # 4. CONSECUTIVE ATTENDANCE - Real API call
        try:
            attendance_data = search_view.get_consecutive_attendance(patient_id)
            behavior_data['consecutive_attendance'] = {
                'streak': attendance_data['streak'],
                'description': f"{attendance_data['streak']} consecutive attendance{'s' if attendance_data['streak'] != 1 else ''}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ Consecutive attendance: {attendance_data['streak']}")
        except Exception as e:
            print(f"❌ Consecutive attendance error: {e}")
            behavior_data['consecutive_attendance'] = {'streak': 0, 'description': '0 consecutive attendances', 'points': 0}
        
        # 5. REFERRER SCORE - Real API call
        try:
            referrer_data = search_view.get_referrer_score(patient_id)
            behavior_data['referrer_score'] = {
                'referrals': referrer_data['referrals'],
                'description': f"{referrer_data['referrals']} referral{'s' if referrer_data['referrals'] != 1 else ''}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ Referrals made: {referrer_data['referrals']}")
        except Exception as e:
            print(f"❌ Referrer score error: {e}")
            behavior_data['referrer_score'] = {'referrals': 0, 'description': '0 referrals', 'points': 0}
        
        # 6. CANCELLATIONS - Real API call
        try:
            cancel_data = search_view.get_cancellations(patient_id)
            behavior_data['cancellations'] = {
                'count': cancel_data['count'],
                'description': f"{cancel_data['count']} cancellation{'s' if cancel_data['count'] != 1 else ''}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ Cancellations: {cancel_data['count']}")
        except Exception as e:
            print(f"❌ Cancellations error: {e}")
            behavior_data['cancellations'] = {'count': 0, 'description': '0 cancellations', 'points': 0}
        
        # 7. DNA (Did Not Arrive) - Real API call
        try:
            dna_data = search_view.get_dna_count(patient_id)
            behavior_data['dna'] = {
                'count': dna_data['count'],
                'description': f"{dna_data['count']} DNA occurrence{'s' if dna_data['count'] != 1 else ''}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ DNA occurrences: {dna_data['count']}")
        except Exception as e:
            print(f"❌ DNA error: {e}")
            behavior_data['dna'] = {'count': 0, 'description': '0 DNA occurrences', 'points': 0}
        
        # 8. UNPAID INVOICES - Real API call
        try:
            unpaid_data = search_view.get_unpaid_invoices(patient_id)
            behavior_data['unpaid_invoices'] = {
                'count': unpaid_data['count'],
                'description': f"{unpaid_data['count']} unpaid invoice{'s' if unpaid_data['count'] != 1 else ''}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ Unpaid invoices: {unpaid_data['count']}")
        except Exception as e:
            print(f"❌ Unpaid invoices error: {e}")
            behavior_data['unpaid_invoices'] = {'count': 0, 'description': '0 unpaid invoices', 'points': 0}
        
        # 9. OPEN DNA INVOICES - Real API call
        try:
            open_dna_data = search_view.get_open_dna_invoices(patient_id)
            behavior_data['open_dna_invoice'] = {
                'count': open_dna_data['count'],
                'description': f"{'Has' if open_dna_data['has_open_dna'] else 'No'} open DNA invoice{'s' if open_dna_data['count'] != 1 else ''}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
                'has_penalty': open_dna_data['has_open_dna']
            }
            print(f"✅ Open DNA invoices: {open_dna_data['count']}")
        except Exception as e:
            print(f"❌ Open DNA invoices error: {e}")
            behavior_data['open_dna_invoice'] = {'count': 0, 'description': 'No open DNA invoice', 'points': 0, 'has_penalty': False}
        
        # 10. LIKABILITY - Manual scoring (unchanged)
        try:
            patient = Patient.objects.get(cliniko_id=patient_id)
            likability_score = patient.likability
            behavior_data['likability'] = {
                'score': likability_score,
                'description': f"Likability score: {likability_score}",
                'points': 0,  # Phase 1: Show raw data, no scoring yet
            }
            print(f"✅ Likability score: {likability_score}")
        except Patient.DoesNotExist:
            behavior_data['likability'] = {'score': 0, 'description': 'Likability score: 0', 'points': 0}
        except Exception as e:
            print(f"❌ Likability error: {e}")
            behavior_data['likability'] = {'score': 0, 'description': 'Likability score: 0', 'points': 0}
        
        print(f"✅ PHASE 1 COMPLETE: Extracted {len(behavior_data)} real behaviors for patient {patient_id}")
        return behavior_data
        
    except Exception as e:
        print(f"❌ Error in extract_patient_behavior_data: {e}")
        raise

@csrf_exempt
def update_clinic_settings(request):
    try:
        if request.method == 'GET':
            settings = RatedAppSettings.objects.first()
            if not settings:
                return JsonResponse({
                    'success': False, 
                    'error': 'No settings found'
                }, status=404)
            
            return JsonResponse({
                'success': True,
                'settings': {
                    'clinic_information': {
                        'clinic_name': settings.clinic_name,
                        'clinic_location': settings.clinic_location or '',
                        'clinic_timezone': settings.clinic_timezone
                    },
                    'connectivity': {
                        'software_integration': settings.software_integration or '',
                        'api_key': '****' + settings.api_key[-4:] if settings.api_key else None
                    }
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            
            # Validate section
            section = data.get('section')
            if not section:
                return JsonResponse({
                    'success': False, 
                    'error': 'Section is required'
                }, status=400)
            
            # Get existing settings
            settings = RatedAppSettings.objects.first()
            
            # Validation and update logic
            section_handlers = {
                'clinic_information': {
                    'validate': lambda d: bool(d.get('clinic_name')),
                    'update': lambda settings, d: {
                        'clinic_name': d.get('clinic_name'),
                        'clinic_location': d.get('clinic_location', settings.clinic_location),
                        'clinic_timezone': d.get('clinic_timezone', settings.clinic_timezone)
                    }
                },
                'connectivity': {
                    'validate': lambda d: True,  # No strict validation
                    'update': lambda settings, d: {
                        'software_integration': d.get('software_integration', settings.software_integration),
                        'api_key': d.get('api_key', settings.api_key)
                    }
                }
            }
            
            # Check if section is supported
            if section not in section_handlers:
                return JsonResponse({
                    'success': False, 
                    'error': f'Unsupported section: {section}'
                }, status=400)
            
            # Validate section data
            handler = section_handlers[section]
            if not handler['validate'](data):
                return JsonResponse({
                    'success': False, 
                    'error': f'Invalid data for {section} section'
                }, status=400)
            
            # Update settings
            updates = handler['update'](settings, data)
            for key, value in updates.items():
                setattr(settings, key, value)
            
            settings.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{section.replace("_", " ").title()} settings updated successfully',
                'updated_section': section,
                'settings': {
                    'clinic_information': {
                        'clinic_name': settings.clinic_name,
                        'clinic_location': settings.clinic_location,
                        'clinic_timezone': settings.clinic_timezone
                    },
                    'connectivity': {
                        'software_integration': settings.software_integration or '',
                        'api_key': '****' + settings.api_key[-4] if settings.api_key else None
                    }
                }
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid JSON',
            'details': 'Request body must be a valid JSON object'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': 'Unexpected error',
            'details': str(e)
        }, status=500)
@require_http_methods(["GET"])
def validate_cliniko_api_key(request):
    api_key = request.GET.get('api_key')
    
    if not api_key:
        return JsonResponse({
            'status': 'Disconnected',
            'error': 'API key required'
        }, status=400)
    
    try:
        # Encode API key for Basic Auth
        encoded_key = base64.b64encode(f"{api_key}:".encode()).decode()
        
        response = requests.get(
            'https://api.au1.cliniko.com/v1/patients',
            headers={
                'Accept': 'application/json',
                'Authorization': f'Basic {encoded_key}'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return JsonResponse({
                'status': 'Connected',
                'message': 'API key is valid'
            })
        else:
            return JsonResponse({
                'status': 'Disconnected',
                'error': 'Invalid API key'
            }, status=401)
    
    except requests.RequestException as e:
        return JsonResponse({
            'status': 'Disconnected',
            'error': 'Network Error'
        }, status=500)