import json
import logging
import requests
import base64
import time
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST, require_http_methods
from django.views import View
from django.contrib import messages
from django.urls import reverse
from django.db.models import F
from django.db import models, IntegrityError, transaction
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Your existing integration imports
from .integrations.factory import IntegrationFactory
from .integrations.base_client import BaseClient
from .integrations.base_normalizer import BaseNormalizer

# Model Imports
from .models import (
    ScoringConfiguration, 
    Patient, 
    AgeBracket, 
    SpendBracket, 
    RatedAppSettings
)

# Behavioral processing
from .behavioral_processor import BehavioralProcessor

# Configure logging
logger = logging.getLogger('ratedapp.views_plugin')

def get_integration_client():
    """
    Get the appropriate integration client based on RatedApp settings
    
    Returns:
        tuple: (client, normalizer) or (None, None)
    """
    try:
        settings_obj = RatedAppSettings.objects.first()
        
        if not settings_obj:
            logger.error("No RatedApp settings found")
            return None, None
        
        # Use plugin system if enabled
        if settings_obj.use_plugin_system:
            client = IntegrationFactory.get_client(settings_obj)
            normalizer = IntegrationFactory.get_normalizer(settings_obj)
            return client, normalizer
        
        return None, None
            
    except Exception as e:
        logger.error(f"Error getting integration client: {e}")
        return None, None

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

def get_referrer_count(patient_id):
    """
    Get the number of patients referred by a specific patient using plugin system
    
    Args:
        patient_id (str): The patient ID
        
    Returns:
        int: Number of patients referred by this patient
    """
    try:
        # Get integration client
        client, normalizer = get_integration_client()
        
        if not client:
            logger.error(f"No integration client available for referrer count")
            return 0
        
        # Use client's get_referrals method
        referral_data = client.get_referrals(patient_id)
        
        # Log referral information
        referral_count = referral_data.get('referral_count', 0)
        logger.info(f"🔗 Referrer count for patient {patient_id}: {referral_count}")
        
        return referral_count
        
    except Exception as e:
        logger.error(f"❌ Error getting referrer count for patient {patient_id}: {e}")
        return 0

def calculate_referrer_score(patient_id, points_per_referral, max_points):
    """
    Calculate referrer score with points cap logic using plugin system
    
    Args:
        patient_id (str): The patient ID
        points_per_referral (int): Points awarded per referral
        max_points (int): Maximum points cap (from slider)
        
    Returns:
        int: Final referrer score (capped)
    """
    try:
        # Get referral count
        referral_count = get_referrer_count(patient_id)
        
        # Calculate raw score
        raw_score = referral_count * points_per_referral
        final_score = min(raw_score, max_points)
        
        logger.info(
            f"🔗 Referrer score calculation: "
            f"{referral_count} referrals × {points_per_referral} points = {raw_score}, "
            f"capped at {max_points} = {final_score}"
        )
        
        return final_score
    
    except Exception as e:
        logger.error(f"❌ Referrer score calculation error: {e}")
        return 0

class HomeView(View):
    def get(self, request):
        """
        Render the home page with plugin system feature flag check
        
        Args:
            request (HttpRequest): Incoming HTTP request
        
        Returns:
            HttpResponse: Rendered home page template
        """
        try:
            # Check if plugin system is enabled
            settings_obj = RatedAppSettings.objects.first()
            
            # Log access attempt
            logger.info(f"Accessing HomeView: Plugin system {'enabled' if settings_obj and settings_obj.use_plugin_system else 'disabled'}")
            
            # Render template (same as original implementation)
            return render(request, 'patient_rating/home.html')
        
        except Exception as e:
            # Log any unexpected errors
            logger.error(f"Error in HomeView: {e}")
            
            # Fallback to rendering template even if there's an error
            return render(request, 'patient_rating/home.html')

