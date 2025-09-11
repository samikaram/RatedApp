from typing import Dict, Any
from ..base_normalizer import BaseNormalizer

class ClinikoNormalizer(BaseNormalizer):
    @classmethod
    def normalize_patient(cls, raw_patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize patient data from Cliniko raw data
        
        :param raw_patient_data: Raw patient data from Cliniko API
        :return: Standardized patient data dictionary
        """
        return {
            'id': raw_patient_data.get('id'),
            'first_name': raw_patient_data.get('first_name', ''),
            'last_name': raw_patient_data.get('last_name', ''),
            'full_name': f"{raw_patient_data.get('first_name', '')} {raw_patient_data.get('last_name', '')}".strip(),
            'email': raw_patient_data.get('email', ''),
            'phone': raw_patient_data.get('mobile_phone', ''),
            'date_of_birth': raw_patient_data.get('date_of_birth'),
            'created_at': raw_patient_data.get('created_at'),
            'updated_at': raw_patient_data.get('updated_at')
        }

    @classmethod
    def normalize_appointment(self, raw_appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize appointment data from Cliniko raw data
        
        :param raw_appointment_data: Raw appointment data from Cliniko API
        :return: Standardized appointment data dictionary
        """
        return {
            'id': raw_appointment_data.get('id'),
            'patient_id': raw_appointment_data.get('patient_id'),
            'starts_at': raw_appointment_data.get('starts_at'),
            'ends_at': raw_appointment_data.get('ends_at'),
            'status': 'cancelled' if raw_appointment_data.get('cancelled_at') else 'active',
            'cancelled_at': raw_appointment_data.get('cancelled_at'),
            'did_not_arrive': raw_appointment_data.get('did_not_arrive', False)
        }

    @classmethod
    def normalize_invoice(self, raw_invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize invoice data from Cliniko raw data
        
        :param raw_invoice_data: Raw invoice data from Cliniko API
        :return: Standardized invoice data dictionary
        """
        return {
            'id': raw_invoice_data.get('id'),
            'patient_id': raw_invoice_data.get('patient_id'),
            'total_amount': raw_invoice_data.get('total_amount', 0.0),
            'created_at': raw_invoice_data.get('created_at'),
            'closed_at': raw_invoice_data.get('closed_at'),
            'is_paid': raw_invoice_data.get('closed_at') is not None
        }

    @classmethod
    def normalize_referral(self, raw_referral_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize referral data from Cliniko raw data
        
        :param raw_referral_data: Raw referral data from Cliniko API
        :return: Standardized referral data dictionary
        """
        return {
            'id': raw_referral_data.get('id'),
            'referrer_id': raw_referral_data.get('referrer_id'),
            'patient_id': raw_referral_data.get('patient', {}).get('id'),
            'referral_source_type': raw_referral_data.get('referral_source_type', {}).get('name')
        }
