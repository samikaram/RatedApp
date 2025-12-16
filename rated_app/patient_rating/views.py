import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_http_methods
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db.models import F
from django.db import models, IntegrityError, transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command  # NEW
from threading import Thread  # NEW
import time
from django.utils import timezone
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Import models
from .models import (
    RatedAppSettings, ScoringConfiguration, Patient, 
    AgeBracket, SpendBracket, AnalyticsJob
)

# Import plugin architecture components
from .integrations.factory import IntegrationFactory
from .behavioral_processor import BehavioralProcessor

# Helper function for safe integer conversion
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
            # Get settings and initialize plugin client
            settings = RatedAppSettings.objects.first()
            if not settings:
                return render(request, 'patient_rating/patient_search.html', {
                    'error': 'System not configured. Please configure settings first.'
                })
            
            # Get client and normalizer from factory
            client = IntegrationFactory.get_client(settings)
            normalizer = IntegrationFactory.get_normalizer(settings)
            
            if search_type == 'name':
                patients = self.search_by_name_plugin(search_value, client, normalizer)
            elif search_type == 'id':
                patients = self.search_by_id_plugin(search_value, client, normalizer)
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
    
    def search_by_name_plugin(self, name, client, normalizer):
        """Search patients by name using plugin architecture"""
        # Use client to search patients
        raw_patients = client.search_patients(name=name)
        
        # Normalize and format patient data
        formatted_patients = []
        for raw_patient in raw_patients:
            normalized = normalizer.normalize_patient(raw_patient)
            
            # Extract phone numbers if available
            phone = self.get_phone_numbers_plugin(raw_patient)
            
            formatted_patients.append({
                'id': normalized['id'],
                'first_name': normalized['first_name'],
                'last_name': normalized['last_name'],
                'email': normalized['email'],
                'phone': phone,
                'date_of_birth': normalized['date_of_birth'],
                'full_name': normalized['full_name']
            })
        
        return formatted_patients
    
    def search_by_id_plugin(self, patient_id, client, normalizer):
        """Search patient by ID using plugin architecture"""
        # Get specific patient using filter
        patients = client.get_patients(filters={'id': patient_id})
        
        if not patients:
            return []
        
        raw_patient = patients[0]
        normalized = normalizer.normalize_patient(raw_patient)
        phone = self.get_phone_numbers_plugin(raw_patient)
        
        return [{
            'id': normalized['id'],
            'first_name': normalized['first_name'],
            'last_name': normalized['last_name'],
            'email': normalized['email'],
            'phone': phone,
            'date_of_birth': normalized['date_of_birth'],
            'full_name': normalized['full_name']
        }]
    
    def get_phone_numbers_plugin(self, patient):
        """Extract phone numbers from raw patient data"""
        phone_numbers = patient.get('patient_phone_numbers', [])
        if not phone_numbers:
            # Try mobile phone field
            mobile = patient.get('mobile_phone', '')
            return mobile if mobile else "Not provided"
        
        formatted_phones = []
        for phone in phone_numbers:
            number = phone.get('number', '')
            phone_type = phone.get('phone_type', '')
            if number:
                formatted_phones.append(f"{number} ({phone_type})")
        return " | ".join(formatted_phones) if formatted_phones else "Not provided"
    
    def get_open_dna_invoices(self, patient_id):
        """Get open DNA invoices using plugin architecture"""
        try:
            settings = RatedAppSettings.objects.first()
            if not settings:
                return {'count': 0, 'has_open_dna': False, 'description': 'System not configured'}
            
            client = IntegrationFactory.get_client(settings)
            
            # Get invoices for patient
            invoices = client.get_invoices(patient_id)
            
            open_dna_count = 0
            for invoice in invoices:
                # Check if unpaid and DNA-related
                if (not invoice.get('closed_at') and 
                    ('DNA' in str(invoice.get('description', '')).upper() or
                     'DID NOT ARRIVE' in str(invoice.get('description', '')).upper() or
                     'DNA' in str(invoice.get('notes', '')).upper())):
                    open_dna_count += 1
            
            return {
                'count': open_dna_count,
                'has_open_dna': open_dna_count > 0,
                'description': f"{open_dna_count} open DNA invoices" if open_dna_count != 1 else "1 open DNA invoice"
            }
            
        except Exception as e:
            print(f"Error getting DNA invoices for patient {patient_id}: {e}")
            return {'count': 0, 'has_open_dna': False, 'description': "Error loading DNA invoices"}
    
    def get_likability_data(self, patient_id):
        """Get or create likability data for a patient"""
        try:
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'likability': 0}
            )
            
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
            print(f"Error getting likability for patient {patient_id}: {e}")
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
                
                if not (-100 <= likability <= 100):
                    return JsonResponse({'success': False, 'error': 'Likability must be between -100 and 100'})
                
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'patient_name': f'Patient {patient_id}'}
                )
                
                patient.likability = likability
                patient.save()
                
                return JsonResponse({'success': True, 'likability': likability})
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Continue with existing analysis logic
        try:
            config = ScoringConfiguration.get_active_config()
            analysis = self.analyze_patient_behavior_plugin(patient_id, config)
            
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
    
    def analyze_patient_behavior_plugin(self, patient_id, config):
        """Analyze patient behavior using plugin architecture"""
        try:
            settings = RatedAppSettings.objects.first()
            if not settings:
                return None
            
            # Get client and normalizer
            client = IntegrationFactory.get_client(settings)
            normalizer = IntegrationFactory.get_normalizer(settings)
            
            # Get raw data from Cliniko
            patients = client.get_patients(filters={'id': patient_id})
            if not patients:
                return None
            
            raw_patient = patients[0]
            appointments = client.get_appointments(patient_id)
            invoices = client.get_invoices(patient_id)
            referral_data = client.get_referrals(patient_id)
            
            # Normalize the data
            normalized_patient = normalizer.normalize_patient(raw_patient)
            
            # Prepare data for behavioral processor (use RAW data as processor expects Cliniko format)
            patient_data = {
                'id': patient_id,
                'date_of_birth': raw_patient.get('date_of_birth'),  # Use raw DOB
                'appointments': appointments,  # Raw appointments
                'invoices': invoices,  # Raw invoices
                'referrals': referral_data.get('referred_patient_ids', []) if isinstance(referral_data, dict) else []
            }
            
            # Process behavior using BehavioralProcessor
            processor = BehavioralProcessor()
            result = processor.process_patient_behavior(patient_data, config, settings)
            
            # Add patient name from normalized data
            result['patient_name'] = normalized_patient['full_name']
            
            return result
            
        except Exception as e:
            print(f"Error in analyze_patient_behavior_plugin: {e}")
            import traceback
            traceback.print_exc()
            return None