class PatientSearchView(View):
    def get(self, request):
        """
        Render the patient search page with plugin system feature flag check
        
        Args:
            request (HttpRequest): Incoming HTTP request
        
        Returns:
            HttpResponse: Rendered patient search template
        """
        try:
            # Check if plugin system is enabled
            settings_obj = RatedAppSettings.objects.first()
            
            # Log access attempt
            logger.info(f"Accessing PatientSearchView: Plugin system {'enabled' if settings_obj and settings_obj.use_plugin_system else 'disabled'}")
            
            # Render template (same as original implementation)
            return render(request, 'patient_rating/patient_search.html')
        
        except Exception as e:
            # Log any unexpected errors
            logger.error(f"Error in PatientSearchView GET: {e}")
            
            # Fallback to rendering template even if there's an error
            return render(request, 'patient_rating/patient_search.html')
    
    def post(self, request):
        """
        Handle patient search requests using plugin system
        
        Args:
            request (HttpRequest): POST request with search parameters
        
        Returns:
            HttpResponse: Rendered template with search results
        """
        search_type = request.POST.get('search_type', 'name')
        search_value = request.POST.get('search_value', '').strip()
        
        if not search_value:
            return render(request, 'patient_rating/patient_search.html', {
                'error': 'Please enter a search value'
            })
        
        try:
            # Check if plugin system is enabled
            settings_obj = RatedAppSettings.objects.first()
            use_plugin = settings_obj and settings_obj.use_plugin_system
            
            logger.info(f"Patient search request: type={search_type}, value={search_value}, plugin={'enabled' if use_plugin else 'disabled'}")
            
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
            logger.error(f"Patient search error: {e}")
            return render(request, 'patient_rating/patient_search.html', {
                'error': f'Search failed: {str(e)}'
            })
    
    def get_phone_numbers(self, patient):
        """
        Format patient phone numbers for display
        
        Args:
            patient (dict): Patient data from integration client
            
        Returns:
            str: Formatted phone numbers string
        """
        try:
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
            
        except Exception as e:
            logger.error(f"Error formatting phone numbers: {e}")
            return "Not provided"
    
    def search_by_name(self, name):
        """
        Search patients by name using plugin system
        
        Args:
            name (str): Patient name to search for
            
        Returns:
            list: List of formatted patient data
        """
        try:
            # Get integration client
            client, normalizer = get_integration_client()
            
            if not client:
                logger.warning("No integration client available, search unavailable")
                return []
            
            # Use plugin system to search patients
            raw_patients = client.search_patients_by_name(name)
            
            # Normalize the data
            if normalizer:
                normalized_patients = normalizer.normalize_patient_list(raw_patients)
            else:
                normalized_patients = raw_patients
            
            # Format for frontend
            formatted_patients = []
            for patient in normalized_patients:
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
            
            logger.info(f"Name search completed: found {len(formatted_patients)} patients")
            return formatted_patients
            
        except Exception as e:
            logger.error(f"Error in search_by_name: {e}")
            return []
    
    def search_by_id(self, patient_id):
        """
        Search patient by ID using plugin system
        
        Args:
            patient_id (str): Patient ID to search for
            
        Returns:
            list: List containing single patient data or empty list
        """
        try:
            # Get integration client
            client, normalizer = get_integration_client()
            
            if not client:
                logger.warning("No integration client available, search unavailable")
                return []
            
            # Use plugin system to get patient by ID
            raw_patient = client.get_patient_by_id(patient_id)
            
            if not raw_patient:
                logger.info(f"No patient found with ID: {patient_id}")
                return []
            
            # Normalize the data
            if normalizer:
                normalized_patient = normalizer.normalize_patient_data(raw_patient)
            else:
                normalized_patient = raw_patient
            
            # Format for frontend
            phone = self.get_phone_numbers(normalized_patient)
            formatted_patient = {
                'id': normalized_patient.get('id'),
                'first_name': normalized_patient.get('first_name'),
                'last_name': normalized_patient.get('last_name'),
                'email': normalized_patient.get('email'),
                'phone': phone,
                'date_of_birth': normalized_patient.get('date_of_birth'),
                'full_name': f"{normalized_patient.get('first_name', '')} {normalized_patient.get('last_name', '')}".strip()
            }
            
            logger.info(f"ID search completed: found patient {patient_id}")
            return [formatted_patient]
            
        except Exception as e:
            logger.error(f"Error in search_by_id: {e}")
            return []

    def get_open_dna_invoices(self, patient_id):
        """
        Extract and count open DNA (Did Not Arrive) invoices for a patient using plugin system
        
        Args:
            patient_id (str): Patient ID
            
        Returns:
            dict: DNA invoice data with count, status, and description
        """
        try:
            # Get integration client
            client, normalizer = get_integration_client()
            
            if not client:
                logger.warning("No integration client available for DNA invoices")
                return {
                    'count': 0,
                    'has_open_dna': False,
                    'description': "Integration unavailable"
                }
            
            # Use plugin system to get invoices
            invoices_data = client.get_patient_invoices(patient_id)
            
            # Normalize if normalizer available
            if normalizer:
                invoices_data = normalizer.normalize_invoices_data(invoices_data)
            
            # Count open DNA invoices
            open_dna_count = 0
            invoices = invoices_data.get('invoices', [])
            
            for invoice in invoices:
                if (invoice.get('status') == 'unpaid' and 
                    ('DNA' in str(invoice.get('description', '')).upper() or
                     'DID NOT ARRIVE' in str(invoice.get('description', '')).upper())):
                    open_dna_count += 1
            
            logger.info(f"DNA invoices check for patient {patient_id}: {open_dna_count} open")
            
            return {
                'count': open_dna_count,
                'has_open_dna': open_dna_count > 0,
                'description': f"{open_dna_count} open DNA invoices" if open_dna_count != 1 else "1 open DNA invoice"
            }
            
        except Exception as e:
            logger.error(f"Error getting DNA invoices for patient {patient_id}: {e}")
            return {
                'count': 0,
                'has_open_dna': False,
                'description': "Error loading DNA invoices"
            }

    def get_likability_data(self, patient_id):
        """
        Get or create likability data for a patient (unchanged - uses local database)
        
        Args:
            patient_id (str): Patient ID
            
        Returns:
            dict: Likability data with score, description, and status flags
        """
        try:
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
            
            logger.info(f"Likability data for patient {patient_id}: {patient.likability}")
            
            return {
                'likability_score': patient.likability,
                'description': description,
                'status': status,
                'is_positive': patient.likability > 0,
                'is_negative': patient.likability < 0,
                'is_neutral': patient.likability == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting likability for patient {patient_id}: {e}")
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
        """
        Render the patient analysis page with plugin system feature flag check
        
        Args:
            request (HttpRequest): Incoming HTTP request
            patient_id (str): ID of the patient to analyze
        
        Returns:
            HttpResponse: Rendered patient analysis template
        """
        try:
            # Check if plugin system is enabled
            settings_obj = RatedAppSettings.objects.first()
            use_plugin = settings_obj and settings_obj.use_plugin_system
            
            # Log access attempt
            logger.info(f"Accessing PatientAnalysisView for patient {patient_id}: Plugin system {'enabled' if use_plugin else 'disabled'}")
            
            # Render template (same as original implementation)
            return render(request, 'patient_rating/patient_analysis.html', {
                'patient_id': patient_id
            })
        
        except Exception as e:
            # Log any unexpected errors
            logger.error(f"Error in PatientAnalysisView GET for patient {patient_id}: {e}")
            
            # Fallback to rendering template even if there's an error
            return render(request, 'patient_rating/patient_analysis.html', {
                'patient_id': patient_id,
                'error': 'Unable to load patient analysis page'
            })
    
    def post(self, request, patient_id):
        """
        Handle patient analysis requests using plugin system
        
        Args:
            request (HttpRequest): POST request with analysis parameters
            patient_id (str): ID of the patient to analyze
        
        Returns:
            JsonResponse: Patient analysis data or error information
        """
        action = request.POST.get('action')
        
        # Likability Update Action
        if action == 'update_likability':
            try:
                likability = int(request.POST.get('likability', 0))
                
                # Validate likability value
                if not (-100 <= likability <= 100):
                    return JsonResponse({
                        'success': False, 
                        'error': 'Likability must be between -100 and 100'
                    })
                
                # Get or create patient
                patient, created = Patient.objects.get_or_create(
                    cliniko_patient_id=patient_id,
                    defaults={'patient_name': f'Patient {patient_id}'}
                )
                
                # Update likability
                patient.likability = likability
                patient.save()
                
                logger.info(f"Likability updated for patient {patient_id}: {likability}")
                
                return JsonResponse({
                    'success': True, 
                    'likability': likability
                })
                
            except Exception as e:
                logger.error(f"Error updating likability for patient {patient_id}: {e}")
                return JsonResponse({
                    'success': False, 
                    'error': str(e)
                })
        
        # Patient Behavior Analysis Action
        try:
            # Check if plugin system is enabled
            settings_obj = RatedAppSettings.objects.first()
            use_plugin = settings_obj and settings_obj.use_plugin_system
            
            # Get active scoring configuration
            config = ScoringConfiguration.get_active_config()
            
            logger.info(f"Analyzing patient {patient_id} behavior: Plugin system {'enabled' if use_plugin else 'disabled'}")
            
            # Use plugin system or fallback to existing analyzer
            if use_plugin:
                # Placeholder for plugin system behavior analysis
                # In a real implementation, this would use the integration client
                client, normalizer = get_integration_client()
                
                if client:
                    # Retrieve patient data using plugin system
                    patient_data = client.get_patient_by_id(patient_id)
                    
                    if normalizer:
                        patient_data = normalizer.normalize_patient_data(patient_data)
                    
                    # Analyze behavior using normalized data
                    analysis = analyze_patient_behavior(patient_id, config)
                else:
                    # Fallback to existing analyzer if no client available
                    analysis = analyze_patient_behavior(patient_id, config)
            else:
                # Use existing analyzer
                analysis = analyze_patient_behavior(patient_id, config)
            
            if analysis:
                logger.info(f"Patient {patient_id} analysis successful")
                return JsonResponse({
                    'status': 'success',
                    'analysis': analysis
                })
            else:
                logger.warning(f"Patient {patient_id} analysis failed")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Analysis failed'
                })
        
        except Exception as e:
            logger.error(f"Comprehensive error in patient analysis for {patient_id}: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

class UpdateLikabilityView(View):
    def post(self, request):
        """
        Update patient likability score using plugin system
        
        Args:
            request (HttpRequest): POST request with likability update
        
        Returns:
            JsonResponse: Result of likability update
        """
        try:
            # Check if plugin system is enabled
            settings_obj = RatedAppSettings.objects.first()
            use_plugin = settings_obj and settings_obj.use_plugin_system
            
            # Extract patient ID and likability value
            patient_id = request.POST.get('patient_id')
            likability_value = int(request.POST.get('likability', 0))
            
            # Validate input parameters
            if not patient_id:
                logger.warning("UpdateLikabilityView: No patient ID provided")
                return JsonResponse({
                    'success': False, 
                    'error': 'Patient ID is required'
                })
            
            # Validate likability value
            if not (-100 <= likability_value <= 100):
                logger.warning(f"UpdateLikabilityView: Invalid likability value {likability_value}")
                return JsonResponse({
                    'success': False, 
                    'error': 'Likability must be between -100 and 100'
                })
            
            # Log plugin system status
            logger.info(f"UpdateLikabilityView: Updating likability for patient {patient_id}, Plugin system {'enabled' if use_plugin else 'disabled'}")
            
            # Use plugin system if enabled
            if use_plugin:
                try:
                    # Get integration client
                    client, normalizer = get_integration_client()
                    
                    if client:
                        # Attempt to update patient data via plugin system
                        updated = client.update_patient_likability(patient_id, likability_value)
                        if not updated:
                            logger.warning(f"Plugin system update failed for patient {patient_id}")
                except Exception as plugin_error:
                    logger.error(f"Plugin system likability update error: {plugin_error}")
                    # Fall back to local database method if plugin update fails
            
            # Always update local database record
            patient, created = Patient.objects.get_or_create(
                cliniko_patient_id=patient_id,
                defaults={'patient_name': f'Patient {patient_id}'}
            )
            
            # Update likability
            patient.likability = likability_value
            patient.save()
            
            logger.info(f"Likability updated successfully for patient {patient_id}: {likability_value}")
            
            return JsonResponse({
                'success': True, 
                'likability': likability_value
            })
        
        except Exception as e:
            logger.error(f"Comprehensive error in UpdateLikabilityView: {e}")
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })

