import base64
import requests
from django.conf import settings
from typing import Dict, Any

class AuthenticationHandler:
    """
    Handles authentication for different software integrations
    Supports multiple authentication methods
    """
    
    @staticmethod
    def get_headers(settings_obj) -> Dict[str, str]:
        """
        Generate authentication headers based on software type and auth method
        
        :param settings_obj: RatedAppSettings instance
        :return: Dictionary of authentication headers
        """
        auth_method = settings_obj.auth_type
        api_key = settings_obj.api_key
        
        if auth_method == 'basic':
            return AuthenticationHandler._basic_auth_headers(api_key)
        elif auth_method == 'oauth2':
            return AuthenticationHandler._oauth_headers(api_key)
        elif auth_method == 'api_key':
            return AuthenticationHandler._api_key_headers(api_key)
        else:
            raise ValueError(f"Unsupported authentication type: {auth_method}")
    
    @staticmethod
    def _basic_auth_headers(api_key: str) -> Dict[str, str]:
        """
        Generate Basic Authentication headers
        
        :param api_key: API key for basic authentication
        :return: Headers for Basic Authentication
        """
        if not api_key:
            raise ValueError("API key is required for Basic Authentication")
        
        encoded_key = base64.b64encode(f"{api_key}:".encode()).decode()
        return {
            'Authorization': f'Basic {encoded_key}',
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def _oauth_headers(access_token: str) -> Dict[str, str]:
        """
        Generate OAuth 2.0 Authentication headers
        
        :param access_token: OAuth access token
        :return: Headers for OAuth Authentication
        """
        if not access_token:
            raise ValueError("Access token is required for OAuth")
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def _api_key_headers(api_key: str) -> Dict[str, str]:
        """
        Generate API Key Authentication headers
        
        :param api_key: API key for authentication
        :return: Headers for API Key Authentication
        """
        if not api_key:
            raise ValueError("API key is required")
        
        return {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    @classmethod
    def validate_credentials(cls, settings_obj) -> bool:
        """
        Validate credentials by making a test API call
        
        :param settings_obj: RatedAppSettings instance
        :return: Boolean indicating credential validity
        """
        try:
            headers = cls.get_headers(settings_obj)
            response = requests.get(
                settings_obj.base_url + 'patients',  # Example endpoint
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Credential validation failed: {e}")
            return False