class UpdateLikabilityView(View):
    def post(self, request):
        try:
            patient_id = request.POST.get('patient_id')
            likability_value = int(request.POST.get('likability', 0))
            
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'patient_name': f'Patient {patient_id}'}
            )
            
            patient.likability = likability_value
            patient.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


def get_referrer_count_plugin(patient_id, settings):
    """Get referrer count using plugin architecture"""
    try:
        client = IntegrationFactory.get_client(settings)
        referral_data = client.get_referrals(patient_id)
        
        if isinstance(referral_data, dict):
            return referral_data.get('referral_count', 0)
        return 0
        
    except Exception as e:
        print(f"Error getting referrer count for patient {patient_id}: {e}")
        return 0


def calculate_referrer_score(patient_id, points_per_referral, max_points):
    """Calculate referrer score with points cap logic"""
    settings = RatedAppSettings.objects.first()
    if not settings:
        return 0
    
    referral_count = get_referrer_count_plugin(patient_id, settings)
    raw_score = referral_count * points_per_referral
    final_score = min(raw_score, max_points)
    
    print(f"Referrer score for patient {patient_id}: {referral_count} referrals × {points_per_referral} points = {raw_score}, capped at {max_points} = {final_score}")
    
    return final_score


def unified_dashboard(request):
    print("=== UNIFIED DASHBOARD REQUEST DEBUG ===")
    print(f"Method: {request.method}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    print(f"POST data: {dict(request.POST)}")
    print("=" * 50)
    
    # AJAX Handlers
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        action = request.POST.get("action")
        print(f"AJAX ACTION RECEIVED: {action}")
        
        if action == "search_patients":
            search_term = request.POST.get("search_term", "").strip()
            print(f"SEARCH REQUEST: '{search_term}'")
            
            if len(search_term) < 2:
                print("Search term too short")
                return JsonResponse({"success": False, "error": "Search term too short"})
            
            try:
                settings = RatedAppSettings.objects.first()
                if not settings:
                    return JsonResponse({"success": False, "error": "System not configured"})
                
                client = IntegrationFactory.get_client(settings)
                normalizer = IntegrationFactory.get_normalizer(settings)
                
                # Search using plugin
                raw_patients = client.search_patients(name=search_term)
                
                test_patients = []
                for raw_patient in raw_patients:
                    normalized = normalizer.normalize_patient(raw_patient)
                    test_patients.append({
                        "id": normalized['id'],
                        "name": normalized['full_name']
                    })
                
                if not test_patients:
                    test_patients = [{"id": 0, "name": "No patients found"}]
                
            except Exception as e:
                print(f"API Error: {e}")
                test_patients = [{"id": 0, "name": f"Search error: {str(e)}"}]
            
            print(f"Returning {len(test_patients)} test patients")
            
            return JsonResponse({
                "success": True,
                "patients": test_patients
            })
        
        elif action == 'update_likability':
            try:
                patient_id = request.POST.get('patient_id')
                likability = int(request.POST.get('likability', 0))
                
                if not (-100 <= likability <= 100):
                    return JsonResponse({'success': False, 'error': 'Likability must be between -100 and 100'})
                
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'patient_name': f'Patient {patient_id}'}
                )
                
                patient.likability = likability
                patient.save()
                
                print(f"SAVED LIKABILITY: Patient {patient_id} = {likability}")
                return JsonResponse({'success': True, 'likability': likability})
                
            except Exception as e:
                print(f"LIKABILITY ERROR: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'update_weights':
            try:
                # Store testing configuration in session instead of database
                testing_config = {
                    'is_testing': True,
                    'future_appointments_weight': int(request.POST.get("future_appointments_weight", 0)),
                    'age_demographics_weight': int(request.POST.get("age_demographics_weight", 0)),
                    'yearly_spend_weight': int(request.POST.get("yearly_spend_weight", 0)),
                    'consecutive_attendance_weight': int(request.POST.get("consecutive_attendance_weight", 0)),
                    'referrer_score_weight': int(request.POST.get("referrer_score_weight", 0)),
                    'cancellations_weight': int(request.POST.get("cancellations_weight", 0)),
                    'dna_weight': int(request.POST.get("dna_weight", 0)),
                    'unpaid_invoices_weight': int(request.POST.get("unpaid_invoices_weight", 0)),
                    'open_dna_invoice_weight': int(request.POST.get("open_dna_invoice_weight", 0)),
                    'points_per_consecutive_attendance': int(request.POST.get("points_per_consecutive_attendance", 0)),
                    'points_per_cancellation': int(request.POST.get("points_per_cancellation", 0)),
                    'points_per_dna': int(request.POST.get("points_per_dna", 0)),
                    'points_per_unpaid_invoice': int(request.POST.get("points_per_unpaid_invoice", 0)),
                    'points_per_referral': int(request.POST.get("points_per_referral", 0))
                }
                
                request.session['testing_config'] = testing_config
                
                return JsonResponse({
                    "success": True,
                    "message": "Testing configuration active"
                })
                
            except Exception as e:
                print(f"Error in update_weights: {e}")
                return JsonResponse({"success": False, "error": str(e)})
                
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
                
                config.save()
                
                return JsonResponse({
                    "success": True,
                    "message": "Weights updated successfully"
                })
                
            except Exception as e:
                print(f"Error updating weights: {e}")
                return JsonResponse({"success": False, "error": str(e)})
        
        elif action == 'update_preset':
            try:
                import json
                
                preset_name = request.POST.get('preset_name')
                if not preset_name:
                    return JsonResponse({"success": False, "error": "Preset name required"})
                
                print(f"UPDATE PRESET: {preset_name}")
                
                try:
                    preset_config = ScoringConfiguration.objects.get(name=preset_name)
                    print(f"Found preset to update: {preset_config.id}")
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
                
                # Update all points values
                preset_config.points_per_consecutive_attendance = int(request.POST.get("points_per_consecutive_attendance", 0))
                preset_config.points_per_cancellation = int(request.POST.get("points_per_cancellation", 0))
                preset_config.points_per_dna = int(request.POST.get("points_per_dna", 0))
                preset_config.points_per_unpaid_invoice = int(request.POST.get("points_per_unpaid_invoice", 0))
                preset_config.points_per_referral = int(request.POST.get("points_per_referral", 0))
                
                preset_config.save()
                print(f"Updated preset configuration: {preset_name}")
                
                # Process age brackets data
                age_brackets_data = request.POST.get('age_brackets_data')
                if age_brackets_data:
                    try:
                        age_brackets = json.loads(age_brackets_data)
                        print(f"Received {len(age_brackets)} age brackets from screen")
                        
                        AgeBracket.objects.filter(config=preset_config).delete()
                        print(f"Deleted existing age brackets for preset")
                        
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
                        print(f"Created {len(new_age_brackets)} new age brackets from screen state")
                        
                    except json.JSONDecodeError as e:
                        print(f"Error parsing age brackets JSON: {e}")
                    except Exception as e:
                        print(f"Error processing age brackets: {e}")
                
                # Process spend brackets data
                spend_brackets_data = request.POST.get('spend_brackets_data')
                if spend_brackets_data:
                    try:
                        spend_brackets = json.loads(spend_brackets_data)
                        print(f"Received {len(spend_brackets)} spend brackets from screen")
                        
                        SpendBracket.objects.filter(config=preset_config).delete()
                        print(f"Deleted existing spend brackets for preset")
                        
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
                        print(f"Created {len(new_spend_brackets)} new spend brackets from screen state")
                        
                    except json.JSONDecodeError as e:
                        print(f"Error parsing spend brackets JSON: {e}")
                    except Exception as e:
                        print(f"Error processing spend brackets: {e}")
                
                return JsonResponse({
                    "success": True,
                    "message": f"Preset '{preset_name}' updated successfully with screen state"
                })
                
            except Exception as e:
                print(f"Error updating preset: {e}")
                return JsonResponse({"success": False, "error": str(e)})
        
        elif action == 'load_patient_behavior':
            try:
                patient_id = request.POST.get('patient_id')
                if not patient_id:
                    return JsonResponse({'success': False, 'error': 'Patient ID required'})
                
                print(f'Loading comprehensive behavior data for patient {patient_id}')
                
                try:
                    # Check for testing configuration in session first
                    if request.session.get('testing_config'):
                        # Use testing config from session
                        config = request.session['testing_config']
                    else:
                        # Use active behavior preset
                        config = ScoringConfiguration.objects.filter(is_active_for_behavior=True).first()
                    
                    if not config:
                        return JsonResponse({'success': False, 'error': 'No active scoring configuration found'})
                except Exception as e:
                    print(f"Error getting active config: {e}")
                    return JsonResponse({'success': False, 'error': 'Configuration error'})
                
                # Extract behavior data using plugin architecture
                behavior_data = extract_patient_behavior_data_plugin(patient_id, config)
                
                # Calculate total score and letter grade
                total_score = calculate_total_score(behavior_data)
                letter_grade = calculate_letter_grade(total_score)
                
                print(f'Comprehensive behavior data loaded: {total_score} points, grade {letter_grade}')
                print(f'Behaviors loaded: {len(behavior_data)} categories')
                
                # Format data for frontend
                formatted_data = {}
                for behavior_name, behavior_info in behavior_data.items():
                    if isinstance(behavior_info, dict):
                        points = behavior_info.get('points', 0)
                        count = behavior_info.get('count', 0)
                        
                        # Create descriptions
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
                        
                        formatted_data[behavior_name] = {
                            'description': description,
                            'points': points,
                            'count': count,
                            'has_penalty': points < 0
                        }
                    else:
                        formatted_data[behavior_name] = {
                            'description': f"{behavior_name}: {behavior_info}",
                            'points': behavior_info,
                            'count': 0,
                            'has_penalty': behavior_info < 0
                        }
                
                print(f'Formatted {len(formatted_data)} behaviors for update functions')
                
                return JsonResponse({
                    'success': True,
                    'behavior_data': formatted_data,
                    'total_score': total_score,
                    'letter_grade': letter_grade,
                    'patient_id': patient_id
                })
                
            except Exception as e:
                print(f"Error loading comprehensive patient behavior: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'save_preset':
            try:
                print("SAVE PRESET: Reading screen values directly")
                
                preset_name = request.POST.get('preset_name', '').strip()
                preset_description = request.POST.get('preset_description', '').strip()
                
                if not preset_name:
                    return JsonResponse({'success': False, 'error': 'Preset name is required'})
                
                print(f"Creating preset: '{preset_name}'")
                
                config_data = {
                    'name': preset_name,
                    'description': preset_description,
                    'is_active_for_behavior': False,
                    
                    # Slider weights
                    'future_appointments_weight': int(request.POST.get('future_appointments_weight', 20)),
                    'age_demographics_weight': int(request.POST.get('age_demographics_weight', 20)),
                    'yearly_spend_weight': int(request.POST.get('yearly_spend_weight', 30)),
                    'consecutive_attendance_weight': int(request.POST.get('consecutive_attendance_weight', 20)),
                    'referrer_score_weight': int(request.POST.get('referrer_score_weight', 100)),
                    'cancellations_weight': int(request.POST.get('cancellations_weight', 20)),
                    'dna_weight': int(request.POST.get('dna_weight', 30)),
                    'unpaid_invoices_weight': int(request.POST.get('unpaid_invoices_weight', 60)),
                    'open_dna_invoice_weight': int(request.POST.get('open_dna_invoice_weight', 100)),
                    
                    # Points per occurrence
                    'points_per_consecutive_attendance': int(request.POST.get('points_per_consecutive_attendance', 3)),
                    'points_per_referral': int(request.POST.get('points_per_referral', 10)),
                    'points_per_cancellation': int(request.POST.get('points_per_cancellation', 3)),
                    'points_per_dna': int(request.POST.get('points_per_dna', 8)),
                    'points_per_unpaid_invoice': int(request.POST.get('points_per_unpaid_invoice', 20))
                }
                
                print(f"Screen values captured: {len(config_data)} fields")
                
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
                            order=index + 1
                        )
                    print(f"Age brackets added: {len(age_brackets)}")
                
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
                            order=index + 1
                        )
                    print(f"Spend brackets added: {len(spend_brackets)}")
                
                print(f"PRESET CREATED: '{preset_name}' (ID: {new_preset.id}) - NOT APPLIED")
                
                return JsonResponse({
                    'success': True,
                    'preset_id': new_preset.id,
                    'preset_name': preset_name,
                    'message': f"Preset '{preset_name}' created successfully"
                })
                
            except Exception as e:
                print(f"SAVE PRESET ERROR: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'load_patient_data':
            patient_id = request.POST.get('patient_id')
            
            if not patient_id:
                return JsonResponse({'success': False, 'error': 'No patient ID provided'})
            
            try:
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
        
        elif action == "apply_preset":
            try:
                preset_id = request.POST.get("preset_id")
                if not preset_id:
                    return JsonResponse({"success": False, "error": "No preset ID provided"})
                
                try:
                    preset = ScoringConfiguration.objects.get(id=preset_id)
                    
                    # Clear testing mode
                    if 'testing_config' in request.session:
                        del request.session['testing_config']
                    
                    # Set as active for behavior
                    ScoringConfiguration.objects.all().update(is_active_for_behavior=False)
                    preset.is_active_for_behavior = True
                    preset.save()
                    
                    print(f"DEBUG: Preset {preset.name} activated successfully")
                    
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
                                "max_spend": float(bracket.max_spend) if bracket.max_spend else None,
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
                import traceback
                print("DEBUG: Unexpected error in apply_preset:")
                traceback.print_exc()
                
                return JsonResponse({
                    "success": False, 
                    "error": str(e)
                }, status=500)

        elif action == 'set_analytics_preset':
            try:
                preset_id = request.POST.get('preset_id')
                if not preset_id:
                    return JsonResponse({'success': False, 'error': 'No preset ID provided'})
                
                # Clear all analytics flags
                ScoringConfiguration.objects.all().update(is_active_for_analytics=False)
                
                # Set selected preset as active for analytics
                preset = ScoringConfiguration.objects.get(id=preset_id)
                preset.is_active_for_analytics = True
                preset.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Analytics preset set to {preset.name}'
                })
                
            except ScoringConfiguration.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Preset not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request handling
    if request.method == 'GET':
        age_brackets = []
        spend_brackets = []
        
        try:
            active_config = ScoringConfiguration.objects.filter(is_active_for_behavior=True).first()
            if not active_config:
                # Ensure at least one preset exists
                active_config = ScoringConfiguration.objects.first()
                if not active_config:
                    active_config = ScoringConfiguration.objects.create(
                        name="Default Configuration",
                        description="Auto-created default configuration",
                        is_active_for_behavior=True
                    )
                else:
                    active_config.is_active_for_behavior = True
                    active_config.save()
        except Exception as e:
            print(f"Error getting active config: {e}")
            active_config = None
        
        if active_config:
            try:
                age_brackets = AgeBracket.objects.filter(config=active_config).order_by('order')
                spend_brackets = SpendBracket.objects.filter(config=active_config).order_by('order')
                print(f"Loaded {len(age_brackets)} age brackets and {len(spend_brackets)} spend brackets")
            except Exception as e:
                print(f"Error loading brackets: {e}")
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
                    'is_active': preset.is_active_for_behavior,
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
        
        age_brackets = []
        for bracket in preset.age_brackets.all().order_by('order'):
            age_brackets.append({
                'id': bracket.id,
                'min_age': bracket.min_age,
                'max_age': bracket.max_age,
                'percentage': bracket.percentage,
                'order': bracket.order
            })
        
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
            'is_active': preset.is_active_for_behavior,
            'created_at': preset.created_at.isoformat(),
            'updated_at': preset.updated_at.isoformat(),
            
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
            
            # Brackets
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