class PatientDashboardScoreView(View):
    """
    Dedicated endpoint for unified dashboard to get patient scores AND behavior data.
    Uses plugin system with feature flag and comprehensive error handling.
    """
    def get(self, request, patient_id):
        """
        Retrieve patient dashboard score using plugin system
        
        Args:
            request (HttpRequest): Incoming HTTP request
            patient_id (str): ID of the patient to analyze
        
        Returns:
            JsonResponse: Patient score, grade, and behavior data
        """
        try:
            # Check if plugin system is enabled
            settings_obj = RatedAppSettings.objects.first()
            use_plugin = settings_obj and settings_obj.use_plugin_system
            
            # Log access attempt
            logger.info(f"PatientDashboardScoreView: Analyzing patient {patient_id}, Plugin system {'enabled' if use_plugin else 'disabled'}")
            
            # Get active scoring configuration
            try:
                config = ScoringConfiguration.get_active_config()
                if not config:
                    logger.warning("No active scoring configuration found")
                    return JsonResponse({
                        'success': False,
                        'error': 'No active scoring configuration',
                        'patient_id': patient_id
                    })
            except Exception as config_error:
                logger.error(f"Error retrieving scoring configuration: {config_error}")
                return JsonResponse({
                    'success': False,
                    'error': 'Configuration retrieval failed',
                    'patient_id': patient_id
                })
            
            # Use plugin system if enabled
            if use_plugin:
                try:
                    # Get integration client
                    client, normalizer = get_integration_client()
                    
                    if client:
                        # Retrieve patient data using plugin system
                        patient_data = client.get_patient_by_id(patient_id)
                        
                        if normalizer:
                            patient_data = normalizer.normalize_patient_data(patient_data)
                        
                        # Use plugin system to calculate behavior data
                        analysis_result = client.calculate_patient_behavior(patient_id, config)
                    else:
                        # Fallback to existing analyzer if no client available
                        analysis_result = analyze_patient_behavior(patient_id, config)
                except Exception as plugin_error:
                    logger.error(f"Plugin system analysis error: {plugin_error}")
                    # Fallback to existing analyzer
                    analysis_result = analyze_patient_behavior(patient_id, config)
            else:
                # Use existing analyzer
                analysis_result = analyze_patient_behavior(patient_id, config)
            
            # Validate analysis result
            if not analysis_result or 'behavior_data' not in analysis_result:
                logger.warning(f"No behavior data found for patient {patient_id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to calculate patient score',
                    'patient_id': patient_id
                })
            
            # Prepare response
            response_data = {
                'success': True,
                'score': analysis_result.get('total_score', 0),
                'grade': analysis_result.get('letter_grade', 'F'),
                'patient_id': patient_id,
                'behavior_data': analysis_result['behavior_data'],
                'patient_name': analysis_result.get('patient_name', f'Patient {patient_id}')
            }
            
            logger.info(f"Patient {patient_id} dashboard score calculated: {response_data['score']} points, grade {response_data['grade']}")
            
            return JsonResponse(response_data)
        
        except Exception as e:
            logger.error(f"Comprehensive error in PatientDashboardScoreView for patient {patient_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Unexpected error calculating patient score',
                'patient_id': patient_id
            })
