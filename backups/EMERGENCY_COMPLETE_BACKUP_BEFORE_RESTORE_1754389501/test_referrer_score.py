#!/usr/bin/env python3
"""
REFERRER SCORE TEST - BRONWYN KEDICIOGLU
Testing referral source filtering by referrer field
Adhering to official Cliniko API documentation
"""

import requests
import json
import base64
from datetime import datetime
import pytz

# ✅ CORRECT API KEY - July 3, 2025
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Bronwyn's patient ID
BRONWYN_PATIENT_ID = "1707655488738428562"

def get_auth_header(api_key):
    """Create proper Cliniko API authentication header"""
    credentials = f"{api_key}:"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"

def test_referrer_filtering():
    """Test referrer score calculation using proper API filtering"""
    print("🎯 REFERRER SCORE TEST - BRONWYN KEDICIOGLU")
    print("="*80)
    print("✅ USING: Official Cliniko API documentation")
    print("✅ TESTING: Referral source filtering by referrer field")
    print(f"✅ BRONWYN PATIENT ID: {BRONWYN_PATIENT_ID}")
    print("="*80)
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    try:
        # TEST 1: Try filtering by referrer field with Bronwyn's patient ID
        print(f"\n🔍 TEST 1: Filter by referrer field")
        print(f"📡 Testing: q[]=referrer:{BRONWYN_PATIENT_ID}")
        
        filter_params = {
            'q[]': f'referrer:{BRONWYN_PATIENT_ID}'
        }
        
        response = requests.get(
            f"{BASE_URL}/referral_sources",
            headers=headers,
            params=filter_params
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            referral_sources = data.get('referral_sources', [])
            
            print(f"✅ SUCCESS: Found {len(referral_sources)} referral sources")
            print(f"🎯 BRONWYN'S REFERRER SCORE: {len(referral_sources)}")
            
            # Show details of found referrals
            for i, ref_source in enumerate(referral_sources, 1):
                print(f"\n   📋 REFERRAL {i}:")
                print(f"      ID: {ref_source.get('id')}")
                print(f"      Patient: {ref_source.get('patient', {}).get('links', {}).get('self', 'N/A')}")
                print(f"      Referrer: {ref_source.get('referrer', 'N/A')}")
                print(f"      Notes: {ref_source.get('notes', 'N/A')}")
            
            return len(referral_sources)
            
        elif response.status_code == 400:
            print(f"❌ ERROR 400: {response.text}")
            print(f"🔍 This means 'referrer' field is not filterable")
            return None
            
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def test_alternative_approaches():
    """Test alternative approaches if direct filtering doesn't work"""
    print(f"\n🔍 TESTING ALTERNATIVE APPROACHES:")
    print("="*60)
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    # TEST 2: Get first page of referral sources to examine structure
    print(f"\n📡 TEST 2: Examine referral source structure")
    
    try:
        response = requests.get(
            f"{BASE_URL}/referral_sources",
            headers=headers,
            params={'per_page': 5}  # Just get 5 to examine structure
        )
        
        if response.status_code == 200:
            data = response.json()
            referral_sources = data.get('referral_sources', [])
            
            print(f"✅ Retrieved {len(referral_sources)} sample referral sources")
            
            for i, ref_source in enumerate(referral_sources, 1):
                print(f"\n   📋 SAMPLE {i}:")
                print(f"      ID: {ref_source.get('id')}")
                print(f"      Referrer: {ref_source.get('referrer')}")
                print(f"      Referrer Type: {ref_source.get('referrer_type')}")
                print(f"      Patient: {ref_source.get('patient', {}).get('links', {}).get('self', 'N/A')}")
                print(f"      Notes: {ref_source.get('notes', 'N/A')}")
                
                # Check if referrer contains patient ID structure
                referrer = ref_source.get('referrer')
                if referrer and isinstance(referrer, dict):
                    print(f"      Referrer Details: {referrer}")
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def main():
    """Main test function"""
    print("🚀 STARTING REFERRER SCORE TEST")
    print("📋 Adhering to official Cliniko API documentation")
    print(f"📅 Test Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    
    # Test direct filtering approach
    referrer_score = test_referrer_filtering()
    
    # Test alternative approaches
    test_alternative_approaches()
    
    # Final results
    print(f"\n🎯 FINAL TEST RESULTS:")
    print("="*80)
    
    if referrer_score is not None:
        print(f"✅ BRONWYN'S REFERRER SCORE: {referrer_score}")
        print(f"✅ EXPECTED: 1")
        print(f"✅ MATCH: {'YES' if referrer_score == 1 else 'NO'}")
        print(f"✅ METHOD: Direct API filtering")
    else:
        print(f"❌ DIRECT FILTERING FAILED")
        print(f"🔍 Need alternative approach for referrer score calculation")
    
    print(f"\n🎉 TEST COMPLETE!")

if __name__ == "__main__":
    main()

