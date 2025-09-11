import requests
import pytz
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .software_integrations import AuthenticationHandler
from .data_normalizers import DataNormalizer

class SoftwareAPIClient:
    """
    Unified API client for practice management software
    Handles API interactions across different software platforms
    """
    
    def __init__(self, settings_obj):
        """
        Initialize API client with specific software settings
        
        :param settings_obj: RatedAppSettings instance
        """
        self.settings = settings_obj
        self.base_url = settings_obj.base_url
        self.software_type = settings_obj.software_type
        self.clinic_timezone = settings_obj.clinic_timezone or 'Australia/Sydney'
    
    def _convert_timestamp_to_clinic_timezone(self, timestamp_str):
        """
        Convert a timestamp to the clinic's selected timezone
        
        :param timestamp_str: Timestamp string (preferably in ISO format)
        :return: Timestamp converted to clinic's timezone
        """
        try:
            # Parse the timestamp (assuming UTC)
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
            
            # Convert to clinic's timezone
            clinic_tz = pytz.timezone(self.clinic_timezone)
            converted_time = utc_time.astimezone(clinic_tz)
            
            return converted_time.isoformat()
        except Exception as e:
            print(f"Timestamp conversion error: {e}")
            return timestamp_str  # Return original if conversion fails
    
    def get_paginated_data(self, endpoint, params, description):
        """
        Get all paginated data from Cliniko API
        
        :param endpoint: API endpoint to query
        :param params: Query parameters
        :param description: Description for logging
        :return: List of all retrieved items
        """
        all_data = []
        page = 1
        
        while True:
            current_params = params.copy() if params else {}
            current_params['page'] = page
            current_params['per_page'] = 100
            
            url = f"{self.base_url}/{endpoint}"
            
            try:
                response = requests.get(url, headers=AuthenticationHandler.get_headers(self.settings), params=current_params)
                
                if response.status_code != 200:
                    print(f"❌ API Error {response.status_code}: {response.text}")
                    break
                
                data = response.json()
                
                # Handle different response structures
                if endpoint == 'individual_appointments':
                    items = data.get('individual_appointments', [])
                elif endpoint == 'patients':
                    items = data.get('patients', [])
                elif endpoint == 'invoices':
                    items = data.get('invoices', [])
                else:
                    items = data.get('items', [])
                
                all_data.extend(items)
                
                # Check if there are more pages
                if len(items) < 100:
                    break
                
                page += 1
            
            except Exception as e:
                print(f"Error retrieving paginated data: {e}")
                break
        
        return all_data
    
    def get_patient_appointments(self, patient_id):
        """
        Retrieve all appointments for a patient
        
        :param patient_id: Unique patient identifier
        :return: List of all appointments (active and cancelled)
        """
        # Get active appointments
        active_filter_params = {'q[]': [f'patient_id:={patient_id}']}
        active_appointments = self.get_paginated_data('individual_appointments', active_filter_params, f'active appointments for patient {patient_id}')
        
        # Get cancelled appointments
        cancelled_filter_params = {'q[]': [f'patient_id:={patient_id}', 'cancelled_at:?']}
        cancelled_appointments = self.get_paginated_data('individual_appointments', cancelled_filter_params, f'cancelled appointments for patient {patient_id}')
        
        # Combine and convert timestamps
        all_appointments = active_appointments + cancelled_appointments
        for appointment in all_appointments:
            if 'starts_at' in appointment:
                appointment['starts_at'] = self._convert_timestamp_to_clinic_timezone(appointment['starts_at'])
            if 'ends_at' in appointment:
                appointment['ends_at'] = self._convert_timestamp_to_clinic_timezone(appointment['ends_at'])
            if 'cancelled_at' in appointment and appointment['cancelled_at']:
                appointment['cancelled_at'] = self._convert_timestamp_to_clinic_timezone(appointment['cancelled_at'])
        
        return all_appointments
    
    def get_patient_invoices(self, patient_id):
        """
        Retrieve all invoices for a patient
        
        :param patient_id: Unique patient identifier
        :return: List of all invoices
        """
        filter_params = {'q[]': [f'patient_id:={patient_id}']}
        invoices = self.get_paginated_data('invoices', filter_params, f'invoices for patient {patient_id}')
        
        # Convert timestamps
        for invoice in invoices:
            if 'created_at' in invoice:
                invoice['created_at'] = self._convert_timestamp_to_clinic_timezone(invoice['created_at'])
            if 'updated_at' in invoice:
                invoice['updated_at'] = self._convert_timestamp_to_clinic_timezone(invoice['updated_at'])
            if 'closed_at' in invoice and invoice['closed_at']:
                invoice['closed_at'] = self._convert_timestamp_to_clinic_timezone(invoice['closed_at'])
        
        return invoices
    
    def get_patient_referrals(self, patient_id):
        """
        Retrieve referral sources for a patient
        
        :param patient_id: Unique patient identifier
        :return: List of referral sources
        """
        referrer_params = {
            'q[]': f'referrer_id:={patient_id}',
            'per_page': 50
        }
        
        try:
            referrer_data = self.get_paginated_data('referral_sources', referrer_params, f'referrals for patient {patient_id}')
            return referrer_data
        except Exception as e:
            print(f"Error retrieving referrals: {e}")
            return []
    
    def get_patients(self, 
                     page: int = 1, 
                     per_page: int = 100, 
                     filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve patient list from the software
        
        :param page: Page number for pagination
        :param per_page: Number of patients per page
        :param filters: Optional filters for patient retrieval
        :return: List of normalized patient data
        """
        try:
            # Generate authentication headers
            headers = AuthenticationHandler.get_headers(self.settings)
            
            # Construct query parameters
            params = {
                'page': page,
                'per_page': per_page,
                **(filters or {})
            }
            
            # Make API request
            response = requests.get(
                f"{self.base_url}patients", 
                headers=headers, 
                params=params
            )
            
            response.raise_for_status()  # Raise exception for bad responses
            
            # Normalize patient data
            raw_patients = response.json().get('patients', [])
            
            # Convert timestamps if present
            for patient in raw_patients:
                if 'created_at' in patient:
                    patient['created_at'] = self._convert_timestamp_to_clinic_timezone(patient['created_at'])
                if 'updated_at' in patient:
                    patient['updated_at'] = self._convert_timestamp_to_clinic_timezone(patient['updated_at'])
            
            normalized_patients = [
                DataNormalizer.normalize_patient_data(patient, self.software_type)
                for patient in raw_patients
            ]
            
            return normalized_patients
        
        except requests.RequestException as e:
            print(f"API request error: {e}")
            return []
    
    def search_patients(self, 
                        name: Optional[str] = None, 
                        page: int = 1, 
                        per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Search patients with precise matching logic
        
        :param name: Search term (first name, last name, or full name)
        :param page: Page number for pagination
        :param per_page: Number of patients per page
        :return: List of normalized patient data
        """
        try:
            # Generate authentication headers
            headers = AuthenticationHandler.get_headers(self.settings)
            
            # Prepare search parameters
            params = {
                'page': page,
                'per_page': per_page,
                'search': name
            }
            
            # Make API request
            response = requests.get(
                f"{self.base_url}patients", 
                headers=headers, 
                params=params
            )
            
            response.raise_for_status()
            
            # Get raw patients data
            raw_data = response.json()
            raw_patients = raw_data.get('patients', [])
            
            # Convert timestamps if present
            for patient in raw_patients:
                if 'created_at' in patient:
                    patient['created_at'] = self._convert_timestamp_to_clinic_timezone(patient['created_at'])
                if 'updated_at' in patient:
                    patient['updated_at'] = self._convert_timestamp_to_clinic_timezone(patient['updated_at'])
            
            # Custom filtering function
            def filter_patients(patient):
                full_name = f"{patient['first_name']} {patient['last_name']}".lower()
                first_name = patient['first_name'].lower()
                last_name = patient['last_name'].lower()
                search_term = name.lower() if name else ''
                
                # Exact full name match
                if ' ' in search_term and full_name == search_term:
                    return True
                
                # Exact last name match (no spaces in search term)
                if ' ' not in search_term and search_term == last_name:
                    return True
                
                # First name starts with search term (no spaces)
                if ' ' not in search_term and first_name.startswith(search_term):
                    return True
                
                # Very short search term (3 chars or less)
                if len(search_term) <= 3 and (first_name.startswith(search_term) or last_name.startswith(search_term)):
                    return True
                
                return False
            
            # Apply filtering
            filtered_patients = list(filter(filter_patients, raw_patients))
            
            # Normalize patient data
            normalized_patients = [
                DataNormalizer.normalize_patient_data(patient, self.software_type)
                for patient in filtered_patients
            ]
            
            return normalized_patients
        
        except requests.RequestException as e:
            print(f"Patient search error: {e}")
            return []
    
    def get_patient_details(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve detailed information for a specific patient
        
        :param patient_id: Unique identifier for the patient
        :return: Normalized patient details or None
        """
        try:
            headers = AuthenticationHandler.get_headers(self.settings)
            
            response = requests.get(
                f"{self.base_url}patients/{patient_id}", 
                headers=headers
            )
            
            response.raise_for_status()
            
            patient_data = response.json()
            
            # Convert timestamps if present
            if 'created_at' in patient_data:
                patient_data['created_at'] = self._convert_timestamp_to_clinic_timezone(patient_data['created_at'])
            if 'updated_at' in patient_data:
                patient_data['updated_at'] = self._convert_timestamp_to_clinic_timezone(patient_data['updated_at'])
            
            return DataNormalizer.normalize_patient_data(patient_data, self.software_type)
        
        except requests.RequestException as e:
            print(f"Patient details retrieval error: {e}")
            return None
    
    def validate_connection(self) -> bool:
        """
        Validate software integration connection
        
        :return: Boolean indicating successful connection
        """
        return AuthenticationHandler.validate_credentials(self.settings)
