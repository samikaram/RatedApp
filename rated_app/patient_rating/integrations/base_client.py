from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class BaseClient(ABC):
    def __init__(self, settings):
        """
        Initialize client with software-specific settings
        
        :param settings: Configuration settings for the software
        """
        self.settings = settings
        self.base_url = settings.base_url
        self.api_key = settings.api_key

    @abstractmethod
    def get_patients(
        self, 
        page: int = 1, 
        per_page: int = 100, 
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Retrieve patients from the software
        
        :param page: Page number for pagination
        :param per_page: Number of patients per page
        :param filters: Optional filters for patient retrieval
        :return: List of patient data
        """
        pass

    @abstractmethod
    def search_patients(
        self, 
        name: Optional[str] = None, 
        page: int = 1, 
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search patients with name-based filtering
        
        :param name: Search term (first name, last name, or full name)
        :param page: Page number for pagination
        :param per_page: Number of patients per page
        :return: List of normalized patient data
        """
        pass

    @abstractmethod
    def get_appointments(
        self, 
        patient_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve appointments for a specific patient
        
        :param patient_id: Unique identifier for the patient
        :param start_date: Optional start date for filtering
        :param end_date: Optional end date for filtering
        :return: List of appointment data
        """
        pass

    @abstractmethod
    def get_invoices(
        self, 
        patient_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve invoices for a specific patient
        
        :param patient_id: Unique identifier for the patient
        :param start_date: Optional start date for filtering
        :param end_date: Optional end date for filtering
        :return: List of invoice data
        """
        pass

    @abstractmethod
    def get_referrals(
        self, 
        patient_id: str
    ) -> List[Dict]:
        """
        Retrieve referrals for a specific patient
        
        :param patient_id: Unique identifier for the patient
        :return: List of referral data
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate the connection to the software's API
        
        :return: Boolean indicating successful connection
        """
        pass

    @abstractmethod
    def get_appointments_by_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        page: int = 1, 
        per_page: int = 100
    ) -> List[Dict]:
        """
        Retrieve appointments within a date range
        
        :param start_date: Start date in ISO format
        :param end_date: End date in ISO format
        :param page: Page number for pagination
        :param per_page: Number of results per page
        :return: List of appointment data
        """
        pass
    
    @abstractmethod
    def update_appointment_notes(
        self, 
        appointment_id: str, 
        notes: str, 
        append: bool = True
    ) -> bool:
        """
        Update appointment notes field
        
        :param appointment_id: Unique appointment identifier
        :param notes: Notes text to add
        :param append: Whether to append or replace notes
        :return: Success status
        """
        pass
    
    @abstractmethod
    def batch_get_patients(
        self, 
        patient_ids: List[str]
    ) -> List[Dict]:
        """
        Get multiple patients in one or more API calls
        
        :param patient_ids: List of patient IDs to fetch
        :return: List of patient data
        """
        pass
    
    @abstractmethod
    def get_patients_with_appointments_in_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        Get unique patients who had appointments in date range
        
        :param start_date: Start date in ISO format
        :param end_date: End date in ISO format
        :return: List of unique patient data with basic info
        """
        pass
    
    @abstractmethod
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get API rate limit information for this integration
        
        :return: Dictionary with rate limit details
        """
        pass
