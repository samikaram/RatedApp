#!/usr/bin/env python3
import requests
import base64
from datetime import datetime
import pytz

print("🔍 SIMPLE RESCHEDULED APPOINTMENTS DIAGNOSTIC")
print("="*50)

# API Configuration
api_key = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"

# Authentication
auth_string = f"{api_key}:"
encoded_auth = base64.b64encode(auth_string.encode()).decode()

headers = {
    'Authorization': f'Basic {encoded_auth}',
    'Accept': 'application/json',
    'User-Agent': 'Simple Diagnostic'
}

print("✅ Authentication setup complete")

# Test API connection
base_url = "https://api.au1.cliniko.com/v1"
aest = pytz.timezone('Australia/Sydney')
utc = pytz.UTC

# Extended range: June 22 - July 15, 2025
extended_start_aest = aest.localize(datetime(2025, 6, 22, 0, 0, 0))
extended_end_aest = aest.localize(datetime(2025, 7, 15, 23, 59, 59))

extended_start_utc = extended_start_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')
extended_end_utc = extended_end_aest.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%SZ')

print(f"🔍 Checking appointments from {extended_start_utc} to {extended_end_utc}")

# Get first page of appointments
url = f"{base_url}/individual_appointments"
params = {
    'q[]': [
        f'starts_at:>{extended_start_utc}',
        f'starts_at:<{extended_end_utc}'
    ],
    'per_page': 10,
    'page': 1
}

try:
    response = requests.get(url, headers=headers, params=params)
    print(f"📡 API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        appointments = data.get('individual_appointments', [])
        print(f"✅ Found {len(appointments)} appointments in extended range")
        
        if appointments:
            print(f"\n📅 Sample appointment:")
            apt = appointments[0]
            print(f"   ID: {apt.get('id')}")
            print(f"   Starts: {apt.get('starts_at')}")
            print(f"   Created: {apt.get('created_at')}")
            print(f"   Updated: {apt.get('updated_at')}")
        else:
            print("❌ No appointments found in extended range")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {str(e)}")

print("\n🎯 Simple diagnostic complete")

