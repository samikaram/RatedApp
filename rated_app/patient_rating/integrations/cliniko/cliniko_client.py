import requests
import pytz
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from ..base_client import BaseClient
from ...software_integrations import AuthenticationHandler

class ClinikoClient(BaseClient):
    def get_patients(
            self, 
            page: int = 1, 
            per_page: int = 100, 
            filters: Optional[Dict] = None
        ) -> List[Dict]:
        """
        Retrieve patients from Cliniko
        """
        try:
            # Prepare parameters
            params = {
                'page': page,
                'per_page': per_page
            }
            
            # Prioritize q[] filter, convert id to q[] if necessary
            if filters:
                if 'q[]' in filters:
                    # Use q[] as-is if provided
                    params['q[]'] = filters['q[]']
                elif 'id' in filters:
                    # Convert id to q[] format
                    params['q[]'] = f'id:={filters["id"]}'
            
            # Make API request
            response = requests.get(
                f"{self.base_url}patients", 
                headers=AuthenticationHandler.get_headers(self.settings), 
                params=params
            )
            
            response.raise_for_status()
            
            # Extract and convert patient data
            raw_patients = response.json().get('patients', [])
            
            # Convert timestamps
            for patient in raw_patients:
                if 'created_at' in patient:
                    patient['created_at'] = self._convert_timestamp(patient['created_at'])
                if 'updated_at' in patient:
                    patient['updated_at'] = self._convert_timestamp(patient['updated_at'])
            
            return raw_patients
        
        except requests.RequestException as e:
            print(f"Cliniko patient retrieval error: {e}")
            return []

    def get_appointments(
        self, 
        patient_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve appointments for a specific patient
        """
        try:
            # Prepare filters
            filter_params = {'q[]': [f'patient_id:={patient_id}']}
            
            # Add date filters if provided
            if start_date:
                filter_params['q[]'].append(f'starts_at:>={start_date}')
            if end_date:
                filter_params['q[]'].append(f'starts_at:<={end_date}')
            
            # Retrieve active appointments
            active_appointments = self._get_paginated_data(
                'individual_appointments', 
                filter_params, 
                f'appointments for patient {patient_id}'
            )
            
            # Retrieve cancelled appointments
            cancelled_filter_params = {
                'q[]': [
                    f'patient_id:={patient_id}', 
                    'cancelled_at:?'
                ]
            }
            cancelled_appointments = self._get_paginated_data(
                'individual_appointments', 
                cancelled_filter_params, 
                f'cancelled appointments for patient {patient_id}'
            )
            
            # Combine and convert timestamps
            all_appointments = active_appointments + cancelled_appointments
            for appointment in all_appointments:
                if 'starts_at' in appointment:
                    appointment['starts_at'] = self._convert_timestamp(appointment['starts_at'])
                if 'ends_at' in appointment:
                    appointment['ends_at'] = self._convert_timestamp(appointment['ends_at'])
                if 'cancelled_at' in appointment and appointment['cancelled_at']:
                    appointment['cancelled_at'] = self._convert_timestamp(appointment['cancelled_at'])
            
            return all_appointments
        
        except Exception as e:
            print(f"Cliniko appointments retrieval error: {e}")
            return []

    def get_invoices(
        self, 
        patient_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve invoices for a specific patient
        """
        try:
            # Prepare filters
            filter_params = {'q[]': [f'patient_id:={patient_id}']}
            
            # Add date filters if provided
            if start_date:
                filter_params['q[]'].append(f'created_at:>={start_date}')
            if end_date:
                filter_params['q[]'].append(f'created_at:<={end_date}')
            
            # Retrieve invoices
            invoices = self._get_paginated_data(
                'invoices', 
                filter_params, 
                f'invoices for patient {patient_id}'
            )
            
            # Convert timestamps
            for invoice in invoices:
                if 'created_at' in invoice:
                    invoice['created_at'] = self._convert_timestamp(invoice['created_at'])
                if 'updated_at' in invoice:
                    invoice['updated_at'] = self._convert_timestamp(invoice['updated_at'])
                if 'closed_at' in invoice and invoice['closed_at']:
                    invoice['closed_at'] = self._convert_timestamp(invoice['closed_at'])
            
            return invoices
        
        except Exception as e:
            print(f"Cliniko invoices retrieval error: {e}")
            return []

    def get_referrals(self, patient_id: str) -> List[Dict]:
        """
        Retrieve referral sources for a specific patient
        Finds patients referred by this patient
        """
        try:
            referrer_params = {
                'q[]': f'referrer_id:={patient_id}',
                'per_page': 50
            }
            
            referrer_data = self._get_paginated_data(
                'referral_sources', 
                referrer_params, 
                f'referrals for patient {patient_id}'
            )
            
            # Extract referred patient IDs from links
            referred_patients = [
                referral['patient']['links']['self'].split('/')[-1] 
                for referral in referrer_data 
                if 'patient' in referral and 'links' in referral['patient']
            ]
            
            return {
                'referral_count': len(referred_patients),
                'referred_patient_ids': referred_patients
            }
        
        except Exception as e:
            print(f"Cliniko referrals retrieval error: {e}")
            return {'referral_count': 0, 'referred_patient_ids': []}

    def search_patients(
        self, 
        name: Optional[str] = None, 
        page: int = 1, 
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search patients with precise matching logic
        
        :param name: Search term (first name, last name, or full name)
        :param page: Page number for pagination
        :param per_page: Number of patients per page
        :return: List of normalized patient data
        """
        try:
            # Prepare search parameters
            params = {
                'page': page,
                'per_page': per_page,
                'search': name
            }
            
            # Make API request
            response = requests.get(
                f"{self.base_url}patients", 
                headers=AuthenticationHandler.get_headers(self.settings), 
                params=params
            )
            
            response.raise_for_status()
            
            # Get raw patients data
            raw_data = response.json()
            raw_patients = raw_data.get('patients', [])
            
            # Convert timestamps if present
            for patient in raw_patients:
                if 'created_at' in patient:
                    patient['created_at'] = self._convert_timestamp(patient['created_at'])
                if 'updated_at' in patient:
                    patient['updated_at'] = self._convert_timestamp(patient['updated_at'])
            
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
            
            return filtered_patients
        
        except requests.RequestException as e:
            print(f"Patient search error: {e}")
            return []

    def validate_connection(self) -> bool:
        """
        Validate the connection to Cliniko API
        """
        return AuthenticationHandler.validate_credentials(self.settings)

    def _get_paginated_data(self, endpoint: str, params: Dict, description: str) -> List[Dict]:
        """
        Get all paginated data from Cliniko API
        """
        all_data = []
        page = 1
        
        while True:
            current_params = params.copy()
            current_params['page'] = page
            current_params['per_page'] = 100
            
            url = f"{self.base_url}{endpoint}"
            
            try:
                response = requests.get(
                    url, 
                    headers=AuthenticationHandler.get_headers(self.settings), 
                    params=current_params
                )
                
                if response.status_code != 200:
                    print(f"❌ Cliniko API Error {response.status_code}: {response.text}")
                    break
                
                data = response.json()
                
                # Handle different response structures
                if endpoint == 'individual_appointments':
                    items = data.get('individual_appointments', [])
                elif endpoint == 'patients':
                    items = data.get('patients', [])
                elif endpoint == 'invoices':
                    items = data.get('invoices', [])
                elif endpoint == 'referral_sources':
                    items = data.get('referral_sources', [])
                else:
                    items = data.get('items', [])
                
                all_data.extend(items)
                
                # Check if there are more pages
                if len(items) < 100:
                    break
                
                page += 1
            
            except Exception as e:
                print(f"Cliniko data retrieval error: {e}")
                break
        
        return all_data

    def _convert_timestamp(self, timestamp_str: str) -> str:
        """
        Convert a timestamp to the clinic's selected timezone
        """
        try:
            # Parse the timestamp (assuming UTC)
            utc_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            utc_time = utc_time.replace(tzinfo=pytz.UTC)
            
            # Convert to clinic's timezone
            clinic_tz = pytz.timezone(self.settings.clinic_timezone or 'Australia/Sydney')
            converted_time = utc_time.astimezone(clinic_tz)
            
            return converted_time.isoformat()
        except Exception as e:
            print(f"Timestamp conversion error: {e}")
            return timestamp_str

    def get_appointments_by_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        page: int = 1, 
        per_page: int = 100
    ) -> List[Dict]:
        """
        Retrieve appointments within a date range from Cliniko
        """
        try:
            # Ensure dates are in correct format with Z suffix
            if not start_date.endswith('Z'):
                start_date = f"{start_date}Z"
            if not end_date.endswith('Z'):
                end_date = f"{end_date}Z"
            
            # Use Cliniko's filtering
            filter_params = {
                'q[]': [
                    f'starts_at:>={start_date}',
                    f'starts_at:<={end_date}'
                ],
                'per_page': per_page,
                'page': page
            }
            
            appointments = self._get_paginated_data(
                'individual_appointments',
                filter_params,
                f'appointments from {start_date} to {end_date}'
            )
            
            return appointments
            
        except Exception as e:
            print(f"Error fetching appointments by date range: {e}")
            return []
    
    def update_appointment_notes(
        self, 
        appointment_id: str, 
        notes: str, 
        append: bool = True
    ) -> bool:
        """
        Update appointment notes in Cliniko
        Note: Cliniko uses 'notes' field on appointments
        """
        try:
            # First, get current appointment to preserve existing notes if appending
            url = f"{self.base_url}appointments/{appointment_id}"
            response = requests.get(
                url,
                headers=AuthenticationHandler.get_headers(self.settings)
            )
            
            if response.status_code != 200:
                print(f"Failed to get appointment {appointment_id}: {response.status_code}")
                return False
            
            appointment = response.json()
            current_notes = appointment.get('notes', '')
            
            if append and current_notes:
                # Remove any existing rating (pattern: Rated [A-F+])
                cleaned_notes = re.sub(r'Rated [A-F]\+?\s*', '', current_notes)
                # Prepend new rating
                new_notes = f"{notes} {cleaned_notes}".strip()
            else:
                new_notes = notes
            
            # Update appointment with new notes
            update_data = {
                'notes': new_notes
            }
            
            response = requests.put(
                url,
                headers=AuthenticationHandler.get_headers(self.settings),
                json=update_data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error updating appointment notes: {e}")
            return False
    
    def batch_get_patients(
        self, 
        patient_ids: List[str]
    ) -> List[Dict]:
        """
        Get multiple patients - Cliniko doesn't support true batch,
        so we'll optimize with concurrent requests where possible
        """
        patients = []
        
        # Process in chunks to avoid overwhelming the API
        chunk_size = 10
        for i in range(0, len(patient_ids), chunk_size):
            chunk = patient_ids[i:i+chunk_size]
            
            for patient_id in chunk:
                try:
                    filter_params = {'id': patient_id}
                    patient_data = self.get_patients(filters=filter_params)
                    if patient_data:
                        patients.extend(patient_data)
                    
                    # Small delay between requests
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"Error fetching patient {patient_id}: {e}")
                    continue
            
            # Longer pause between chunks
            if i + chunk_size < len(patient_ids):
                time.sleep(2)
        
        return patients
    
    def get_patients_with_appointments_in_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        Get unique patients who had appointments in the specified date range
        """
        try:
            # Get all appointments in range
            appointments = self.get_appointments_by_date_range(start_date, end_date)
            
            # Extract unique patient information
            seen_patient_ids = set()
            patient_details = []
            
            for appointment in appointments:
                patient_link = appointment.get('patient', {}).get('links', {}).get('self', '')
                if patient_link:
                    patient_id = patient_link.split('/')[-1]
                    
                    # Skip if we've already processed this patient
                    if patient_id not in seen_patient_ids:
                        # Get basic patient info from appointment
                        patient_info = {
                            'patient_id': patient_id,
                            'appointment_start': appointment.get('starts_at'),
                            # We'll fetch full details later to avoid too many API calls
                        }
                        
                        patient_details.append(patient_info)
                        seen_patient_ids.add(patient_id)
            
            # Now fetch full details for unique patients
            for patient_info in patient_details:
                try:
                    patients = self.get_patients(filters={'id': patient_info['patient_id']})
                    if patients:
                        patient = patients[0]
                        patient_info['name'] = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
                        patient_info['email'] = patient.get('email')
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error fetching details for patient {patient_info['patient_id']}: {e}")
                    patient_info['name'] = f"Patient {patient_info['patient_id']}"
            
            return patient_details
            
        except Exception as e:
            print(f"Error getting patients with appointments: {e}")
            return []
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Return Cliniko's rate limit information
        """
        return {
            'requests_per_minute': 200,
            'recommended_delay': 0.5,  # seconds between requests
            'batch_size': 100,  # max records per request
            'concurrent_requests': 1,  # Cliniko prefers sequential
            'retry_after': 60,  # seconds to wait if rate limited
        }
    
    def update_patient_appointment_notes(
        self,
        patient_id: str,
        rating_text: str
    ) -> bool:
        """
        Update the most recent appointment notes for a patient
        Used by analytics processing
        """
        try:
            # Get patient's most recent appointment
            appointments = self.get_appointments(patient_id)
            
            if not appointments:
                print(f"No appointments found for patient {patient_id}")
                return False
            
            # Sort by start time and get most recent
            sorted_appointments = sorted(
                appointments,
                key=lambda x: x.get('starts_at', ''),
                reverse=True
            )
            
            most_recent = sorted_appointments[0]
            appointment_id = most_recent.get('id')
            
            if not appointment_id:
                print(f"No appointment ID found for patient {patient_id}")
                return False
            
            # Update the appointment notes
            return self.update_appointment_notes(appointment_id, rating_text, append=True)
            
        except Exception as e:
            print(f"Error updating patient appointment notes: {e}")
            return False
