#!/usr/bin/env python3
"""
REFERRER SCORE TEST - COMPREHENSIVE REFERRAL SOURCES ENDPOINT ANALYSIS
Testing GET /referral_sources endpoint for efficient referrer score calculation
Following official Cliniko Referral Sources documentation
Examining actual referral records and filtering capabilities
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

# Known patient IDs for testing
BRONWYN_PATIENT_ID = "1707655488738428562"
SAMI_PATIENT_ID = "1104221"

def get_auth_header(api_key):
    """Create proper Cliniko API authentication header"""
    credentials = f"{api_key}:"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"

def test_referral_sources_endpoint():
    """Test the main /referral_sources endpoint"""
    print("🔍 STEP 1: TEST REFERRAL SOURCES ENDPOINT")
    print("="*70)
    print(f"✅ Endpoint: GET /referral_sources")
    print(f"✅ Following: Official Cliniko Referral Sources documentation")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    try:
        # Test basic endpoint
        response = requests.get(
            f"{BASE_URL}/referral_sources",
            headers=headers
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Successfully retrieved referral sources")
            print(f"\n📋 API RESPONSE STRUCTURE:")
            print(f"   Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Look for referral sources list
            referral_sources = []
            if isinstance(data, dict):
                for key in ['referral_sources', 'data', 'sources']:
                    if key in data and isinstance(data[key], list):
                        referral_sources = data[key]
                        print(f"   🎯 FOUND REFERRAL SOURCES: {len(referral_sources)} items in '{key}' field")
                        break
            
            if referral_sources:
                print(f"\n📋 FIRST 5 REFERRAL SOURCES:")
                for i, source in enumerate(referral_sources[:5]):
                    print(f"   {i+1}. {json.dumps(source, indent=6)}")
                    
                # Look for referrer information
                referrer_fields = []
                for source in referral_sources[:10]:
                    if isinstance(source, dict):
                        for key in source.keys():
                            if 'referrer' in key.lower() or 'patient' in key.lower():
                                if key not in referrer_fields:
                                    referrer_fields.append(key)
                
                if referrer_fields:
                    print(f"\n🎯 REFERRER-RELATED FIELDS FOUND: {referrer_fields}")
                else:
                    print(f"\n⚠️ No obvious referrer fields found")
                    
            else:
                print(f"\n⚠️ No referral sources list found in response")
                print(f"📋 Complete Response: {json.dumps(data, indent=2)}")
                
            return data
            
        elif response.status_code == 404:
            print(f"❌ ERROR 404: Referral sources endpoint not found")
            print(f"⚠️ This endpoint may not exist in your Cliniko account")
            return None
        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def test_referral_sources_filtering():
    """Test filtering capabilities on referral sources endpoint"""
    print(f"\n🔍 STEP 2: TEST REFERRAL SOURCES FILTERING")
    print("="*70)
    print(f"✅ Testing various filter parameters for referral sources")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    # Test different potential filters
    test_filters = [
        ('patient_id', SAMI_PATIENT_ID),           # Filter by patient who made referral
        ('referrer_id', SAMI_PATIENT_ID),         # Filter by referrer ID
        ('referred_patient_id', BRONWYN_PATIENT_ID), # Filter by who was referred
        ('source_patient_id', SAMI_PATIENT_ID),   # Alternative patient field
        ('id', '>0'),                             # Basic ID filter
        ('created_at', '>2020-01-01T00:00:00Z'),  # Date filter
        ('updated_at', '>2020-01-01T00:00:00Z'),  # Updated date filter
    ]
    
    successful_filters = []
    
    for filter_name, filter_value in test_filters:
        try:
            print(f"\n📡 Testing filter: {filter_name}:{filter_value}")
            
            filter_params = {
                'q[]': f'{filter_name}:{filter_value}'
            }
            
            response = requests.get(
                f"{BASE_URL}/referral_sources",
                headers=headers,
                params=filter_params
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Count results
                count = 0
                if isinstance(data, dict):
                    for key in ['referral_sources', 'data', 'sources']:
                        if key in data and isinstance(data[key], list):
                            count = len(data[key])
                            break
                
                print(f"✅ SUCCESS: Found {count} referral sources with {filter_name}:{filter_value}")
                successful_filters.append((filter_name, filter_value, count))
                
                # Show sample results if any
                if count > 0 and isinstance(data, dict):
                    for key in ['referral_sources', 'data', 'sources']:
                        if key in data and isinstance(data[key], list) and data[key]:
                            sample = data[key][0]
                            print(f"   📋 Sample: {json.dumps(sample, indent=6)}")
                            break
                            
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', response.text)
                print(f"❌ ERROR 400: {error_msg}")
            elif response.status_code == 404:
                print(f"❌ ERROR 404: Endpoint not found")
            else:
                print(f"❌ ERROR {response.status_code}: {response.text}")
                
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            
    return successful_filters

def test_individual_patient_referral_source():
    """Test individual patient referral source endpoint"""
    print(f"\n🔍 STEP 3: TEST INDIVIDUAL PATIENT REFERRAL SOURCE")
    print("="*70)
    print(f"✅ Testing GET /patients/{{patient_id}}/referral_source")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    test_patients = [
        (SAMI_PATIENT_ID, "Sami Karam"),
        (BRONWYN_PATIENT_ID, "Bronwyn Kedicioglu")
    ]
    
    patient_referral_data = []
    
    for patient_id, patient_name in test_patients:
        try:
            print(f"\n📋 TESTING: {patient_name} (ID: {patient_id})")
            
            # Test individual patient referral source
            response = requests.get(
                f"{BASE_URL}/patients/{patient_id}/referral_source",
                headers=headers
            )
            
            print(f"   📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS: Retrieved referral source data")
                print(f"   📋 Response: {json.dumps(data, indent=6)}")
                
                patient_referral_data.append({
                    'patient_id': patient_id,
                    'patient_name': patient_name,
                    'referral_source_data': data
                })
                
            elif response.status_code == 404:
                print(f"   ❌ ERROR 404: No referral source found or endpoint doesn't exist")
            else:
                print(f"   ❌ ERROR {response.status_code}: {response.text}")
                
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            
    return patient_referral_data

def search_for_referrals_by_patient():
    """Search for patients who have been referred by our test patients"""
    print(f"\n🔍 STEP 4: SEARCH FOR REFERRALS BY PATIENT")
    print("="*70)
    print(f"✅ Searching for patients referred by Sami and Bronwyn")
    
    headers = {
        'Authorization': get_auth_header(API_KEY),
        'Accept': 'application/json',
        'User-Agent': 'RatedApp Patient Behavior System'
    }
    
    # Search patients for referral source mentions
    try:
        print(f"\n📡 Searching patients for referral source data...")
        
        # Get patients with pagination to search for referral sources
        page = 1
        referral_matches = []
        
        while page <= 5:  # Limit to first 5 pages for testing
            print(f"   📄 Checking page {page}...")
            
            response = requests.get(
                f"{BASE_URL}/patients",
                headers=headers,
                params={'page': page, 'per_page': 50}
            )
            
            if response.status_code == 200:
                data = response.json()
                patients = data.get('patients', [])
                
                if not patients:
                    print(f"   ⚠️ No more patients found on page {page}")
                    break
                
                # Search for referral source mentions
                for patient in patients:
                    referral_source = patient.get('referral_source', '')
                    
                    if referral_source and isinstance(referral_source, str):
                        # Look for Sami or Bronwyn mentions
                        if 'sami' in referral_source.lower() or 'karam' in referral_source.lower():
                            referral_matches.append({
                                'referred_patient': f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                                'referred_patient_id': patient.get('id'),
                                'referral_source': referral_source,
                                'referrer': 'Sami Karam'
                            })
                            print(f"   🎯 FOUND SAMI REFERRAL: {patient.get('first_name', '')} {patient.get('last_name', '')}")
                            
                        elif 'bronwyn' in referral_source.lower() or 'kedicioglu' in referral_source.lower():
                            referral_matches.append({
                                'referred_patient': f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                                'referred_patient_id': patient.get('id'),
                                'referral_source': referral_source,
                                'referrer': 'Bronwyn Kedicioglu'
                            })
                            print(f"   🎯 FOUND BRONWYN REFERRAL: {patient.get('first_name', '')} {patient.get('last_name', '')}")
                
                page += 1
                time.sleep(0.5)  # Rate limiting
                
            else:
                print(f"   ❌ ERROR {response.status_code}: {response.text}")
                break
                
        return referral_matches
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return []

def main():
    """Main comprehensive test function"""
    print("🚀 STARTING COMPREHENSIVE REFERRAL SOURCES ANALYSIS")
    print("📋 Following official Cliniko Referral Sources documentation")
    print(f"📅 Test Date: {datetime.now(AEST).strftime('%Y-%m-%d %H:%M:%S AEST')}")
    print("🎯 REFERRER SCORE TEST - REFERRAL SOURCES ENDPOINT")
    print("="*80)
    print("✅ APPROACH: Test /referral_sources endpoint for efficient referrer scoring")
    print("✅ STEP 1: Test basic /referral_sources endpoint")
    print("✅ STEP 2: Test filtering capabilities on referral sources")
    print("✅ STEP 3: Test individual patient referral source endpoints")
    print("✅ STEP 4: Search for actual referrals by our test patients")
    print("✅ GOAL: Determine if referrer scores can be calculated efficiently")
    print("="*80)
    
    # Step 1: Test basic referral sources endpoint
    referral_sources_data = test_referral_sources_endpoint()
    
    # Step 2: Test filtering capabilities
    successful_filters = test_referral_sources_filtering()
    
    # Step 3: Test individual patient referral source
    patient_referral_data = test_individual_patient_referral_source()
    
    # Step 4: Search for referrals by patient
    referral_matches = search_for_referrals_by_patient()
    
    # Final comprehensive results
    print(f"\n🎯 FINAL COMPREHENSIVE RESULTS:")
    print("="*80)
    
    # Analyze results
    endpoint_exists = referral_sources_data is not None
    filtering_works = len(successful_filters) > 0
    individual_endpoints_work = len(patient_referral_data) > 0
    referrals_found = len(referral_matches) > 0
    
    print(f"📊 REFERRAL SOURCES ENDPOINT EXISTS: {endpoint_exists}")
    print(f"📊 FILTERING CAPABILITIES: {len(successful_filters)} working filters")
    print(f"📊 INDIVIDUAL PATIENT ENDPOINTS: {len(patient_referral_data)} successful")
    print(f"📊 ACTUAL REFERRALS FOUND: {len(referral_matches)}")
    
    # Calculate referrer scores
    sami_referrer_score = len([r for r in referral_matches if r['referrer'] == 'Sami Karam'])
    bronwyn_referrer_score = len([r for r in referral_matches if r['referrer'] == 'Bronwyn Kedicioglu'])
    
    print(f"\n🎯 REFERRER SCORES:")
    print(f"   Sami Karam: {sami_referrer_score}")
    print(f"   Bronwyn Kedicioglu: {bronwyn_referrer_score}")
    
    if referrals_found:
        print(f"\n📋 REFERRAL DETAILS:")
        for match in referral_matches:
            print(f"   ✅ {match['referred_patient']} referred by {match['referrer']}")
            print(f"      Referral Source: {match['referral_source']}")
    
    # Determine efficiency
    if endpoint_exists and filtering_works:
        efficiency_rating = "HIGH"
        recommendation = "Implement referrer scores using discovered filtering"
    elif endpoint_exists and individual_endpoints_work:
        efficiency_rating = "MEDIUM"
        recommendation = "Implement referrer scores using individual patient endpoints"
    elif referrals_found:
        efficiency_rating = "LOW"
        recommendation = "Implement referrer scores using patient search (slow but functional)"
    else:
        efficiency_rating = "NOT FEASIBLE"
        recommendation = "Remove referrer scores from 11-category system"
    
    print(f"\n📊 EFFICIENCY ANALYSIS:")
    print(f"   Rating: {efficiency_rating}")
    print(f"   Recommendation: {recommendation}")
    
    # Save comprehensive results
    results = {
        'extraction_date': datetime.now(AEST).isoformat(),
        'test_patients': {
            'sami_patient_id': SAMI_PATIENT_ID,
            'bronwyn_patient_id': BRONWYN_PATIENT_ID
        },
        'endpoint_analysis': {
            'referral_sources_endpoint_exists': endpoint_exists,
            'referral_sources_data': referral_sources_data,
            'successful_filters': successful_filters,
            'individual_patient_data': patient_referral_data
        },
        'referral_matches': referral_matches,
        'referrer_scores': {
            'sami_karam': sami_referrer_score,
            'bronwyn_kedicioglu': bronwyn_referrer_score
        },
        'efficiency_analysis': {
            'rating': efficiency_rating,
            'recommendation': recommendation,
            'filtering_works': filtering_works,
            'individual_endpoints_work': individual_endpoints_work
        },
        'method': 'Comprehensive referral sources endpoint analysis'
    }
    
    filename = f"comprehensive_referral_sources_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"🎉 COMPREHENSIVE REFERRAL SOURCES ANALYSIS COMPLETE!")
    
    # Final recommendations
    print(f"\n📋 FINAL RECOMMENDATIONS:")
    print("="*80)
    
    if efficiency_rating == "HIGH":
        print(f"✅ BREAKTHROUGH: Referrer scores can be calculated EFFICIENTLY!")
        print(f"✅ Method: Use /referral_sources endpoint with server-side filtering")
        print(f"✅ Implementation: Single API call per patient for referrer score")
        print(f"✅ Next step: Integrate into main patient behavior extraction system")
        print(f"✅ Keep 11-category patient rating system")
        
    elif efficiency_rating == "MEDIUM":
        print(f"✅ PARTIAL SUCCESS: Referrer scores can be calculated with moderate efficiency")
        print(f"✅ Method: Use individual patient referral source endpoints")
        print(f"✅ Implementation: 1-2 API calls per patient for referrer score")
        print(f"✅ Next step: Implement with caching for better performance")
        print(f"✅ Keep 11-category patient rating system")
        
    elif efficiency_rating == "LOW":
        print(f"⚠️ LIMITED SUCCESS: Referrer scores possible but inefficient")
        print(f"⚠️ Method: Patient search through referral_source field")
        print(f"⚠️ Implementation: Multiple API calls, slower performance")
        print(f"💡 Recommendation: Consider removing referrer scores for better performance")
        print(f"💡 Alternative: Keep 10-category system for speed")
        
    else:
        print(f"❌ NO EFFICIENT METHOD FOUND: Referrer scores not feasible")
        print(f"❌ Recommendation: Remove referrer scores from system")
        print(f"✅ Focus on 10-category patient rating system")
        print(f"✅ Maintain fast, scalable performance")
    
    print(f"\n🎯 NEXT ACTIONS:")
    if efficiency_rating in ["HIGH", "MEDIUM"]:
        print(f"1. ✅ Implement referrer score calculation using discovered method")
        print(f"2. ✅ Test referrer score calculation for multiple patients")
        print(f"3. ✅ Integrate into main patient behavior extraction system")
        print(f"4. ✅ Finalize 11-category patient rating system")
        print(f"5. ✅ Deploy comprehensive patient behavior analysis")
    else:
        print(f"1. 🔄 Finalize 10-category patient rating system (recommended)")
        print(f"2. ✅ Focus on optimizing existing behavior categories")
        print(f"3. ✅ Deploy efficient patient behavior analysis")
        print(f"4. 💡 Consider alternative referral tracking methods in future")

if __name__ == "__main__":
    main()
