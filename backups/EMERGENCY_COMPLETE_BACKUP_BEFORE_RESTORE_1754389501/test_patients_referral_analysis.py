#!/usr/bin/env python3
"""
REFERRER SCORE TEST - BRONWYN KEDICIOGLU
Testing /patients endpoint for referral information
Following referrers.links.self discovery from Patient referral source type
Examining patient records for referral-related fields
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
PATIENTS_ENDPOINT = "https://api.au1.cliniko.com/v1/patients"  # From referrers.links.self

def get_auth_header(api_key):
    """Create proper Cliniko API authentication header"""
    credentials = f"{api_key}:"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"

def examine_bronwyn_patient_record():
    """Examine Bronwyn's patient record for referral information"""
    print("🔍 STEP 1: EXAMINE BRONWYN'S PATIENT RECORD")
    print("="*70)
    print(f"✅ Bronwyn's Patient ID: {BRONWYN_PATIENT_ID}")
    print(f"✅ Following: referrers.links.self from Patient referral source type")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    try:
        # Get Bronwyn's complete patient record
        response = requests.get(
            f"{BASE_URL}/patients/{BRONWYN_PATIENT_ID}",
            headers=headers
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            patient = data.get('patient', {})
            
            print(f"✅ Successfully retrieved Bronwyn's patient record")
            print(f"\n📋 COMPLETE PATIENT RECORD:")
            print(json.dumps(data, indent=2))
            
            # Look for referral-related fields
            referral_fields = []
            potential_referral_keys = [
                'referrals', 'referrals_made', 'referred_patients', 'referrer',
                'referrer_id', 'referral_source', 'referral_count', 'referring_patients',
                'patient_referrals', 'made_referrals', 'referral_history'
            ]
            
            print(f"\n🔍 SEARCHING FOR REFERRAL FIELDS:")
            for key in potential_referral_keys:
                if key in patient:
                    referral_fields.append((key, patient[key]))
                    print(f"   ✅ FOUND: {key} = {patient[key]}")
            
            if not referral_fields:
                print(f"   ⚠️ No obvious referral fields found in patient record")
                
            # Check links for referral-related endpoints
            links = patient.get('links', {})
            if links:
                print(f"\n🔗 PATIENT LINKS:")
                for link_name, link_url in links.items():
                    print(f"   {link_name}: {link_url}")
                    
                    # Look for referral-related links
                    if any(ref_word in link_name.lower() for ref_word in ['referral', 'refer']):
                        print(f"   🎯 POTENTIAL REFERRAL LINK: {link_name}")
                        
            return patient, referral_fields
            
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return None, []
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None, []

def test_patients_endpoint_filtering():
    """Test filtering patients endpoint for referral information"""
    print(f"\n🔍 STEP 2: TEST PATIENTS ENDPOINT FILTERING")
    print("="*70)
    print(f"✅ Endpoint: {PATIENTS_ENDPOINT}")
    print(f"✅ Testing various referral-related filters")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    # Test different referral-related filters
    test_filters = [
        ('referrer_id', BRONWYN_PATIENT_ID),
        ('referral_source', 'Patient'),
        ('referred_by', BRONWYN_PATIENT_ID),
        ('referrer', BRONWYN_PATIENT_ID),
        ('referral_source_id', '37606'),  # Patient referral source type ID
    ]
    
    successful_filters = []
    
    for filter_name, filter_value in test_filters:
        try:
            print(f"\n📡 Testing filter: {filter_name}:{filter_value}")
            
            filter_params = {
                'q[]': f'{filter_name}:{filter_value}'
            }
            
            response = requests.get(
                PATIENTS_ENDPOINT,
                headers=headers,
                params=filter_params
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                patients = data.get('patients', [])
                print(f"✅ SUCCESS: Found {len(patients)} patients with {filter_name}:{filter_value}")
                
                if patients:
                    successful_filters.append((filter_name, filter_value, len(patients)))
                    
                    # Show first few results
                    for i, patient in enumerate(patients[:3]):
                        name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
                        print(f"   📋 Patient {i+1}: {name} (ID: {patient.get('id')})")
                        
                        # Look for referral source information
                        if patient.get('referral_source'):
                            print(f"      Referral Source: {patient['referral_source']}")
                            
            elif response.status_code == 400:
                error_msg = response.json().get('message', response.text)
                print(f"❌ ERROR 400: {error_msg}")
                if 'not filterable' in error_msg.lower():
                    print(f"   ⚠️ {filter_name} is not filterable")
            else:
                print(f"❌ ERROR {response.status_code}: {response.text}")
                
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            
    return successful_filters

def search_patients_for_referral_source():
    """Search patients with referral_source containing referrer information"""
    print(f"\n🔍 STEP 3: SEARCH PATIENTS BY REFERRAL SOURCE")
    print("="*70)
    print(f"✅ Looking for patients with referral_source data")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    try:
        # Get patients with pagination to find referral source examples
        response = requests.get(
            f"{PATIENTS_ENDPOINT}?per_page=50",
            headers=headers
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            patients = data.get('patients', [])
            
            print(f"✅ Retrieved {len(patients)} patients")
            
            # Look for patients with referral_source data
            referral_source_examples = []
            bronwyn_referrals = []
            
            for patient in patients:
                referral_source = patient.get('referral_source')
                if referral_source:
                    referral_source_examples.append({
                        'patient_id': patient.get('id'),
                        'name': f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                        'referral_source': referral_source
                    })
                    
                    # Check if referral source mentions Bronwyn
                    if isinstance(referral_source, dict):
                        # Check for referrer_id in referral_source
                        if referral_source.get('referrer_id') == BRONWYN_PATIENT_ID:
                            bronwyn_referrals.append(patient)
                            print(f"🎯 FOUND BRONWYN REFERRAL: {patient.get('first_name')} {patient.get('last_name')}")
                            
                    elif isinstance(referral_source, str):
                        # Check for Bronwyn's name in referral source string
                        if 'bronwyn' in referral_source.lower() or 'kedicioglu' in referral_source.lower():
                            bronwyn_referrals.append(patient)
                            print(f"🎯 FOUND BRONWYN REFERRAL: {patient.get('first_name')} {patient.get('last_name')}")
            
            print(f"\n📋 REFERRAL SOURCE EXAMPLES ({len(referral_source_examples)} found):")
            for i, example in enumerate(referral_source_examples[:10]):
                print(f"   {i+1}. {example['name']} (ID: {example['patient_id']})")
                print(f"      Referral Source: {example['referral_source']}")
                
            print(f"\n🎯 BRONWYN'S REFERRALS: {len(bronwyn_referrals)}")
            if bronwyn_referrals:
                for referral in bronwyn_referrals:
                    name = f"{referral.get('first_name', '')} {referral.get('last_name', '')}"
                    print(f"   ✅ {name} (ID: {referral.get('id')})")
                    print(f"      Referral Source: {referral.get('referral_source')}")
                    
            return len(bronwyn_referrals), bronwyn_referrals
            
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return 0, []
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return 0, []

def main():
    """Main test function"""
    print("🚀 STARTING PATIENTS ENDPOINT REFERRAL ANALYSIS")
    print("📋 Following referrers.links.self discovery from Patient referral source type")
    print(f"📅 Test Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🎯 REFERRER SCORE TEST - BRONWYN KEDICIOGLU")
    print("="*80)
    print("✅ BREAKTHROUGH: referrers field points to /patients endpoint")
    print("✅ STEP 1: Examine Bronwyn's patient record for referral fields")
    print("✅ STEP 2: Test patients endpoint filtering for referral data")
    print("✅ STEP 3: Search patients for referral_source containing Bronwyn")
    print("✅ GOAL: Find efficient way to calculate referrer scores")
    print("="*80)
    
    # Step 1: Examine Bronwyn's patient record
    patient_record, referral_fields = examine_bronwyn_patient_record()
    
    # Step 2: Test patients endpoint filtering
    successful_filters = test_patients_endpoint_filtering()
    
    # Step 3: Search patients for referral source data
    referrer_score, bronwyn_referrals = search_patients_for_referral_source()
    
    # Final results
    print(f"\n🎯 FINAL TEST RESULTS:")
    print("="*80)
    
    if referrer_score > 0:
        print(f"✅ BRONWYN'S REFERRER SCORE: {referrer_score}")
        print(f"✅ METHOD: Patients endpoint referral_source search")
        print(f"🎉 SUCCESS: Found {referrer_score} patient(s) referred by Bronwyn!")
        
        for referral in bronwyn_referrals:
            name = f"{referral.get('first_name', '')} {referral.get('last_name', '')}"
            print(f"   📋 Referred Patient: {name}")
            
    elif successful_filters:
        print(f"✅ SUCCESSFUL FILTERS FOUND: {len(successful_filters)}")
        for filter_name, filter_value, count in successful_filters:
            print(f"   📋 {filter_name}:{filter_value} = {count} patients")
        print(f"🔍 May need to explore these filters further")
        
    elif referral_fields:
        print(f"✅ REFERRAL FIELDS FOUND IN BRONWYN'S RECORD: {len(referral_fields)}")
        for field_name, field_value in referral_fields:
            print(f"   📋 {field_name}: {field_value}")
        print(f"🔍 May contain referral information")
        
    else:
        print(f"⚠️ BRONWYN'S REFERRER SCORE: 0")
        print(f"🔍 No referral information found in patients endpoint")
        print(f"💡 May need to explore referral_sources endpoint with different approach")
    
    # Save results
    results = {
        'extraction_date': datetime.now(AEST).isoformat(),
        'bronwyn_patient_id': BRONWYN_PATIENT_ID,
        'patients_endpoint': PATIENTS_ENDPOINT,
        'patient_record': patient_record,
        'referral_fields': referral_fields,
        'successful_filters': successful_filters,
        'referrer_score': referrer_score,
        'bronwyn_referrals': bronwyn_referrals,
        'method': 'Patients endpoint referral analysis'
    }
    
    filename = f"bronwyn_referrer_score_patients_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"🎉 PATIENTS ENDPOINT ANALYSIS COMPLETE!")

if __name__ == "__main__":
    main()

