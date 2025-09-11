#!/usr/bin/env python3
"""
REFERRER SCORE TEST - BRONWYN KEDICIOGLU
Testing referrers links from Patient referral source type
Following official Cliniko ReferralSourceType schema documentation
Examining referrers field links and structure
"""

import requests
import json
import base64
from datetime import datetime
import pytz
import time

# ✅ CORRECT API KEY - July 3, 2025
API_KEY = "MS0xNzIwNjExOTk1MjMwNjY3Nzk4LWJieWZXTDBvV2w5L1pYOFVsK3hsRlFPeHlocmhkbVRw-au1"
BASE_URL = "https://api.au1.cliniko.com/v1"
AEST = pytz.timezone('Australia/Sydney')

# Known IDs
BRONWYN_PATIENT_ID = "1707655488738428562"
PATIENT_TYPE_ID = "37606"  # From previous test

def get_auth_header(api_key):
    """Create proper Cliniko API authentication header"""
    credentials = f"{api_key}:"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"

def get_referral_source_type_with_links():
    """Get Patient referral source type and examine links structure"""
    print("🔍 STEP 1: GET PATIENT REFERRAL SOURCE TYPE WITH LINKS")
    print("="*70)
    print(f"✅ Patient Type ID: {PATIENT_TYPE_ID}")
    print(f"✅ Following: Official Cliniko ReferralSourceType schema")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    try:
        # Get the Patient referral source type
        response = requests.get(
            f"{BASE_URL}/referral_source_types/{PATIENT_TYPE_ID}",
            headers=headers
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Parse the full response
            full_response = response.json()
            print(f"✅ Successfully retrieved referral source type")
            
            # Show the complete response structure
            print(f"\n📋 COMPLETE API RESPONSE:")
            print(json.dumps(full_response, indent=2))
            
            # Extract the referral source type data
            ref_type = full_response.get('referral_source_type', {})
            
            print(f"\n📋 REFERRAL SOURCE TYPE DATA:")
            print(f"   ID: {ref_type.get('id')}")
            print(f"   Name: {ref_type.get('name')}")
            print(f"   Referrer Type: {ref_type.get('referrer_type')}")
            print(f"   Created: {ref_type.get('created_at')}")
            print(f"   Updated: {ref_type.get('updated_at')}")
            
            # Check for links structure
            links = ref_type.get('links', {})
            if links:
                print(f"\n🔗 LINKS STRUCTURE FOUND:")
                for link_name, link_url in links.items():
                    print(f"   {link_name}: {link_url}")
            
            # Check for referrers field specifically
            referrers = ref_type.get('referrers')
            if referrers:
                print(f"\n🎯 REFERRERS FIELD FOUND!")
                print(f"   Type: {type(referrers)}")
                print(f"   Content: {referrers}")
                
                # If referrers has links, extract them
                if isinstance(referrers, dict):
                    referrers_links = referrers.get('links', {})
                    if referrers_links:
                        print(f"   Referrers Links: {referrers_links}")
                        return ref_type, referrers_links.get('self')
                    else:
                        print(f"   No links found in referrers field")
            else:
                print(f"\n⚠️ No referrers field in response")
                
            # Check for subcategories
            subcategories = ref_type.get('subcategories')
            if subcategories:
                print(f"\n📋 SUBCATEGORIES FIELD:")
                print(f"   Type: {type(subcategories)}")
                print(f"   Content: {subcategories}")
                
                if isinstance(subcategories, dict):
                    subcat_links = subcategories.get('links', {})
                    if subcat_links:
                        print(f"   Subcategories Links: {subcat_links}")
            
            return ref_type, None
            
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None, None

def test_referrers_endpoint(referrers_url):
    """Test the referrers endpoint to find actual referring patients"""
    if not referrers_url:
        print(f"\n⚠️ No referrers URL provided")
        return None
        
    print(f"\n🔍 STEP 2: TEST REFERRERS ENDPOINT")
    print("="*70)
    print(f"✅ Referrers URL: {referrers_url}")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    try:
        response = requests.get(referrers_url, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Successfully retrieved referrers data")
            print(f"\n📋 COMPLETE REFERRERS RESPONSE:")
            print(json.dumps(data, indent=2))
            
            # Look for referring patients
            referrers_list = []
            if isinstance(data, dict):
                # Check different possible structures
                for key in ['referrers', 'patients', 'data', 'results']:
                    if key in data and isinstance(data[key], list):
                        referrers_list = data[key]
                        print(f"\n🎯 FOUND REFERRERS LIST: {len(referrers_list)} items")
                        break
                        
                if not referrers_list and 'referrers' in data:
                    # Handle case where referrers is not a list
                    referrers_list = [data['referrers']] if data['referrers'] else []
            
            # Search for Bronwyn in referrers
            bronwyn_found = False
            bronwyn_referrals = 0
            
            if referrers_list:
                print(f"\n📋 EXAMINING REFERRERS:")
                for i, referrer in enumerate(referrers_list):
                    print(f"\n   📋 REFERRER {i+1}:")
                    
                    if isinstance(referrer, dict):
                        for ref_key, ref_value in referrer.items():
                            print(f"      {ref_key}: {ref_value}")
                            
                        # Check if this is Bronwyn
                        referrer_id = str(referrer.get('id', ''))
                        if referrer_id == BRONWYN_PATIENT_ID:
                            bronwyn_found = True
                            print(f"      🎯 BRONWYN FOUND AS REFERRER!")
                            
                            # Count her referrals
                            referral_count = referrer.get('referral_count', 0)
                            if referral_count:
                                bronwyn_referrals = referral_count
                                print(f"      🎯 BRONWYN'S REFERRAL COUNT: {referral_count}")
                    else:
                        print(f"      Content: {referrer}")
                        
            if bronwyn_found:
                print(f"\n✅ SUCCESS: Bronwyn found in referrers!")
                print(f"✅ Referral count: {bronwyn_referrals}")
                return bronwyn_referrals
            else:
                print(f"\n⚠️ Bronwyn not found in referrers list")
                return 0
                
        elif response.status_code == 404:
            print(f"❌ ERROR 404: Referrers endpoint not found")
            return None
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def test_alternative_referrers_endpoints():
    """Test alternative ways to access referrers data"""
    print(f"\n🔍 STEP 3: TEST ALTERNATIVE REFERRERS ENDPOINTS")
    print("="*70)
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    # Test different possible referrers endpoints
    test_endpoints = [
        f"{BASE_URL}/referral_source_types/{PATIENT_TYPE_ID}/referrers",
        f"{BASE_URL}/referrers",
        f"{BASE_URL}/patients/{BRONWYN_PATIENT_ID}/referrals",
        f"{BASE_URL}/patients/{BRONWYN_PATIENT_ID}/referred_patients"
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"\n📡 Testing: {endpoint}")
            
            response = requests.get(endpoint, headers=headers)
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: {endpoint}")
                print(f"📋 Response structure:")
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            print(f"   {key}: {len(value)} items")
                        else:
                            print(f"   {key}: {type(value)}")
                            
                # Look for Bronwyn-related data
                data_str = json.dumps(data).lower()
                if 'bronwyn' in data_str or BRONWYN_PATIENT_ID in data_str:
                    print(f"🎯 BRONWYN DATA FOUND!")
                    return data
                    
            elif response.status_code == 404:
                print(f"❌ 404: Endpoint not found")
            else:
                print(f"❌ ERROR {response.status_code}: {response.text}")
                
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            
    return None

def main():
    """Main test function"""
    print("🚀 STARTING COMPREHENSIVE REFERRERS LINKS TEST")
    print("📋 Following official Cliniko ReferralSourceType schema documentation")
    print(f"📅 Test Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🎯 REFERRER SCORE TEST - BRONWYN KEDICIOGLU")
    print("="*80)
    print("✅ APPROACH: Follow referrers links from Patient referral source type")
    print("✅ STEP 1: Get Patient referral source type with complete structure")
    print("✅ STEP 2: Follow referrers links if available")
    print("✅ STEP 3: Test alternative referrers endpoints")
    print("✅ GOAL: Find Bronwyn's referrer score efficiently")
    print("="*80)
    
    # Step 1: Get referral source type with links
    ref_type, referrers_url = get_referral_source_type_with_links()
    
    # Step 2: Test referrers endpoint if available
    referrer_score = 0
    if referrers_url:
        score = test_referrers_endpoint(referrers_url)
        if score is not None:
            referrer_score = score
    
    # Step 3: Test alternative endpoints
    alternative_data = test_alternative_referrers_endpoints()
    
    # Final results
    print(f"\n🎯 FINAL TEST RESULTS:")
    print("="*80)
    
    if referrer_score > 0:
        print(f"✅ BRONWYN'S REFERRER SCORE: {referrer_score}")
        print(f"✅ METHOD: Referrers links endpoint")
        print(f"🎉 SUCCESS: Found efficient way to calculate referrer scores!")
    elif alternative_data:
        print(f"✅ ALTERNATIVE DATA FOUND")
        print(f"🔍 May contain referrer information")
    else:
        print(f"⚠️ BRONWYN'S REFERRER SCORE: 0")
        print(f"🔍 No referrers links or alternative endpoints worked")
    
    # Save results
    results = {
        'extraction_date': datetime.now(AEST).isoformat(),
        'bronwyn_patient_id': BRONWYN_PATIENT_ID,
        'patient_type_id': PATIENT_TYPE_ID,
        'referral_source_type_structure': ref_type,
        'referrers_url': referrers_url,
        'referrer_score': referrer_score,
        'alternative_data': alternative_data,
        'method': 'Referrers links comprehensive test'
    }
    
    filename = f"bronwyn_referrer_score_referrers_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"🎉 COMPREHENSIVE TEST COMPLETE!")

if __name__ == "__main__":
    main()