def clear_age_brackets(request):
    """Clear all age brackets for the active configuration"""
    if request.method == 'POST':
        try:
            active_config = ScoringConfiguration.objects.filter(is_active_for_behavior=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
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
            
            active_config = ScoringConfiguration.objects.filter(is_active_for_behavior=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            brackets_data = json.loads(request.POST.get('brackets', '[]'))
            
            age_brackets = []
            for i, bracket in enumerate(brackets_data):
                age_brackets.append(AgeBracket(
                    config=active_config,
                    min_age=bracket.get('min_age', 0),
                    max_age=bracket.get('max_age', 100),
                    percentage=bracket.get('percentage', 0),
                    order=i + 1
                ))
            
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
            active_config = ScoringConfiguration.objects.filter(is_active_for_behavior=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
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
            
            active_config = ScoringConfiguration.objects.filter(is_active_for_behavior=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            brackets_data = json.loads(request.POST.get('brackets', '[]'))
            
            spend_brackets = []
            for i, bracket in enumerate(brackets_data):
                spend_brackets.append(SpendBracket(
                    config=active_config,
                    min_spend=bracket.get('min_spend', 0),
                    max_spend=bracket.get('max_spend', 10000),
                    percentage=bracket.get('percentage', 0),
                    order=i + 1
                ))
            
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
    """Delete preset with protection for last preset and active presets"""
    try:
        preset_id = request.POST.get('preset_id')
        
        if not preset_id:
            return JsonResponse({'success': False, 'error': 'No preset ID provided'})
        
        # Check if this is the last preset
        if ScoringConfiguration.objects.count() <= 1:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete the last remaining preset'
            })
        
        try:
            preset_to_delete = ScoringConfiguration.objects.get(id=preset_id)
        except ScoringConfiguration.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Preset not found'})
        
        preset_name = preset_to_delete.name
        
        # Check if preset is active for behavior or analytics
        replacement_needed_for = []
        if preset_to_delete.is_active_for_behavior:
            replacement_needed_for.append('behavior')
        if preset_to_delete.is_active_for_analytics:
            replacement_needed_for.append('analytics')
        
        if replacement_needed_for:
            # Get replacement preset ID from request
            replacement_id = request.POST.get('replacement_preset_id')
            if not replacement_id:
                return JsonResponse({
                    'success': False,
                    'error': f'This preset is active for {" and ".join(replacement_needed_for)}. Please provide a replacement preset.',
                    'needs_replacement': True,
                    'active_for': replacement_needed_for
                })
            
            try:
                replacement_preset = ScoringConfiguration.objects.get(id=replacement_id)
                
                # Set replacement as active
                if 'behavior' in replacement_needed_for:
                    replacement_preset.is_active_for_behavior = True
                if 'analytics' in replacement_needed_for:
                    replacement_preset.is_active_for_analytics = True
                replacement_preset.save()
                
            except ScoringConfiguration.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Replacement preset not found'})
        
        # Delete the preset
        preset_to_delete.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Preset "{preset_name}" deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def create_preset(request):
    """Create a new preset"""
    if request.method == 'POST':
        try:
            preset_name = request.POST.get('preset_name', '').strip()
            preset_description = request.POST.get('preset_description', '').strip()
            
            if not preset_name:
                return JsonResponse({'success': False, 'error': 'Preset name is required'})
            
            if len(preset_name) > 50:
                return JsonResponse({'success': False, 'error': 'Preset name must be 50 characters or less'})
            
            if len(preset_description) > 200:
                return JsonResponse({'success': False, 'error': 'Description must be 200 characters or less'})
            
            if ScoringConfiguration.objects.filter(name=preset_name).exists():
                return JsonResponse({'success': False, 'error': f'Preset name "{preset_name}" already exists'})
            
            active_config = ScoringConfiguration.objects.filter(is_active_for_behavior=True).first()
            if not active_config:
                return JsonResponse({'success': False, 'error': 'No active configuration found'})
            
            new_preset = ScoringConfiguration.objects.create(
                name=preset_name,
                description=preset_description,
                is_active_for_behavior=False,
                future_appointments_weight=safe_int(request.POST.get('future_appointments_weight'), active_config.future_appointments_weight),
                age_demographics_weight=safe_int(request.POST.get('age_demographics_weight'), active_config.age_demographics_weight),
                yearly_spend_weight=safe_int(request.POST.get('yearly_spend_weight'), active_config.yearly_spend_weight),
                consecutive_attendance_weight=safe_int(request.POST.get('consecutive_attendance_weight'), active_config.consecutive_attendance_weight),
                referrer_score_weight=safe_int(request.POST.get('referrer_score_weight'), active_config.referrer_score_weight),
                cancellations_weight=safe_int(request.POST.get('cancellations_weight'), active_config.cancellations_weight),
                dna_weight=safe_int(request.POST.get('dna_weight'), active_config.dna_weight),
                unpaid_invoices_weight=safe_int(request.POST.get('unpaid_invoices_weight'), active_config.unpaid_invoices_weight),
                open_dna_invoice_weight=safe_int(request.POST.get('open_dna_invoice_weight'), active_config.open_dna_invoice_weight),
                points_per_consecutive_attendance=safe_int(request.POST.get('points_per_consecutive_attendance'), active_config.points_per_consecutive_attendance),
                points_per_referral=safe_int(request.POST.get('points_per_referral'), active_config.points_per_referral),
                points_per_cancellation=safe_int(request.POST.get('points_per_cancellation'), active_config.points_per_cancellation),
                points_per_dna=safe_int(request.POST.get('points_per_dna'), active_config.points_per_dna),
                points_per_unpaid_invoice=safe_int(request.POST.get('points_per_unpaid_invoice'), active_config.points_per_unpaid_invoice)
            )
            
            age_brackets_copied = 0
            spend_brackets_copied = 0
            
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
                for bracket in active_config.age_brackets.all():
                    AgeBracket.objects.create(
                        config=new_preset,
                        min_age=bracket.min_age,
                        max_age=bracket.max_age,
                        percentage=bracket.percentage,
                        order=bracket.order
                    )
                    age_brackets_copied += 1
            
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
            
            if not (-100 <= likability <= 100):
                return JsonResponse({'success': False, 'error': 'Likability must be between -100 and 100'})
            
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'patient_name': f'Patient {patient_id}'}
            )
            
            patient.likability = likability
            patient.save()
            
            return JsonResponse({'success': True, 'likability': likability})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


