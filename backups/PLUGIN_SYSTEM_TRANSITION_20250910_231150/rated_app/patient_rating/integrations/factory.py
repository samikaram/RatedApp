from typing import Union

from .base_client import BaseClient
from .base_normalizer import BaseNormalizer

class IntegrationFactory:
    @staticmethod
    def get_client(settings) -> BaseClient:
        """
        Get the appropriate client based on software type
        
        :param settings: Software settings object
        :return: Instantiated client for the specified software
        """
        software_type = settings.software_type.lower()
        
        if software_type == 'cliniko':
            from .cliniko.cliniko_client import ClinikoClient
            return ClinikoClient(settings)
        
        # Future software integrations will be added here
        
        raise ValueError(f"Unsupported software type: {software_type}")
    
    @staticmethod
    def get_normalizer(settings) -> BaseNormalizer:
        """
        Get the appropriate normalizer based on software type
        
        :param settings: Software settings object
        :return: Instantiated normalizer for the specified software
        """
        software_type = settings.software_type.lower()
        
        if software_type == 'cliniko':
            from .cliniko.cliniko_normalizer import ClinikoNormalizer
            return ClinikoNormalizer()
        
        # Future software integrations will be added here
        
        raise ValueError(f"Unsupported software type: {software_type}")
