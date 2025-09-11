from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseNormalizer(ABC):
    @abstractmethod
    def normalize_patient(self, raw_patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize patient data from raw API response
        
        :param raw_patient_data: Raw patient data from software API
        :return: Standardized patient data dictionary
        """
        pass

    @abstractmethod
    def normalize_appointment(self, raw_appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize appointment data from raw API response
        
        :param raw_appointment_data: Raw appointment data from software API
        :return: Standardized appointment data dictionary
        """
        pass

    @abstractmethod
    def normalize_invoice(self, raw_invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize invoice data from raw API response
        
        :param raw_invoice_data: Raw invoice data from software API
        :return: Standardized invoice data dictionary
        """
        pass

    @abstractmethod
    def normalize_referral(self, raw_referral_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize referral data from raw API response
        
        :param raw_referral_data: Raw referral data from software API
        :return: Standardized referral data dictionary
        """
        pass