class PatientDashboardScoreView(View):
    """Dedicated endpoint for unified dashboard to get patient scores AND behavior data"""
    def get(self, request, patient_id):
        try:
            config = ScoringConfiguration.get_active_config()
            
            # Use plugin architecture for analysis
            analysis_view = PatientAnalysisView()
            analysis_result = analysis_view.analyze_patient_behavior_plugin(patient_id, config)
            
            if analysis_result and 'behavior_data' in analysis_result:
                return JsonResponse({
                    'success': True,
                    'score': analysis_result.get('total_score', 0),
                    'grade': analysis_result.get('letter_grade', 'F'),
                    'patient_id': patient_id,
                    'behavior_data': analysis_result['behavior_data'],
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


# Helper functions for patient behavior extraction using plugin architecture
def extract_patient_behavior_data_plugin(patient_id, config):
    """Extract comprehensive patient behavior data using plugin architecture"""
    try:
        print(f"Extracting behavior data for patient {patient_id}")
        
        # Handle both dictionary (testing mode) and object configs
        if isinstance(config, dict):
            # Testing mode - create a temporary config object
            from types import SimpleNamespace
            config = SimpleNamespace(**config)
        
        settings = RatedAppSettings.objects.first()
        if not settings:
            return {}
        
        # Get client directly
        client = IntegrationFactory.get_client(settings)
        
        # Get raw data from Cliniko
        patients = client.get_patients(filters={'id': patient_id})
        if not patients:
            return {}
        
        raw_patient = patients[0]
        appointments = client.get_appointments(patient_id)
        invoices = client.get_invoices(patient_id)
        referral_data = client.get_referrals(patient_id)
        
        # Prepare data for behavioral processor
        patient_data = {
            'id': patient_id,
            'date_of_birth': raw_patient.get('date_of_birth'),
            'appointments': appointments,
            'invoices': invoices,
            'referrals': referral_data.get('referred_patient_ids', []) if isinstance(referral_data, dict) else []
        }
        
        # Process behavior
        processor = BehavioralProcessor()
        result = processor.process_patient_behavior(patient_data, config, settings)
        
        if result and 'behavior_data' in result:
            return result['behavior_data']
        
        return {}
        
    except Exception as e:
        print(f"Error in extract_patient_behavior_data_plugin: {e}")
        import traceback
        traceback.print_exc()
        return {}


def calculate_total_score(behavior_data):
    """Calculate total score from behavior data"""
    return sum(
        data.get('points', 0) 
        for data in behavior_data.values() 
        if isinstance(data, dict)
    )


def calculate_letter_grade(total_score):
    """Calculate letter grade from total score"""
    if total_score >= 100:
        return 'A+'
    elif total_score >= 80:
        return 'A'
    elif total_score >= 60:
        return 'B'
    elif total_score >= 40:
        return 'C'
    elif total_score >= 20:
        return 'D'
    else:
        return 'F'


@csrf_exempt
def update_clinic_settings(request):
    """Update clinic settings"""
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
                        'clinic_timezone': settings.clinic_timezone,
                        'clinic_email': settings.clinic_email or ''
                    },
                    'connectivity': {
                        'software_integration': settings.software_integration or '',
                        'api_key': '****' + settings.api_key[-4:] if settings.api_key else None
                    }
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            
            section = data.get('section')
            if not section:
                return JsonResponse({
                    'success': False, 
                    'error': 'Section is required'
                }, status=400)
            
            settings = RatedAppSettings.objects.first()
            
            section_handlers = {
                'clinic_information': {
                    'validate': lambda d: bool(d.get('clinic_name') and d.get('clinic_email')),
                    'update': lambda settings, d: {
                        'clinic_name': d.get('clinic_name'),
                        'clinic_location': d.get('clinic_location', settings.clinic_location),
                        'clinic_timezone': d.get('clinic_timezone', settings.clinic_timezone),
                        'clinic_email': d.get('clinic_email', settings.clinic_email if hasattr(settings, 'clinic_email') else '')
                    }
                },
                'connectivity': {
                    'validate': lambda d: True,
                    'update': lambda settings, d: {
                        'software_integration': d.get('software_integration', settings.software_integration),
                        'api_key': d.get('api_key', settings.api_key)
                    }
                }
            }
            
            if section not in section_handlers:
                return JsonResponse({
                    'success': False, 
                    'error': f'Unsupported section: {section}'
                }, status=400)
            
            handler = section_handlers[section]
            if not handler['validate'](data):
                return JsonResponse({
                    'success': False, 
                    'error': f'Invalid data for {section} section'
                }, status=400)
            
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
                        'clinic_timezone': settings.clinic_timezone,
                        'clinic_email': settings.clinic_email or ''
                    },
                    'connectivity': {
                        'software_integration': settings.software_integration or '',
                        'api_key': '****' + settings.api_key[-4:] if settings.api_key else None
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
    """Validate API key using plugin architecture"""
    api_key = request.GET.get('api_key')
    
    if not api_key:
        return JsonResponse({
            'status': 'Disconnected',
            'error': 'API key required'
        }, status=400)
    
    try:
        # Create temporary settings object for validation
        temp_settings = RatedAppSettings.objects.first()
        if not temp_settings:
            temp_settings = RatedAppSettings()
            temp_settings.software_type = 'cliniko'
            temp_settings.base_url = 'https://api.au1.cliniko.com/v1/'
            temp_settings.auth_type = 'basic'
        
        # Set the API key to validate
        temp_settings.api_key = api_key
        
        # Get client and validate
        client = IntegrationFactory.get_client(temp_settings)
        is_valid = client.validate_connection()
        
        if is_valid:
            return JsonResponse({
                'status': 'Connected',
                'message': 'API key is valid'
            })
        else:
            return JsonResponse({
                'status': 'Disconnected',
                'error': 'Invalid API key'
            }, status=401)
    
    except Exception as e:
        return JsonResponse({
            'status': 'Disconnected',
            'error': 'Network Error'
        }, status=500)

@require_http_methods(["GET", "POST"])
def analytics_config(request):
    """Get or update analytics configuration"""
    settings = RatedAppSettings.objects.first()
    
    if request.method == "GET":
        try:
            # Get current analytics job if exists
            current_job = settings.analytics_last_job if settings else None
            
            response_data = {
                'success': True,
                'enabled': settings.analytics_enabled if settings else False,
                'current_job': None
            }
            
            if current_job:
                response_data['current_job'] = {
                    'id': current_job.id,
                    'date_range': current_job.date_range,
                    'frequency': current_job.frequency,
                    'scheduled_time': current_job.scheduled_time.strftime('%H:%M'),
                    'scheduled_day': current_job.scheduled_day,
                    'preset_id': current_job.preset.id if current_job.preset else None,
                    'preset_name': current_job.preset.name if current_job.preset else None,
                    'status': current_job.status,
                    'is_test_mode': current_job.is_test_mode,
                    'last_run': current_job.last_run_completed.isoformat() if current_job.last_run_completed else None,
                    'next_run': current_job.next_run.isoformat() if current_job.next_run else None,
                    'patients_processed': current_job.patients_processed,
                    'total_patients': current_job.total_patients,
                }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['date_range', 'frequency', 'scheduled_time', 'preset_id']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Check for test mode flag
            is_test_mode = data.get('is_test_mode', False)
            
            # Validate 1 day can only be manual
            if data['date_range'] == '1d' and data['frequency'] != 'manual':
                return JsonResponse({
                    'success': False,
                    'error': '1 day range can only be used with Manual frequency'
                }, status=400)
            
            # Get preset
            preset = ScoringConfiguration.objects.filter(id=data['preset_id']).first()
            if not preset:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid preset selected'
                }, status=400)
            
            # Calculate date range sizes for comparison
            date_range_order = {
                '1d': 1,
                '3': 90,
                '6': 180,
                '1y': 365,
                '2y': 730,
                '5y': 1825,
                '10y': 3650
            }
            
            with transaction.atomic():
                # Check for existing jobs (exclude test mode jobs from conflict check)
                existing_jobs = AnalyticsJob.objects.filter(
                    status__in=['pending', 'running'],
                    is_test_mode=False
                ).exclude(
                    date_range='1d',
                    frequency='manual',
                    is_test_mode=True
                )
                
                # If this is not a test mode job, check for conflicts
                if not is_test_mode:
                    for existing_job in existing_jobs:
                        # Cancel existing production jobs
                        existing_job.cancel_requested = True
                        existing_job.save()
                        
                        # Prepare replacement message
                        existing_range_size = date_range_order.get(existing_job.date_range, 0)
                        new_range_size = date_range_order.get(data['date_range'], 0)
                        
                        if new_range_size != existing_range_size:
                            message = f"Replacing {existing_job.date_range} job with {data['date_range']} job"
                        else:
                            message = f"Replacing existing {existing_job.date_range} job with new settings"
                        
                        logger.info(message)
                
                # Parse the time string to a time object
                from datetime import time as datetime_time
                time_parts = data['scheduled_time'].split(':')
                scheduled_time_obj = datetime_time(
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]) if len(time_parts) > 1 else 0
                )
                
                # Create new job
                job = AnalyticsJob.objects.create(
                    date_range=data['date_range'],
                    preset=preset,
                    frequency=data['frequency'],
                    scheduled_time=scheduled_time_obj,
                    scheduled_day=data.get('scheduled_day') if data['frequency'] == 'weekly' else None,
                    status='pending',
                    is_test_mode=is_test_mode,
                    created_by=request.user.username if request.user.is_authenticated else 'system'
                )
                
                # Calculate next run time for scheduled jobs
                if job.frequency in ['daily', 'weekly']:
                    job.calculate_next_run()
                    job.save()
                
                # Update settings
                if not settings:
                    settings = RatedAppSettings.objects.create(
                        clinic_name='Default Clinic'
                    )
                
                settings.analytics_enabled = True
                settings.analytics_preset = preset
                settings.analytics_last_job = job
                settings.save()
                
                # Prepare response message
                if is_test_mode:
                    response_message = 'Analytics test job configured (will not update Cliniko)'
                else:
                    response_message = f'Analytics configuration saved{" (replaced existing job)" if existing_jobs else ""}'
            
            return JsonResponse({
                'success': True,
                'message': response_message,
                'job_id': job.id,
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'is_test_mode': is_test_mode
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@require_http_methods(["POST"])
def analytics_start(request):
    """Manually start analytics processing"""
    try:
        settings = RatedAppSettings.objects.first()
        if not settings or not settings.analytics_last_job:
            return JsonResponse({
                'success': False,
                'error': 'No analytics job configured'
            }, status=400)
        
        job = settings.analytics_last_job
        
        # Check if job is already running
        if job.status == 'running':
            return JsonResponse({
                'success': False,
                'error': 'Analytics already running'
            }, status=400)
        
        # Cancel any other running jobs (except test mode jobs)
        if not job.is_test_mode:
            other_running = AnalyticsJob.objects.filter(
                status='running',
                is_test_mode=False
            ).exclude(id=job.id)
            
            for other_job in other_running:
                other_job.cancel_requested = True
                other_job.save()
                logger.info(f"Cancelled job {other_job.id} to start job {job.id}")
        
        # Mark job as running immediately
        job.status = 'running'
        job.last_run_started = timezone.now()
        job.cancel_requested = False
        job.patients_processed = 0
        job.patients_failed = 0
        job.processed_patient_ids = []
        job.failed_patient_ids = []
        job.error_log = ''
        if job.is_test_mode:
            job.test_results = {}
        job.save()
        
        # Trigger processing in background
        from django.core.management import call_command
        from threading import Thread
        
        def run_analytics():
            try:
                call_command('process_analytics')
            except Exception as e:
                print(f"Analytics processing error: {e}")
                job.refresh_from_db()
                if job.status == 'running':
                    job.status = 'failed'
                    job.error_log = str(e)
                    job.save()
        
        thread = Thread(target=run_analytics)
        thread.daemon = True
        thread.start()
        
        test_mode_msg = ' (TEST MODE - will not update Cliniko)' if job.is_test_mode else ''
        
        return JsonResponse({
            'success': True,
            'message': f'Analytics processing started{test_mode_msg}',
            'job_id': job.id,
            'is_test_mode': job.is_test_mode
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def analytics_cancel(request):
    """Cancel running analytics job"""
    try:
        settings = RatedAppSettings.objects.first()
        if not settings or not settings.analytics_last_job:
            return JsonResponse({
                'success': False,
                'error': 'No analytics job configured'
            }, status=400)
        
        job = settings.analytics_last_job
        
        if job.status != 'running':
            return JsonResponse({
                'success': False,
                'error': 'No analytics currently running'
            }, status=400)
        
        # Set cancellation flag
        job.cancel_requested = True
        job.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cancellation requested. Will stop after current patient.',
            'job_id': job.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def analytics_status(request):
    """Get current analytics job status"""
    try:
        settings = RatedAppSettings.objects.first()
        if not settings or not settings.analytics_last_job:
            return JsonResponse({
                'success': True,
                'status': 'not_configured'
            })
        
        job = settings.analytics_last_job
        
        # Calculate progress percentage
        progress = 0
        if job.total_patients > 0:
            progress = int((job.patients_processed / job.total_patients) * 100)
        
        response_data = {
            'success': True,
            'status': job.status,
            'progress': progress,
            'patients_processed': job.patients_processed,
            'total_patients': job.total_patients,
            'patients_failed': job.patients_failed,
            'last_run_started': job.last_run_started.isoformat() if job.last_run_started else None,
            'last_run_completed': job.last_run_completed.isoformat() if job.last_run_completed else None,
            'next_run': job.next_run.isoformat() if job.next_run else None,
        }
        
        # Format status message
        if job.status == 'running':
            response_data['message'] = f'Analysing... ({job.patients_processed}/{job.total_patients})'
        elif job.status == 'completed':
            if job.last_run_completed:
                completed_time = job.last_run_completed.strftime('%Y-%m-%d %H:%M')
                response_data['message'] = f'Completed ({completed_time})'
            else:
                response_data['message'] = 'Completed'
        elif job.status == 'partial':
            response_data['message'] = f'Partial Completion ({job.patients_processed}/{job.total_patients})'
        elif job.status == 'failed':
            response_data['message'] = 'Failed - Check error log'
        elif job.status == 'cancelled':
            response_data['message'] = 'Cancelled by user'
        else:
            response_data['message'] = 'Ready to run'
        
        # Add error information if available
        if job.error_log:
            response_data['errors'] = job.error_log[-500:]  # Last 500 chars of error log
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def send_analytics_email_log(job, settings):
    """Send email log after analytics completion"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Skip email for test mode
        if job.is_test_mode:
            logger.info("Test mode - skipping email notification")
            return True
            
        # Check if email is configured
        if not settings.clinic_email or not settings.smtp_username:
            logger.info("Email not configured - skipping notification")
            return False
        
        # Prepare email content
        subject = f"RatedApp Analytics Log - {job.get_status_display()}"
        if job.is_test_mode:
            subject += " [TEST MODE]"
        
        # Build log content
        log_lines = [
            "RatedApp Analytics Processing Log",
            "=" * 50,
            f"Clinic Name: {settings.clinic_name}",
            f"Clinic Location: {settings.clinic_location}",
            f"Clinic Timezone: {settings.clinic_timezone}",
            f"User Email: {settings.clinic_email}",
            f"Integrated Software: {settings.software_type}",
            f"Date Range Analysed: {job.date_range}",
            f"Frequency: {job.frequency}",
            f"Preset Selected: {job.preset.name if job.preset else 'None'}",
            f"Test Mode: {'Yes' if job.is_test_mode else 'No'}",
            f"Process Started: {job.last_run_started.strftime('%Y-%m-%d %H:%M:%S %Z') if job.last_run_started else 'N/A'}",
            f"Process Completed: {job.last_run_completed.strftime('%Y-%m-%d %H:%M:%S %Z') if job.last_run_completed else 'N/A'}",
            "",
            "Patient Processing Results:",
            "=" * 50,
        ]
        
        # Add patient details
        successful_count = len(job.processed_patient_ids)
        failed_count = len(job.failed_patient_ids)
        
        # Add summary for successful patients
        if successful_count > 0:
            log_lines.append(f"\nSuccessfully Processed: {successful_count} patients")
            if successful_count <= 20:  # Only list first 20
                for patient_id in job.processed_patient_ids[:20]:
                    try:
                        patient = Patient.objects.get(cliniko_patient_id=patient_id)
                        # Mask last 4 digits of ID
                        masked_id = patient_id[:-4] + '****' if len(patient_id) > 4 else '****'
                        log_lines.append(
                            f"  - {patient.patient_name}, ID: {masked_id}, "
                            f"Score: {patient.total_score}, Rating: {patient.calculated_rating}"
                        )
                    except Patient.DoesNotExist:
                        pass
                if successful_count > 20:
                    log_lines.append(f"  ... and {successful_count - 20} more")
        
        # Add summary for failed patients
        if failed_count > 0:
            log_lines.append(f"\nFailed Processing: {failed_count} patients")
            for failed_info in job.failed_patient_ids[:10]:  # Only first 10
                patient_id = failed_info.get('id', 'Unknown')
                patient_name = failed_info.get('name', 'Unknown')
                error = failed_info.get('error', 'Unknown error')
                
                # Mask last 4 digits of ID
                masked_id = patient_id[:-4] + '****' if len(patient_id) > 4 else '****'
                log_lines.append(
                    f"  - {patient_name}, ID: {masked_id}, Error: {error[:50]}"
                )
            if failed_count > 10:
                log_lines.append(f"  ... and {failed_count - 10} more")
        
        log_lines.extend([
            "",
            "=" * 50,
            f"Total Processed: {successful_count}",
            f"Total Failed: {failed_count}",
            f"Status: {job.get_status_display()}",
        ])
        
        if job.is_test_mode:
            log_lines.append("\n[TEST MODE - No Cliniko updates were made]")
        
        # Create log file content
        log_content = "\n".join(log_lines)
        
        # Setup email
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_username
        msg['To'] = settings.clinic_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(log_content, 'plain'))
        
        # Send email
        try:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Analytics email sent to {settings.clinic_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            # Still log to console
            print("\n" + "="*50)
            print("ANALYTICS LOG (Email send failed)")
            print("="*50)
            print(log_content)
            return False
        
    except Exception as e:
        logger.error(f"Error preparing analytics email: {e}")
        return False

@require_http_methods(["GET"])
def analytics_presets(request):
    """Get available presets for analytics"""
    try:
        # Get all presets that can be used for analytics
        presets = ScoringConfiguration.objects.filter(is_active_for_analytics=True).values(
            'id', 'name', 'description'
        )
        
        # Check if any preset is currently used by analytics
        settings = RatedAppSettings.objects.first()
        active_analytics_preset_id = None
        if settings and settings.analytics_preset:
            active_analytics_preset_id = settings.analytics_preset.id
        
        preset_list = []
        for preset in presets:
            preset_data = dict(preset)
            preset_data['is_analytics_active'] = (preset['id'] == active_analytics_preset_id)
            preset_list.append(preset_data)
        
        return JsonResponse({
            'success': True,
            'presets': preset_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)